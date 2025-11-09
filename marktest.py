

import json
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
    Icon,
    Icons,
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
    Dropdown,
    DropdownController,
    DropdownTheme,
    VerticalDirection,
)
from plugins.markdown import MarkdownEditor
from plugins.markdown.controller import MarkdownEditorController
from plugins.markdown.utils.sys_font_loader import get_system_fonts_as_json

formatted_fonts_json = get_system_fonts_as_json()
# print(json.loads(formatted_fonts_json))
fonts = json.loads(formatted_fonts_json)
labels = []
for font in fonts:
    labels.append(font["label"])
    if font["label"] == "Verdana":
        print("val: ", font["val"])

class EditorPageState(State):
    def __init__(self):
        super().__init__()
        self.count = 0
        self.editor_controller = MarkdownEditorController()
        self.d_controller = DropdownController(selectedValue=labels[0])

        # --- THE CRITICAL FIX ---
        # Create the MarkdownEditor widget instance ONCE and store it.
        # It will now persist across all rebuilds.
        self.editor_widget = MarkdownEditor(
            key=Key("markdown_editor"),
            controller=self.editor_controller,
            show_grid=True
        )
        # --- END OF FIX ---

         # --- THE CRITICAL FIX ---
        # Create the entire STATIC layout tree for the editor ONCE.
        # This prevents the reconciler from destroying and recreating it on every build.
        self.editor_layout = Container(
                key=Key("editor_outer_container"),
                width="100%",
                height="70vh",
                child=Container(
                    key=Key("editor_container"),
                    width="100%",
                    height="70vh",
                    cssClass="editor-container",
                    child=Container(
                        key=Key("editor_inner"),
                        width="100%",
                        height="70vh",
                        cssClass="editor-inner-container",
                        child=self.editor_widget,
                    ),
                ),
            )
        # --- END OF FIX ---

        self.dropdown = Dropdown(
                controller=self.d_controller,
                key=Key("my_dropdown"),
                items=labels,
                onChanged=self.changeFont,
                dropDirection=VerticalDirection.DOWN,
                theme=DropdownTheme(
                    width=330,
                    dropDownHeight=500,
                    dropdownMargin=EdgeInsets.only(bottom=12),
                    fontSize=12,
                    borderWidth=0.0,
                    borderColor=Colors.transparent,
                    backgroundColor=(
                        Colors.hex("#837b7b")
                    ),
                    dropdownColor=(
                        Colors.hex("#837b7b")
                    ),
                ),
            )

    def bold(self):
        self.editor_controller.exec_command('bold')
        self.editor_controller.focus()

    def focus_editor(self):
        self.editor_controller.focus()
        # self.setState()

    def increment(self):
        self.count += 1
        print("Incremented count to:", self.count)
        self.setState()

    def setFont(self, font_family: str):
        self.editor_controller.set_font_name(font_family=font_family)
        self.editor_controller.focus()

    def changeFont(self, new_value):
        print("Font changed!: ", new_value)
        for font in fonts:
            if font["label"] == new_value:
                self.setFont(font["val"])

    def load_markdown(self):
        """Loads a sample Markdown string into the editor."""
        sample_md = """
# Hello, Markdown!

This content was loaded from a **Markdown** string in Python.

- Item 1
- Item 2

Here is a code block:
```python
def greet():
    print("Hello from a code block!")
greet()
```
"""
        self.editor_controller.load_from_markdown(sample_md)
        self.editor_controller.focus()
        self.setState()

    def export_markdown(self):
        """Exports the editor content and prints it to the console."""
        markdown_content = self.editor_controller.export_to_markdown()
        
        print("\n" + "="*20)
        print("EXPORTED MARKDOWN:")
        print("="*20)
        print(markdown_content)
        print("="*20 + "\n")

    # --- ADD A NEW HANDLER METHOD ---
    def replace_selection(self):
        """Replaces the selected text with a sample Markdown quote."""
        sample_quote_md = (
            "> This is a blockquote that was just inserted!\n>\n"
            "> It replaced the text you had highlighted."
            "\nhey there"
        )
        self.editor_controller.replace_selection_from_markdown(sample_quote_md)
        self.editor_controller.focus()
        # As per the docstring, we DO NOT call setState() here.

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
                                f"Markdown Editor  [Builds: {self.count}] ",
                                key=Key("editor_page_title"),
                                style=TextStyle(
                                    color=Colors.black,
                                    fontSize=24,
                                    fontWeight="bold",
                                ),
                            ),
                            ElevatedButton(
                        child=Text(
                                "increment",
                                key=Key("inc_editor_page_title"),  
                            ),
                        key=Key("inc_bold"),
                        onPressed=self.increment,
                    ),
                    Icon(
                        icon=Icons.javascript_rounded, 
                        key=Key("smile_icon"),
                        color=Colors.hex("#f0db4f"),
                        size=32,
                        ),
                        ],
                    ),
                    SizedBox(
                        height=16,
                        key=Key("header_spacer"),
                    ),
                    # --- NEW: Add the new buttons to the UI ---
                Row(
                    key=Key("control_buttons_row"),
                    children=[
                        ElevatedButton(
                            child=Text("Bold", key=Key("bold_btn_text")),
                            key=Key("elv_bold"),
                            onPressed=self.bold,
                        ),
                        SizedBox(width=10),
                        ElevatedButton(
                            child=Text("Load MD", key=Key("load_btn_text")),
                            key=Key("elv_load"),
                            onPressed=self.load_markdown,
                        ),
                        SizedBox(width=10),
                        ElevatedButton(
                            child=Text("Export MD", key=Key("export_btn_text")),
                            key=Key("elv_export"),
                            onPressed=self.export_markdown,
                        ),
                        SizedBox(width=10),
                        # --- ADD THE NEW BUTTON ---
                        ElevatedButton(
                            child=Text("Replace Selection", key=Key("replace_btn_text")),
                            key=Key("elv_replace"),
                            onPressed=self.replace_selection,
                        ),
                    ]
                ),
                # --- END OF NEW BUTTONS ---
                    SizedBox(
                        height=16,
                        key=Key("header_b_spacer"),
                    ),
                    # --- THE CRITICAL FIX ---
                    # Use the stored, persistent layout instance.
                    self.editor_layout,
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
