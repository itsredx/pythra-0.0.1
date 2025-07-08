from song_utils import group_songs

# Sample data
songs = [
    {
        "title": "A Sky Full of Stars",
        "artist": "Coldplay",
        "album": "Ghost Stories",
        "genre": "Pop",
        "duration": "4:28",
    },
    {
        "title": "aaah!",
        "artist": "Slipknot",
        "album": "Mate. Feed. Kill. Repeat.",
        "genre": "Metal",
        "duration": "3:39",
    },
    {
        "title": "Back in Black",
        "artist": "AC/DC",
        "album": "Back in Black",
        "genre": "Rock",
        "duration": "4:15",
    },
    {
        "title": "Back in Blue",
        "artist": "AC/DC",
        "album": "Back in Blue",
        "genre": "Rock",
        "duration": "4:15",
    },
    {
        "title": "Adventure of a Lifetime",
        "artist": "Coldplay",
        "album": "A Head Full of Dreams",
        "genre": "Pop",
        "duration": "4:24",
    },
]

grouped = group_songs(songs, key="title")
print(grouped)

# Example rendering loop in your framework’s ListView or Column
# for group in grouped:
#     heading = group["heading"]
#     print(f"=== {heading} ===")  # You can create a heading widget here

#     for item in group["items"]:
#         print(item)


from pythra.core import Framework
from pythra.widgets import *
from pythra.state import StatefulWidget, State
from pythra.base import Key
from pythra.styles import *


class MyApp(StatefulWidget):
    def createState(self) -> State:
        return MyAppState()


class MyAppState(State):
    def build(self):
        # A nice blue theme for our scrollbar
        blue_theme = ScrollbarTheme(
            width=12,
            thumbColor="#2196F3",
            trackColor="rgba(0, 0, 128, 0.1)",
            thumbHoverColor="#1976D2",
            radius=6,
        )
        # song_list = [Container(child=Text(item)) for item in group["items"]]
        long_list = [
            Container(
                key=Key(f"List_item_"),
                # color=Colors.lightpink if item["id"] % 2 != 0 else Colors.transparent,
                padding=EdgeInsets.all(6),
                margin=EdgeInsets.only(right=24),
                child=Row(
                    children=[
                        # Text(group["heading"]),
                        Container(
                            key=Key(f"List_item_container"),
                            # color=Colors.lightpink if item["id"] % 2 != 0 else Colors.transparent,
                            padding=EdgeInsets.all(6),
                            margin=EdgeInsets.only(right=24),
                            child=Column(
                                children=[
                                    Text(group["heading"]),
                                    Row(
                                        children=[
                                            Text(item["title"]),
                                            SizedBox(width=20),
                                            Text(item["artist"]),
                                            SizedBox(width=20),
                                            Text(item["album"]),
                                            SizedBox(width=20),
                                            Text(item["genre"]),
                                            SizedBox(width=20),
                                            Text(item["duration"]),
                                            SizedBox(width=20),
                                            Text(item["now_playing"]),
                                            SizedBox(width=20),
                                        ]
                                    ),
                                ]
                            ),
                        )
                        for item in group["items"]
                    ]
                ),
            )
            for group in grouped
        ]

        return Scaffold(
            appBar=AppBar(title=Text("SimpleBar Integration Demo")),
            body=Container(
                color=Colors.lightgreen,
                height=300,
                padding=EdgeInsets.all(16),
                child=Container(
                    color=Colors.lightpink,
                    height="100%",
                    child=Scrollbar(
                        # The Scrollbar now defines the scrollable area's height
                        height=100,
                        theme=blue_theme,
                        autoHide=False,  # Make scrollbar always visible for demo
                        child=Column(
                            crossAxisAlignment=CrossAxisAlignment.STRETCH,
                            children=[
                                Container(
                                    height=200,
                                    padding=EdgeInsets.all(16),
                                    child=Scrollbar(
                                        # The Scrollbar now defines the scrollable area's height
                                        height=100,
                                        theme=blue_theme,
                                        autoHide=False,  # Make scrollbar always visible for demo
                                        child=ListView(
                                            padding=EdgeInsets.all(12),
                                            children=long_list,
                                        ),
                                    ),
                                ),
                                SizedBox(
                                    height=20,
                                ),
                                Container(
                                    height=200,
                                    padding=EdgeInsets.all(16),
                                    child=Scrollbar(
                                        # The Scrollbar now defines the scrollable area's height
                                        height=100,
                                        theme=blue_theme,
                                        autoHide=False,  # Make scrollbar always visible for demo
                                        child=ListView(
                                            padding=EdgeInsets.all(12),
                                            children=long_list,
                                        ),
                                    ),
                                ),
                                SizedBox(
                                    height=20,
                                ),
                                Container(
                                    height=200,
                                    padding=EdgeInsets.all(16),
                                    child=Scrollbar(
                                        # The Scrollbar now defines the scrollable area's height
                                        height=100,
                                        theme=blue_theme,
                                        autoHide=False,  # Make scrollbar always visible for demo
                                        child=ListView(
                                            padding=EdgeInsets.all(12),
                                            children=long_list,
                                        ),
                                    ),
                                ),
                                SizedBox(
                                    height=50,
                                ),
                            ],
                        ),
                    ),
                ),
            ),
        )


if __name__ == "__main__":
    app = Framework.instance()
    app.set_root(MyApp(key=Key("app")))
    app.run(title="Pythra with SimpleBar")
