from .segment import Segment


class Package:
    def __init__(self, data):
        self.data = data
        self.size = len(data)

    def split(self, split_size=8, add_size=4):
        segments = [self.data[i:i + split_size] for i in range(0, self.size, split_size)]
        res = []

        seq = 0
        for i in range(0, len(segments)):
            segment = segments[i]
            ack = seq + len(segment)
            res.append(Segment(seq, ack, segment, add_size))
            seq = ack

        return res

    def __repr__(self):
        return f'Data: {self.data}'

    @staticmethod
    def concatenation(segments):
        data = b''.join([segment.data for segment in segments])

        res = Package(data)
        return res
