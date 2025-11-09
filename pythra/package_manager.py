"""
PyThra Package Manager - Centralized package management system

This module provides:
- Package discovery from multiple sources
- Dependency resolution with conflict handling  
- Package loading and caching
- Version management
- Integration with PyThra framework
"""

import os
import json
import sys
import site
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import logging
from collections import defaultdict, deque
import weakref

from .package_system import (
    PackageManifest, PackageInfo,PackageType,
    PackageLoadError, DependencyResolutionError
)


logger = logging.getLogger(__name__)


class PackageSource:
    """Base class for package sources"""
    
    def discover_packages(self) -> Dict[str, List[PackageInfo]]:
        """Discover packages from this source"""
        raise NotImplementedError
    
    def load_package_manifest(self, package_path: Path) -> Optional[PackageManifest]:
        """Load package manifest from path"""
        raise NotImplementedError


class LocalPackageSource(PackageSource):
    """Package source for local plugins directory"""
    
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
    
    def discover_packages(self) -> Dict[str, List[PackageInfo]]:
        """Discover packages from local plugins directory"""
        packages = defaultdict(list)
        
        if not self.plugins_dir.exists() or not self.plugins_dir.is_dir():
            return packages
        
        logger.info(f"Discovering packages in {self.plugins_dir}")
        
        for potential_package_dir in self.plugins_dir.iterdir():
            if not potential_package_dir.is_dir():
                continue
                
            # Try loading enhanced manifest first
            manifest = self._load_enhanced_manifest(potential_package_dir)
            if not manifest:
                # Fall back to legacy pythra_plugin.py format
                manifest = self._load_legacy_manifest(potential_package_dir)
            
            if manifest:
                package_info = PackageInfo(
                    manifest=manifest,
                    path=potential_package_dir
                )
                packages[manifest.name].append(package_info)
                logger.info(f"Found package: {manifest.name} v{manifest.version}")
        
        return packages
    
    def _load_enhanced_manifest(self, package_path: Path) -> Optional[PackageManifest]:
        """Load enhanced package.json manifest"""
        manifest_file = package_path / "package.json"
        if not manifest_file.exists():
            return None
        
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return PackageManifest.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load enhanced manifest from {manifest_file}: {e}")
            return None
    
    def _load_legacy_manifest(self, package_path: Path) -> Optional[PackageManifest]:
        """Load legacy pythra_plugin.py manifest and convert to new format"""
        manifest_file = package_path / "pythra_plugin.py"
        if not manifest_file.exists():
            return None
        
        try:
            # Dynamically import the manifest
            spec = importlib.util.spec_from_file_location(
                f"plugin.{package_path.name}", 
                manifest_file
            )
            module = importlib.util.module_from_spec(spec) # type: ignore
            spec.loader.exec_module(module) # type: ignore
            
            if not hasattr(module, 'PYTHRA_PLUGIN'):
                return None
            
            plugin_info = module.PYTHRA_PLUGIN
            
            # Convert legacy format to new PackageManifest
            manifest_data = {
                "name": plugin_info.get("name", package_path.name),
                "version": plugin_info.get("version", "0.1.0"),
                "description": plugin_info.get("description", "Legacy PyThra plugin"),
                "package_type": PackageType.PLUGIN.value,
                "asset_dir": plugin_info.get("asset_dir", "public"),
                "css_files": plugin_info.get("css_files", []),
                "js_modules": plugin_info.get("js_modules", {}),
                "tags": ["legacy-plugin"]
            }
            
            return PackageManifest.from_dict(manifest_data)
            
        except Exception as e:
            logger.warning(f"Failed to load legacy manifest from {manifest_file}: {e}")
            return None


class SitePackagesSource(PackageSource):
    """Package source for installed Python packages with PyThra plugins"""
    
    def discover_packages(self) -> Dict[str, List[PackageInfo]]:
        """Discover PyThra packages installed via pip"""
        packages = defaultdict(list)
        
        # Check all site-packages directories
        for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
            if not site_dir or not os.path.exists(site_dir):
                continue
                
            site_path = Path(site_dir)
            logger.debug(f"Checking site-packages: {site_path}")
            
            # Look for pythra_* packages or packages with pythra entry points
            for package_dir in site_path.iterdir():
                if package_dir.is_dir() and (
                    package_dir.name.startswith('pythra_') or 
                    self._has_pythra_entry_point(package_dir)
                ):
                    manifest = self._load_installed_manifest(package_dir)
                    if manifest:
                        package_info = PackageInfo(
                            manifest=manifest,
                            path=package_dir
                        )
                        packages[manifest.name].append(package_info)
        
        return packages
    
    def _has_pythra_entry_point(self, package_dir: Path) -> bool:
        """Check if package has PyThra entry points"""
        # Check for package.json with pythra metadata
        package_json = package_dir / "package.json" 
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                return "pythra" in data or data.get("package_type") in [pt.value for pt in PackageType]
            except:
                pass
        
        # Check for entry_points.txt or setup.cfg
        metadata_dir = package_dir.parent / f"{package_dir.name}.dist-info"
        if metadata_dir.exists():
            entry_points = metadata_dir / "entry_points.txt"
            if entry_points.exists():
                try:
                    with open(entry_points) as f:
                        content = f.read()
                        return "pythra" in content.lower()
                except:
                    pass
        
        return False
    
    def _load_installed_manifest(self, package_dir: Path) -> Optional[PackageManifest]:
        """Load manifest from installed package"""
        # Try package.json first
        package_json = package_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                return PackageManifest.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load manifest from {package_json}: {e}")
        
        # Try to extract info from package metadata
        try:
            metadata_dir = package_dir.parent / f"{package_dir.name}.dist-info"
            if metadata_dir.exists():
                metadata_file = metadata_dir / "METADATA"
                if metadata_file.exists():
                    return self._parse_wheel_metadata(metadata_file, package_dir)
        except Exception as e:
            logger.debug(f"Failed to parse wheel metadata for {package_dir}: {e}")
        
        return None
    
    def _parse_wheel_metadata(self, metadata_file: Path, package_dir: Path) -> Optional[PackageManifest]:
        """Parse wheel METADATA file to create PackageManifest"""
        try:
            metadata = {}
            with open(metadata_file) as f:
                for line in f:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
            
            return PackageManifest(
                name=metadata.get("Name", package_dir.name),
                version=metadata.get("Version", "0.1.0"),
                description=metadata.get("Summary", "PyThra package"),
                package_type=PackageType.WIDGET_LIBRARY,  # Default for installed packages
                homepage=metadata.get("Home-page"),
                author_name=metadata.get("Author"), # type: ignore
                author_email=metadata.get("Author-email"), # type: ignore
                license=metadata.get("License", "Unknown"),
                tags=["installed-package"]
            )
        except Exception as e:
            logger.warning(f"Failed to parse wheel metadata {metadata_file}: {e}")
            return None


class DependencyResolver:
    """Resolves package dependencies and handles conflicts"""
    
    def __init__(self, packages: Dict[str, List[PackageInfo]]):
        self.packages = packages
    
    def resolve_dependencies(
        self, 
        root_packages: List[str],
        include_dev: bool = False
    ) -> Tuple[Dict[str, PackageInfo], List[str]]:
        """
        Resolve dependencies for given root packages
        
        Returns:
            Tuple of (resolved_packages, warnings)
        """
        resolved = {}
        warnings = []
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(root_packages, include_dev)
        
        # Topological sort with conflict resolution
        try:
            resolved_order = self._topological_sort_with_conflicts(dependency_graph)
            
            for package_name in resolved_order:
                # Select best version for each package
                selected_package = self._select_best_version(package_name, dependency_graph)
                if selected_package:
                    resolved[package_name] = selected_package
                else:
                    warnings.append(f"Could not resolve package: {package_name}")
                    
        except DependencyResolutionError as e:
            raise DependencyResolutionError(f"Failed to resolve dependencies: {e}")
        
        return resolved, warnings
    
    def _build_dependency_graph(
        self, 
        root_packages: List[str], 
        include_dev: bool
    ) -> Dict[str, Set[str]]:
        """Build directed dependency graph"""
        graph = defaultdict(set)
        visited = set()
        
        def visit(package_name: str):
            if package_name in visited:
                return
            visited.add(package_name)
            
            if package_name not in self.packages:
                return
            
            # Use latest version for dependency analysis
            package_info = self._get_latest_version(package_name)
            if not package_info:
                return
            
            dependencies = package_info.manifest.dependencies
            if include_dev:
                dependencies.update(package_info.manifest.dev_dependencies)
            
            for dep_name in dependencies:
                graph[package_name].add(dep_name)
                visit(dep_name)  # Recursively visit dependencies
        
        # Start from root packages
        for package_name in root_packages:
            visit(package_name)
        
        return graph
    
    def _topological_sort_with_conflicts(self, graph: Dict[str, Set[str]]) -> List[str]:
        """Topological sort with cycle detection"""
        in_degree = defaultdict(int)
        all_nodes = set(graph.keys())
        
        # Calculate in-degrees
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
                all_nodes.add(neighbor)
        
        # Initialize queue with nodes having no dependencies
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Reduce in-degree of neighbors
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(result) != len(all_nodes):
            remaining = all_nodes - set(result)
            raise DependencyResolutionError(f"Circular dependency detected involving: {remaining}")
        
        return result
    
    def _select_best_version(
        self, 
        package_name: str, 
        dependency_graph: Dict[str, Set[str]]
    ) -> Optional[PackageInfo]:
        """Select the best version of a package considering all constraints"""
        if package_name not in self.packages:
            return None
        
        available_versions = self.packages[package_name]
        
        # Collect all constraints for this package
        constraints = []
        for dependent_name, dependencies in dependency_graph.items():
            if package_name in dependencies and dependent_name in self.packages:
                dependent_info = self._get_latest_version(dependent_name)
                if dependent_info and package_name in dependent_info.manifest.dependencies:
                    constraints.append(dependent_info.manifest.dependencies[package_name])
        
        # Find version that satisfies all constraints
        for package_info in sorted(available_versions, 
                                 key=lambda p: p.manifest.version, 
                                 reverse=True):  # Prefer latest versions
            if all(constraint.satisfies(package_info.manifest.version) for constraint in constraints):
                return package_info
        
        return None
    
    def _get_latest_version(self, package_name: str) -> Optional[PackageInfo]:
        """Get the latest version of a package"""
        if package_name not in self.packages:
            return None
        
        versions = self.packages[package_name]
        return max(versions, key=lambda p: p.manifest.version, default=None)


class PackageManager:
    """Main package manager for PyThra framework"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.plugins_dir = project_root / "plugins"
        
        # Package sources
        self.sources = [
            LocalPackageSource(self.plugins_dir),
            SitePackagesSource()
        ]
        
        # Cache
        self._all_packages: Dict[str, List[PackageInfo]] = {}
        self._loaded_packages: Dict[str, PackageInfo] = {}
        self._js_modules_cache: Dict[str, Dict[str, str]] = {}
        
        # Framework reference (weak to avoid circular references)
        self._framework_ref = None
    
    def set_framework(self, framework):
        """Set weak reference to framework instance"""
        self._framework_ref = weakref.ref(framework)
    
    def _add_virtual_pythra_package(self):
        """Add virtual pythra package to satisfy dependencies"""
        from . import __version__
        
        # Create virtual pythra package manifest
        virtual_manifest_data = {
            "name": "pythra",
            "version": getattr(sys.modules.get('pythra', None), '__version__', "0.1.0"),
            "description": "PyThra Framework Core",
            "package_type": "utility",
            "python_modules": [],
            "tags": ["virtual", "framework"]
        }
        
        virtual_manifest = PackageManifest.from_dict(virtual_manifest_data)
        virtual_package_info = PackageInfo(
            manifest=virtual_manifest,
            path=Path(__file__).parent,  # Point to pythra toolkit directory
            loaded=True  # Mark as already loaded since it's the framework itself
        )
        
        self._all_packages["pythra"].append(virtual_package_info)
    
    def discover_all_packages(self, force_refresh: bool = False) -> Dict[str, List[PackageInfo]]:
        """Discover all packages from all sources"""
        if not self._all_packages or force_refresh:
            self._all_packages = defaultdict(list)
            
            # Add virtual pythra package to satisfy dependencies
            self._add_virtual_pythra_package()
            
            for source in self.sources:
                try:
                    packages = source.discover_packages()
                    for name, package_list in packages.items():
                        self._all_packages[name].extend(package_list)
                except Exception as e:
                    logger.error(f"Failed to discover packages from {source}: {e}")
        
        return dict(self._all_packages)
    
    def get_package(self, name: str, version: Optional[str] = None) -> Optional[PackageInfo]:
        """Get specific package by name and optional version"""
        packages = self.discover_all_packages()
        
        if name not in packages:
            return None
        
        if version is None:
            # Return latest version
            return max(packages[name], key=lambda p: p.manifest.version, default=None)
        
        # Find specific version
        for package in packages[name]:
            if package.manifest.version == version:
                return package
        
        return None
    
    def resolve_and_load_packages(
        self, 
        package_names: List[str],
        include_dev: bool = False
    ) -> Tuple[Dict[str, PackageInfo], List[str]]:
        """Resolve dependencies and load packages"""
        all_packages = self.discover_all_packages()
        
        resolver = DependencyResolver(all_packages)
        resolved_packages, warnings = resolver.resolve_dependencies(
            package_names, 
            include_dev
        )
        
        # Load resolved packages
        loaded_packages = {}
        for name, package_info in resolved_packages.items():
            try:
                self._load_package(package_info)
                loaded_packages[name] = package_info
                self._loaded_packages[name] = package_info
            except PackageLoadError as e:
                warnings.append(f"Failed to load {name}: {e}")
        
        return loaded_packages, warnings
    
    def _load_package(self, package_info: PackageInfo):
        """Load a single package"""
        if package_info.loaded:
            return
        
        try:
            manifest = package_info.manifest
            logger.info(f"Loading package: {manifest.name} v{manifest.version}")
            
            # Validate manifest
            validation_errors = manifest.validate()
            if validation_errors:
                raise PackageLoadError(f"Invalid manifest: {validation_errors}")
            
            # Create package module in sys.modules to support relative imports
            package_module = importlib.util.module_from_spec(
                importlib.util.spec_from_loader(
                    manifest.name, 
                    loader=None, 
                    origin=str(package_info.path)
                ) # type: ignore
            )
            package_module.__path__ = [str(package_info.path)]
            sys.modules[manifest.name] = package_module
            
            # Load Python modules
            if manifest.python_modules:
                for module_name in manifest.python_modules:
                    # print(f"Module name: {module_name}")
                    try:
                        self._load_python_module(package_info, module_name)
                        print(f"✅ Module name: {module_name} Loaded")
                    except Exception as e:
                        print(f"Failed to load Python module {module_name}: {e}")
                        logger.warning(f"Failed to load Python module {module_name}: {e}")
            
            # Cache JS modules
            if manifest.js_modules:
                self._cache_js_modules(package_info)
            
            package_info.loaded = True
            logger.info(f"Successfully loaded package: {manifest.name}")
            
        except Exception as e:
            package_info.load_error = str(e)
            raise PackageLoadError(f"Failed to load package {package_info.manifest.name}: {e}")
    
    def _load_python_module(self, package_info: PackageInfo, module_name: str):
        """Load Python module from package"""
        module_path = package_info.path / f"{module_name}.py"
        if not module_path.exists():
            module_path = package_info.path / module_name / "__init__.py"
        
        if not module_path.exists():
            raise PackageLoadError(f"Python module {module_name} not found in {package_info.path}")
        
        # Import the module
        spec = importlib.util.spec_from_file_location(
            f"{package_info.manifest.name}.{module_name}",
            module_path
        )
        module = importlib.util.module_from_spec(spec) # type: ignore
        spec.loader.exec_module(module) # type: ignore
        
                # Cache the module
        package_info.python_modules_cache[module_name] = module
        
        # Add to sys.modules for future imports
        sys.modules[f"{package_info.manifest.name}.{module_name}"] = module
        
        # If this is a widget or plugin module, ensure it has access to the framework
        framework = self._framework_ref() if self._framework_ref else None
        if framework and hasattr(module, 'register_with_framework'):
            try:
                module.register_with_framework(framework)
            except Exception as e:
                logger.warning(f"Failed to register module {module_name} with framework: {e}")    
    
    def _cache_js_modules(self, package_info: PackageInfo):
        """Cache JavaScript modules paths for framework"""
        for engine_name, js_file in package_info.manifest.js_modules.items():
            full_path = package_info.get_asset_path(js_file)
            if full_path.exists():
                package_info.js_modules_cache[engine_name] = str(full_path)
                
                # Add to framework's plugin JS modules if framework is available
                framework = self._framework_ref() if self._framework_ref else None
                if framework:
                    framework.plugin_js_modules[engine_name] = {
                        "path": str(full_path),
                        "plugin": package_info.manifest.name
                    }
    
    def get_asset_server_dirs(self) -> Dict[str, str]:
        """Get asset directories for the framework's asset server"""
        serve_dirs = {}
        
        for name, package_info in self._loaded_packages.items():
            if package_info.manifest.asset_dir:
                url_prefix = f"packages/{name}"
                fs_path = str(package_info.path / package_info.manifest.asset_dir)
                serve_dirs[url_prefix] = fs_path
        
        return serve_dirs
    
    def list_packages(self, package_type: Optional[PackageType] = None) -> List[PackageInfo]:
        """List all discovered packages, optionally filtered by type"""
        all_packages = self.discover_all_packages()
        
        packages = []
        for package_list in all_packages.values():
            for package_info in package_list:
                if package_type is None or package_info.manifest.package_type == package_type:
                    packages.append(package_info)
        
        return sorted(packages, key=lambda p: (p.manifest.name, p.manifest.version))
    
    def get_loaded_packages(self) -> Dict[str, PackageInfo]:
        """Get all currently loaded packages"""
        return dict(self._loaded_packages)