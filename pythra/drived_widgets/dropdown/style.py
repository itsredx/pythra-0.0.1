from ...styles import *

# ==============================================================================
# 1. THEME (The Data and Style Models)
# ==============================================================================



class DerivedDropdownTheme:
    """Encapsulates the styling properties for the DerivedDropdown widget."""

    def __init__(
        self,
        backgroundColor=Colors.hex("#FFFFFF"),
        borderColor=Colors.hex("#AAAAAA"),
        width=45,
        borderWidth=1.0,
        borderRadius=8.0,
        textColor=Colors.hex("#000000"),
        fontSize=14.0,
        padding=EdgeInsets.symmetric(vertical=8, horizontal=12),
        dropdownColor=Colors.hex("#FFFFFF"),
        dropdownTextColor=Colors.hex("#000000"),
        selectedItemColor=Colors.hex("#E0E0E0"),
        selectedItemShape= BorderRadius.all(4),
        dropdownMargin=EdgeInsets.only(top=45),
        itemPadding = EdgeInsets.symmetric(horizontal=12, vertical=8),
    ):
        self.backgroundColor = backgroundColor
        self.borderColor = borderColor
        self.width = width
        self.borderWidth = borderWidth
        self.borderRadius = borderRadius
        self.textColor = textColor
        self.fontSize = fontSize
        self.padding = padding
        self.dropdownColor = dropdownColor
        self.dropdownTextColor = dropdownTextColor
        self.selectedItemColor = selectedItemColor
        self.selectedItemShape = selectedItemShape
        self.dropdownMargin = dropdownMargin
        self.itemPadding = itemPadding