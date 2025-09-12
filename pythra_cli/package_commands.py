"""
Package management commands for PyThra CLI

This module provides package management functionality integrated with the existing Typer-based CLI.
"""
from __future__ import annotations
import typer
import sys
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Add pythra path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Try importing the package system modules
    from pythra.package_manager import PackageManager
    from pythra.package_system import PackageType, PackageManifest, PackageInfo
    from pythra.package_registry import MockRegistry
    from pythra.package_security import get_package_validator
    PACKAGE_SYSTEM_AVAILABLE = True
except ImportError as e:
    # Create fallback stubs if package system isn't available
    PACKAGE_SYSTEM_AVAILABLE = False
    PackageManager = None
    PackageType = None
    PackageManifest = None
    PackageInfo = None
    MockRegistry = None
    get_package_validator = None

console = Console()

# Create package sub-app
package_app = typer.Typer(
    name="package",
    help="Package management commands",
    add_completion=False
)


@package_app.command("list")
def list_packages(
    package_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by package type (plugin, widgets, theme, utility, app)"),
    local_only: bool = typer.Option(False, "--local-only", "-l", help="Show only local packages"),
    output_format: str = typer.Option("table", "--format", "-f", help="Output format (table, json, detailed)")
):
    """List discovered packages"""
    if not PACKAGE_SYSTEM_AVAILABLE:
        console.print("[red]Package system not available. Please install required dependencies.[/red]")
        raise typer.Exit(code=1)
    
    try:
        # Initialize package manager
        project_root = Path.cwd()
        manager = PackageManager(project_root)
        
        # Discover packages
        all_packages = manager.discover_all_packages()
        
        # Filter by type if specified
        filter_type = PackageType(package_type) if package_type else None
        
        packages_to_show = []
        for name, package_list in all_packages.items():
            for pkg_info in package_list:
                # Apply filters
                if filter_type and pkg_info.manifest.package_type != filter_type:
                    continue
                
                if local_only and not pkg_info.path.parent.name == "plugins":
                    continue
                
                packages_to_show.append(pkg_info)
        
        if not packages_to_show:
            console.print("No packages found matching criteria.")
            return
        
        # Output in requested format
        if output_format == "json":
            package_data = []
            for pkg in packages_to_show:
                package_data.append({
                    'name': pkg.manifest.name,
                    'version': pkg.manifest.version,
                    'description': pkg.manifest.description,
                    'type': pkg.manifest.package_type.value,
                    'path': str(pkg.path),
                    'loaded': pkg.loaded
                })
            print(json.dumps(package_data, indent=2))
            
        elif output_format == "detailed":
            for pkg in packages_to_show:
                console.print(f"\n[bold blue]📦 {pkg.manifest.name}[/bold blue] [dim]v{pkg.manifest.version}[/dim]")
                console.print(f"   {pkg.manifest.description}")
                console.print(f"   [dim]Type:[/dim] {pkg.manifest.package_type.value}")
                console.print(f"   [dim]Path:[/dim] {pkg.path}")
                if pkg.manifest.tags:
                    console.print(f"   [dim]Tags:[/dim] {', '.join(pkg.manifest.tags)}")
                if pkg.manifest.author:
                    console.print(f"   [dim]Author:[/dim] {pkg.manifest.author.name}")
                status = "[green]✅ Loaded[/green]" if pkg.loaded else "[yellow]⏸️ Not loaded[/yellow]"
                console.print(f"   [dim]Status:[/dim] {status}")
                
        else:  # table format
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Name", style="cyan")
            table.add_column("Version", style="dim")
            table.add_column("Type", style="green")
            table.add_column("Description", style="white")
            table.add_column("Status", justify="center")
            
            for pkg in packages_to_show:
                status = "✅" if pkg.loaded else "⏸️"
                description = pkg.manifest.description
                if len(description) > 50:
                    description = description[:47] + "..."
                    
                table.add_row(
                    pkg.manifest.name,
                    pkg.manifest.version,
                    pkg.manifest.package_type.value,
                    description,
                    status
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error listing packages: {e}[/red]")
        raise typer.Exit(code=1)


@package_app.command("info")
def package_info(
    package_name: str = typer.Argument(..., help="Package name to get info about")
):
    """Show detailed information about a package"""
    if not PACKAGE_SYSTEM_AVAILABLE:
        console.print("[red]Package system not available. Please install required dependencies.[/red]")
        raise typer.Exit(code=1)
    
    try:
        project_root = Path.cwd()
        manager = PackageManager(project_root)
        
        # Try to find package locally first
        all_packages = manager.discover_all_packages()
        
        if package_name in all_packages:
            pkg_info = all_packages[package_name][0]  # Get first version
            manifest = pkg_info.manifest
            
            console.print(f"\n[bold blue]📦 {manifest.name}[/bold blue] [dim]v{manifest.version}[/dim]")
            console.print("=" * 50)
            console.print(f"[bold]Description:[/bold] {manifest.description}")
            console.print(f"[bold]Type:[/bold] {manifest.package_type.value}")
            console.print(f"[bold]Path:[/bold] {pkg_info.path}")
            
            if manifest.author:
                console.print(f"[bold]Author:[/bold] {manifest.author.name}")
                if manifest.author.email:
                    console.print(f"[bold]Email:[/bold] {manifest.author.email}")
            
            if manifest.homepage:
                console.print(f"[bold]Homepage:[/bold] {manifest.homepage}")
            
            if manifest.repository:
                console.print(f"[bold]Repository:[/bold] {manifest.repository.url}")
            
            console.print(f"[bold]License:[/bold] {manifest.license}")
            
            if manifest.tags:
                console.print(f"[bold]Tags:[/bold] {', '.join(manifest.tags)}")
            
            if manifest.dependencies:
                console.print(f"\n[bold]Dependencies:[/bold]")
                for dep_name, dep in manifest.dependencies.items():
                    console.print(f"  • {dep_name}: {dep.version_constraint}")
            
            if manifest.js_modules:
                console.print(f"\n[bold]JavaScript Modules:[/bold]")
                for name, path in manifest.js_modules.items():
                    console.print(f"  • {name}: {path}")
            
            if manifest.python_modules:
                console.print(f"\n[bold]Python Modules:[/bold] {', '.join(manifest.python_modules)}")
            
            status = "[green]✅ Loaded[/green]" if pkg_info.loaded else "[yellow]⏸️ Not loaded[/yellow]"
            console.print(f"\n[bold]Status:[/bold] {status}")
            
        else:
            console.print(f"[yellow]Package '{package_name}' not found locally. Checking registry...[/yellow]")
            
            # Check mock registry for demonstration
            registry = MockRegistry()
            package_info = registry.get_package_info(package_name)
            
            if package_info:
                console.print(f"\n[bold blue]📦 {package_info.name}[/bold blue] [dim](Registry)[/dim]")
                console.print("=" * 50)
                console.print(f"[bold]Description:[/bold] {package_info.description}")
                console.print(f"[bold]Latest Version:[/bold] {package_info.latest_version}")
                console.print(f"[bold]Downloads:[/bold] {package_info.downloads}")
                
                if package_info.homepage:
                    console.print(f"[bold]Homepage:[/bold] {package_info.homepage}")
                
                if package_info.repository:
                    console.print(f"[bold]Repository:[/bold] {package_info.repository}")
                
                console.print(f"\n[bold]Available Versions:[/bold]")
                for ver, ver_info in package_info.versions.items():
                    status = " [red](yanked)[/red]" if ver_info.yanked else ""
                    console.print(f"  • {ver}: {ver_info.size_bytes / 1024:.1f} KB{status}")
            else:
                console.print(f"[red]Package '{package_name}' not found[/red]")
                raise typer.Exit(code=1)
                
    except Exception as e:
        console.print(f"[red]Error getting package info: {e}[/red]")
        raise typer.Exit(code=1)


@package_app.command("search")
def search_packages(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results")
):
    """Search for packages in the registry"""
    if not PACKAGE_SYSTEM_AVAILABLE:
        console.print("[red]Package system not available. Please install required dependencies.[/red]")
        raise typer.Exit(code=1)
    
    try:
        # Use mock registry for demonstration
        registry = MockRegistry()
        
        console.print(f"🔍 Searching for '[cyan]{query}[/cyan]'...")
        
        results = registry.search_packages(query, limit)
        
        if not results:
            console.print("No packages found matching your search.")
            return
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="dim")
        table.add_column("Description", style="white")
        table.add_column("Downloads", justify="right", style="green")
        
        for pkg in results:
            description = pkg.description
            if len(description) > 60:
                description = description[:57] + "..."
                
            table.add_row(
                pkg.name,
                pkg.latest_version,
                description,
                str(pkg.downloads)
            )
        
        console.print(table)
        console.print(f"\nShowing {len(results)} results")
        
    except Exception as e:
        console.print(f"[red]Error searching packages: {e}[/red]")
        raise typer.Exit(code=1)


@package_app.command("validate")
def validate_package(
    package_path: str = typer.Argument(..., help="Path to package directory"),
    check_files: bool = typer.Option(True, "--check-files/--no-check-files", help="Perform detailed file scanning")
):
    """Validate a package for security and integrity"""
    if not PACKAGE_SYSTEM_AVAILABLE:
        console.print("[red]Package system not available. Please install required dependencies.[/red]")
        raise typer.Exit(code=1)
    
    try:
        package_path = Path(package_path)
        
        # Load package manifest
        manifest_file = package_path / "package.json"
        if not manifest_file.exists():
            manifest_file = package_path / "pythra_plugin.py"
        
        if not manifest_file.exists():
            console.print("[red]No package manifest found[/red]")
            raise typer.Exit(code=1)
        
        # Create PackageInfo
        if manifest_file.name == "package.json":
            with open(manifest_file) as f:
                data = json.load(f)
            manifest = PackageManifest.from_dict(data)
        else:
            console.print("[yellow]Legacy manifest format - validation limited[/yellow]")
            return
        
        package_info = PackageInfo(manifest=manifest, path=package_path)
        
        # Validate package
        validator = get_package_validator()
        result = validator.validate_package(package_info, check_files=check_files)
        
        console.print(f"\n🔍 [bold]Validating {manifest.name}[/bold] [dim]v{manifest.version}[/dim]")
        console.print("=" * 50)
        
        # Show validation status
        if result.valid:
            console.print("[green]✅ Package validation passed[/green]")
        else:
            console.print("[red]❌ Package validation failed[/red]")
        
        manifest_status = "[green]✅[/green]" if result.manifest_valid else "[red]❌[/red]"
        console.print(f"📝 Manifest valid: {manifest_status}")
        
        if check_files:
            checksum_status = "[green]✅[/green]" if result.checksum_verified else "[red]❌[/red]"
            console.print(f"🔐 Checksums verified: {checksum_status}")
            
            safety_status = "[green]✅ Safe[/green]" if result.is_safe() else "[yellow]⚠️ Issues found[/yellow]"
            console.print(f"🛡️ Security status: {safety_status}")
        
        # Show errors
        if result.errors:
            console.print(f"\n[red]❌ Errors ({len(result.errors)}):[/red]")
            for error in result.errors:
                console.print(f"  • {error}")
        
        # Show warnings
        if result.warnings:
            console.print(f"\n[yellow]⚠️ Warnings ({len(result.warnings)}):[/yellow]")
            for warning in result.warnings:
                console.print(f"  • {warning}")
        
        # Show security issues grouped by severity
        if result.security_issues:
            console.print(f"\n🛡️ [bold]Security Issues ({len(result.security_issues)}):[/bold]")
            
            severity_colors = {
                "critical": "red",
                "high": "yellow", 
                "medium": "blue",
                "low": "dim",
                "info": "green"
            }
            
            severity_icons = {
                "critical": "🚨",
                "high": "⚠️",
                "medium": "💡",
                "low": "ℹ️",
                "info": "📋"
            }
            
            for severity in ["critical", "high", "medium", "low", "info"]:
                issues = [i for i in result.security_issues if i.severity == severity]
                if not issues:
                    continue
                
                color = severity_colors.get(severity, "white")
                icon = severity_icons.get(severity, "❓")
                
                console.print(f"\n  {icon} [{color}]{severity.upper()} ({len(issues)}):[/{color}]")
                for issue in issues:
                    location = ""
                    if issue.file_path:
                        location = f" in {Path(issue.file_path).name}"
                        if issue.line_number:
                            location += f":{issue.line_number}"
                    
                    console.print(f"    • {issue.message}{location}")
        
        if not result.valid:
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"[red]Error validating package: {e}[/red]")
        raise typer.Exit(code=1)


@package_app.command("install")
def install_package(
    package_name: str = typer.Argument(..., help="Package name to install"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Specific version to install"),
    local: bool = typer.Option(False, "--local", help="Install from local path"),
    force: bool = typer.Option(False, "--force", help="Force installation even if validation fails")
):
    """Install a package (simulated - not fully implemented yet)"""
    if not PACKAGE_SYSTEM_AVAILABLE:
        console.print("[red]Package system not available. Please install required dependencies.[/red]")
        raise typer.Exit(code=1)
    
    try:
        if local:
            console.print("[yellow]Local package installation not yet implemented[/yellow]")
            return
        
        # Use mock registry for demonstration
        registry = MockRegistry()
        
        package_info = registry.get_package_info(package_name)
        if not package_info:
            console.print(f"[red]Package '{package_name}' not found in registry[/red]")
            raise typer.Exit(code=1)
        
        # Select version
        if version is None:
            version = package_info.latest_version
        
        if version not in package_info.versions:
            available = list(package_info.versions.keys())
            console.print(f"[red]Version {version} not found. Available: {available}[/red]")
            raise typer.Exit(code=1)
        
        console.print(f"📦 Installing [cyan]{package_name}[/cyan] [dim]v{version}[/dim]...")
        
        pkg_version = package_info.versions[version]
        console.print(f"   [dim]Description:[/dim] {pkg_version.manifest.description}")
        console.print(f"   [dim]Size:[/dim] {pkg_version.size_bytes / 1024:.1f} KB")
        console.print(f"   [dim]Published:[/dim] {pkg_version.published_at}")
        
        if pkg_version.manifest.dependencies:
            deps = list(pkg_version.manifest.dependencies.keys())
            console.print(f"   [dim]Dependencies:[/dim] {deps}")
        
        console.print("[green]✅ Package installation simulated[/green] [dim](actual installation not yet implemented)[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error installing package: {e}[/red]")
        raise typer.Exit(code=1)


@package_app.command("clean")
def clean_cache(
    clear_cache: bool = typer.Option(False, "--clear-cache", help="Clear package cache")
):
    """Clean up package system"""
    if not PACKAGE_SYSTEM_AVAILABLE:
        console.print("[red]Package system not available. Please install required dependencies.[/red]")
        raise typer.Exit(code=1)
    
    try:
        if clear_cache:
            console.print("[green]✅ Package cache cleared[/green] [dim](simulated)[/dim]")
        else:
            console.print("Specify --clear-cache or other cleanup options")
            
    except Exception as e:
        console.print(f"[red]Error cleaning: {e}[/red]")
        raise typer.Exit(code=1)