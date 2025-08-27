"""import subprocess
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
"""

#!/usr/bin/env python3
"""
cli.py run helper

Usage:
    python cli.py run                  # runs lib/main.py
    python cli.py run --script lib/v_list.py
"""

import subprocess
import sys
import os
import argparse

def run_command(script: str):
    """
    Start and manage the given script with restart/quit loop.
    """
    process = None
    try:
        while True:
            # Start the app
            print(f"[+] Starting {script}")
            process = subprocess.Popen([sys.executable, script])

            # Wait for user input
            cmd = input("\nPress [r] + Enter to restart, [q] + Enter to quit: ").strip().lower()

            if cmd == "q":
                print("Exiting...")
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                break
            elif cmd == "r":
                print("Restarting app...")
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                # loop continues → new process starts
            else:
                print("Unknown command. Use r to restart or q to quit.")
    finally:
        if process and process.poll() is None:
            process.kill()

def main():
    parser = argparse.ArgumentParser(description="Run application with restart/quit loop")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # run subcommand
    p_run = sub.add_parser("run", help="Run the app with restart/quit loop")
    p_run.add_argument("--script", "-s", type=str, default="lib/main.py",
                       help="Script to run (default: lib/main.py)")

    args = parser.parse_args()

    if args.cmd == "run":
        run_command(args.script)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
