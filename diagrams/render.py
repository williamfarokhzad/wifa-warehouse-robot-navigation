"""Render original teaching figures. Run from any directory; requires Pillow."""
from pathlib import Path
import json
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from planner import position, read_scenario, schedule

BG, INK, MUTED = '#eef7f3', '#153149', '#364e63'
COLORS = {'A': '#00695f', 'B': '#7845a1'}


def font(size):
    return ImageFont.load_default(size=size)


def draw_steps(filename, title, subtitle, scenario, paths, notes, footer):
    width, panel_h = 760, 187
    height = 135 + ((len(notes) + 1) // 2) * panel_h + 55
    img = Image.new('RGB', (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((27, 20), title, fill=INK, font=font(41))
    draw.text((29, 73), subtitle, fill=MUTED, font=font(26))
    for tick, note in enumerate(notes):
        x0, y0 = 26 + (tick % 2) * 359, 119 + (tick // 2) * panel_h
        draw.rounded_rectangle((x0, y0, x0 + 350, y0 + 175), radius=15, fill='white', outline='#acc6bd', width=2)
        draw.text((x0 + 12, y0 + 12), f'Tick {tick}', fill=INK, font=font(26))
        for y in range(3):
            for x in range(3):
                if (x, y) not in scenario.cells:
                    continue
                xx, yy = x0 + 16 + 41*x, y0 + 46 + 41*y
                draw.rounded_rectangle((xx, yy, xx + 39, yy + 39), radius=6, fill='#dcebe6', outline='#6f928a', width=2)
        for name, path in paths.items():
            x, y = position(path, tick)
            xx, yy = x0 + 35 + 41*x, y0 + 65 + 41*y
            draw.ellipse((xx-16, yy-16, xx+16, yy+16), fill=COLORS[name])
            draw.text((xx, yy), name, anchor='mm', fill='white', font=font(23))
        draw.multiline_text((x0 + 155, y0 + 55), note, fill=INK, font=font(26), spacing=7)
    draw.text((27, height - 46), footer, fill=MUTED, font=font(25))
    img.save(HERE / f'{filename}.webp', format='WEBP', quality=90, method=6)
    img.resize((380, height//2), Image.Resampling.LANCZOS).save(HERE / f'{filename}-380.webp', format='WEBP', quality=88, method=6)


def read(name):
    return read_scenario(json.loads((HERE.parent / 'examples' / f'{name}.json').read_text()))


if __name__ == '__main__':
    crossing = read('crossing')
    draw_steps('warehouse-crossing-ticks', 'One crossing, two robots', 'A = teal. B = purple. Each panel is one tick.', crossing, schedule(crossing),
               ['Both at\nstart', 'A crosses\nB waits', 'A parks\nB crosses', 'A stays\nB parks'], 'Synthetic routes from crossing.json')
    bay = read('aisle-swap')
    witness = {'A': [(0,1),(1,1),(1,0),(1,1),(2,1)], 'B': [(2,1),(2,1),(1,1),(0,1)]}
    draw_steps('warehouse-side-bay', 'The side bay breaks the deadlock', 'A = teal. B = purple. The free bay is above.', bay, witness,
               ['Facing\neach other', 'A enters\nthe aisle', 'A yields\nin the bay', 'B parks\nA returns', 'A parks\nB stays'], 'Hand planned witness checked in the unit tests')
