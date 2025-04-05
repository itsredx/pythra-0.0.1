from framework.styles import *
from framework.widgets import Text
from framework.base import *

class Column(Widget):
    shared_styles = {}  # Shared CSS for Column styles

    def __init__(self, children=None, key=None, mainAxisAlignment=MainAxisAlignment.START, mainAxisSize=MainAxisSize.MAX, crossAxisAlignment=CrossAxisAlignment.CENTER, textDirection=TextDirection.LTR, verticalDirection=VerticalDirection.DOWN, textBaseline=TextBaseline.alphabetic):
        super().__init__(widget_id=None)
        self.children = children or []
        self.key = key
        self.mainAxisAlignment = mainAxisAlignment
        self.mainAxisSize = mainAxisSize
        self.crossAxisAlignment = crossAxisAlignment
        self.textDirection = textDirection
        self.verticalDirection = verticalDirection
        self.textBaseline = textBaseline

        # Generate a unique style key for deduplication
        self.style_key = (
            self.mainAxisAlignment,
            self.mainAxisSize,
            self.crossAxisAlignment,
            self.textDirection,
            self.verticalDirection,
            self.textBaseline,
        )

        # Assign a shared CSS class based on the style key
        if self.style_key not in Column.shared_styles:
            self.css_class = f"shared-column-{len(Column.shared_styles)}"
            Column.shared_styles[self.style_key] = self.css_class
        else:
            self.css_class = Column.shared_styles[self.style_key]

        # Add children widgets
        for child in self.children:
            self.add_child(child) if child else None  # Register each child widget

    def to_css(self):
        """Generate the shared CSS rules for Column styles."""
        css_rules = ""
        for style_key, css_class in Column.shared_styles.items():
            (
                mainAxisAlignment,
                mainAxisSize,
                crossAxisAlignment,
                textDirection,
                verticalDirection,
                textBaseline,
            ) = style_key

            # Build CSS for the specific style key
            styles = (
                f"display: flex; "
                f"flex-direction: column; "
                f"justify-content: {mainAxisAlignment}; "
                f"align-items: {crossAxisAlignment}; "
                f"direction: {textDirection}; "
                f"vertical-align: {textBaseline};"
            )
            if mainAxisSize == 'min':
                styles += "height: auto;"
            elif mainAxisSize == 'max':
                styles += "width: 100%;"

            css_rules += f"""
            .{css_class} {{
                {styles}
            }}
            """
        return css_rules

    def to_html(self):
        """Generate HTML for the Column widget."""
        children_html = ''.join([child.to_html() for child in self.children])

        return f"<div id='{self.widget_id()}' class='{self.css_class}'>{children_html}</div>"


# Define some child widgets
child1 = Text("Child 1")
child2 = Text("Child 2")

# Create two Columns with the same style
column1 = Column(
    children=[child1, child2],
    mainAxisAlignment=MainAxisAlignment.CENTER,
    crossAxisAlignment=CrossAxisAlignment.START
)

column2 = Column(
    children=[child2],
    mainAxisAlignment=MainAxisAlignment.CENTER,
    crossAxisAlignment=CrossAxisAlignment.START
)

# Output CSS and HTML
print(column1.to_css())  # Shared CSS for both columns
print(column1.to_html())  # HTML for column1
print(column2.to_html())  # HTML for column2 (reuses shared CSS)
