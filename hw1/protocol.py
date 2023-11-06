import logging
import socket
import asyncio
import logging
import time

from aiologger.loggers.json import JsonLogger

MODE = "SYNC"
if MODE == "ASYNC":
    logger = JsonLogger.with_default_handlers(
        name="logger",
    )
else:
    logging.basicConfig(filename=f"/logs/{int(time.time())}.log", filemode="w", level=logging.DEBUG)
    logger = logging


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


class MyTCPProtocol(UDPBasedProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.split_size = 16
        self.size_add_info = 4

        self.int2byte = lambda x: int.to_bytes(x, self.size_add_info, 'big')
        self.byte2int = lambda x: int.from_bytes(x, 'big')

        self.OK = 0
        self.FAIL = 1

    def split_package(self, data):
        segments = [data[i:i + self.split_size] for i in range(0, len(data), self.split_size)]
        seq = 0
        for i in range(len(segments)):
            segment = segments[i]
            ack = seq + len(segment)
            segments[i] = self.int2byte(seq) + self.int2byte(ack) + self.int2byte(i) + segment
            seq = ack

        return segments

    def sendSegment(self, segment):
        bytes_request = self.sendto(segment) - 3 * self.size_add_info
        response = self.recvfrom(self.size_add_info)
        status_code = self.byte2int(response)

        return bytes_request

    def getSegment(self, size, prev_ack):
        request = self.recvfrom(size)

        seq_segment = self.byte2int(request[:self.size_add_info])
        ack_segment = self.byte2int(request[self.size_add_info:2 * self.size_add_info])
        id_segment = self.byte2int(request[2 * self.size_add_info:3 * self.size_add_info])
        data_segment = request[3 * self.size_add_info:]

        return ack_segment, id_segment, data_segment

    def send(self, data: bytes):
        print(f"[OUT] Split data")
        segments = self.split_package(data)

        req = self.sendto(self.int2byte(len(segments)))
        res = self.recvfrom(self.size_add_info)

        response = 0
        for i in range(len(segments)):
            segment = segments[i]
            response += self.sendSegment(segment)

        return response

    def recv(self, n: int) -> object:
        request = self.recvfrom(self.split_size)
        numbers_of_segments = self.byte2int(request)
        buffer_segments = [b'' for _ in range(numbers_of_segments)]
        response = self.sendto(self.int2byte(self.OK))

        ack = 0
        for i in range(numbers_of_segments):
            ack_cur, identity, data = self.getSegment(self.size_add_info * 3 + self.split_size, ack)
            buffer_segments[identity] = data
            ack = ack_cur

        print(f"[IN] {buffer_segments}")
        package = b''.join(buffer_segments)
        if len(package) != n:
            self.sendto(self.int2byte(self.FAIL))
            logger.error(f"Package not equal size: {len(package)} != {n}")

        return package
