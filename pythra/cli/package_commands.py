"""
PyThra CLI Package Management Commands

This module provides CLI commands for:
- Package discovery and listing
- Package installation and removal  
- Package validation and security scanning
- Package registry interaction
"""

import os
import sys
import json
import click
from pathlib import Path
from typing import List, Optional
from tabulate import tabulate

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from package_manager import PackageManager
from package_system import PackageType, PackageManifest
from package_registry import get_default_registry, MockRegistry
from package_security import get_package_validator, get_package_whitelist


@click.group(name='package')
def package_group():
    """Package management commands"""
    pass


@package_group.command()
@click.option('--type', 'package_type', 
              type=click.Choice(['plugin', 'widgets', 'theme', 'utility', 'app']),
              help='Filter by package type')
@click.option('--local-only', is_flag=True, help='Show only local packages')
@click.option('--format', 'output_format', 
              type=click.Choice(['table', 'json', 'detailed']),
              default='table', help='Output format')
def list(package_type: Optional[str], local_only: bool, output_format: str):
    """List discovered packages"""
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
            click.echo("No packages found matching criteria.")
            return
        
        # Output in requested format
        if output_format == 'json':
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
            click.echo(json.dumps(package_data, indent=2))
            
        elif output_format == 'detailed':
            for pkg in packages_to_show:
                click.echo(f"\n📦 {pkg.manifest.name} v{pkg.manifest.version}")
                click.echo(f"   {pkg.manifest.description}")
                click.echo(f"   Type: {pkg.manifest.package_type.value}")
                click.echo(f"   Path: {pkg.path}")
                if pkg.manifest.tags:
                    click.echo(f"   Tags: {', '.join(pkg.manifest.tags)}")
                if pkg.manifest.author:
                    click.echo(f"   Author: {pkg.manifest.author.name}")
                click.echo(f"   Status: {'✅ Loaded' if pkg.loaded else '⏸️  Not loaded'}")
                
        else:  # table format
            table_data = []
            for pkg in packages_to_show:
                table_data.append([
                    pkg.manifest.name,
                    pkg.manifest.version,
                    pkg.manifest.package_type.value,
                    pkg.manifest.description[:50] + ("..." if len(pkg.manifest.description) > 50 else ""),
                    "✅" if pkg.loaded else "⏸️"
                ])
            
            click.echo(tabulate(
                table_data,
                headers=['Name', 'Version', 'Type', 'Description', 'Status'],
                tablefmt='grid'
            ))
            
    except Exception as e:
        click.echo(f"Error listing packages: {e}", err=True)
        sys.exit(1)


@package_group.command()
@click.argument('package_name')
@click.option('--version', help='Specific version to install')
@click.option('--local', is_flag=True, help='Install from local path')
@click.option('--force', is_flag=True, help='Force installation even if validation fails')
@click.option('--no-deps', is_flag=True, help='Skip dependency resolution')
def install(package_name: str, version: Optional[str], local: bool, force: bool, no_deps: bool):
    """Install a package"""
    try:
        project_root = Path.cwd()
        manager = PackageManager(project_root)
        
        if local:
            # Install from local path
            local_path = Path(package_name)
            if not local_path.exists():
                click.echo(f"Local path not found: {package_name}", err=True)
                sys.exit(1)
            
            # Load manifest
            manifest_file = local_path / "package.json"
            if not manifest_file.exists():
                manifest_file = local_path / "pythra_plugin.py"
            
            if not manifest_file.exists():
                click.echo("No package manifest found in local path", err=True)
                sys.exit(1)
            
            # TODO: Implement local package installation
            click.echo("Local package installation not yet implemented")
            return
        
        # Install from registry
        registry = get_default_registry()
        
        # In development, use mock registry
        if not hasattr(registry, 'session') or not registry.session:
            click.echo("Using mock registry for demonstration")
            registry = MockRegistry()
        
        # Search for package
        package_info = registry.get_package_info(package_name)
        if not package_info:
            click.echo(f"Package '{package_name}' not found in registry", err=True)
            sys.exit(1)
        
        # Select version
        if version is None:
            version = package_info.latest_version
        
        if version not in package_info.versions:
            available = list(package_info.versions.keys())
            click.echo(f"Version {version} not found. Available: {available}", err=True)
            sys.exit(1)
        
        click.echo(f"📦 Installing {package_name} v{version}...")
        
        # TODO: Implement actual package installation from registry
        # For now, just show what would be installed
        pkg_version = package_info.versions[version]
        click.echo(f"   Description: {pkg_version.manifest.description}")
        click.echo(f"   Size: {pkg_version.size_bytes / 1024:.1f} KB")
        click.echo(f"   Published: {pkg_version.published_at}")
        
        if not no_deps and pkg_version.manifest.dependencies:
            click.echo(f"   Dependencies: {list(pkg_version.manifest.dependencies.keys())}")
        
        click.echo("✅ Package installation simulated (actual installation not yet implemented)")
        
    except Exception as e:
        click.echo(f"Error installing package: {e}", err=True)
        sys.exit(1)


@package_group.command()
@click.argument('package_name')
def remove(package_name: str):
    """Remove an installed package"""
    try:
        project_root = Path.cwd()
        manager = PackageManager(project_root)
        
        # Check if package is installed
        loaded_packages = manager.get_loaded_packages()
        
        if package_name not in loaded_packages:
            click.echo(f"Package '{package_name}' is not installed", err=True)
            sys.exit(1)
        
        package_info = loaded_packages[package_name]
        
        # Confirm removal
        if not click.confirm(f"Remove package '{package_name}' v{package_info.manifest.version}?"):
            click.echo("Removal cancelled")
            return
        
        # TODO: Implement package removal
        click.echo(f"🗑️ Package removal not yet implemented")
        click.echo(f"To manually remove, delete: {package_info.path}")
        
    except Exception as e:
        click.echo(f"Error removing package: {e}", err=True)
        sys.exit(1)


@package_group.command()
@click.argument('package_name')
def info(package_name: str):
    """Show detailed information about a package"""
    try:
        project_root = Path.cwd()
        manager = PackageManager(project_root)
        
        # Try to find package locally first
        all_packages = manager.discover_all_packages()
        
        if package_name in all_packages:
            pkg_info = all_packages[package_name][0]  # Get first version
            manifest = pkg_info.manifest
            
            click.echo(f"\n📦 {manifest.name} v{manifest.version}")
            click.echo("=" * 50)
            click.echo(f"Description: {manifest.description}")
            click.echo(f"Type: {manifest.package_type.value}")
            click.echo(f"Path: {pkg_info.path}")
            
            if manifest.author:
                click.echo(f"Author: {manifest.author.name}")
                if manifest.author.email:
                    click.echo(f"Email: {manifest.author.email}")
            
            if manifest.homepage:
                click.echo(f"Homepage: {manifest.homepage}")
            
            if manifest.repository:
                click.echo(f"Repository: {manifest.repository.url}")
            
            click.echo(f"License: {manifest.license}")
            
            if manifest.tags:
                click.echo(f"Tags: {', '.join(manifest.tags)}")
            
            if manifest.dependencies:
                click.echo(f"\nDependencies:")
                for dep_name, dep in manifest.dependencies.items():
                    click.echo(f"  - {dep_name}: {dep.version_constraint}")
            
            if manifest.js_modules:
                click.echo(f"\nJavaScript Modules:")
                for name, path in manifest.js_modules.items():
                    click.echo(f"  - {name}: {path}")
            
            if manifest.python_modules:
                click.echo(f"\nPython Modules: {', '.join(manifest.python_modules)}")
            
            click.echo(f"\nStatus: {'✅ Loaded' if pkg_info.loaded else '⏸️ Not loaded'}")
            
        else:
            click.echo(f"Package '{package_name}' not found locally. Checking registry...")
            
            # Check registry
            registry = get_default_registry()
            if not hasattr(registry, 'session') or not registry.session:
                registry = MockRegistry()
            
            package_info = registry.get_package_info(package_name)
            if package_info:
                click.echo(f"\n📦 {package_info.name} (Registry)")
                click.echo("=" * 50)
                click.echo(f"Description: {package_info.description}")
                click.echo(f"Latest Version: {package_info.latest_version}")
                click.echo(f"Downloads: {package_info.downloads}")
                
                if package_info.homepage:
                    click.echo(f"Homepage: {package_info.homepage}")
                
                if package_info.repository:
                    click.echo(f"Repository: {package_info.repository}")
                
                click.echo(f"\nAvailable Versions:")
                for ver, ver_info in package_info.versions.items():
                    status = " (yanked)" if ver_info.yanked else ""
                    click.echo(f"  - {ver}: {ver_info.size_bytes / 1024:.1f} KB{status}")
            else:
                click.echo(f"Package '{package_name}' not found", err=True)
                sys.exit(1)
                
    except Exception as e:
        click.echo(f"Error getting package info: {e}", err=True)
        sys.exit(1)


@package_group.command()
@click.argument('query')
@click.option('--limit', default=10, help='Maximum number of results')
def search(query: str, limit: int):
    """Search for packages in the registry"""
    try:
        # Use mock registry for demonstration
        registry = MockRegistry()
        
        click.echo(f"🔍 Searching for '{query}'...")
        
        results = registry.search_packages(query, limit)
        
        if not results:
            click.echo("No packages found matching your search.")
            return
        
        table_data = []
        for pkg in results:
            table_data.append([
                pkg.name,
                pkg.latest_version,
                pkg.description[:60] + ("..." if len(pkg.description) > 60 else ""),
                pkg.downloads
            ])
        
        click.echo(tabulate(
            table_data,
            headers=['Name', 'Version', 'Description', 'Downloads'],
            tablefmt='grid'
        ))
        
        click.echo(f"\nShowing {len(results)} results")
        
    except Exception as e:
        click.echo(f"Error searching packages: {e}", err=True)
        sys.exit(1)


@package_group.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.option('--check-files', is_flag=True, help='Perform detailed file scanning')
def validate(package_path: str, check_files: bool):
    """Validate a package for security and integrity"""
    try:
        package_path = Path(package_path)
        
        # Load package manifest
        manifest_file = package_path / "package.json"
        if not manifest_file.exists():
            manifest_file = package_path / "pythra_plugin.py"
        
        if not manifest_file.exists():
            click.echo("No package manifest found", err=True)
            sys.exit(1)
        
        # Create PackageInfo
        if manifest_file.name == "package.json":
            with open(manifest_file) as f:
                data = json.load(f)
            manifest = PackageManifest.from_dict(data)
        else:
            click.echo("Legacy manifest format - validation limited")
            return
        
        from package_system import PackageInfo
        package_info = PackageInfo(manifest=manifest, path=package_path)
        
        # Validate package
        validator = get_package_validator()
        result = validator.validate_package(package_info, check_files=check_files)
        
        click.echo(f"\n🔍 Validating {manifest.name} v{manifest.version}")
        click.echo("=" * 50)
        
        # Show validation status
        if result.valid:
            click.echo("✅ Package validation passed")
        else:
            click.echo("❌ Package validation failed")
        
        click.echo(f"📝 Manifest valid: {'✅' if result.manifest_valid else '❌'}")
        
        if check_files:
            click.echo(f"🔐 Checksums verified: {'✅' if result.checksum_verified else '❌'}")
            click.echo(f"🛡️ Security status: {'✅ Safe' if result.is_safe() else '⚠️ Issues found'}")
        
        # Show errors
        if result.errors:
            click.echo(f"\n❌ Errors ({len(result.errors)}):")
            for error in result.errors:
                click.echo(f"  - {error}")
        
        # Show warnings
        if result.warnings:
            click.echo(f"\n⚠️ Warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                click.echo(f"  - {warning}")
        
        # Show security issues
        if result.security_issues:
            click.echo(f"\n🛡️ Security Issues ({len(result.security_issues)}):")
            
            # Group by severity
            severity_order = ["critical", "high", "medium", "low", "info"]
            for severity in severity_order:
                issues = [i for i in result.security_issues if i.severity == severity]
                if not issues:
                    continue
                
                severity_icon = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "💡", 
                    "low": "ℹ️",
                    "info": "📋"
                }.get(severity, "❓")
                
                click.echo(f"\n  {severity_icon} {severity.upper()} ({len(issues)}):")
                for issue in issues:
                    location = ""
                    if issue.file_path:
                        location = f" in {Path(issue.file_path).name}"
                        if issue.line_number:
                            location += f":{issue.line_number}"
                    
                    click.echo(f"    - {issue.message}{location}")
        
        if not result.valid:
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error validating package: {e}", err=True)
        sys.exit(1)


@package_group.command()
@click.option('--clear-cache', is_flag=True, help='Clear package cache')
def clean(clear_cache: bool):
    """Clean up package system"""
    try:
        if clear_cache:
            registry = get_default_registry()
            if hasattr(registry, 'clear_cache'):
                registry.clear_cache()
                click.echo("✅ Package cache cleared")
            else:
                click.echo("Cache clearing not available")
        else:
            click.echo("Specify --clear-cache or other cleanup options")
            
    except Exception as e:
        click.echo(f"Error cleaning: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    package_group()