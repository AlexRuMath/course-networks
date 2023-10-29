class Segment:
    def __init__(self, seq, ack, data, size_bytes=4):
        self.seq = seq
        self.ack = ack
        self.data = data
        self.size_bytes = size_bytes

    def serialize(self):
        res = int.to_bytes(self.seq, self.size_bytes, 'big') + \
              int.to_bytes(self.ack, self.size_bytes, 'big') + \
              self.data
        return res

    def __repr__(self):
        return f"Seq: {self.seq}; Ack: {self.ack}; Data: {self.data}"

    @staticmethod
    def deserialize(value, size_bytes):
        seq = int.from_bytes(value[:size_bytes], 'big')
        ack = int.from_bytes(value[size_bytes:2 * size_bytes], 'big')
        data = value[2 * size_bytes:]

        segment = Segment(seq, ack, data, size_bytes)
        return segment
