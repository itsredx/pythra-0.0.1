"""
PyThra Package System - Enhanced plugin/package management similar to pub.dev

This module provides:
- Enhanced package manifest structure with dependencies and metadata
- Package discovery and loading system
- Dependency resolution
- Version management
- Security and validation features
"""

import os
import json
import hashlib
import importlib.util
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
try:
    import semver
    SEMVER_AVAILABLE = True
except ImportError:
    SEMVER_AVAILABLE = False
    print("Warning: semver package not available. Install with: pip install semver")
    
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    # requests is optional for now
    
import weakref
from urllib.parse import urlparse


class PackageType(Enum):
    """Types of PyThra packages"""
    PLUGIN = "plugin"           # Traditional plugins with JS/CSS assets
    WIDGET_LIBRARY = "widgets" # Pure widget libraries
    THEME = "theme"            # Theme packages
    UTILITY = "utility"        # Utility packages
    COMPLETE_APP = "app"       # Complete application templates


class DependencyConstraint(Enum):
    """Dependency constraint types"""
    EXACT = "exact"           # ==1.0.0
    COMPATIBLE = "compatible" # ^1.0.0 (semver compatible)
    GREATER = "greater"       # >=1.0.0
    RANGE = "range"          # 1.0.0-2.0.0


@dataclass
class PackageDependency:
    """Represents a package dependency"""
    name: str
    version_constraint: str
    constraint_type: DependencyConstraint = DependencyConstraint.COMPATIBLE
    optional: bool = False
    description: Optional[str] = None
    
    def satisfies(self, version: str) -> bool:
        """Check if a version satisfies this dependency constraint"""
        if not SEMVER_AVAILABLE:
            # Fallback to simple string comparison if semver not available
            return version == self.version_constraint.lstrip("^>=")
            
        try:
            if self.constraint_type == DependencyConstraint.EXACT:
                return semver.compare(version, self.version_constraint.lstrip("=")) == 0 # pyright: ignore[reportPossiblyUnboundVariable]
            elif self.constraint_type == DependencyConstraint.COMPATIBLE:
                return semver.satisfies(version, self.version_constraint) # type: ignore
            elif self.constraint_type == DependencyConstraint.GREATER:
                return semver.compare(version, self.version_constraint.lstrip(">=")) >= 0
            elif self.constraint_type == DependencyConstraint.RANGE:
                min_ver, max_ver = self.version_constraint.split("-")
                return (semver.compare(version, min_ver) >= 0 and 
                       semver.compare(version, max_ver) <= 0)
        except Exception:
            return False
        return False


@dataclass
class PackageAuthor:
    """Package author information"""
    name: str
    email: Optional[str] = None
    url: Optional[str] = None


@dataclass
class PackageRepository:
    """Package repository information"""
    type: str = "git"  # git, hg, svn, etc.
    url: Optional[str] = None
    directory: Optional[str] = None


@dataclass
class PackageManifest:
    """Enhanced package manifest similar to pub.dev package.json"""
    # Basic package info
    name: str
    version: str
    description: str
    package_type: PackageType = PackageType.PLUGIN
    
    # Author and repository info
    author: Optional[PackageAuthor] = None
    authors: List[PackageAuthor] = field(default_factory=list)
    homepage: Optional[str] = None
    repository: Optional[PackageRepository] = None
    documentation: Optional[str] = None
    license: str = "MIT"
    
    # Package metadata
    tags: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    
    # Dependencies
    dependencies: Dict[str, PackageDependency] = field(default_factory=dict)
    dev_dependencies: Dict[str, PackageDependency] = field(default_factory=dict)
    peer_dependencies: Dict[str, PackageDependency] = field(default_factory=dict)
    
    # PyThra-specific configuration
    pythra_version: str = ">=0.1.0"  # Minimum PyThra version required
    
    # Asset configuration
    asset_dir: str = "public"
    css_files: List[str] = field(default_factory=list)
    js_modules: Dict[str, str] = field(default_factory=dict)
    
    # Python module exports
    python_modules: List[str] = field(default_factory=list)
    main_module: Optional[str] = None  # Main entry point
    
    # External dependencies (npm packages, CDN resources, etc.)
    external_dependencies: Dict[str, str] = field(default_factory=dict)
    
    # Package configuration
    config_schema: Optional[Dict[str, Any]] = None  # JSON schema for configuration
    
    # Security and integrity
    checksums: Dict[str, str] = field(default_factory=dict)
    signature: Optional[str] = None
    
    # Compatibility
    min_python_version: str = "3.8"
    max_python_version: Optional[str] = None
    supported_platforms: List[str] = field(default_factory=lambda: ["windows", "linux", "macos"])
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PackageManifest':
        """Create PackageManifest from dictionary"""
        # Handle nested objects
        if 'author' in data and isinstance(data['author'], dict):
            data['author'] = PackageAuthor(**data['author'])
        
        if 'authors' in data and isinstance(data['authors'], list):
            data['authors'] = [PackageAuthor(**author) if isinstance(author, dict) else author 
                              for author in data['authors']]
        
        if 'repository' in data and isinstance(data['repository'], dict):
            data['repository'] = PackageRepository(**data['repository'])
        
        if 'package_type' in data and isinstance(data['package_type'], str):
            data['package_type'] = PackageType(data['package_type'])
        
        # Handle dependencies
        for dep_type in ['dependencies', 'dev_dependencies', 'peer_dependencies']:
            if dep_type in data and isinstance(data[dep_type], dict):
                deps = {}
                for name, dep_info in data[dep_type].items():
                    if isinstance(dep_info, str):
                        # Simple version string
                        deps[name] = PackageDependency(name=name, version_constraint=dep_info)
                    elif isinstance(dep_info, dict):
                        # Full dependency object
                        deps[name] = PackageDependency(name=name, **dep_info)
                data[dep_type] = deps
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert PackageManifest to dictionary"""
        return asdict(self)
    
    def validate(self) -> List[str]:
        """Validate the package manifest and return list of errors"""
        errors = []
        
        if not self.name or not self.name.strip():
            errors.append("Package name is required")
        
        if not self.version:
            errors.append("Package version is required")
        elif SEMVER_AVAILABLE:
            try:
                semver.VersionInfo.parse(self.version)
            except ValueError:
                errors.append(f"Invalid version format: {self.version}")
        
        if not self.description or not self.description.strip():
            errors.append("Package description is required")
        
        # Validate dependency versions
        for dep_name, dep in self.dependencies.items():
            if not dep.version_constraint:
                errors.append(f"Dependency {dep_name} missing version constraint")
        
        # Validate asset files exist (if package is local)
        # This would be implemented when loading from filesystem
        
        return errors
    
    def get_dependency_names(self, include_dev: bool = False, include_peer: bool = False) -> Set[str]:
        """Get all dependency names"""
        deps = set(self.dependencies.keys())
        if include_dev:
            deps.update(self.dev_dependencies.keys())
        if include_peer:
            deps.update(self.peer_dependencies.keys())
        return deps


@dataclass 
class PackageInfo:
    """Information about an installed/available package"""
    manifest: PackageManifest
    path: Path
    loaded: bool = False
    load_error: Optional[str] = None
    python_modules_cache: Dict[str, Any] = field(default_factory=dict)
    js_modules_cache: Dict[str, str] = field(default_factory=dict)
    
    def get_asset_path(self, relative_path: str) -> Path:
        """Get full path to an asset file"""
        return self.path / self.manifest.asset_dir / relative_path
    
    def get_js_module_path(self, module_name: str) -> Optional[Path]:
        """Get full path to a JS module"""
        if module_name in self.manifest.js_modules:
            return self.get_asset_path(self.manifest.js_modules[module_name])
        return None


class PackageLoadError(Exception):
    """Exception raised when package loading fails"""
    pass


class DependencyResolutionError(Exception):
    """Exception raised when dependency resolution fails"""
    pass


def parse_version_constraint(constraint: str) -> Tuple[str, DependencyConstraint]:
    """Parse version constraint string into version and constraint type"""
    constraint = constraint.strip()
    
    if constraint.startswith("=="):
        return constraint[2:], DependencyConstraint.EXACT
    elif constraint.startswith("^"):
        return constraint[1:], DependencyConstraint.COMPATIBLE
    elif constraint.startswith(">="):
        return constraint[2:], DependencyConstraint.GREATER
    elif "-" in constraint and not constraint.startswith("-"):
        return constraint, DependencyConstraint.RANGE
    else:
        # Default to compatible
        return constraint, DependencyConstraint.COMPATIBLE


def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate checksum of a file"""
    hash_algo = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_algo.update(chunk)
    return hash_algo.hexdigest()