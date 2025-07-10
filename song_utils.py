# from collections import defaultdict
# from typing import List, Dict

# # Sample data with now_playing flag
# songs: List[Dict[str, str]] = [
#     {
#         "title": "A Sky Full of Stars",
#         "artist": "Coldplay",
#         "album": "Ghost Stories",
#         "genre": "Pop",
#         "duration": "4:28",
#         "now_playing": False
#     },
#     {
#         "title": "aaah!",
#         "artist": "Slipknot",
#         "album": "Mate. Feed. Kill. Repeat.",
#         "genre": "Metal",
#         "duration": "3:39",
#         "now_playing": True
#     },
#     {
#         "title": "Back in Black",
#         "artist": "AC/DC",
#         "album": "Back in Black",
#         "genre": "Rock",
#         "duration": "4:15",
#         "now_playing": False
#     },
#     {
#         "title": "Adventure of a Lifetime",
#         "artist": "Coldplay",
#         "album": "A Head Full of Dreams",
#         "genre": "Pop",
#         "duration": "4:24",
#         "now_playing": False
#     },
#     # … more songs …
# ]

# def print_grouped(
#     songs: List[Dict[str, str]],
#     key: str,
#     fields_order: List[str] = None
# ) -> None:
#     """
#     Group and print songs by the first-letter heading of 'title',
#     or by the full value for 'artist' and 'genre'.
#     """
#     if fields_order is None:
#         fields_order = ["title", "artist", "album", "genre", "duration", "now_playing"]

#     # 1) Build groups
#     groups = defaultdict(list)
#     for song in songs:
#         value = song.get(key, "").strip()
#         if key == "title":
#             heading = value[0].upper() if value else "#"
#         else:
#             heading = value or "#"
#         groups[heading].append(song)

#     # 2) Sort headings
#     if key == "title":
#         # Alphabet headings; put '#' last if present
#         headings = sorted(h for h in groups if h != "#")
#         if "#" in groups:
#             headings.append("#")
#     else:
#         # Full-value headings, sorted lexicographically
#         headings = sorted(groups.keys())

#     # 3) Print
#     for heading in headings:
#         print(f"\n{heading}")
#         bucket = groups[heading]
#         # sort within bucket by chosen key (case-insensitive)
#         bucket_sorted = sorted(bucket, key=lambda s: s.get(key, "").lower())
#         for s in bucket_sorted:
#             line = " | ".join(f"{fld}: {s.get(fld, '')}" for fld in fields_order)
#             print("  ", line)

# # --- Example outputs ---

# print("=== By Title ===")
# print_grouped(songs, key="title")

# print("\n=== By Artist ===")
# print_grouped(songs, key="artist")

# print("\n=== By Genre ===")
# print_grouped(songs, key="genre")


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

    if fields_order is None:
        fields_order = ["title", "artist", "album", "genre", "duration", "now_playing"]

    groups = defaultdict(list)

    for song in songs:
        value = song.get(key, "").strip()
        if key == "title":
            if not value:
                heading = "#"
            else:
                first = value[0].upper()
                # only A–Z map to themselves; everything else becomes “#”
                heading = first if first.isalpha() else "#"
        else:
            heading = value or "#"
        # ensure song has now_playing field
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

    # Build structured result
    grouped_result = []
    for heading in headings:
        bucket = groups[heading]
        # sort within bucket by key field
        bucket_sorted = sorted(bucket, key=lambda s: s.get(key, "").lower())
        grouped_result.append({
            "heading": heading,
            "items": [
                {fld: s.get(fld, "") for fld in fields_order}
                for s in bucket_sorted
            ]
        })

    return grouped_result

