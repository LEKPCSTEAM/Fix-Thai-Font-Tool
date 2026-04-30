"""
convert.py — แปลง TTF เป็น LVGL .c font file ด้วย lv_font_conv
ต้องติดตั้ง lv_font_conv ก่อน: npm install -g lv_font_conv
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_OUTPUT_DIR = Path("output")
RANGE_LATIN = "0x20-0x7F"
RANGE_THAI = "0x0E00-0x0E7F"


def _find_lv_font_conv() -> str | None:
    cmd = shutil.which("lv_font_conv")
    if cmd:
        return cmd
    nvm_bin = Path.home() / ".nvm" / "versions"
    if nvm_bin.exists():
        for p in sorted(nvm_bin.rglob("lv_font_conv")):
            return str(p)
    return None


def _stem(path: Path) -> str:
    return path.stem.lower().replace(" ", "_").replace("-", "_")


def convert_one(
    font_path: Path,
    size: int,
    bpp: int,
    ranges: list[str],
    output_dir: Path,
    lv_cmd: str,
) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / f"{_stem(font_path)}_{size}.c"

    cmd = [lv_cmd, "--no-compress", "--bpp",
           str(bpp), "--size", str(size), "--format", "lvgl"]
    for r in ranges:
        cmd += ["--font", str(font_path), "-r", r]
    cmd += ["-o", str(out_file)]

    print(f"  size={size}px  bpp={bpp}  → {out_file.name} ...",
          end=" ", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("FAILED")
        print(result.stderr, file=sys.stderr)
        return None

    kb = out_file.stat().st_size / 1024
    print(f"OK  ({kb:.0f} KB)")
    return out_file


def _print_usage(files: list[Path]) -> None:
    if not files:
        return
    print("\n─── วิธีใช้ใน LVGL ───────────────────────────────────")
    for f in files:
        print(f"LV_FONT_DECLARE({f.stem});")
    ex = files[0].stem
    print(f"""
lv_obj_t *label = lv_label_create(lv_scr_act());
lv_obj_set_style_text_font(label, &{ex}, 0);
lv_label_set_text(label, "สวัสดี Hello น้ำ เที่ยว");""")
    print("──────────────────────────────────────────────────────")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="to-lvgl",
        description="แปลง TTF เป็น LVGL .c font file",
    )
    parser.add_argument("font", help="ไฟล์ TTF")
    parser.add_argument(
        "--size",
        type=int,
        nargs="+",
        default=[20],
        metavar="PX",
        help="ขนาด px (default: 20) รับหลายค่าได้ เช่น --size 16 20 24",
    )
    parser.add_argument(
        "--bpp",
        type=int,
        default=4,
        choices=[1, 2, 4, 8],
        help="Bits per pixel / anti-aliasing (default: 4)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        metavar="DIR",
        help=f"โฟลเดอร์ output (default: ./{DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument("--latin-only", action="store_true",
                        help="เฉพาะ Latin 0x20-0x7F")
    parser.add_argument("--thai-only", action="store_true",
                        help="เฉพาะ Thai 0x0E00-0x0E7F")
    args = parser.parse_args()

    font_path = Path(args.font).expanduser().resolve()
    if not font_path.exists():
        print(f"Error: ไม่พบไฟล์ {font_path}", file=sys.stderr)
        sys.exit(1)

    lv_cmd = _find_lv_font_conv()
    if not lv_cmd:
        print("Error: ไม่พบ lv_font_conv\nติดตั้งด้วย: npm install -g lv_font_conv", file=sys.stderr)
        sys.exit(1)

    ranges = (
        [RANGE_LATIN] if args.latin_only
        else [RANGE_THAI] if args.thai_only
        else [RANGE_LATIN, RANGE_THAI]
    )

    output_dir = Path(args.output_dir).expanduser().resolve()
    print(f"Font      : {font_path.name}")
    print(f"Ranges    : {', '.join(ranges)}")
    print(f"Output dir: {output_dir}")
    print()

    generated = []
    for size in args.size:
        out = convert_one(font_path, size, args.bpp,
                          ranges, output_dir, lv_cmd)
        if out:
            generated.append(out)

    if generated:
        _print_usage(generated)
