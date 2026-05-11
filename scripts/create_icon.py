"""Generate the Windows .ico used by Electron and PyInstaller.

The generated icon is intentionally not committed because some PR/review
systems reject binary files. Run this script before development or packaging.
It uses only the Python standard library.
"""

from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_PATH = ROOT / "electron" / "assets" / "icon.ico"
SIZE = 256


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    )


def build_png() -> bytes:
    rows: list[bytes] = []
    for y in range(SIZE):
        row = bytearray([0])
        for x in range(SIZE):
            dx = x - SIZE // 2
            dy = y - SIZE // 2
            radius_squared = dx * dx + dy * dy

            # Simple blue gradient with a light gear-like mark.
            if 2600 < radius_squared < 3600 or radius_squared < 550:
                rgba = (248, 250, 252, 255)
            else:
                rgba = (37 + y // 8, 99 + x // 8, 235, 255)
            row.extend(rgba)
        rows.append(bytes(row))

    raw = b"".join(rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )


def build_ico(png: bytes) -> bytes:
    header = struct.pack("<HHH", 0, 1, 1)
    directory_entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 6 + 16)
    return header + directory_entry + png


def main() -> None:
    ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    ICON_PATH.write_bytes(build_ico(build_png()))
    print(f"Generated {ICON_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
