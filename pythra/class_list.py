import re

file_path = "widgets.py"  # change to your actual file path

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Regex to match Python class definitions
class_names = re.findall(r'^\s*class\s+([A-Za-z_]\w*)', content, re.MULTILINE)

# Print them as a numbered list
for i, name in enumerate(class_names, start=1):
    print(f"{i}. {name}")
