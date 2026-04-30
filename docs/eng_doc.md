# lvgl-thai-font-tool

Fix Thai vowel stacking in TTF fonts and convert to LVGL `.c` for ESP32 — no shaping engine required.

## The Problem

LVGL has no text shaping engine for Thai. This means combining marks (vowels and tone marks) render at the same vertical position as the base consonant, causing them to stack on top of each other.

Words like **น้ำ (water)**, **เที่ยว (travel)**, and **ข้อ (item)** display incorrectly out of the box.

### Before / After

![Before](image_before.png)
![After](image_after.png)

### Why it happens

Thai fonts use OpenType **GPOS** tables to fine-tune mark positions at render time. LVGL reads glyph bitmaps directly and ignores GPOS, so marks fall back to their default glyph-metric positions — which often overlap each other.

### How this tool fixes it

Instead of adding a shaping engine, we **bake the correct vertical offsets directly into the font** before conversion. Thai combining marks are split into two levels:

```
Level 2 → ่ ้ ๊ ๋ ์ ํ   (tone marks, thanthakat, nikhahit — shifted up)
Level 1 → ั ิ ี ึ ื ็   (vowels — kept at original position, above consonant)
Base    → ก ข ค ง ...    (consonants)
```

Level-2 marks are shifted upward so they sit above Level-1 marks without overlapping.

## Requirements

| Tool | Install |
|------|---------|
| Python ≥ 3.12 | [python.org](https://www.python.org) |
| [uv](https://docs.astral.sh/uv/) | `brew install uv` |
| [lv_font_conv](https://github.com/lvgl/lv_font_conv) | `npm install -g lv_font_conv` |

## Windows setup (extra)

1. Install Python 3.12+ from python.org and check "Add python.exe to PATH".
2. Install Node.js LTS (includes `npm`).
3. Install uv in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

If `uv` is not found, close and reopen the terminal before running the setup commands below.

## Setup

```bash
git clone https://github.com/LEKPCSTEAM/LVGL-Thai-Font-Tool.git
cd lvgl-thai-font-tool
uv sync
```

## Commands

### `fix-thai` — Fix Thai mark positions

```bash
uv run fix-thai MyFont.ttf
# output: MyFont_fixed.ttf (same directory)
```

| Option | Default | Description |
|--------|---------|-------------|
| `-o, --output` | `<name>_fixed.ttf` | Output file path |
| `--shift` | `220` | Units to shift Level-2 marks up (scaled by UPM) |
| `--info` | — | Print font info without modifying |

**Examples:**

```bash
# Inspect font before fixing
uv run fix-thai MyFont.ttf --info

# Custom output path
uv run fix-thai MyFont.ttf -o MyFont_lvgl.ttf

# Increase shift for larger fonts
uv run fix-thai MyFont.ttf --shift 280
```

---

### `to-lvgl` — Convert TTF to LVGL `.c`

```bash
uv run to-lvgl MyFont_fixed.ttf
# output: ./output/myfont_fixed_20.c
```

| Option | Default | Description |
|--------|---------|-------------|
| `--size PX [PX ...]` | `20` | Font size(s) in pixels |
| `--bpp {1,2,4,8}` | `4` | Bits per pixel (anti-aliasing quality) |
| `--output-dir DIR` | `./output` | Output directory |
| `--latin-only` | — | Include only Latin (0x20–0x7F) |
| `--thai-only` | — | Include only Thai (0x0E00–0x0E7F) |

**Examples:**

```bash
# Generate multiple sizes at once
uv run to-lvgl MyFont_fixed.ttf --size 16 20 24

# Custom output directory
uv run to-lvgl MyFont_fixed.ttf --size 20 --output-dir ./myproject/fonts

# Reduce Flash usage on ESP32
uv run to-lvgl MyFont_fixed.ttf --size 20 --bpp 2

# Latin only (e.g. Urbanist for Latin, separate Thai font)
uv run to-lvgl MyFont_fixed.ttf --latin-only
```

---

### One-liner: fix and convert in a single command

```bash
uv run fix-thai MyFont.ttf && uv run to-lvgl MyFont_fixed.ttf --size 16 20 24
```

## Using the Font in LVGL (ESP32)

Copy the generated `.c` file into your project, then:

```c
LV_FONT_DECLARE(myfont_fixed_20);

lv_obj_t *label = lv_label_create(lv_scr_act());
lv_obj_set_style_text_font(label, &myfont_fixed_20, 0);
lv_label_set_text(label, "น้ำ เที่ยว ข้อ ก็ได้ Hello");
```

## Troubleshooting

### Tone marks still overlap vowel marks

Increase `--shift`:

```bash
uv run fix-thai MyFont.ttf --shift 280
uv run to-lvgl MyFont_fixed.ttf --size 20
```

### Tone marks appear too high

Decrease `--shift`:

```bash
uv run fix-thai MyFont.ttf --shift 160
```

### Choosing the right `--shift` value

The default `--shift 220` is calibrated for fonts with **UPM = 1000**. The tool automatically scales the shift proportionally for other UPM values (e.g. 2048). Use `--info` to check your font's UPM before adjusting.

```bash
uv run fix-thai MyFont.ttf --info
# UPM: 1000
# Level-1 marks yMin ≈ 636, consonant yMax ≈ 566
# → gap = 70 units, shift = 220 puts tone marks well above vowels
```

### Font has no Thai glyphs

This tool only repositions existing Thai glyphs — it cannot add them. Use a font that already includes Thai (e.g. Kanit, LINE Seed Sans TH, Noto Sans Thai).

## Tested Fonts

| Font | Result |
|------|--------|
| LINE Seed Sans TH | ✅ |
| Kanit | ✅ |

## License

MIT
