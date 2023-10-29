class Response:
    OK = 200
    FAIL_PACKAGE = 500

    def __init__(self, status_code, msg, size_bytes=4):
        self.status_code = status_code
        self.msg = msg
        self.size_bytes = size_bytes

    def __repr__(self):
        return f'Status code: {self.status_code}; Msg: {self.msg}'

    @staticmethod
    def deserialize(value, size_bytes):
        status_code = int.from_bytes(value[:size_bytes], 'big')
        msg = int.from_bytes(value[size_bytes:2 * size_bytes], 'big')

        response = Response(status_code, msg, size_bytes)
        return response
