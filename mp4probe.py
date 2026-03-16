import os
import struct
import sys
from argparse import ArgumentParser
from typing import List

from mp4analyzer import MP4Box, parse_mp4_boxes
from mp4analyzer.boxes import FileTypeBox, MovieBox, MovieHeaderBox, MetaBox, UserDataBox


def printable_only(data: bytes):
    r = ""
    for b in data:
        if b >= 0x32 and b < 0x7e:
            r += chr(b)
        else:
            r += "."
    return r


def find_meta(box: MP4Box):
    for child in box.children:
        if isinstance(child, MovieHeaderBox):
            meta = find_meta(child)
            if meta:
                return meta
        elif isinstance(child, UserDataBox):
            meta = find_meta(child)
            if meta:
                return meta
        else:
            if isinstance(child, MetaBox):
                return printable_only(child.data)
    return ""


class Boxes:
    def __init__(self, boxes: List[MP4Box]):
        self.boxes = boxes

    def __str__(self) -> str:
        r = ""
        meta = []
        for box in self.boxes:
            s = box.type
            if isinstance(box, FileTypeBox):
                s += ":[" + box.major_brand + ",".join(box.compatible_brands) + "]"
            if isinstance(box, MovieBox):
                meta.append("[" + find_meta(box) + "]")
            if r != "":
                r += " / "
            r += s
        if meta != []:
            r += " / meta:[" + ",".join(meta) + "]"
        return r

        return r


class Mp4File:
    def __init__(self):
        self.name = None
        self.boxes = None

    def __str__(self) -> str:
        return self.name + ": " + self.boxes.__str__()

    def open(self, filename: str) -> Mp4File:
        self.name = filename
        self.boxes = Boxes(parse_mp4_boxes(filename))

        return self


def examine_mp4(filename: str):
    f = Mp4File().open(filename)
    print(f)


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
