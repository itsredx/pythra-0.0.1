# plugins/markdown/style.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pythra.styles import Colors  # Import Pythra's color system

@dataclass
class EditorGridStyle:
    """Styling configuration for the editor's grid background."""
    enabled: bool = False
    dot_color: str = Colors.GREY
    dot_size: int = 1
    dot_spacing: int = 20
    background_color: str = Colors.GREY

@dataclass
class EditorToolbarStyle:
    """Styling configuration for the editor's toolbar."""
    background_color: str = Colors.WHITE
    border_color: str = Colors.GREY
    hover_color: str = Colors.BLUE
    active_color: str = Colors.BLUE
    icon_color: str = Colors.GREY
    separator_color: str = Colors.GREY
    height: str = "40px"
    button_padding: str = "8px"
    border_radius: str = "4px"
    shadow: str = "0 2px 4px rgba(0,0,0,0.1)"

@dataclass
class EditorContentStyle:
    """Styling configuration for the editor's content area."""
    text_color: str = Colors.GREY
    background_color: str = Colors.WHITE
    placeholder_color: str = Colors.GREY
    selection_color: str = Colors.BLUE
    link_color: str = Colors.BLUE
    code_background: str = Colors.GREY
    blockquote_border: str = Colors.GREY
    heading_color: str = Colors.GREY
    font_family: str = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    font_size: str = "16px"
    line_height: str = "1.5"
    padding: str = "20px"

@dataclass
class EditorStyle:
    """Main style configuration for the Markdown editor."""
    DEFAULT_HEIGHT: str = '500px'
    DEFAULT_WIDTH: str = '100%'
    
    # Theme colors
    accent_color: str = Colors.BLUE
    accent_hover: str = Colors.BLUE
    error_color: str = Colors.RED
    
    # Sub-styles
    grid: EditorGridStyle = field(default_factory=EditorGridStyle)
    toolbar: EditorToolbarStyle = field(default_factory=EditorToolbarStyle)
    content: EditorContentStyle = field(default_factory=EditorContentStyle)
    
    # Border styling
    border_color: str = Colors.GREY
    border_radius: str = "4px"
    border_width: str = "1px"
    
    # Focus state
    focus_ring_color: str = Colors.BLUE
    focus_ring_width: str = "2px"
    
    # Sizing
    min_height: str = "200px"
    max_height: str = "800px"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the style configuration to a dictionary for JS."""
        return {
            'defaults': {
                'height': self.DEFAULT_HEIGHT,
                'width': self.DEFAULT_WIDTH,
                'minHeight': self.min_height,
                'maxHeight': self.max_height,
            },
            'theme': {
                'accentColor': self.accent_color,
                'accentHover': self.accent_hover,
                'errorColor': self.error_color,
                'borderColor': self.border_color,
                'borderRadius': self.border_radius,
                'borderWidth': self.border_width,
                'focusRing': {
                    'color': self.focus_ring_color,
                    'width': self.focus_ring_width,
                }
            },
            'grid': {
                'enabled': self.grid.enabled,
                'dotColor': self.grid.dot_color,
                'dotSize': self.grid.dot_size,
                'dotSpacing': self.grid.dot_spacing,
                'backgroundColor': self.grid.background_color,
            },
            'toolbar': {
                'backgroundColor': self.toolbar.background_color,
                'borderColor': self.toolbar.border_color,
                'hoverColor': self.toolbar.hover_color,
                'activeColor': self.toolbar.active_color,
                'iconColor': self.toolbar.icon_color,
                'separatorColor': self.toolbar.separator_color,
                'height': self.toolbar.height,
                'buttonPadding': self.toolbar.button_padding,
                'borderRadius': self.toolbar.border_radius,
                'shadow': self.toolbar.shadow,
            },
            'content': {
                'textColor': self.content.text_color,
                'backgroundColor': self.content.background_color,
                'placeholderColor': self.content.placeholder_color,
                'selectionColor': self.content.selection_color,
                'linkColor': self.content.link_color,
                'codeBackground': self.content.code_background,
                'blockquoteBorder': self.content.blockquote_border,
                'headingColor': self.content.heading_color,
                'fontFamily': self.content.font_family,
                'fontSize': self.content.font_size,
                'lineHeight': self.content.line_height,
                'padding': self.content.padding,
            }
        }

