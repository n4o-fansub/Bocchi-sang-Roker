import re
from pathlib import Path

from ass_parser import AssFile

__all__ = ("write_ass",)
bubblesub_time_re = re.compile(r"{TIME:(?P<start>-?\d+),(?P<end>-?\d+)}", re.MULTILINE)


def rewrite_events_list(events_str: str):
    # Remove the {TIME:...} tags
    new_events = []
    for line in events_str.splitlines():
        new_events.append(bubblesub_time_re.sub("", line))
    return "\n".join(new_events)


def write_ass(ass_data: AssFile, path: Path) -> None:
    """Write an ASS file to disk."""
    with path.open("w", encoding="utf-8") as fp:
        # BOM header since sometimes it fuckes UTF-8 up
        fp.write("\ufeff")
        fp.write(ass_data.script_info.to_ass_string().rstrip() + "\n\n")
        fp.write(ass_data.styles.to_ass_string().rstrip() + "\n\n")
        fp.write(rewrite_events_list(ass_data.events.to_ass_string().rstrip()) + "\n")
        for section in ass_data.extra_sections:
            fp.write("\n")
            fp.write(section.to_ass_string().rstrip() + "\n")
