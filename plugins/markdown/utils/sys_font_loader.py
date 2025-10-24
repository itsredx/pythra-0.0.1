import json
from matplotlib import font_manager

def get_system_fonts_as_json():
    """
    Finds all unique system font families and formats them into a JSON string
    suitable for a dropdown, with common fonts placed at the top.
    
    Returns:
        str: A JSON string representing a list of font dictionaries.
    """
    
    # 1. Define a list of common, high-priority fonts.
    # The "System Default" uses a robust CSS font stack.
    default_fonts = [
        { "label": "System Default", "val": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif' },
        { "label": "Arial", "val": "Arial, sans-serif" },
        { "label": "Verdana", "val": "Verdana, sans-serif" },
        { "label": "Times New Roman", "val": "'Times New Roman', serif" },
        { "label": "Georgia", "val": "Georgia, serif" },
        { "label": "Courier New", "val": "'Courier New', monospace" },
    ]
    
    # 2. Get all unique font family names from the system.
    # We use a set to automatically handle duplicates.
    try:
        font_paths = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
        font_names = sorted({font_manager.FontProperties(fname=fname).get_name() for fname in font_paths})
    except Exception as e:
        print(f"Warning: Could not get system fonts. Falling back to defaults. Error: {e}")
        font_names = []

    # 3. Combine the lists.
    # Start with our defaults, then add unique system fonts that aren't already in the default list.
    final_font_list = list(default_fonts)
    default_labels = {font['label'] for font in default_fonts}
    
    for name in font_names:
        if name not in default_labels:
            final_font_list.append({"label": name, "val": name})
            
    # 4. Convert the final list to a JSON string.
    return json.dumps(final_font_list, indent=2)

# --- Main execution ---
if __name__ == "__main__":
    formatted_fonts_json = get_system_fonts_as_json()
    print(formatted_fonts_json)

    # In your real application, you would pass this JSON string to your
    # frontend when initializing the editor. For example:
    #
    # editor_options = {
    #     "callback": "my_callback",
    #     "instanceId": "my_editor",
    #     "fontList": json.loads(formatted_fonts_json) # Pass the actual list object
    # }