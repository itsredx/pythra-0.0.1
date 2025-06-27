# generate_icons.py

# Path to the codepoints file you downloaded
CODEPOINTS_FILE = "C:\\Users\\SMILETECH COMPUTERS\\Documents\\pythra_0.0.2_new_state\\pythra\\codepoints.txt"
# Path where you want to save the generated Python file
OUTPUT_FILE = "pythra/icons.py"

def generate():
    icon_names = []
    with open(CODEPOINTS_FILE, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                icon_names.append(parts[0])

    with open(OUTPUT_FILE, 'w') as f:
        f.write("# pythra/icons.py\n")
        f.write("# This file is auto-generated. Do not edit manually.\n\n")
        f.write("from dataclasses import dataclass\n\n")
        f.write("@dataclass(frozen=True)\n")
        f.write("class IconData:\n")
        f.write('    """An immutable data class representing an icon from a font."""\n')
        f.write("    name: str\n")
        f.write("    fontFamily: str\n\n")
        f.write("class Icons:\n")
        f.write('    """A helper class containing static references to all Material Symbols."""\n')

        # Generate for all three styles
        styles = {
            "outlined": "Material Symbols Outlined",
            "rounded": "Material Symbols Rounded",
            "sharp": "Material Symbols Sharp"
        }

        for style_suffix, font_family in styles.items():
            for name in icon_names:
                # Python identifiers can't start with a number.
                var_name = f"_{name}" if name[0].isdigit() else name
                f.write(f"    {var_name}_{style_suffix} = IconData(name=\"{name}\", fontFamily=\"{font_family}\")\n")
            f.write("\n")

        # Create default versions (e.g., Icons.home points to Icons.home_outlined)
        for name in icon_names:
            var_name = f"_{name}" if name[0].isdigit() else name
            f.write(f"    {var_name} = {var_name}_outlined\n")

        print(f"Successfully generated {len(icon_names) * 4} icon references in {OUTPUT_FILE}")

if __name__ == "__main__":
    generate()