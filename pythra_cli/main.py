import typer
import sys
import os
import subprocess
import threading
import time
import shutil
from pathlib import Path

# --- Pythra Framework Imports ---
# This will work once the package is installed in editable mode.
# We include a fallback for running the script directly during development.
try:
    from pythra import Framework, Widget
except ImportError:
    # This allows the CLI to find the framework when you are developing the CLI itself.
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from pythra import Framework, Widget


# Create the main Typer application object
app = typer.Typer(
    name="pythra",
    help="The official CLI for the Pythra Framework.",
    add_completion=False
)

# --- Process Manager for the `run` command ---

class AppProcessManager:
    """
    Manages a Pythra application running as a child process,
    allowing it to be killed and restarted on command.
    """
    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)
        self.process: subprocess.Popen = None

    def start(self):
        """Starts the application as a new child process."""
        print(f"\n🚀 Launching: python {os.path.basename(self.file_path)}")
        command = [sys.executable, "-u", self.file_path]
        self.process = subprocess.Popen(command)

    def restart(self):
        """Kills the current application process and starts a new one."""
        print("--- [Clean Restart Triggered] ---")
        if self.process and self.process.poll() is None:
            print(f"Terminating process {self.process.pid}...")
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                print("Process did not terminate gracefully, forcing kill.")
                self.process.kill()
            print("Process terminated.")
        
        time.sleep(0.5) # Give the OS a moment to release resources
        self.start()

def keyboard_listener(manager: AppProcessManager):
    """Listens for the 'r' key on a background thread."""
    print("\n🔥 Clean Restart active. Press [r] + Enter to trigger.")
    for line in sys.stdin:
        if line.strip().lower() == 'r':
            manager.restart()
        # You could add a 'q' command here to quit gracefully if desired

# --- CLI Commands ---

@app.command()
def run(
    file_path: str = typer.Argument(
        "lib/main.py",
        help="The path to the main application file to run.",
        show_default=True,
    ),
):
    """
    Runs a Pythra application with a real-time, clean restart feature.
    """
    target_file = Path(file_path)
    if not target_file.exists():
        # A common case: user is in the project root but didn't specify the file.
        if Path.cwd().name == target_file.parent.name and (Path.cwd() / file_path).exists():
            target_file = Path.cwd() / file_path
        else:
            print(f"❌ Error: Application file not found at '{file_path}'")
            raise typer.Exit(code=1)

    manager = AppProcessManager(file_path=str(target_file))
    listener_thread = threading.Thread(target=keyboard_listener, args=(manager,), daemon=True)
    
    manager.start()
    listener_thread.start()

    # Wait for the process to exit (e.g., user closes the window)
    if manager.process:
        manager.process.wait()

    print("👋 Application process has exited.")

@app.command(name="create-project")
def create_project(
    project_name: str = typer.Argument(..., help="The name for the new project directory.")
):
    """
    Creates a new Pythra project with a standard directory structure and starter code.
    """
    project_path = Path.cwd() / project_name
    
    if project_path.exists():
        print(f"❌ Error: Directory '{project_name}' already exists.")
        raise typer.Exit(code=1)

    print(f"✅ Creating a new Pythra project in: {project_path}")

    try:
        # Find the path to the template *within the installed package*.
        # This makes the CLI work regardless of where it's run from.
        template_path = Path(__file__).parent.parent / 'project_template'
        
        if not template_path.exists():
            print("❌ Fatal Error: Could not find the project template directory.")
            print(f"   (Searched at: {template_path})")
            raise typer.Exit(code=1)

        # Copy the entire template directory to the new project path
        shutil.copytree(template_path, project_path)
        
        print("\n🎉 Project created successfully!")
        print("\nTo get started:")
        print(f"  1. cd {project_name}")
        print(f"  2. (Optional) Create a Python virtual environment.")
        print(f"  3. pythra run")

    except Exception as e:
        print(f"❌ An error occurred while creating the project:")
        print(e)
        if project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()