# =============================================================================
# PYTHRA CLI SYSTEM - The "Command Center" for PyThra Development
# =============================================================================

"""
PyThra Command Line Interface (CLI)

This is your "command center" for working with PyThra projects! Think of it like
the "control room" that helps you manage your PyThra applications from the terminal.

**What can the PyThra CLI do?**
🚀 **Project Management**:
   - Create new projects instantly
   - Run your applications
   - Build apps for distribution
   - Check if everything is working properly

🎮 **Available Commands**:
   - `pythra create-project <name>` - Creates a new PyThra project
   - `pythra run` - Runs your PyThra application
   - `pythra build` - Builds your app for distribution
   - `pythra doctor` - Checks if PyThra is working properly
   - `pythra package <command>` - Manages packages and plugins

**Real-world analogy:**
Think of the PyThra CLI like a "Swiss Army Knife" for app development:
- Just like a Swiss Army Knife has tools for different tasks
- The CLI has commands for different development tasks
- You use the right tool/command for what you want to accomplish

**How to use it:**
Open your terminal and type `pythra` followed by a command:
```bash
# Create a new app called "my-awesome-app"
pythra create-project my-awesome-app

# Run your app
cd my-awesome-app
pythra run

# Check if everything is working
pythra doctor
```

This file contains all the command implementations that make the CLI work!
"""

import click
from .package_commands import package_group


@click.group()
@click.version_option()
def cli():
    """PyThra Framework - Modern desktop GUI development in Python"""
    pass


# =============================================================================
# CREATE PROJECT COMMAND - The "Project Generator" 
# =============================================================================

@cli.command()
@click.argument('project_name')
@click.option('--template', default='basic', help='Project template to use')
def create_project(project_name: str, template: str):
    """
    Creates a brand new PyThra project with everything you need to get started!
    
    **What this command does:**
    Think of it like a "project starter kit generator" that:
    1. 📁 Creates a new folder for your project
    2. 🏷️ Sets up the proper directory structure (lib/, assets/, plugins/, etc.)
    3. 📝 Creates template files with working example code
    4. ⚙️ Sets up configuration files with sensible defaults
    5. 📚 Generates documentation to help you get started
    
    **Real-world analogy:**
    Like using a "house blueprint" to build a new house - it gives you
    the basic structure, rooms, and utilities, so you can focus on decorating
    and customizing instead of building from scratch.
    
    **Example usage:**
    ```bash
    pythra create-project my-calculator-app
    pythra create-project photo-editor --template advanced
    ```
    
    **What you get:**
    - A working counter app as an example
    - Proper project structure
    - Configuration file (config.yaml)
    - README with instructions
    - Everything ready to run with `pythra run`
    """
    try:
        from pathlib import Path
        import shutil
        
        project_path = Path.cwd() / project_name
        
        if project_path.exists():
            click.echo(f"Error: Directory '{project_name}' already exists", err=True)
            return
        
        # Create project directory structure
        project_path.mkdir()
        (project_path / "lib").mkdir()
        (project_path / "assets").mkdir()
        (project_path / "plugins").mkdir()
        (project_path / "render").mkdir()
        
        # Create basic files
        main_py_content = '''# Welcome to your new PyThra App!
from pythra import (
    Framework, StatefulWidget, State, Column, Row, Key, Widget,
    Container, Text, Alignment, Colors, Center, ElevatedButton,
    SizedBox, MainAxisAlignment, CrossAxisAlignment
)


class CounterState(State):
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1
        self.setState()

    def build(self) -> Widget:
        return Center(
            child=Column(
                key=Key("main_column"),
                mainAxisAlignment=MainAxisAlignment.CENTER,
                children=[
                    Text(
                        "PyThra Counter App",
                        key=Key("title"),
                        style={"fontSize": 24, "fontWeight": "bold"}
                    ),
                    SizedBox(height=20, key=Key("spacer1")),
                    Text(
                        f"Count: {self.count}",
                        key=Key("counter_text"),
                        style={"fontSize": 18}
                    ),
                    SizedBox(height=20, key=Key("spacer2")),
                    ElevatedButton(
                        child=Text("Increment", key=Key("button_text")),
                        onPressed=self.increment,
                        key=Key("increment_button")
                    )
                ]
            )
        )


class CounterApp(StatefulWidget):
    def createState(self) -> CounterState:
        return CounterState()


if __name__ == "__main__":
    app = Framework.instance()
    app.set_root(CounterApp(key=Key("counter_app")))
    app.run(title=f"{project_name} - PyThra App")
'''
        
        config_yaml_content = f'''# PyThra Project Configuration
app_name: "{project_name}"
version: "1.0.0"

# Window Configuration
win_width: 800
win_height: 600
frameless: false
maximixed: false
fixed_size: false

# Asset Configuration
assets_dir: "assets"
render_dir: "render"
assets_server_port: 0  # 0 = auto-assign port

# Development
Debug: true
'''
        
        # Write files
        with open(project_path / "lib" / "main.py", 'w') as f:
            f.write(main_py_content)
        
        with open(project_path / "config.yaml", 'w') as f:
            f.write(config_yaml_content)
        
        # Create README
        readme_content = f'''# {project_name}

A PyThra desktop application.

## Getting Started

1. Navigate to the project directory:
   ```
   cd {project_name}
   ```

2. Run the application:
   ```
   pythra run
   ```

## Project Structure

- `lib/main.py` - Main application code
- `config.yaml` - Application configuration
- `assets/` - Images, fonts, and other resources
- `plugins/` - Local plugins
- `render/` - Generated web assets (auto-created)

## Package Management

- List packages: `pythra package list`
- Search packages: `pythra package search <query>`
- Install packages: `pythra package install <name>`
- Validate packages: `pythra package validate <path>`

## Documentation

Visit https://docs.pythra.dev for more information.
'''
        
        with open(project_path / "README.md", 'w') as f:
            f.write(readme_content)
        
        click.echo(f"\n🎉 PyThra CLI | Successfully created new project: '{project_name}'!")
        click.echo(f"📁 PyThra CLI | Project location: {project_path}")
        click.echo(f"")
        click.echo(f"🚀 Next steps to run your app:")
        click.echo(f"  1. cd {project_name}")
        click.echo(f"  2. pythra run")
        click.echo(f"\n✨ Your new PyThra app is ready! Happy coding! 🎨")
        
    except Exception as e:
        click.echo(f"Error creating project: {e}", err=True)


@cli.command()
@click.option('--script', default='lib/main.py', help='Script to run')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def run(script: str, debug: bool):
    """Run a PyThra application"""
    try:
        from pathlib import Path
        import subprocess
        import sys
        
        script_path = Path(script)
        
        if not script_path.exists():
            click.echo(f"Error: Script '{script}' not found", err=True)
            return
        
        # Run the script
        env = {}
        if debug:
            env['PYTHRA_DEBUG'] = '1'
        
        result = subprocess.run([sys.executable, str(script_path)], env=env)
        sys.exit(result.returncode)
        
    except Exception as e:
        click.echo(f"Error running script: {e}", err=True)


@cli.command()
@click.option('--onefile', is_flag=True, help='Create single executable')
@click.option('--icon', help='Icon file for executable')
@click.option('--output-dir', default='build', help='Output directory')
def build(onefile: bool, icon: str, output_dir: str):
    """Build PyThra application for distribution"""
    try:
        import subprocess
        from pathlib import Path
        
        build_dir = Path(output_dir)
        build_dir.mkdir(exist_ok=True)
        
        # Basic PyInstaller command
        cmd = ['pyinstaller']
        
        if onefile:
            cmd.append('--onefile')
        else:
            cmd.append('--onedir')
        
        if icon:
            cmd.extend(['--icon', icon])
        
        cmd.extend([
            '--distpath', str(build_dir),
            '--workpath', str(build_dir / 'temp'),
            '--specpath', str(build_dir),
            'lib/main.py'
        ])
        
        click.echo("🔨 PyThra CLI | Building your application for distribution...")
        click.echo(f"Command: {' '.join(cmd)}")
        
        # Check if PyInstaller is available
        try:
            subprocess.run(['pyinstaller', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo("❌ PyInstaller not found. Install with: pip install pyinstaller", err=True)
            return
        
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            click.echo("✅ PyThra CLI | Build completed successfully!")
            click.echo(f"📦 PyThra CLI | Your app is ready in: {build_dir}")
        else:
            click.echo("❌ Build failed", err=True)
        
    except Exception as e:
        click.echo(f"Error building application: {e}", err=True)


@cli.command()
def doctor():
    """Check PyThra installation and dependencies"""
    try:
        import sys
        from pathlib import Path
        
        click.echo("🔍 PyThra CLI | Installation Health Check")
        click.echo("=" * 40)
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 8):
            click.echo(f"✅ Python {python_version} (supported)")
        else:
            click.echo(f"❌ Python {python_version} (requires 3.8+)")
        
        # Check required dependencies
        required_packages = [
            ('PySide6', 'PySide6'),
            ('click', 'click'),
            ('PyYAML', 'yaml'),
        ]
        
        optional_packages = [
            ('semver', 'semver'),
            ('requests', 'requests'),
            ('tabulate', 'tabulate'),
        ]
        
        click.echo(f"\n📦 Required Dependencies:")
        for display_name, import_name in required_packages:
            try:
                __import__(import_name)
                click.echo(f"✅ {display_name}")
            except ImportError:
                click.echo(f"❌ {display_name} (missing)")
        
        click.echo(f"\n📦 Optional Dependencies:")
        for display_name, import_name in optional_packages:
            try:
                __import__(import_name)
                click.echo(f"✅ {display_name}")
            except ImportError:
                click.echo(f"⚠️ {display_name} (recommended)")
        
        # Check project structure if in a project
        if Path('config.yaml').exists():
            click.echo(f"\n📁 Project Structure:")
            expected_dirs = ['lib', 'assets', 'plugins']
            for dir_name in expected_dirs:
                if Path(dir_name).exists():
                    click.echo(f"✅ {dir_name}/")
                else:
                    click.echo(f"⚠️ {dir_name}/ (recommended)")
            
            if Path('lib/main.py').exists():
                click.echo(f"✅ lib/main.py")
            else:
                click.echo(f"❌ lib/main.py (missing)")
        else:
            click.echo(f"\n📁 No PyThra project detected in current directory")
        
        click.echo(f"\n🎯 Installation Summary:")
        click.echo(f"PyThra framework appears to be properly installed!")
        
    except Exception as e:
        click.echo(f"Error checking installation: {e}", err=True)


# Add the package management commands
cli.add_command(package_group)


if __name__ == '__main__':
    cli()