import subprocess
import sys
import os
import signal

def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py <app.py>")
        sys.exit(1)

    script = sys.argv[1]
    process = None

    while True:
        # Start the app
        process = subprocess.Popen([sys.executable, script])

        # Wait for user input
        cmd = input("\nPress [r] + Enter to restart, [q] + Enter to quit: ").strip().lower()

        if cmd == "q":
            print("Exiting...")
            # Kill running app if still alive
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
            break
        elif cmd == "r":
            print("Restarting app...")
            # Kill old app
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
            # Then loop continues → new process starts
        else:
            print("Unknown command. Use r to restart or q to quit.")

if __name__ == "__main__":
    main()
