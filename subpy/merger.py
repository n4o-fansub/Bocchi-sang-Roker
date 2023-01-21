from copy import copy
from datetime import timedelta

from ass_parser import AssEvent, AssFile

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


def merge_ass_and_sync(
    target: AssFile,
    source: AssFile,
    target_sync: int | str | None = None,
    bump_layer: int = 0,
    *,
    config: dict | None = None,
):
    """
    Merge `source` into `target`, and sync it to `target_sync` if possible.
    """
    config = config or {}
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
    comment_start_idx = 0
    comment_found_at = -1
    for i, line in enumerate(target.events):
        if i == 0 and not line.is_comment:  # No comment at top of the file
            break
        # Check if comment and the found_at is not set
        if line.is_comment and comment_found_at == -1:
            comment_found_at = i
            continue
        # Check if comment and the jump between the comment is not 1
        # If true, break loop
        if line.is_comment and comment_found_at != -1:
            if i - comment_found_at != 1:
                break
            comment_found_at = i
    if comment_found_at != -1:
        comment_start_idx = comment_found_at
    used_styles = set()
    conf_skip_templater = config.get("yeettemplater", False)
    comments_set: list[AssEvent] = []
    for line in source.events:  # iter the source events
        efx = line.effect
        lx = copy(line)
        if diff != 0:
            lx.start = lx.start + diff
            lx.end = lx.end + diff
        lx.layer += bump_layer
        # Append to target
        if (
            efx.startswith("code ")
            or efx.startswith("template ")
            or efx.startswith("mixin ")
            and conf_skip_templater
            and lx.is_comment
        ):
            # yeet out template
            lx.set_text("{template has been removed, please see the original file}")
            lx.effect = ""
            lx.actor = "kfx-templater"
        used_styles.add(lx.style_name)
        if line.is_comment and line.effect != "sync":
            comments_set.append(lx)
        else:
            target.events.append(lx)
    for comment in comments_set:
        target.events.insert(comment_start_idx, comment)
        comment_start_idx += 1
    # copy style
    for style in used_styles:
        tgs = target.styles.get_by_name(style)
        if (sgs := source.styles.get_by_name(style)) is not None:
            if tgs is not None:
                target.styles[tgs.index] = copy(sgs)
            else:
                target.styles.append(copy(sgs))
