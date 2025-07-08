from pythra.styles import *
from pythra.widgets import Text
from pythra.base import *

# Output CSS and HTML
print(BoxDecoration(color=Colors.gradient("hdggs", Colors.red, Colors.blue)).to_css_dict())  # Shared CSS for both columns
# print(column1.to_html())  # HTML for column1
# print(column2.to_html())  # HTML for column2 (reuses shared CSS)
