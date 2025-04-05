#framework/styles.py
from enum import Enum

Colors = Colors()

class EdgeInsets:
    """
    A class representing the padding or margin for a widget, with values for left, top, right, and bottom edges.

    Attributes:
        left (int): The padding/margin value on the left side.
        top (int): The padding/margin value on the top side.
        right (int): The padding/margin value on the right side.
        bottom (int): The padding/margin value on the bottom side.
    """
    def __init__(self, left=0, top=0, right=0, bottom=0):
        """
        Initializes the EdgeInsets object with values for left, top, right, and bottom edges.

        Args:
            left (int): Padding/margin value for the left side (default is 0).
            top (int): Padding/margin value for the top side (default is 0).
            right (int): Padding/margin value for the right side (default is 0).
            bottom (int): Padding/margin value for the bottom side (default is 0).
        """
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    @staticmethod
    def all(value):
        """
        Creates EdgeInsets with the same value for all four sides.

        Args:
            value (int): The padding/margin value for all sides.

        Returns:
            EdgeInsets: An EdgeInsets object with the given value for all sides.
        """
        return EdgeInsets(left=value, top=value, right=value, bottom=value)

    @staticmethod
    def symmetric(horizontal=0, vertical=0):
        """
        Creates EdgeInsets with symmetric horizontal and vertical values.

        Args:
            horizontal (int): Padding/margin value for the left and right sides (default is 0).
            vertical (int): Padding/margin value for the top and bottom sides (default is 0).

        Returns:
            EdgeInsets: An EdgeInsets object with symmetric horizontal and vertical values.
        """
        return EdgeInsets(left=horizontal, right=horizontal, top=vertical, bottom=vertical)

    @staticmethod
    def LRTB(left=0, right=0, top=0, bottom=0):
        """
        Creates EdgeInsets with specific values for left, right, top, and bottom edges.

        Args:
            left (int): Padding/margin value for the left side (default is 0).
            right (int): Padding/margin value for the right side (default is 0).
            top (int): Padding/margin value for the top side (default is 0).
            bottom (int): Padding/margin value for the bottom side (default is 0).

        Returns:
            EdgeInsets: An EdgeInsets object with the specified values for all sides.
        """
        return EdgeInsets(left=left, right=right, top=top, bottom=bottom)

    def to_css(self):
        """
        Converts the EdgeInsets object to a CSS string format.

        Returns:
            str: A string representing the CSS margin or padding for the EdgeInsets.
        """
        return f"{self.top}px {self.right}px {self.bottom}px {self.left}px"
    
    def to_int_vertical(self):
        """
        Calculates the total vertical padding/margin (top + bottom).

        Returns:
            int: The sum of the top and bottom values.
        """
        return self.top + self.bottom

    def to_int_horizontal(self):
        """
        Calculates the total horizontal padding/margin (left + right).

        Returns:
            int: The sum of the left and right values.
        """
        return self.right + self.left
    
    # --- Add __eq__ and __hash__ for compatibility ---
    def __eq__(self, other):
        if not isinstance(other, EdgeInsets):
            return NotImplemented
        return (self.left == other.left and
                self.top == other.top and
                self.right == other.right and
                self.bottom == other.bottom)

    def __hash__(self):
        # Hash a tuple of the relevant attributes
        return hash((self.left, self.top, self.right, self.bottom))

    # --- Optional: Add representation for debugging ---
    def __repr__(self):
         # Check for common patterns for cleaner representation
         if self.left == self.top == self.right == self.bottom:
              return f"EdgeInsets.all({self.left})"
         if self.left == self.right and self.top == self.bottom:
              return f"EdgeInsets.symmetric(horizontal={self.left}, vertical={self.top})"
         return f"EdgeInsets(left={self.left}, top={self.top}, right={self.right}, bottom={self.bottom})"

    # --- Optional: Add a way to get a simple representation for render_props ---
    def to_dict(self):
         # Or to_tuple if you prefer
         return {'left': self.left, 'top': self.top, 'right': self.right, 'bottom': self.bottom}
    


class Alignment:
    """
    A class representing the alignment of a widget within a container. Defines how content is aligned in both 
    the horizontal and vertical directions.

    Attributes:
        justify_content (str): The alignment of the content in the main axis (e.g., 'center', 'flex-start').
        align_items (str): The alignment of the content in the cross axis (e.g., 'center', 'flex-start').
    """
    def __init__(self, justify_content, align_items):
        """
        Initializes the Alignment object with horizontal and vertical alignment properties.

        Args:
            justify_content (str): The alignment in the main axis (horizontal).
            align_items (str): The alignment in the cross axis (vertical).
        """
        self.justify_content = justify_content
        self.align_items = align_items

    @staticmethod
    def center():
        """
        Returns an Alignment object with center alignment for both axes.

        Returns:
            Alignment: An Alignment object with 'center' for both horizontal and vertical alignment.
        """
        return Alignment('center', 'center')

    @staticmethod
    def top_left():
        """
        Returns an Alignment object with top-left alignment.

        Returns:
            Alignment: An Alignment object with 'flex-start' for both horizontal and vertical alignment.
        """
        return Alignment('flex-start', 'flex-start')

    @staticmethod
    def top_center():
        """
        Returns an Alignment object with top-center alignment.

        Returns:
            Alignment: An Alignment object with 'center' for horizontal and 'flex-start' for vertical alignment.
        """
        return Alignment('center', 'flex-start')

    @staticmethod
    def top_right():
        """
        Returns an Alignment object with top-right alignment.

        Returns:
            Alignment: An Alignment object with 'flex-end' for horizontal and 'flex-start' for vertical alignment.
        """
        return Alignment('flex-end', 'flex-start')

    @staticmethod
    def center_left():
        """
        Returns an Alignment object with center-left alignment.

        Returns:
            Alignment: An Alignment object with 'flex-start' for horizontal and 'center' for vertical alignment.
        """
        return Alignment('flex-start', 'center')

    @staticmethod
    def center_right():
        """
        Returns an Alignment object with center-right alignment.

        Returns:
            Alignment: An Alignment object with 'flex-end' for horizontal and 'center' for vertical alignment.
        """
        return Alignment('flex-end', 'center')

    @staticmethod
    def bottom_left():
        """
        Returns an Alignment object with bottom-left alignment.

        Returns:
            Alignment: An Alignment object with 'flex-start' for horizontal and 'flex-end' for vertical alignment.
        """
        return Alignment('flex-start', 'flex-end')

    @staticmethod
    def bottom_center():
        """
        Returns an Alignment object with bottom-center alignment.

        Returns:
            Alignment: An Alignment object with 'center' for horizontal and 'flex-end' for vertical alignment.
        """
        return Alignment('center', 'flex-end')

    @staticmethod
    def bottom_right():
        """
        Returns an Alignment object with bottom-right alignment.

        Returns:
            Alignment: An Alignment object with 'flex-end' for both horizontal and vertical alignment.
        """
        return Alignment('flex-end', 'flex-end')

    def to_css(self):
        """
        Converts the Alignment object to a CSS string for flexbox layout.

        Returns:
            str: A string representing the CSS for align-items and justify-content properties.
        """
        return f"display: flex; justify-content: {self.justify_content}; align-items: {self.align_items};"

class TextAlign:
    """
    A class representing the horizontal text alignment within a container.

    Attributes:
        text_align (str): The text alignment (e.g., 'center', 'left', 'right').
    """
    def __init__(self, text_align):
        """
        Initializes the TextAlign object with a specific text alignment.

        Args:
            text_align (str): The text alignment (e.g., 'center', 'left', 'right').
        """
        self.text_align = text_align

    @staticmethod
    def center():
        """
        Returns a TextAlign object with center alignment.

        Returns:
            TextAlign: A TextAlign object with 'center' alignment.
        """
        return TextAlign('center')

    @staticmethod
    def left():
        """
        Returns a TextAlign object with left alignment.

        Returns:
            TextAlign: A TextAlign object with 'flex-start' alignment.
        """
        return TextAlign('flex-start')

    @staticmethod
    def right():
        """
        Returns a TextAlign object with right alignment.

        Returns:
            TextAlign: A TextAlign object with 'flex-end' alignment.
        """
        return TextAlign('flex-end')

    def to_css(self):
        """
        Converts the TextAlign object to a CSS string for text alignment.

        Returns:
            str: A string representing the CSS text-align property.
        """
        return f"{self.text_align};"

class BoxConstraints:
    """
    A class representing the constraints for the width and height of a widget, including min and max values.

    Attributes:
        min_width (int): The minimum width of the widget.
        max_width (int): The maximum width of the widget.
        min_height (int): The minimum height of the widget.
        max_height (int): The maximum height of the widget.
    """
    def __init__(self, min_width=None, max_width=None, min_height=None, max_height=None):
        """
        Initializes the BoxConstraints object with optional minimum and maximum width/height values.

        Args:
            min_width (int): The minimum width of the widget (default is None).
            max_width (int): The maximum width of the widget (default is None).
            min_height (int): The minimum height of the widget (default is None).
            max_height (int): The maximum height of the widget (default is None).
        """
        self.min_width = min_width
        self.max_width = max_width
        self.min_height = min_height
        self.max_height = max_height

    def to_css(self):
        """
        Converts the BoxConstraints object to a CSS string for width and height constraints.

        Returns:
            str: A string representing the CSS for min-width, max-width, min-height, and max-height.
        """
        styles = []
        if self.min_width is not None:
            styles.append(f"min-width: {self.min_width}px;")
        if self.max_width is not None:
            styles.append(f"max-width: {self.max_width}px;")
        if self.min_height is not None:
            styles.append(f"min-height: {self.min_height}px;")
        if self.max_height is not None:
            styles.append(f"max-height: {self.max_height}px;")
        return " ".join(styles)

class Colors:
    """
    A class to handle color representations, including hexadecimal and RGBA formats.
    """
    
    def __getattr__(self, name):
        """
        Retrieves the color name as an attribute of the class.
        
        Args:
            name (str): The name of the color attribute.

        Returns:
            str: The color name.
        """
        return name

    @staticmethod
    def hex(hex_code):
        """
        Validates and returns a hexadecimal color code.

        Args:
            hex_code (str): A hexadecimal color code string.

        Raises:
            ValueError: If the hex code does not start with a '#'.

        Returns:
            str: The validated hex color code.
        """
        if not hex_code.startswith("#"):
            raise ValueError("Hex code should start with #")
        return hex_code

    @staticmethod
    def rgba(red, blue, green, alpha):
        """
        Returns an RGBA color string.

        Args:
            red (int): The red component of the color (0-255).
            blue (int): The blue component of the color (0-255).
            green (int): The green component of the color (0-255).
            alpha (float): The alpha (opacity) component (0.0 to 1.0).

        Returns:
            str: The RGBA color string.
        """
        return f"rgba({red}, {blue}, {green}, {alpha})"

    

class BoxShadow:
    """
    A class to represent a box shadow style for an element.
    """
    def __init__(self, color, offset, blurRadius, spreadRadius):
        """
        Initializes the box shadow.

        Args:
            color (str): The color of the shadow.
            offset (str): The offset of the shadow, e.g., '10px 10px'.
            blurRadius (int): The blur radius of the shadow in pixels.
            spreadRadius (int): The spread radius of the shadow in pixels.
        """
        self.color = color
        self.offset = offset
        self.blurRadius =blurRadius
        self.spreadRadius =spreadRadius

    def to_css(self):
        """
        Converts the box shadow to a CSS-compatible string.

        Returns:
            str: The CSS box shadow property.
        """
        return f'{self.offset} {self.blurRadius}px {self.spreadRadius}px {self.color}'


def Offset(x, y):
    """
    Creates an offset string for box shadows or other offset-based styles.

    Args:
        x (int): The horizontal offset.
        y (int): The vertical offset.

    Returns:
        str: The formatted offset string in pixels (e.g., '10px 10px').
    """
    offset_x = x
    offset_y = y

    return f'{offset_x}px {offset_y}px'


class BoxDecoration:
    """
    A class for defining and converting a box decoration style into CSS properties.
    """
    def __init__(self, color=None, border=None, borderRadius=None, boxShadow=None, transform=None, padding=None):
        """
        Initializes the BoxDecoration object.

        Args:
            color (str, optional): The background color of the box.
            border (str, optional): The border style of the box.
            borderRadius (int, optional): The border radius of the box in pixels.
            boxShadow (BoxShadow, optional): A BoxShadow object for the box shadow.
            transform (str, optional): A transformation applied to the box, such as rotation.
            padding (EdgeInsets, optional): Padding to be applied to the box.
        """
        if color:
            self.color = color 
        else:
            self.color = None
        self.border = border
        self.borderRadius = borderRadius
        self.boxShadow = boxShadow
        self.transform = transform
        self.padding = padding

    def to_css(self):
        """
        Converts the box decoration to a CSS-compatible string.

        Returns:
            str: The CSS box decoration property.
        """
        styles = []
        if self.color:
            styles.append(f"background-color: {self.color};")
        if self.border:
            styles.append(f"border: {self.border};")
        if self.borderRadius:
            styles.append(f"border-radius: {self.borderRadius}px;")
        if self.boxShadow:
            styles.append(f"box-shadow: {self.boxShadow.to_css()};")
        if self.transform:
            styles.append(f"transform: {self.transform};")
        if self.padding:
            styles.append(f"padding: {self.padding.to_css()};")
        return ' '.join(styles)

class ClipBehavior(Enum):
    """
    An enumeration for the various clip behavior options.
    """
    NONE = 'none'
    HARD_EDGE = 'hardEdge'
    ANTI_ALIAS = 'antiAlias'
    ANTI_ALIAS_WITH_SAVE_LAYER = 'antiAliasWithSaveLayer'
 
class ImageFit():
    """
    A class to represent different image fit options for an element.
    """
    CONTAIN = 'contain'
    COVER = 'cover'
    FILL = 'fill'
    NONE = 'none'
    SCALE_DOWN = 'scale-down'

class MainAxisSize:
    """
    A class to represent main axis sizing options.
    """
    MIN = 'min'
    MAX = 'max'

class MainAxisAlignment:
    """
    A class to represent main axis alignment options for Flex and Row widgets.
    """
    START = 'flex-start'
    END = 'flex-end'
    CENTER = 'center'
    SPACE_BETWEEN = 'space-between'
    SPACE_AROUND = 'space-around'
    SPACE_EVENLY = 'space-evenly'

class CrossAxisAlignment:
    """
    A class to represent cross axis alignment options for Flex and Row widgets.
    """
    START = 'flex-start'
    END = 'flex-end'
    CENTER = 'center'
    STRETCH = 'stretch'
    BASELINE = 'baseline'
    
class Axis:
    """
    A class to represent axis options for Flex and other layout widgets.
    """
    VERTICAL = 'vertical'
    HORIZONTAL = 'horizontal'
    
class TextStyle:
    """
    A class representing text style properties for a widget.
    
    Attributes:
        color (str): The color of the text.
        fontSize (int): The size of the font in pixels.
        fontWeight (str): The weight of the font (e.g., 'bold', 'normal').
        fontStyle (str): The style of the font (e.g., 'italic').
        letterSpacing (int): The spacing between letters in pixels.
        wordSpacing (int): The spacing between words in pixels.
        textDecoration (str): The text decoration (e.g., 'underline', 'line-through').
    
    Methods:
        to_css(): Converts the text style properties to a CSS string.
    """
    def __init__(self, color=None, fontSize=None, fontWeight=None, fontStyle=None, letterSpacing=None, wordSpacing=None, textDecoration=None):
        self.color = color
        self.fontSize = fontSize
        self.fontWeight = fontWeight
        self.fontStyle = fontStyle
        self.letterSpacing = letterSpacing
        self.wordSpacing = wordSpacing
        self.textDecoration = textDecoration

    def to_css(self):
        """
        Converts the text style attributes to a CSS string.

        Returns:
            str: A string representing the text style in CSS format.
        """
        style = ""
        if self.color:
            style += f"color: {self.color};"
        if self.fontSize:
            style += f"font-size: {self.fontSize}px;"
        if self.fontWeight:
            style += f"font-weight: {self.fontWeight};"
        if self.fontStyle:
            style += f"font-style: {self.fontStyle};"
        if self.letterSpacing:
            style += f"letter-spacing: {self.letterSpacing}px;"
        if self.wordSpacing:
            style += f"word-spacing: {self.wordSpacing}px;"
        if self.textDecoration:
            style += f"text-decoration: {self.textDecoration};"
        return style


class BorderStyle:
    """
    A class representing various border styles.
    
    This class defines the different types of border styles that can be applied to widgets.

    Attributes:
        NONE (str): No border.
        DOTTED (str): Dotted border.
        DASHED (str): Dashed border.
        SOLID (str): Solid border.
        DOUBLE (str): Double border.
        GROOVE (str): Groove border.
        RIDGE (str): Ridge border.
        INSET (str): Inset border.
        OUTSET (str): Outset border.
        HIDDEN (str): Hidden border.
    """
    NONE = 'none'
    DOTTED = 'dotted'
    DASHED = 'dashed'
    SOLID = 'solid'
    DOUBLE ='double'
    GROOVE = 'groove'
    RIDGE = 'ridge'
    INSET = 'inset'
    OUTSET = 'outset'
    HIDDEN = 'hidden'


class BorderRadius:
    """
    A class for defining the border radius for each corner of a widget.
    
    Attributes:
        top_left (int): The top-left corner radius in pixels.
        top_right (int): The top-right corner radius in pixels.
        bottom_right (int): The bottom-right corner radius in pixels.
        bottom_left (int): The bottom-left corner radius in pixels.
    
    Methods:
        all(value): Creates a border radius where all corners are the same.
        to_css(): Converts the border radius properties to a CSS string.
    """
    @staticmethod
    def all(value):
        """
        Creates a border radius where all corners are the same.
        
        Args:
            value (int): The radius value for all corners.

        Returns:
            BorderRadius: A BorderRadius instance with the same value for all corners.
        """
        return BorderRadius(value, value, value, value)
    
    def __init__(self, top_left, top_right, bottom_right, bottom_left):
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_right = bottom_right
        self.bottom_left = bottom_left
    
    def to_css(self):
        """
        Converts the border radius properties to a CSS string.

        Returns:
            str: A string representing the border radius in CSS format.
        """
        return f"border-radius: {self.top_left}px {self.top_right}px {self.bottom_right}px {self.bottom_left}px;"


class BorderSide:
    """
    A class representing the properties of a border side.

    Attributes:
        width (int): The width of the border.
        style (str): The style of the border (e.g., 'solid', 'dotted').
        color (str): The color of the border.
        borderRadius (int): The radius of the border corners.

    Methods:
        to_css(): Converts the border side properties to a CSS string.
        border_to_css(): Returns the border properties in a shorthand CSS format.
        to_int(): Returns the width value multiplied by 2.
    """
    def __init__(self, width=None, style=None, color=None, borderRadius=None):
        self.width = width
        self.style = style
        self.color = color
        self.borderRadius = borderRadius

    def to_css(self):
        """
        Converts the border side properties to a CSS string.

        Returns:
            str: A string representing the border side in CSS format.
        """
        
        width = f"border-width: {self.width}px;" if self.width else ''
        style = f"border-style: {self.style};" if self.style else ''
        color = f"border-color: {self.color};" if self.color else ''
        radius = f"border-radius: {self.borderRadius}px;" if self.borderRadius else ''
        return f"{width} {style} {color} {radius}"

    def border_to_css(self):
        """
        Returns the border properties in a shorthand CSS format.

        Returns:
            str: A shorthand string representing the border properties.
        """
        width = f"{self.width}px" if self.width else ''
        style = self.style if self.style else ''
        color = self.color if self.color else ''
        radius = f"{self.borderRadius}px" if self.borderRadius else ''
        return f"{style} {width} {color} {radius}"

    def to_int(self):
        """
        Returns the width value multiplied by 2.

        Returns:
            int: The width value multiplied by 2.
        """
        return self.width + self.width

class ButtonStyle:
    """
    A class representing the style properties of a button.
    
    Attributes:
        backgroundColor (str): The background color of the button.
        foregroundColor (str): The text color of the button.
        overlayColor (str): The color of the overlay when the button is pressed.
        shadowColor (str): The color of the button's shadow.
        elevation (int): The elevation (shadow) of the button.
        padding (Padding): The padding around the button's content.
        minimumSize (tuple): The minimum size of the button in pixels (width, height).
        side (BorderSide): The border style for the button.
        shape (int): The border radius of the button.
        textStyle (TextStyle): The text style for the button's text.
        alignment (Alignment): The alignment of the button's content.
        icon (str): The URL of the icon displayed on the button.

    Methods:
        to_css(): Converts the button style properties to a CSS string.
    """
    def __init__(self, backgroundColor=None, foregroundColor=None, overlayColor=None, shadowColor=None,
                 elevation=None, padding=None, minimumSize=None, side=None, shape=None, 
                 textStyle=None, alignment=None, icon=None):
        self.backgroundColor = backgroundColor
        self.foregroundColor = foregroundColor
        self.overlayColor = overlayColor
        self.shadowColor = shadowColor
        self.elevation = elevation
        self.padding = padding
        self.minimumSize = minimumSize
        self.side = side
        self.shape = shape
        self.textStyle = textStyle
        self.alignment = alignment
        self.icon = icon

    def to_css(self):
        """
        Converts the button style properties to a CSS string.

        Returns:
            str: A string representing the button style in CSS format.
        """
        styles = []
        if self.backgroundColor:
            styles.append(f"background-color: {self.backgroundColor};")
        if self.foregroundColor:
            styles.append(f"color: {self.foregroundColor};")
        if self.shadowColor:
            styles.append(f"box-shadow: 0px 0px {self.elevation or 0}px {self.shadowColor};")
        if self.padding:
            styles.append(f"padding: {self.padding.to_css()};")
        if self.minimumSize:
            styles.append(f"min-width: {self.minimumSize[0]}px; min-height: {self.minimumSize[1]}px;")
        if self.side:
            styles.append(self.side.to_css())
        else:
            styles.append("border: none;")
        if self.shape:
            styles.append(f"border-radius: {self.shape}px;")
        if self.textStyle:
            styles.append(self.textStyle.to_css())
        if self.alignment:
            styles.append(self.alignment.to_css())
        if self.icon:
            styles.append(f"background-image: url({self.icon}); background-size: contain; background-repeat: no-repeat;")
        return ' '.join(styles)


class ScrollPhysics:
    """
    Specifies the scrolling behavior of a widget.

    Attributes:
        BOUNCING: Allows scrolling beyond content bounds with a spring-like effect.
        CLAMPING: Prevents scrolling beyond content bounds.
        ALWAYS_SCROLLABLE: Enables scrolling even if content does not overflow.
        NEVER_SCROLLABLE: Disables scrolling regardless of content size.
    """
    BOUNCING = 'bouncing'
    CLAMPING = 'clamping'
    ALWAYS_SCROLLABLE = 'alwaysScrollable'
    NEVER_SCROLLABLE = 'neverScrollable'
    
class Overflow:
    """
    Defines how content overflow is handled in a widget.

    Attributes:
        VISIBLE: Content is visible beyond the bounds of the widget.
        HIDDEN: Content is clipped to the bounds of the widget.
        SCROLL: Adds scrolling to manage content overflow.
        AUTO: Automatically decides based on the content size.
    """
    VISIBLE = 'visible'
    HIDDEN = 'hidden'
    SCROLL = 'scroll'
    AUTO = 'auto'    

class StackFit:
    """
    Determines how children are sized within a Stack widget.

    Attributes:
        loose: Children take up as little space as possible.
        expand: Children expand to fill the Stack's available space.
        passthrough: Children retain their original size.
    """
    loose = 'loose'
    expand = 'expand'
    passthrough = 'passthrough'

class TextDirection:
    """
    Specifies the direction in which text flows.

    Attributes:
        LTR: Text flows from left to right.
        RTL: Text flows from right to left.
    """
    LTR = 'ltr'
    RTL = 'rtl'

class TextBaseline():
    """
    Specifies the alignment of text baselines.

    Attributes:
        alphabetic: Aligns the baseline to the bottom of alphabetic characters.
        ideographic: Aligns the baseline to the middle of ideographic characters.
    """
    alphabetic = 'text-bottom'
    ideographic = 'middle'

class VerticalDirection:
    """
    Determines the vertical arrangement of children.

    Attributes:
        DOWN: Children are arranged from top to bottom.
        UP: Children are arranged from bottom to top.
    """
    DOWN = 'down'
    UP = 'up'


class BoxFit:
    """
    Defines how an image or box is fitted into its allocated space.

    Attributes:
        CONTAIN: Scales to fit within the bounds while maintaining aspect ratio.
        COVER: Scales to fill the bounds while maintaining aspect ratio, possibly cropping.
        FILL: Stretches to fill the bounds, disregarding aspect ratio.
        NONE: Does not scale; the content's original size is used.
    """
    CONTAIN = 'contain'
    COVER = 'cover'
    FILL = 'fill'
    NONE = 'none'
