# pythra_cli/main.py

import typer
import sys
import os
import subprocess
import threading
import time
import shutil
from pathlib import Path

# The Typer app object that will be the entry point
app = typer.Typer(
    name="pythra",
    help="The official CLI for the Pythra Framework.",
    add_completion=False
)

# ... (Keep your AppProcessManager and keyboard_listener classes here) ...

@app.command()
def run(
    file_path: str = typer.Argument("lib/main.py", help="The path to the main application file to run."),
):
    """
    Runs a Pythra application with clean restart enabled.
    Defaults to running 'lib/main.py' in the current directory.
    """
    # ... (Your existing 'run' logic is perfect here) ...

@app.command(name="create-project")
def create_project(
    project_name: str = typer.Argument(..., help="The name of the new project directory.")
):
    """
    Creates a new Pythra project with a standard directory structure.
    """
    project_path = Path.cwd() / project_name
    
    if project_path.exists():
        print(f"❌ Error: Directory '{project_name}' already exists.")
        raise typer.Exit(code=1)

    print(f"✅ Creating a new Pythra project in: {project_path}")

    try:
        # This is the key: find the path to the template *within the installed package*.
        # We assume `pythra_cli` and `project_template` are sibling directories.
        template_path = Path(__file__).parent.parent / 'project_template'
        
        # Copy the entire template directory to the new project path
        shutil.copytree(template_path, project_path)
        
        print("\n🎉 Project created successfully!")
        print("To get started:")
        print(f"  1. cd {project_name}")
        print(f"  2. (Optional) Create a virtual environment and install dependencies.")
        print(f"  3. pythra run") # User can now just type `pythra run`

    except Exception as e:
        print(f"❌ An error occurred while creating the project:")
        print(e)
        # Clean up a partially created directory if something went wrong
        if project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()