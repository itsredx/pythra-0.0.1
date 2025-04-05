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

    def update_ui(self):
        # Define the content for each tab
        content = [
            Container(
                child=Text('Welcome to the Home Page!'),
                padding=EdgeInsets.all(20),
                margin=EdgeInsets.all(20),
                constraints= BoxConstraints(max_width= 300, max_height=300),
                decoration=BoxDecoration(
                    color=Colors.color('lightblue'),
                    borderRadius=25,
                    boxShadow=BoxShadow(
                        color=Colors.rgba(0, 0, 0, 0.5),
                        offset=Offset(1, 3),
                        blurRadius=6,
                        spreadRadius=2
                    )
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
                    boxShadow=BoxShadow(
                        color=Colors.rgba(0, 0, 0, 0.5),
                        offset=Offset(2, 3),
                        blurRadius=7,
                        spreadRadius=2
                    )
                )
                )
        ]

        # Set the content based on the current index
        body_content = content[self.currentIndex]

        drawer = Drawer(
            child=Text('hello')
        )

        scaffold = Scaffold(
            appBar= AppBar(
                title=Text('Bottom Navigation Example'),
                elevation=6,
                shadowColor=Colors.rgba(0,0,0,0.2), 
                leading=IconButton(
                    child=Icon('bars'),
                    onPressed='toggle_drawer')
            ) if self.currentIndex == 0 else None,
            body=body_content,  # Use the selected content
            drawer= drawer,
            bottomNavigationBar=BottomNavigationBar(
                items=[
                    BottomNavigationBarItem(icon=Icon('home'), label='Home'),
                    BottomNavigationBarItem(icon=Icon('gear'), label='Settings'),
                ],
                onTap='on_tab_selected',
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
            )
        )

        self.framework.set_root(scaffold)

    def run(self):
        self.framework.api.register_callback('on_tab_selected', self.on_tab_selected)
        self.framework.api.register_callback('toggle_drawer', self.toggle_drawer)
        self.update_ui()
        self.framework.run(title='MyApp')

if __name__ == "__main__":
    app = MyApp()
    app.run()
