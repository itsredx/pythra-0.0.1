"""
PyThra Package Registry - Remote package distribution system

This module provides:
- Registry client for fetching packages from remote repositories
- Package caching and integrity verification
- Future support for pub.dev-style package distribution
"""

import os
import json
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from urllib.parse import urljoin
from dataclasses import dataclass, asdict

from .package_system import PackageManifest, PackageInfo, calculate_file_checksum

# Only import requests if available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PackageVersion:
    """Information about a specific version of a package in the registry"""
    version: str
    manifest: PackageManifest
    download_url: str
    checksums: Dict[str, str]  # file -> checksum mapping
    size_bytes: int
    published_at: str  # ISO timestamp
    yanked: bool = False  # Whether version is yanked/removed


@dataclass
class RegistryPackage:
    """Package information from registry"""
    name: str
    description: str
    homepage: Optional[str] = None
    repository: Optional[str] = None
    versions: Dict[str, PackageVersion] = None
    latest_version: Optional[str] = None
    downloads: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.versions is None:
            self.versions = {}


class PackageRegistry:
    """Client for interacting with PyThra package registries"""
    
    def __init__(self, registry_url: str = None, cache_dir: Path = None):
        self.registry_url = registry_url or "https://packages.pythra.dev"  # Future registry URL
        
        if cache_dir is None:
            # Default cache in user's home directory
            cache_dir = Path.home() / ".pythra" / "package_cache"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Session for connection pooling
        if REQUESTS_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'PyThra-Package-Manager/0.1.0',
                'Accept': 'application/json'
            })
        else:
            self.session = None
            logger.warning("requests not available, registry features disabled")
    
    def search_packages(self, query: str, limit: int = 20) -> List[RegistryPackage]:
        """Search for packages in the registry"""
        if not self.session:
            logger.error("Registry search not available - requests library required")
            return []
        
        try:
            response = self.session.get(
                urljoin(self.registry_url, "/api/search"),
                params={"q": query, "limit": limit},
                timeout=10
            )
            response.raise_for_status()
            
            results = response.json()
            packages = []
            
            for pkg_data in results.get("packages", []):
                package = RegistryPackage(**pkg_data)
                packages.append(package)
            
            return packages
            
        except Exception as e:
            logger.error(f"Failed to search packages: {e}")
            return []
    
    def get_package_info(self, package_name: str) -> Optional[RegistryPackage]:
        """Get detailed information about a package"""
        if not self.session:
            return None
        
        try:
            response = self.session.get(
                urljoin(self.registry_url, f"/api/packages/{package_name}"),
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return RegistryPackage(**data)
            
        except Exception as e:
            logger.error(f"Failed to get package info for {package_name}: {e}")
            return None
    
    def download_package(
        self, 
        package_name: str, 
        version: str = None,
        target_dir: Path = None
    ) -> Optional[PackageInfo]:
        """Download and cache a package from the registry"""
        if not self.session:
            logger.error("Package download not available - requests library required")
            return None
        
        # Get package information
        registry_pkg = self.get_package_info(package_name)
        if not registry_pkg:
            return None
        
        # Select version
        if version is None:
            version = registry_pkg.latest_version
        
        if version not in registry_pkg.versions:
            logger.error(f"Version {version} not found for package {package_name}")
            return None
        
        pkg_version = registry_pkg.versions[version]
        
        # Check cache first
        cached_package = self._get_from_cache(package_name, version)
        if cached_package:
            logger.info(f"Using cached package: {package_name} v{version}")
            return cached_package
        
        # Download package
        try:
            logger.info(f"Downloading {package_name} v{version}...")
            response = self.session.get(pkg_version.download_url, timeout=30)
            response.raise_for_status()
            
            # Determine target directory
            if target_dir is None:
                target_dir = self.cache_dir / f"{package_name}-{version}"
            
            # Extract package (assuming tar.gz format)
            return self._extract_and_verify_package(
                response.content, 
                pkg_version,
                target_dir
            )
            
        except Exception as e:
            logger.error(f"Failed to download {package_name} v{version}: {e}")
            return None
    
    def _get_from_cache(self, package_name: str, version: str) -> Optional[PackageInfo]:
        """Check if package exists in cache and is valid"""
        cache_path = self.cache_dir / f"{package_name}-{version}"
        
        if not cache_path.exists():
            return None
        
        # Try to load manifest
        manifest_file = cache_path / "package.json"
        if not manifest_file.exists():
            # Try legacy manifest
            manifest_file = cache_path / "pythra_plugin.py"
        
        if not manifest_file.exists():
            return None
        
        try:
            if manifest_file.name == "package.json":
                with open(manifest_file) as f:
                    data = json.load(f)
                manifest = PackageManifest.from_dict(data)
            else:
                # Handle legacy format
                return None  # For now, don't cache legacy formats
            
            return PackageInfo(
                manifest=manifest,
                path=cache_path,
                loaded=False
            )
            
        except Exception as e:
            logger.warning(f"Failed to load cached package {package_name} v{version}: {e}")
            return None
    
    def _extract_and_verify_package(
        self, 
        content: bytes, 
        pkg_version: PackageVersion,
        target_dir: Path
    ) -> Optional[PackageInfo]:
        """Extract package content and verify integrity"""
        import tarfile
        
        try:
            # Create temporary file for extraction
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Verify checksum if provided
            if pkg_version.checksums:
                actual_checksum = calculate_file_checksum(Path(temp_file_path))
                expected_checksum = pkg_version.checksums.get("sha256")
                
                if expected_checksum and actual_checksum != expected_checksum:
                    logger.error("Package checksum verification failed")
                    os.unlink(temp_file_path)
                    return None
            
            # Extract to target directory
            target_dir.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(temp_file_path, "r:gz") as tar:
                tar.extractall(target_dir)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            # Load manifest from extracted package
            manifest_file = target_dir / "package.json"
            if manifest_file.exists():
                with open(manifest_file) as f:
                    data = json.load(f)
                manifest = PackageManifest.from_dict(data)
                
                return PackageInfo(
                    manifest=manifest,
                    path=target_dir,
                    loaded=False
                )
            
            logger.error("No manifest found in downloaded package")
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract package: {e}")
            return None
    
    def publish_package(self, package_path: Path, api_token: str) -> bool:
        """Publish a package to the registry (future feature)"""
        if not self.session:
            logger.error("Package publishing not available - requests library required")
            return False
        
        # This would implement package publishing to the registry
        # For now, just a placeholder
        logger.info("Package publishing is not yet implemented")
        return False
    
    def clear_cache(self, package_name: str = None):
        """Clear package cache"""
        if package_name:
            # Clear specific package
            for cache_item in self.cache_dir.glob(f"{package_name}-*"):
                if cache_item.is_dir():
                    shutil.rmtree(cache_item)
                    logger.info(f"Cleared cache for {cache_item.name}")
        else:
            # Clear entire cache
            for cache_item in self.cache_dir.iterdir():
                if cache_item.is_dir():
                    shutil.rmtree(cache_item)
            logger.info("Cleared entire package cache")


class MockRegistry:
    """Mock registry for testing and offline development"""
    
    def __init__(self):
        self.packages = {
            "pythra_material_theme": RegistryPackage(
                name="pythra_material_theme",
                description="Material Design theme for PyThra applications",
                homepage="https://github.com/pythra/material-theme",
                versions={
                    "1.0.0": PackageVersion(
                        version="1.0.0",
                        manifest=PackageManifest(
                            name="pythra_material_theme",
                            version="1.0.0",
                            description="Material Design theme for PyThra applications",
                            package_type="theme",
                            tags=["theme", "material-design", "ui"]
                        ),
                        download_url="https://example.com/downloads/pythra_material_theme-1.0.0.tar.gz",
                        checksums={"sha256": "dummy_checksum"},
                        size_bytes=1024000,
                        published_at="2024-01-01T00:00:00Z"
                    )
                },
                latest_version="1.0.0",
                downloads=150
            ),
            "pythra_charts": RegistryPackage(
                name="pythra_charts",
                description="Beautiful charts and graphs for PyThra",
                versions={
                    "0.5.0": PackageVersion(
                        version="0.5.0",
                        manifest=PackageManifest(
                            name="pythra_charts",
                            version="0.5.0",
                            description="Beautiful charts and graphs for PyThra",
                            package_type="widgets",
                            tags=["charts", "graphs", "visualization"]
                        ),
                        download_url="https://example.com/downloads/pythra_charts-0.5.0.tar.gz",
                        checksums={"sha256": "dummy_checksum"},
                        size_bytes=512000,
                        published_at="2024-01-15T10:30:00Z"
                    )
                },
                latest_version="0.5.0",
                downloads=89
            )
        }
    
    def search_packages(self, query: str, limit: int = 20) -> List[RegistryPackage]:
        """Search mock packages"""
        results = []
        query_lower = query.lower()
        
        for package in self.packages.values():
            if (query_lower in package.name.lower() or 
                query_lower in package.description.lower() or
                any(query_lower in tag for tag in getattr(package.versions.get(package.latest_version).manifest, 'tags', []))):
                results.append(package)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_package_info(self, package_name: str) -> Optional[RegistryPackage]:
        """Get mock package info"""
        return self.packages.get(package_name)


# Global registry instance
default_registry = None

def get_default_registry() -> PackageRegistry:
    """Get the default package registry instance"""
    global default_registry
    if default_registry is None:
        default_registry = PackageRegistry()
    return default_registry