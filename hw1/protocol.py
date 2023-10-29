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
logger.warning_mode = True
logger.status = False

OK = 200
FAIL_PACKAGE = 500


class MyTCPProtocol(UDPBasedProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.size_segment = 20
        self.size_add = 4

    def send(self, data: bytes):
        #logger.info(["OUT", self.remote_addr], f"Data: {data}")
        package = Package(data)
        segments = package.split(self.size_segment, self.size_add)
        sum_bytes = 0

        start = 0
        end = len(segments)

        for i in range(start, end):
            segment = segments[i]
            req_body = segment.serialize()
            logger.warning(["OUT"], str(segment))
            request = self.sendto(req_body) - 2 * segment.size_bytes
            response_body = self.recvfrom(self.size_add)
            response = Response.deserialize(response_body, self.size_add)
            logger.warning(["OUT"], "Response " + str(response))

            if response.status_code != OK:
                logger.err(["OUT", self.remote_addr], f"Code: {response.status_code}, Msg: {response.msg}")

            sum_bytes += request

        return sum_bytes

    def recv(self, n: int) -> object:
        buffer = []
        size_step = self.size_segment + 2 * self.size_add

        prev_ack = 0
        while True:
            segment_bytes = self.recvfrom(size_step)
            segment = Segment.deserialize(segment_bytes, self.size_add)

            logger.warning(["IN", self.remote_addr], str(segment))
            if segment.seq != prev_ack:
                logger.err(["IN", self.remote_addr], f"The order is broken: seq={segment.seq} prev_ack={prev_ack}")
                err_msg = int.to_bytes(FAIL_PACKAGE, self.size_add, 'big') + \
                          int.to_bytes(len(buffer), self.size_add, 'big')
                self.sendto(err_msg)

            prev_ack = segment.ack
            buffer.append(segment.data)

            logger.warning(["IN"], "Send OK")
            self.sendto(int.to_bytes(OK, self.size_add, 'big'))

            len_msg = sum([len(segment) for segment in buffer])

            if segment.ack == n and len_msg == n:
                break

        response = b''.join(buffer)

        #logger.info(["IN", self.remote_addr], f"Return response: {response}")
        return response
