#!/usr/bin/env python3
"""
pythra_cli/main.py - The official Command Line Interface for the Pythra Framework.

Usage:
    pythra create-project <name>         # Create a new, ready-to-use project.
    pythra run [--script <path>]         # Run the project with a clean-restart loop.
    pythra build [--script <path>]       # Build a standalone application folder.
"""
from __future__ import annotations
import typer
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Any, Optional
import yaml
import json
import zlib
import base64
import stat
import time
import uuid

# --- Typer App Initialization ---
app = typer.Typer(
    name="pythra",
    help="The official CLI for the Pythra Framework.",
    add_completion=False
)

# --- Helper Functions (Unchanged, they are excellent) ---

def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def set_debug_false_in_obj(obj: Any) -> None:
    if isinstance(obj, dict):
        for key, val in list(obj.items()):
            if isinstance(key, str) and key.strip().lower() == "debug":
                obj[key] = False
            else:
                set_debug_false_in_obj(val)
    elif isinstance(obj, list):
        for item in obj:
            set_debug_false_in_obj(item)

def generate_embedded_config_module_in_dir(
    dest_dir: Path, data: Any, module_name: str = "_embedded_config.py"
) -> Path:
    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    json_bytes = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    compressed = zlib.compress(json_bytes, level=9)
    b64 = base64.b64encode(compressed).decode("ascii")
    module_path = (dest_dir / module_name).resolve()
    module_contents = f'''"""Auto-generated embedded config module."""
import json, zlib, base64
_CONFIG_B64 = """{b64}"""
def load_embedded_config():
    try:
        raw = base64.b64decode(_CONFIG_B64.encode("ascii"))
        json_bytes = zlib.decompress(raw)
        return json.loads(json_bytes.decode("utf-8"))
    except Exception as e:
        raise RuntimeError("Failed to load embedded config") from e
CONFIG = load_embedded_config()
'''
    with module_path.open("w", encoding="utf-8") as fh:
        fh.write(module_contents)
    print(f"[+] Generated embedded config module: {module_path}")
    return module_path

def force_rmtree(path: Path, retries: int = 5, delay: float = 0.5):
    def onerror(func, p_str, exc_info):
        p = Path(p_str)
        if not os.access(p, os.W_OK):
            os.chmod(p, stat.S_IWUSR)
            func(p_str)
        else:
            raise
    for i in range(retries):
        try:
            shutil.rmtree(path, onerror=onerror)
            return
        except PermissionError:
            print(f"[!] PermissionError removing {path}, retrying {i+1}/{retries}")
            time.sleep(delay)
    try:
        tmp_name = path.parent / f"__old_{path.name}_{uuid.uuid4().hex}"
        path.rename(tmp_name)
        shutil.rmtree(tmp_name, onerror=onerror)
        print(f"[+] Renamed and removed locked folder: {tmp_name}")
    except Exception as e:
        print(f"[!] Could not remove build folder even after retries: {e}")
        raise

# --- CLI Commands ---

@app.command()
def create_project(project_name: str = typer.Argument(..., help="The name for the new project directory.")):
    """Creates a new Pythra project with a standard directory structure."""
    # This command is perfect as-is.
    project_path = Path.cwd() / project_name
    if project_path.exists():
        print(f"❌ Error: Directory '{project_name}' already exists.")
        raise typer.Exit(code=1)
    print(f"✅ Creating a new Pythra project in: {project_path}")
    try:
        template_path = Path(__file__).parent.parent / 'project_template'
        if not template_path.exists():
            print(f"❌ Fatal Error: Could not find project template at '{template_path}'")
            raise typer.Exit(code=1)
        shutil.copytree(template_path, project_path)
        print("\n🎉 Project created successfully!")
        print("To get started:")
        print(f"  1. cd {project_name}")
        print(f"  2. pythra run")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        if project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(code=1)

@app.command()
def run(script: str = typer.Option("lib/main.py", "--script", "-s", help="Script to run relative to the project root.")):
    """Runs the application with a clean-restart-on-keypress loop."""
    # This command is perfect as-is.
    project_root = Path.cwd()
    script_path = (project_root / script).resolve()
    if not script_path.exists():
        print(f"❌ Error: Script not found at '{script_path}'")
        raise typer.Exit(code=1)
    process = None
    try:
        while True:
            print(f"\n🚀 Launching: python {script}")
            process = subprocess.Popen([sys.executable, "-u", str(script_path)])
            cmd = input("🔥 Clean Restart active. Press [r] + Enter to restart, [q] + Enter to quit: ").strip().lower()
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired: process.kill()
            if cmd == 'q':
                print("👋 Exiting...")
                break
            elif cmd != 'r':
                print("❓ Unknown command. Exiting.")
                break
            print("🔄 Restarting application...")
            time.sleep(0.5)
    finally:
        if process and process.poll() is None:
            process.kill()


@app.command()
def build(
    script: str = typer.Option("lib/main.py", "--script", "-s", help="Script to compile, relative to project root."),
    include_dir: Optional[List[str]] = typer.Option(None, "--include-dir", "-d", help="Directory to include (e.g., assets). Can be repeated."),
    include_file: Optional[List[str]] = typer.Option(None, "--include-file", "-f", help="File to include."),
    output_root: str = typer.Option("build", help="Top-level build folder."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print actions but don't execute Nuitka."),
    keep_embedded: bool = typer.Option(False, "--keep-embedded", help="Do not delete the generated _embedded_config.py after build.")
):
    """Builds a standalone application folder using Nuitka."""
    project_root = Path.cwd()
    config_path = project_root / "config.yaml"

    if not config_path.exists():
        print(f"❌ Error: `config.yaml` not found in project root: {project_root}")
        raise typer.Exit(code=1)

    print("--- Starting Pythra Build Process ---")
    
    include_dir = include_dir or ["assets", "web"]
    include_file = include_file or []

    original_config = load_yaml(config_path)
    build_config = yaml.safe_load(yaml.safe_dump(original_config))
    set_debug_false_in_obj(build_config)

    app_name = str(build_config.get("app_name", "PythraApp")).strip()
    version = str(build_config.get("version", "1.0.0"))

    # The final output directory is the target
    final_app_dir = (project_root / output_root / app_name).resolve()
    if final_app_dir.exists():
        print(f"[+] Removing existing build folder: {final_app_dir}")
        force_rmtree(final_app_dir)
    final_app_dir.mkdir(parents=True, exist_ok=True)
    print(f"[+] Created clean build folder: {final_app_dir}")

    script_src = (project_root / script).resolve()
    if not script_src.exists():
        raise FileNotFoundError(f"Script to compile not found: {script_src}")

    embedded_module_path = generate_embedded_config_module_in_dir(dest_dir=final_app_dir, data=build_config)

    try:
        import pythra
        pythra_package_path = Path(pythra.__file__).parent
        print(f"[+] Found Pythra framework at: {pythra_package_path}")
    except ImportError:
        print("❌ Fatal Error: Could not find 'pythra' package. Is it installed with 'pip install -e .'?")
        raise typer.Exit(code=1)

    # Compose data args (use absolute paths)
    dir_args = [f"--include-data-dir={str(project_root / d)}={d}" for d in include_dir]
    file_args = [f"--include-data-file={str(project_root / f)}={f}" for f in include_file]

    nofollow_flags = [
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=setuptools",
        "--nofollow-import-to=Cython",
    ]

    # Build the Nuitka command (no --module-search-path)
    nuitka_cmd = [
        sys.executable, "-m", "nuitka", str(script_src),
        "--standalone",
        # we produce a folder (not onefile) so assets can be visible
        "--enable-plugin=pyside6",
        f"--output-dir={str(final_app_dir)}",
        f"--file-version={version}",
        f"--output-filename={app_name}",
        f"--windows-icon-from-ico={str(project_root / 'assets' / 'icons' / 'icon.ico')}",
        "--windows-console-mode=disable",
        f"--include-package=pythra",
        "--low-memory",
        "--include-module=_embedded_config",
        *nofollow_flags,
        *dir_args,
        *file_args,
    ]

    print("\n" + "="*72)
    print(f"App: {app_name} v{version}")
    print(f"Build will be located in: {final_app_dir}")
    print("Nuitka command to be executed:")
    print(" ".join(nuitka_cmd))
    print("="*72 + "\n")

    if dry_run:
        print("DRY RUN: Skipping Nuitka execution.")
        if not keep_embedded:
            embedded_module_path.unlink(missing_ok=True)
        return

    # Ensure Nuitka can find the pythra package (and the generated _embedded_config in final_app_dir)
    env = os.environ.copy()
    # Prepend the package parent folder and the final_app_dir so imports resolve during compilation.
    # pythra_package_path is like .../site-packages/pythra; parent is site-packages.
    env["PYTHONPATH"] = str(pythra_package_path.parent) + os.pathsep + str(final_app_dir) + os.pathsep + env.get("PYTHONPATH", "")

    try:
        subprocess.run(nuitka_cmd, check=True, env=env)
        print("\n✅ Build completed successfully!")
        print(f"   Application folder located at: {final_app_dir}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("\n❌ Nuitka build failed. Please check the output above for errors.")
        print("   Make sure Nuitka and a C/C++ compiler are installed and configured correctly.")
        raise typer.Exit(code=1)
    finally:
        if not keep_embedded:
            embedded_module_path.unlink(missing_ok=True)
            print(f"[+] Removed temporary embedded module.")


if __name__ == "__main__":
    app()