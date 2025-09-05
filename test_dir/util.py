# from song_utils import group_songs

# # Sample data
# songs = [
#     {
#         "title": "A Sky Full of Stars",
#         "artist": "Coldplay",
#         "album": "Ghost Stories",
#         "genre": "Pop",
#         "duration": "4:28",
#         "now_playing": True,
#     },
#     {
#         "title": "aaah!",
#         "artist": "Slipknot",
#         "album": "Mate. Feed. Kill. Repeat.",
#         "genre": "Metal",
#         "duration": "3:39",
#     },
#     {
#         "title": "Back in Black",
#         "artist": "AC/DC",
#         "album": "Back in Black",
#         "genre": "Rock",
#         "duration": "4:15",
#     },
#     {
#         "title": "Back in Blue",
#         "artist": "AC/DC",
#         "album": "Back in Blue",
#         "genre": "Rock",
#         "duration": "4:15",
#     },
#     {
#         "title": "Adventure of a Lifetime",
#         "artist": "Coldplay",
#         "album": "A Head Full of Dreams",
#         "genre": "Pop",
#         "duration": "4:24",
#     },
# ]
# # print(songs["title"][0].upper())

# grouped = group_songs(songs, key="title")
# print(grouped)

# # Example rendering loop in your framework’s ListView or Column
# # for group in grouped:
# #     heading = group["heading"]
# #     print(f"=== {heading} ===")  # You can create a heading widget here

# #     for item in group["items"]:
# #         print(item)


# from pythra.core import Framework
# from pythra.widgets import *
# from pythra.state import StatefulWidget, State
# from pythra.base import Key
# from pythra.styles import *


# class MyApp(StatefulWidget):
#     def createState(self) -> State:
#         return MyAppState()


# class MyAppState(State):
#     def build(self):
#         # A nice blue theme for our scrollbar
#         blue_theme = ScrollbarTheme(
#             width=12,
#             thumbColor="#2196F3",
#             trackColor="rgba(0, 0, 128, 0.1)",
#             thumbHoverColor="#1976D2",
#             radius=6,
#         )
#         # song_list = [Container(child=Text(item)) for item in group["items"]]
#         # long_list = [
#         #     Container(
#         #         key=Key(f"group_{group['heading']}"),
#         #         # color=Colors.lightpink if item["id"] % 2 != 0 else Colors.transparent,
#         #         padding=EdgeInsets.all(6),
#         #         margin=EdgeInsets.only(right=24),
#         #         child=Row(
#         #             children=[
#         #                 # Text(group["heading"]),
#         #                 Container(
#         #                     key=Key(f"{group['heading']}_{i}"),
#         #                     # color=Colors.lightpink if item["id"] % 2 != 0 else Colors.transparent,
#         #                     padding=EdgeInsets.all(6),
#         #                     margin=EdgeInsets.only(right=24),
#         #                     child=Column(
#         #                         children=[
#         #                             Text(group["heading"]),
#         #                             Row(
#         #                                 children=[
#         #                                     Text(item["title"]),
#         #                                     SizedBox(width=20),
#         #                                     Text(item["artist"]),
#         #                                     SizedBox(width=20),
#         #                                     Text(item["album"]),
#         #                                     SizedBox(width=20),
#         #                                     Text(item["genre"]),
#         #                                     SizedBox(width=20),
#         #                                     Text(item["duration"]),
#         #                                     SizedBox(width=20),
#         #                                     Text(item["now_playing"]),
#         #                                     SizedBox(width=20),
#         #                                 ]
#         #                             ),
#         #                         ]
#         #                     ),
#         #                 )
#         #                 for i, item in enumerate(group["items"])
#         #             ]
#         #         ),
#         #     )
#         #     for group in grouped
#         # ]
#         long_list = []

#         for group in grouped:
#             # heading once
#             long_list.append(
#                 Container(
#                     key=Key(f"heading_{group['heading']}"),
#                     padding=EdgeInsets.symmetric(vertical=8),
#                     child=Text(
#                         group["heading"],
#                         style=TextStyle(fontSize=20, fontWeight="bold")
#                     )
#                 )
#             )

#             # then each song under it
#             for i, item in enumerate(group["items"]):
#                 long_list.append(
#                     Container(
#                         key=Key(f"{group['heading']}_item_{i}"),
#                         padding=EdgeInsets.all(6),
#                         child=Row(
#                             children=[
#                                 Text(item["title"]),
#                                 SizedBox(width=12),
#                                 Text(item["artist"]),
#                                 SizedBox(width=12),
#                                 Text(item["album"]),
#                                 SizedBox(width=12),
#                                 Text(item["genre"]),
#                                 SizedBox(width=12),
#                                 Text(item["duration"]),
#                                 SizedBox(width=12),
#                                 Text(str(item.get("now_playing", False)))
#                             ]
#                         )
#                     )
#                 )


#         return Scaffold(
#             appBar=AppBar(title=Text("SimpleBar Integration Demo")),
#             body=Container(
#                 color=Colors.lightgreen,
#                 height=300,
#                 padding=EdgeInsets.all(16),
#                 child=Container(
#                     color=Colors.lightpink,
#                     height="100%",
#                     child=Scrollbar(
#                         # The Scrollbar now defines the scrollable area's height
#                         height=100,
#                         theme=blue_theme,
#                         autoHide=False,  # Make scrollbar always visible for demo
#                         child=Column(
#                             crossAxisAlignment=CrossAxisAlignment.STRETCH,
#                             children=[
#                                 Container(
#                                     height=200,
#                                     padding=EdgeInsets.all(16),
#                                     child=Scrollbar(
#                                         # The Scrollbar now defines the scrollable area's height
#                                         height=100,
#                                         theme=blue_theme,
#                                         autoHide=False,  # Make scrollbar always visible for demo
#                                         child=ListView(
#                                             padding=EdgeInsets.all(12),
#                                             children=long_list,
#                                         ),
#                                     ),
#                                 ),
#                                 SizedBox(
#                                     height=20,
#                                 ),
#                                 Container(
#                                     height=200,
#                                     padding=EdgeInsets.all(16),
#                                     child=Scrollbar(
#                                         # The Scrollbar now defines the scrollable area's height
#                                         height=100,
#                                         theme=blue_theme,
#                                         autoHide=False,  # Make scrollbar always visible for demo
#                                         child=ListView(
#                                             padding=EdgeInsets.all(12),
#                                             children=long_list,
#                                         ),
#                                     ),
#                                 ),
#                                 SizedBox(
#                                     height=20,
#                                 ),
#                                 Container(
#                                     height=200,
#                                     padding=EdgeInsets.all(16),
#                                     child=Scrollbar(
#                                         # The Scrollbar now defines the scrollable area's height
#                                         height=100,
#                                         theme=blue_theme,
#                                         autoHide=False,  # Make scrollbar always visible for demo
#                                         child=ListView(
#                                             padding=EdgeInsets.all(12),
#                                             children=long_list,
#                                         ),
#                                     ),
#                                 ),
#                                 SizedBox(
#                                     height=50,
#                                 ),
#                             ],
#                         ),
#                     ),
#                 ),
#             ),
#         )


# if __name__ == "__main__":
#     app = Framework.instance()
#     app.set_root(MyApp(key=Key("app")))
#     app.run(title="Pythra with SimpleBar")



from pathlib import Path

from pythra.core      import Framework
from pythra.widgets   import *
from pythra.state     import StatefulWidget, State
from pythra.base      import Key
from pythra.styles    import *

from media_scanner    import scan_media_library
from song_utils       import group_songs


class MyApp(StatefulWidget):
    def createState(self) -> State:
        return MyAppState()


class MyAppState(State):
    def __init__(self):
        # 1) at startup, build your library
        library_path       = Path.home() / "Music"
        artwork_cache_dir  = Path.home() / ".artwork_cache"
        library_cache_file = Path.home() / ".library_cache.json"

        raw_library = scan_media_library(
            library_path       = library_path,
            artwork_cache_dir  = artwork_cache_dir,
            library_cache_file = library_cache_file,
            fallback_artwork_path = None,
            force_rescan       = False
        )
        # 2) convert ffprobe output into the dict shape your UI needs
        #    (keys: title, artist, album, genre, duration, now_playing)
        self.songs = []
        for entry in raw_library:
            self.songs.append({
                "title":       entry["title"],
                "artist":      entry["artist"],
                "album":       entry.get("album", ""),
                "genre":       entry.get("genre", ""),
                "duration":    f"{int(entry['duration_s']//60)}:{int(entry['duration_s']%60):02d}",
                "now_playing": False,
            })

    def build(self):
        # 3) group by first-letter and sort
        grouped = group_songs(self.songs, key="title")

        # 4) build a flat widget list: one heading + its items
        widgets = []
        for grp in grouped:
            widgets.append(
                Text(grp["heading"],
                     key=Key(f"heading_{grp['heading']}"),
                     style=TextStyle(fontSize=22, fontWeight="bold"),
                    #  padding=EdgeInsets.symmetric(vertical=8)
                     )
            )
            for i, song in enumerate(grp["items"]):
                widgets.append(
                    Row(
                        key=Key(f"{grp['heading']}_item_{i}"),
                        # padding=EdgeInsets.symmetric(vertical=4),
                        children=[
                            Text(song["title"],),
                            Text(song["artist"],),
                            Text(song["album"],),
                            Text(song["genre"],),
                            Text(song["duration"],),
                            Text(str(song["now_playing"]),),
                        ]
                    )
                )

        # 5) render one single ListView inside your colored Container
        return Scaffold(
            appBar=AppBar(title=Text("My Music Library")),
            body=Container(
                color=Colors.lightgreen,
                padding=EdgeInsets.all(16),
                child=Scrollbar(
                    theme=ScrollbarTheme(
                        width=10,
                        thumbColor="#2196F3",
                        trackColor="rgba(0,0,128,0.1)",
                        thumbHoverColor="#1976D2",
                        radius=6,
                    ),
                    autoHide=False,
                    child=ListView(
                        # padding=EdgeInsets.all(12),
                        children=widgets,
                    ),
                )
            )
        )


if __name__ == "__main__":
    app = Framework.instance()
    app.set_root(MyApp(key=Key("app")))
    app.run(title="Pythra Music Player")
