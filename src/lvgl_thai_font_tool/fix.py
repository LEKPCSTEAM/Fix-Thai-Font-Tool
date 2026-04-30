"""
fix.py — แก้ Thai mark positions ใน TTF สำหรับ LVGL (ไม่มี shaping engine)
เลื่อน Level-2 marks (วรรณยุกต์ / thanthakat / nikhahit) ขึ้นเพื่อไม่ซ้อน Level-1
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

# Level 1 — ชิดบนพยัญชนะ ไม่ขยับ
LEVEL1: dict[int, str] = {
    0x0E31: "ั",
    0x0E34: "ิ",
    0x0E35: "ี",
    0x0E36: "ึ",
    0x0E37: "ื",
    0x0E47: "็",
}

# Level 2 — เลื่อนขึ้นให้อยู่เหนือ Level 1
LEVEL2: dict[int, str] = {
    0x0E48: "่",
    0x0E49: "้",
    0x0E4A: "๊",
    0x0E4B: "๋",
    0x0E4C: "์",
    0x0E4D: "ํ",
}


def _y_range(glyf_table, name: str) -> tuple[int | None, int | None]:
    g = glyf_table[name]
    if g.isComposite() or g.numberOfContours <= 0:
        return None, None
    coords = list(g.coordinates)
    y_vals = [y for _, y in coords]
    return min(y_vals), max(y_vals)


def _shift(glyf_table, name: str, dy: int) -> None:
    g = glyf_table[name]
    if g.isComposite():
        for comp in g.components:
            comp.y += dy
    elif g.numberOfContours > 0:
        arr = np.array(g.coordinates, dtype=np.int32)
        arr[:, 1] += dy
        g.coordinates = GlyphCoordinates(arr)
        g.recalcBounds(glyf_table)


def print_info(font: TTFont) -> None:
    cmap = font.getBestCmap()
    glyf_table = font["glyf"]
    upm = font["head"].unitsPerEm
    thai_count = sum(1 for cp in cmap if 0x0E00 <= cp <= 0x0E7F)

    print(f"UPM        : {upm}")
    print(f"Has GPOS   : {'GPOS' in font}")
    print(f"Thai glyphs: {thai_count}")

    print("\nLevel-1 marks (ไม่ขยับ):")
    for cp, ch in LEVEL1.items():
        name = cmap.get(cp)
        if name:
            ymin, ymax = _y_range(glyf_table, name)
            if ymin is not None:
                print(f"  U+{cp:04X} {ch}  yMin={ymin:6d}  yMax={ymax:6d}")

    print("\nLevel-2 marks (จะถูกเลื่อนขึ้น):")
    for cp, ch in LEVEL2.items():
        name = cmap.get(cp)
        if name:
            ymin, ymax = _y_range(glyf_table, name)
            if ymin is not None:
                print(f"  U+{cp:04X} {ch}  yMin={ymin:6d}  yMax={ymax:6d}")


def fix_font(input_path: Path, output_path: Path, shift: int) -> None:
    font = TTFont(str(input_path))
    cmap = font.getBestCmap()
    glyf_table = font["glyf"]
    upm = font["head"].unitsPerEm
    dy = int(shift * upm / 1000)

    print(f"Font  : {input_path.name}")
    print(f"UPM   : {upm}  →  shift = {dy} units")
    print()

    for cp, ch in LEVEL2.items():
        name = cmap.get(cp)
        if not name:
            print(f"  ⚠  U+{cp:04X} {ch} ไม่พบใน font")
            continue
        _shift(glyf_table, name, dy)
        print(f"  ✓  U+{cp:04X} {ch} ({name})  +{dy}")

    font.save(str(output_path))
    print(f"\nSaved → {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fix-thai",
        description="แก้ Thai mark positions ใน TTF สำหรับ LVGL",
    )
    parser.add_argument("input", help="ไฟล์ TTF ต้นฉบับ")
    parser.add_argument("-o", "--output", help="ไฟล์ output (default: <name>_fixed.ttf)")
    parser.add_argument(
        "--shift",
        type=int,
        default=220,
        metavar="UNITS",
        help="units ที่เลื่อน Level-2 marks (scale ตาม UPM, default: 220)",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="แสดงข้อมูล font เฉยๆ ไม่แก้ไข",
    )
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"Error: ไม่พบไฟล์ {input_path}", file=sys.stderr)
        sys.exit(1)

    if args.info:
        print_info(TTFont(str(input_path)))
        return

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_path.parent / f"{input_path.stem}_fixed{input_path.suffix}"
    )
    fix_font(input_path, output_path, args.shift)
