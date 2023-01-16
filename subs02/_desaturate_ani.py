# me dumb dumb in lua/templater
# so python to make "desaturate" animation for
# the "Bocchi Hill" sign that I """recreated""" a.k.a stolen
# from Medex and I need to basically animate to "dark".

import math
import ass_parser
import re
from pathlib import Path
import colorsys

path = Path("bocchi02.ts.ass")

subs = ass_parser.read_ass(path)

# HSV_TO = (50°, 58%, 87%)
# HSV_FROM = (39°, 13%, 43%)

onec_regex = re.compile(r"\\1c&H([0-9A-F]{6})&", re.IGNORECASE)


def ass_hex_to_rgb(ass_hex):
    rgb_hex = ass_hex[4:6] + ass_hex[2:4] + ass_hex[0:2]
    rgb = tuple(int(rgb_hex[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return rgb


def ass_hex_to_hsv(ass_hex):
    return colorsys.rgb_to_hsv(*ass_hex_to_rgb(ass_hex))


def rgb_to_ass_hex(rgb):
    rgb_hex = "".join(f"{int(c * 255):02X}" for c in rgb)
    return rgb_hex[4:6] + rgb_hex[2:4] + rgb_hex[0:2]


def hsv_to_ass_hex(hsl):
    rgb = colorsys.hsv_to_rgb(*hsl)
    return rgb_to_ass_hex(rgb)


def desaturate_hsv(hsv):
    h, s, v = hsv
    return (h, s * 0.26, v * 0.43)


matching_colors = set()
total_lines = 0
for sub in subs.events:
    if sub.effect != "desaturate":
        continue
    if mm := onec_regex.search(sub.text):
        if (col := mm.group(1)) not in matching_colors:
            matching_colors.add(col)
        ass_hsv = ass_hex_to_hsv(col)
        target_hsv = desaturate_hsv(ass_hsv)
        target_ass = hsv_to_ass_hex(target_hsv)
        sub.text = onec_regex.sub(r"\\1c&H\1&\\t(0,3939,1.5,\\1c&H" + target_ass + r"&)", sub.text)
        print(sub.text)
        total_lines += 1

total_color_col = math.ceil(len(matching_colors) / 2)

print(matching_colors, total_color_col, len(matching_colors))
print(total_lines)
with path.with_stem("bocchi02.ts.desaturate").open("w", encoding="utf-8") as fp:
    # BOM header
    fp.write("\ufeff")
    fp.write(subs.script_info.to_ass_string().rstrip() + "\n\n")
    fp.write(subs.styles.to_ass_string().rstrip() + "\n\n")
    fp.write(subs.events.to_ass_string().rstrip() + "\n")
    for section in subs.extra_sections:
        fp.write("\n")
        fp.write(section.to_ass_string().rstrip() + "\n")
