# main.py

from framework.core import Framework
from framework.widgets import *
from framework.styles import *


class MyApp:
    def __init__(self):
        self.framework = Framework()
        self.currentIndex = 0

    def on_tab_selected(self, index):
        print(f"Tab {index} selected")
        self.currentIndex = index
        self.update_ui()
        
    def toggle_drawer(self):
        self.framework.toggle_drawer()

    def toggle_end_drawer(self):
        self.framework.toggle_end_drawer()

    def show_bottom_sheet(self):
        self.framework.show_bottom_sheet()

    def hide_bottom_sheet(self):
        self.framework.hide_bottom_sheet()

    def show_snack_bar(self):
        self.framework.show_snack_bar()
    
    def hide_snack_bar(self):
        self.framework.hide_snack_bar()

    def undo(self):
        print("Undo action")

    def update_ui(self):
        # Define the content for each tab
        content = [
            Container(
                child=Column(
                children=[
                    Text('Welcome to the Home Page!'),
                    IconButton(
                        child=Icon('plus'),
                        onPressed= self.show_bottom_sheet),
                    IconButton(
                        child=Icon('flask'),
                        onPressed= self.show_snack_bar),
                ]
            ),
                padding=EdgeInsets.all(20),
                margin=EdgeInsets.all(20),
                constraints= BoxConstraints(max_width= 300, max_height=300),
                decoration=BoxDecoration(
                    color=Colors.color('lightblue'),
                    borderRadius=25,
                )
                ),
            Container(
                child=Text('Settings Page'),
                padding=EdgeInsets.all(20),
                margin=EdgeInsets.all(20),
                constraints= BoxConstraints(max_width= 300, max_height=300),
                decoration=BoxDecoration(
                    color=Colors.color('lightblue'),
                    borderRadius=25,
                )
                )
        ]

        column = Column(
            children=[
                Text('Welcome to the Home Page!'),
                IconButton(
                    child=Icon('plus'),
                    onPressed= self.show_bottom_sheet
                    ),
            ]
        )

        # Set the content based on the current index
        body_content = content[self.currentIndex]

        drawer = Drawer(
            child=Text('Hello'),
            width=300,
            divider=Divider(
                margin=EdgeInsets.symmetric(8,0)
            ),
        )

        end_drawer = EndDrawer(
            child=Text('Hello End'),
            width=250,
            divider=Divider(
                margin=EdgeInsets.symmetric(8,0)
            ),
        )

        snack_bar_action = SnackBarAction(
            label="UNDO",
            onPressed='undo'
        )

        snack_bar = SnackBar(
            content=Text("Item deleted"),
            action=snack_bar_action,
            duration=5000,
            backgroundColor=Colors.color("darkgrey"),
        )

        scaffold = Scaffold(
            appBar= AppBar(
                title=Text('Bottom Navigation Example'),
                elevation=2,
                shadowColor=Colors.rgba(0,0,0,0.2), 
                leading=IconButton(
                    child=Icon('bars'),
                    onPressed= self.toggle_drawer),
                actions=[
                IconButton(
                    child=Icon('bars'),
                    onPressed= self.toggle_end_drawer),
            ],
            ) if self.currentIndex == 0 else None,
            
            body=body_content,  # Use the selected content
            drawer= drawer,
            endDrawer= end_drawer,
            bottomNavigationBar=BottomNavigationBar(
                items=[
                    BottomNavigationBarItem(icon=Icon('home'), label='Home'),
                    BottomNavigationBarItem(icon=Icon('gear'), label='Settings'),
                ],
                onTap= self.on_tab_selected,
                currentIndex=self.currentIndex,
                #fixedColor=Colors.color('blue'),
                backgroundColor=Colors.color('white'),
                elevation=10,
                iconSize=30,
                selectedFontSize=18,
                unselectedFontSize=14,
                selectedItemColor=Colors.color('blue'),
                unselectedItemColor=Colors.color('grey'),
                showSelectedLabels=True,
                showUnselectedLabels=False,
            ),
            bottomSheet=BottomSheet(
                child=Column(
                    children=[
                        Text("This is a BottomSheet"),
                        IconButton(
                            child=Icon('minus'),
                            onPressed= self.hide_bottom_sheet
                            ),
                    ]
                ),
                height=300,
                backgroundColor=Colors.color("lightgrey"),
                enableDrag=True
            ),
            snackBar=snack_bar
        )

        self.framework.set_root(scaffold)

    def run(self):
        #self.framework.api.register_callback('on_tab_selected', self.on_tab_selected)
        #self.framework.api.register_callback('toggle_drawer', self.toggle_drawer)
        #self.framework.api.register_callback('toggle_end_drawer', self.toggle_end_drawer)
        #self.framework.api.register_callback('show_bottom_sheet', self.show_bottom_sheet)
        #self.framework.api.register_callback('hide_bottom_sheet', self.hide_bottom_sheet)
        #self.framework.api.register_callback('show_snack_bar', self.show_snack_bar)
        #self.framework.api.register_callback('undo', self.undo)
        self.update_ui()
        self.framework.run(title='MyApp')

if __name__ == "__main__":
    app = MyApp()
    app.run()
