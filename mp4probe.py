import struct
import sys
from argparse import ArgumentParser

BOX_SIZE = 8


def find_boxes(f, start_offset=0, end_offset=float("inf")):
    """Returns a dictionary of all the data boxes and their absolute starting
    and ending offsets inside the mp4 file.

    Specify a start_offset and end_offset to read sub-boxes.
    """
    s = struct.Struct("> I 4s")
    boxes = {}
    offset = start_offset
    f.seek(offset, 0)
    while offset < end_offset:
        data = f.read(BOX_SIZE)  # read box header
        if data == b"": break  # EOF
        length, text = s.unpack(data)
        if length == 1:
            # f.seek(BOX_SIZE, 1)  # skip to next box
            data = f.read(BOX_SIZE)  # read box header
            if data == b"": break  # EOF
            nilLength, length = struct.unpack(">II", data)
            if nilLength != 0:
                break
            length = length - BOX_SIZE
        f.seek(length - BOX_SIZE, 1)  # skip to next box

        boxes[text] = (offset, offset + length)
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

    print("Duration (sec):", duration / timescale)


def examine_mp4(filename: str):
    print("Examining:", filename)

    with open(filename, "rb") as f:
        boxes = find_boxes(f)
        print(boxes)

        # Sanity check that this really is a movie file.
        assert (boxes[b"ftyp"][0] == 0)

        moov_boxes = find_boxes(f, boxes[b"moov"][0] + BOX_SIZE, boxes[b"moov"][1])
        print(moov_boxes)

        trak_boxes = find_boxes(f, moov_boxes[b"trak"][0] + BOX_SIZE, moov_boxes[b"trak"][1])
        print(trak_boxes)

        udta_boxes = find_boxes(f, moov_boxes[b"udta"][0] + BOX_SIZE, moov_boxes[b"udta"][1])
        print(udta_boxes)

        scan_mvhd(f, moov_boxes[b"mvhd"][0])


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
