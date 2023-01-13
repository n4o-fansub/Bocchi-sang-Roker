import argparse
import sys
from pathlib import Path

from ass_parser import AssFile, read_ass
from pymkv import MKVFile, MKVTrack

from subpy.chapters import Chapter, generate_chapter_file, get_chapters_from_ass
from subpy.fonts import Line, find_fonts, validate_fonts
from subpy.merger import merge_ass_and_sync, parse_sync_timestamp
from subpy.properties import SyncPoint, read_and_parse_properties
from subpy.utils import incr_layer

CURRENT_DIR = Path(__file__).parent
COMMON_DIR = CURRENT_DIR / "common"

properties, raw_prop = read_and_parse_properties(CURRENT_DIR / "properties.yaml", CURRENT_DIR)

parser = argparse.ArgumentParser()
parser.add_argument("episode", type=int)

args = parser.parse_args()
episode: int = args.episode
current_episode = f"{episode:02d}"

basename = raw_prop.get("basename")
episode_meta = properties.get(current_episode)
if episode_meta is None:
    print(f"[!] Episode {current_episode} not found in properties.yaml")
    sys.exit(1)

print(f"[?] Processing episode {current_episode}...")
print(f"[?] Using basename: {basename}")
chapters_data: dict[str, Chapter] = {}
base_ass: AssFile | None = None
fonts_folder: set[Path] = set()
for fmt, paths in episode_meta.scripts.items():
    if len(paths) < 1:
        continue
    read_paths = paths[:]
    if base_ass is None:
        print(f"[+] Using {read_paths[0].name} as base ASS file!")
        base_ass = read_ass(read_paths[0])
        font_folder = paths[0].parent / "fonts"
        fonts_folder.add(font_folder)
        if "dialog" in fmt.lower():
            for line in base_ass.events:
                incr_layer(line, 50)
        chapters_data |= get_chapters_from_ass(base_ass)
        read_paths.pop(0)

    for path in read_paths:
        print(f"[+] Merging {fmt}: {path.name}")
        merge_ass = read_ass(path)
        font_folder = path.parent / "fonts"
        fonts_folder.add(font_folder)
        chapters_data |= get_chapters_from_ass(merge_ass)
        bump_layer = 50 if "dialog" in fmt.lower() else 0
        sync_time = episode_meta.syncs.get(fmt, SyncPoint("-", "-"))
        chapter_point = chapters_data.get(sync_time.chapter)
        sync_act = sync_time.value if sync_time.value != "-" else None
        try:
            sync_act = parse_sync_timestamp(sync_act or "-")
        except ValueError:
            sync_act = None
        if sync_act is None and chapter_point is not None:
            print(f'    [+] Syncing to chapter "{sync_time.chapter}" ({chapter_point.milisecond})')
            sync_act = chapter_point.milisecond
        merge_ass_and_sync(base_ass, merge_ass, sync_act, bump_layer)

if base_ass is None:
    print("[!] Somehow we got an empty episode case?")
    sys.exit(1)

print("[+] Writing merged files!")
final_folder = CURRENT_DIR / "final"
final_folder.mkdir(parents=True, exist_ok=True)
final_file = final_folder / f"{basename}{current_episode}.merged.ass"
with final_file.open("w", encoding="utf-8") as fp:
    # BOM header
    fp.write("\ufeff")
    fp.write(base_ass.script_info.to_ass_string().rstrip() + "\n\n")
    fp.write(base_ass.styles.to_ass_string().rstrip() + "\n\n")
    fp.write(base_ass.events.to_ass_string().rstrip() + "\n")
    for section in base_ass.extra_sections:
        fp.write("\n")
        fp.write(section.to_ass_string().rstrip() + "\n")

print("[?] Validating fonts...")
ttfont, complete_fonts = find_fonts(list(fonts_folder))
font_report = validate_fonts(base_ass, ttfont, True, False)


def format_lines(lines: set[Line], limit=10):
    sorted_lines = sorted(lines)
    if len(sorted_lines) > limit:
        sorted_lines = list(map(lambda x: str(x.pos), sorted_lines[:limit]))
        sorted_lines.append("[...]")
    else:
        sorted_lines = list(map(lambda x: str(x.pos), sorted_lines))
    return " ".join(sorted_lines)


real_problems = False
for problem in font_report.missing_font.values():
    print(f"   - Could not find font {problem.state.font} on line(s): {format_lines(problem.line)}")
    real_problems = True
for problem in font_report.faux_bold.values():
    fweight = problem.font.weight if problem.font else "UNKNOWN"
    fontname = problem.state.font if problem.font is None else str(problem.font.postscript_name)
    print(
        f"   - Faux bold used for font {fontname} (requested weight {problem.state.weight}, "
        f"got {fweight}) on line(s): {format_lines(problem.line)}"
    )
for problem in font_report.faux_italic.values():
    fontname = problem.state.font if problem.font is None else str(problem.font.postscript_name)
    print(f"   - Faux italic used for font {fontname} on line(s): {format_lines(problem.line)}")
for problem in font_report.mismatch_bold.values():
    fweight = problem.font.weight if problem.font else "UNKNOWN"
    fontname = problem.state.font if problem.font is None else str(problem.font.postscript_name)
    print(
        f"   - Requested weight {problem.state.weight} but got for font {fontname} "
        f"got {fweight}) on line(s): {format_lines(problem.line)}"
    )
for problem in font_report.mismatch_italic.values():
    fontname = problem.state.font if problem.font is None else str(problem.font.postscript_name)
    print(f"   - Requested non-italic but got italic for font {fontname} on line(s): {format_lines(problem.line)}")
for problem in font_report.missing_glyphs.values():
    if (ft := problem.font) is None:
        continue
    for line in problem.line:
        if ftmissing := ft.missing_glyphs(line.text):
            missing = " ".join(f"{g}(U+{ord(g):04X})" for g in sorted(ftmissing))
            print(f"   - Missing glyphs {missing} for font {ft.postscript_name} on line: {line.pos}")

if real_problems:
    sys.exit(1)

print("[+] Preparing .mks file...")
mkv = MKVFile()
for font in complete_fonts:
    mkv.add_attachment(str(font))

chapter_txts = generate_chapter_file(list(chapters_data.values()))
chapter_file = final_folder / f"{basename}{current_episode}.chapters.txt"
if chapter_txts is not None:
    print(f"[+] Generating chapter file for {current_episode}")
    chapter_file.write_text(chapter_txts, encoding="utf-8")
    mkv.chapters(str(chapter_file), "ind")
if (eptitle := episode_meta.title) is not None:
    merge_title = f"#{current_episode} - {eptitle}"
    if (basetitle := raw_prop.get("basetitle")) is not None:
        merge_title = f"{basetitle} - {merge_title}"
    mkv.title = merge_title
mkv.add_track(
    MKVTrack(
        str(final_file),
        0,
        "Bahasa Indonesia oleh Interrobang!?",
        "ind",
        default_track=True,
    )
)
mks_file = final_folder / f"{basename}{current_episode}.mks"
print(f"[+] Writing .mks file to {mks_file.name}")
mkv.mux(str(mks_file))