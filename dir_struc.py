import os

def list_directory_tree(start_path):
    """
    Lists all subdirectories and files in a given directory in a tree-like format.

    Args:
        start_path (str): The path to the directory to start listing from.
    """
    if not os.path.isdir(start_path):
        print(f"Error: '{start_path}' is not a valid directory.")
        return

    print(f"Listing contents of: {start_path}")
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f'{subindent}{f}')

# Example usage:
if __name__ == "__main__":
    # You can change this to the directory you want to inspect
    directory_to_inspect = '.' # Current directory

    # Create some dummy directories and files for demonstration
    if not os.path.exists("test_dir"):
        os.makedirs("test_dir/subdir1/subsubdirA")
        os.makedirs("test_dir/subdir2")
        with open("test_dir/file1.txt", "w") as f:
            f.write("This is file1.")
        with open("test_dir/subdir1/file2.txt", "w") as f:
            f.write("This is file2.")
        with open("test_dir/subdir1/subsubdirA/file3.txt", "w") as f:
            f.write("This is file3.")
        with open("test_dir/subdir2/another_file.log", "w") as f:
            f.write("This is another log file.")
        print("Created dummy directory structure for demonstration.")

    list_directory_tree("test_dir")
    print("\n--- Listing current directory (excluding the dummy 'test_dir') ---")
    list_directory_tree(directory_to_inspect)
