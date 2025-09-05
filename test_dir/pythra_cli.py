import typer
import sys
import os
import subprocess
import time

# Create the main Typer application object
app = typer.Typer(
    name="pythra",
    help="A simple and robust CLI to run and manage your Pythra applications.",
    add_completion=False
)

@app.command()
def run(
    file_path: str = typer.Argument(..., help="The path to the Python file of the app to run.")
):
    """
    Runs a Pythra application as a child process.

    This allows the application to be cleanly killed and restarted
    for a true "clean restart" development experience.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at '{file_path}'")
        raise typer.Exit(code=1)

    process = None

    while True:
        # --- Start the App Process ---
        print(f"\n🚀 Launching: python {os.path.basename(file_path)}")
        command = [sys.executable, "-u", file_path]
        process = subprocess.Popen(command)

        # --- Wait for User Input ---
        cmd = input("🔥 Clean Restart active. Press [r] + Enter to restart, [q] + Enter to quit: ").strip().lower()

        if cmd == 'q':
            print("👋 Exiting...")
            if process.poll() is None: # Check if the process is still running
                print(f"Terminating process {process.pid}...")
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    print("Process did not exit gracefully, killing.")
                    process.kill()
            break # Exit the while loop and the CLI

        elif cmd == 'r':
            print("🔄 Restarting application...")
            if process.poll() is None:
                print(f"Terminating process {process.pid}...")
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    print("Process did not exit gracefully, killing.")
                    process.kill()
            
            # Give the OS a moment to release resources (e.g., ports)
            time.sleep(0.5) 
            # The loop will now continue and start a new process
        else:
            print("❓ Unknown command. Please use 'r' or 'q'.")
            # If an unknown command is entered, we should also kill the running process
            # before exiting to avoid leaving a zombie process.
            if process.poll() is None:
                process.terminate()
            break

if __name__ == "__main__":
    app()