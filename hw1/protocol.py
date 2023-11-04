import socket
import time

from src.logger import Logger
from src.package import Package
from src.response import Response
from src.segment import Segment


class UDPBasedProtocol:
    def __init__(self, *, local_addr, remote_addr):
        self.udp_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.remote_addr = remote_addr
        self.udp_socket.bind(local_addr)

    def sendto(self, data):
        return self.udp_socket.sendto(data, self.remote_addr)  # возвращает кол-во отправленных байт

    def recvfrom(self, n):
        msg, addr = self.udp_socket.recvfrom(n)  # (что, откуда)
        return msg  # возвращает данные


logger = Logger(f"/logs/{int(time.time())}.log")
logger.print_mode = False
logger.status = True

OK = 200
FAIL_PACKAGE = 500


class MyTCPProtocol(UDPBasedProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.size_segment = 1024
        self.size_add = 4
        self.LIMIT_TRYING = 5

        self.int2byte = lambda x: int.to_bytes(x, self.size_add, 'big')
        self.byte2int = lambda x: int.from_bytes(x, 'big')

    def sendMsg(self, msg):
        request = self.sendto(msg) - 2 * self.size_add
        response_body = self.recvfrom(self.size_add)
        response = Response.deserialize(response_body, self.size_add)

        return request, response

    def send(self, data: bytes):
        logger.info(["OUT", self.remote_addr], f"Data: {data}")
        package = Package(data)
        segments = package.split(self.size_segment, self.size_add)
        sum_bytes = 0

        start = 0
        end = len(segments)

        handshake = self.int2byte(len(segments))
        _, _ = self.sendMsg(handshake)

        approve = []
        while len(approve) != len(segments):
            for i in range(start, end):
                segment = segments[i]
                req_body = segment.serialize()
                logger.warning(["OUT"], str(segment))
                request, response = self.sendMsg(req_body)
                logger.warning(["OUT"], "Response " + str(response))

                if response.status_code != OK:
                    logger.err(["OUT", self.remote_addr], f"Code: {response.status_code}, Msg: {response.msg}")
                    start = i
                    break

                sum_bytes += request
                approve.append(i)

        return sum_bytes

    def recv(self, n: int) -> object:
        handshake = self.recvfrom(self.size_add)
        count_segments = self.byte2int(handshake)
        self.sendto(self.int2byte(OK))
        buffer = []

        sum_bytes = lambda x: sum([len(seg) for seg in x])
        size_step = self.size_segment + 2 * self.size_add
        b_sum = 0
        prev_ack = 0
        while b_sum != n:
            buffer = [b'' for _ in range(count_segments)]

            for i in range(count_segments):
                res = self.recvfrom(size_step)
                segment = Segment.deserialize(res, self.size_add)

                logger.warning(["IN", self.remote_addr], str(segment))
                if segment.seq != prev_ack:
                    logger.err(["IN", self.remote_addr], f"The order is broken: seq={segment.seq} prev_ack={prev_ack}")
                    err_msg = self.int2byte(FAIL_PACKAGE)
                    self.sendto(err_msg)
                    break

                prev_ack = segment.ack
                buffer[i] = segment.data

                logger.warning(["IN"], "Send OK")
                self.sendto(self.int2byte(OK))

            b_sum = sum_bytes(buffer)

        response = b''.join(buffer)

        logger.info(["IN", self.remote_addr], f"Return response: {response}")
        return response
