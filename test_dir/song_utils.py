from collections import defaultdict
from typing import List, Dict, Any

def group_songs(
    songs: List[Dict[str, Any]],
    key: str,
    fields_order: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Groups and sorts songs for UI rendering.

    Returns a list of dicts with:
    - "heading": group heading (A, B, artist name, genre name)
    - "items": list of song dicts sorted within the group
    """

    # Default order includes sort_id at the end
    if fields_order is None:
        fields_order = [
            "path", "title", "artist", "album",
            "genre", "duration", "now_playing", "id", "sort_id"
        ]

    # Build groups
    groups = defaultdict(list)
    for song in songs:
        value = song.get(key, "").strip()
        # Heading logic
        if key == "title":
            if not value:
                heading = "#"
            else:
                first = value[0].upper()
                heading = first if first.isalpha() else "#"
        else:
            heading = value or "#"
        # Ensure now_playing field exists
        if "now_playing" not in song:
            song["now_playing"] = False
        groups[heading].append(song)

    # Sort headings
    if key == "title":
        headings = sorted(h for h in groups if h != "#")
        if "#" in groups:
            headings.append("#")
    else:
        headings = sorted(groups.keys())

    # Build grouped result
    grouped_result: List[Dict[str, Any]] = []
    for heading in headings:
        bucket = groups[heading]
        # Sort within bucket by the grouping key
        bucket_sorted = sorted(bucket, key=lambda s: s.get(key, "").lower())
        grouped_result.append({
            "heading": heading,
            "items": [
                {fld: s.get(fld, "") for fld in fields_order}
                for s in bucket_sorted
            ]
        })

    # Assign continuous sort_id across all items (skip headings)
    sort_counter = 1
    for group in grouped_result:
        for item in group["items"]:
            item["sort_id"] = sort_counter
            sort_counter += 1

    return grouped_result
