from copy import copy
from datetime import timedelta

from ass_parser import AssFile

from .chapters import Chapter


def timedelta_to_miliseconds(timedelta: timedelta):
    return timedelta.total_seconds() * 1000


def parse_sync_timestamp(sync_ts: str):
    hh, mm, ssms = sync_ts.split(":")
    ss, ms = ssms.split(".")

    final = int(hh) * 3600
    final += int(mm) * 60
    final += int(ss)
    final *= 1000
    final += int(ms)
    return final


def find_sync_point_from_chapter(chapters: list[Chapter], sync_point: str):
    for chapter in chapters:
        if chapter.name == sync_point:
            return chapter.milisecond
    return None


def merge_ass_and_sync(target: AssFile, source: AssFile, target_sync: int | str | None = None, bump_layer: int = 0):
    """
    Merge `source` into `target`, and sync it to `target_sync` if possible.
    """
    # Parse sync time, and convert it to milliseconds
    target_s: int | None = None
    source_s: int | None = None
    if target_sync is not None:
        if isinstance(target_sync, int):
            target_s = target_sync
        else:
            target_s = parse_sync_timestamp(target_sync)
        for line in source.events:
            if line.effect != "sync":
                continue
            source_s = line.start  # the sync point at the source file

    # Calculate the difference between the two sync times
    diff = 0
    if target_s is not None and source_s is not None:
        diff = target_s - source_s
    used_styles = set()
    for line in source.events:  # iter the source events
        efx = line.effect
        if efx.startswith("code ") or efx.startswith("template "):
            # yeet out template
            continue
        lx = copy(line)
        if diff != 0:
            lx.start = lx.start + diff
            lx.end = lx.end + diff
        lx.layer += bump_layer
        # Append to target
        used_styles.add(lx.style_name)
        target.events.append(lx)
    # copy style
    for style in used_styles:
        tgs = target.styles.get_by_name(style)
        if (sgs := source.styles.get_by_name(style)) is not None:
            if tgs is not None:
                target.styles[tgs.index] = copy(sgs)
            else:
                target.styles.append(copy(sgs))
