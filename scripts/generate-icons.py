#!/usr/bin/env python3
"""Generate PNG icons for the Chrome extension."""
import struct
import zlib
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
EXT_ICONS_DIR = os.path.join(PROJECT_DIR, "extension", "icons")
os.makedirs(EXT_ICONS_DIR, exist_ok=True)

def create_png(size, r, g, b):
    def make_chunk(chunk_type, data):
        chunk = chunk_type + data
        return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)

    raw = b""
    cx, cy = size / 2, size / 2
    radius = size / 2
    for y in range(size):
        raw += b"\x00"
        for x in range(size):
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist < radius:
                raw += struct.pack("BBBB", r, g, b, 255)
            else:
                raw += struct.pack("BBBB", 0, 0, 0, 0)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = make_chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    idat = make_chunk(b"IDAT", zlib.compress(raw))
    iend = make_chunk(b"IEND", b"")
    return header + ihdr + idat + iend

for size in [16, 48, 128]:
    png_data = create_png(size, 99, 102, 241)
    path = os.path.join(EXT_ICONS_DIR, f"icon-{size}.png")
    with open(path, "wb") as f:
        f.write(png_data)
    print(f"  Created {path} ({size}x{size})")

print(f"\nExtension icons ready in: {EXT_ICONS_DIR}")
