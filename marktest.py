from pythra import (
    Framework,
    StatefulWidget,
    State,
    Column,
    Row,
    Key,
    Widget,
    Container,
    Text,
    Colors,
    Center,
    SizedBox,
    EdgeInsets,
    TextStyle,
    Expanded,
    ClipPath,
    GradientTheme,
    CrossAxisAlignment,
    ElevatedButton,
)
from plugins.markdown import MarkdownEditor
from plugins.markdown.controller import MarkdownEditorController


class EditorPageState(State):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.editor_controller = MarkdownEditorController()

    def bold(self):
        self.editor_controller.exec_command('bold')
        self.editor_controller.focus()
        # self.setState()

    def increment(self):
        self.count += 1
        self.setState()

    def build(self) -> Widget:
        return Container(
            key=Key("editor_page_wrapper_container"),
            height="100vh",
            width="100vw",
            color=Colors.white,
            padding=EdgeInsets.all(16),
            child=Column(
                key=Key("editor_page_column"),
                children=[
                    Row(
                        key=Key("editor_page_header"),
                        children=[
                            Text(
                                f"Markdown Editor",
                                key=Key("editor_page_title"),
                                style=TextStyle(
                                    color=Colors.black,
                                    fontSize=24,
                                    fontWeight="bold",
                                ),
                            ),
                        ],
                    ),
                    SizedBox(
                        height=16,
                        key=Key("header_spacer"),
                    ),
                    ElevatedButton(
                        child=Text(
                                "Bold",
                                key=Key("bold_editor_page_title"),  
                            ),
                        key=Key("elv_bold"),
                        onPressed=self.bold,
                    ),
                    SizedBox(
                        height=16,
                        key=Key("header_b_spacer"),
                    ),
                    Expanded(
                        child=Container(
                            key=Key("editor_outer_container"),
                            width="100%",
                            height="100%",
                            child=Container(
                                key=Key("editor_container"),
                                width="100%",
                                height="100%",
                                cssClass="editor-container",
                                child=Container(
                                    key=Key("editor_inner"),
                                    width="100%",
                                    height="100%",
                                    cssClass="editor-inner-container",
                                    child=MarkdownEditor(
                                        key=Key("markdown_editor"),
                                        controller=self.editor_controller
                                    ),
                                ),
                            ),
                        ),
                    ),
                ],
            ),
        )


class EditorPage(StatefulWidget):
    def createState(self) -> EditorPageState:
        return EditorPageState()


class Main(StatefulWidget):
    def createState(self):
        class MainState(State):
            def build(self):
                return EditorPage(key=Key("editor_page"))
        return MainState()


if __name__ == "__main__":
    app = Framework.instance()
    app.set_root(Main(key=Key("root")))
    app.run(title="Markdown Editor Test")
