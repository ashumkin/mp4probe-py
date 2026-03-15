import os
import struct
import sys
from argparse import ArgumentParser

BOX_SIZE = 8


class Boxes(dict):
    def info(self):
        r = ",".join(self.keys())

        return r


def find_boxes(f, start_offset=0, end_offset=float("inf")):
    """Returns a dictionary of all the data boxes and their absolute starting
    and ending offsets inside the mp4 file.

    Specify a start_offset and end_offset to read sub-boxes.
    """
    s = struct.Struct("> I 4s")
    boxes = Boxes()
    offset = start_offset
    f.seek(offset, 0)
    while offset < end_offset:
        data = f.read(BOX_SIZE)  # read box header
        if data == b"": break  # EOF
        length, text = s.unpack(data)
        if length == 1:
            data = f.read(BOX_SIZE)  # read box header
            if data == b"": break  # EOF
            nilLength, length = struct.unpack(">II", data)
            if nilLength != 0:
                break
            f.seek(length - 2 * BOX_SIZE, 1)  # skip to next box
        else:
            f.seek(length - BOX_SIZE, 1)  # skip to next box

        boxes[text.decode('UTF-8')] = (offset, offset + length)
        offset += length
    return boxes


def scan_mvhd(f, offset):
    f.seek(offset, 0)
    f.seek(8, 1)  # skip box header

    data = f.read(1)  # read version number
    version = int.from_bytes(data, "big")
    word_size = 8 if version == 1 else 4

    f.seek(3, 1)  # skip flags
    f.seek(word_size * 2, 1)  # skip dates

    timescale = int.from_bytes(f.read(4), "big")
    if timescale == 0: timescale = 600

    duration = int.from_bytes(f.read(word_size), "big")

    # print("Duration (sec):", duration / timescale)


class Meta():
    def __init__(self, bytes):
        self.bytes = bytes

    def __str__(self):
        r = ""
        for b in self.bytes:
            if b < 32 or b > 126:
                r += "."
            else:
                r += chr(b)

        return r

def read_meta(f, offset, end_offset):
    f.seek(offset, 0)
    b = f.read(end_offset - offset)

    return Meta(b)


def examine_mp4(filename: str):
    f = Mp4File()
    f.open(filename)
    print(f)


class Mp4File:
    def __init__(self):
        self.name = None
        self.boxes = Boxes()
        self.moov_boxes = None
        self.meta = None

    def __str__(self):
        return self.name + ": " + str(self.boxes.info() + " meta:" + self.meta.__str__())

    def open(self, filename: str):
        self.name = filename
        with open(filename, "rb") as f:
            boxes = find_boxes(f)

            # Sanity check that this really is a movie file.
            if boxes.get("ftyp") is not None:
                if boxes["ftyp"][0] != 0:
                    return

            self.boxes = boxes
            if self.boxes.get("moov") is not None:
                self.moov_boxes = find_boxes(f, self.boxes["moov"][0] + BOX_SIZE, self.boxes["moov"][1])

                if self.moov_boxes.get("meta") is not None:
                    meta = find_boxes(f, self.moov_boxes["meta"][0] + BOX_SIZE, self.moov_boxes["meta"][1])
                    self.meta = Meta(b"moov[meta]:"+bytes(meta.info(), 'ascii'))

                if self.moov_boxes.get("trak") is not None:
                    self.trak_boxes = find_boxes(f, self.moov_boxes["trak"][0] + BOX_SIZE, self.moov_boxes["trak"][1])

                if self.moov_boxes.get("udta") is not None:
                    self.udta_boxes = find_boxes(f, self.moov_boxes["udta"][0] + BOX_SIZE, self.moov_boxes["udta"][1])

                    meta = self.udta_boxes.get("meta")
                    if meta is not None:
                        meta = read_meta(f, meta[0] + BOX_SIZE, meta[1])
                        self.meta = meta

            # scan_mvhd(f, self.moov_self.boxes["mvhd"][0])


def examine_mp4s(filenames: list):
    for filename in filenames:
        examine_mp4(filename)


def main():
    parser = ArgumentParser()
    parser.add_argument("filenames", action="extend", nargs="+", type=str)
    p = parser.parse_args(sys.argv[1:])
    examine_mp4s(p.filenames)


if __name__ == '__main__':
    main()
