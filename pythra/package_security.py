"""
PyThra Package Security - Validation and security features

This module provides:
- Package integrity verification
- Manifest validation
- Security scanning
- Digital signatures (future)
"""

import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import logging
from dataclasses import dataclass

from .package_system import PackageManifest, PackageInfo, calculate_file_checksum

logger = logging.getLogger(__name__)


@dataclass
class SecurityIssue:
    """Represents a security issue found in a package"""
    severity: str  # "critical", "high", "medium", "low", "info"
    category: str  # "malware", "vulnerability", "policy", "integrity"
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationResult:
    """Result of package validation"""
    valid: bool
    errors: List[str]
    warnings: List[str]
    security_issues: List[SecurityIssue]
    checksum_verified: bool = False
    manifest_valid: bool = False
    
    def is_safe(self) -> bool:
        """Check if package is safe to install based on security issues"""
        critical_issues = [issue for issue in self.security_issues 
                         if issue.severity in ["critical", "high"]]
        return len(critical_issues) == 0


class PackageValidator:
    """Validates packages for security and integrity"""
    
    def __init__(self):
        # Dangerous Python patterns to look for
        self.dangerous_patterns = [
            # Code execution
            (r'exec\s*\(', "critical", "Code execution using exec()"),
            (r'eval\s*\(', "critical", "Code execution using eval()"),
            (r'compile\s*\(', "high", "Dynamic code compilation"),
            (r'__import__\s*\(', "medium", "Dynamic imports"),
            
            # File system access
            (r'os\.system\s*\(', "critical", "System command execution"),
            (r'subprocess\.(run|call|Popen)', "high", "Process execution"),
            (r'open\s*\([^)]*["\']w', "medium", "File writing operations"),
            (r'shutil\.(rmtree|move|copy)', "medium", "File system modification"),
            
            # Network access
            (r'urllib\.request', "medium", "Network requests"),
            (r'requests\.(get|post|put|delete)', "medium", "HTTP requests"),
            (r'socket\.', "medium", "Direct socket operations"),
            
            # Dangerous imports
            (r'import\s+(os|sys|subprocess|shutil)', "medium", "Potentially dangerous imports"),
        ]
        
        # File extensions that should not be in packages
        self.suspicious_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.dll', '.so',
            '.dylib', '.app', '.deb', '.rpm', '.msi', '.dmg'
        }
        
        # Maximum file sizes (in bytes)
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.max_package_size = 100 * 1024 * 1024  # 100MB
    
    def validate_package(self, package_info: PackageInfo, check_files: bool = True) -> ValidationResult:
        """Validate a package for security and integrity"""
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            security_issues=[]
        )
        
        try:
            # 1. Validate manifest
            manifest_errors = self._validate_manifest(package_info.manifest)
            result.errors.extend(manifest_errors)
            result.manifest_valid = len(manifest_errors) == 0
            
            if check_files:
                # 2. Check file integrity
                checksum_issues = self._verify_checksums(package_info)
                result.security_issues.extend(checksum_issues)
                result.checksum_verified = len(checksum_issues) == 0
                
                # 3. Scan files for security issues
                security_issues = self._scan_package_files(package_info)
                result.security_issues.extend(security_issues)
                
                # 4. Check package structure
                structure_issues = self._validate_package_structure(package_info)
                result.security_issues.extend(structure_issues)
            
            # Determine overall validity
            critical_issues = [issue for issue in result.security_issues 
                             if issue.severity in ["critical", "high"]]
            
            if result.errors or critical_issues:
                result.valid = False
            
        except Exception as e:
            logger.error(f"Error validating package {package_info.manifest.name}: {e}")
            result.valid = False
            result.errors.append(f"Validation error: {e}")
        
        return result
    
    def _validate_manifest(self, manifest: PackageManifest) -> List[str]:
        """Validate package manifest"""
        errors = []
        
        # Basic manifest validation
        manifest_errors = manifest.validate()
        errors.extend(manifest_errors)
        
        # Additional security checks
        if not manifest.name or not re.match(r'^[a-z0-9_-]+$', manifest.name):
            errors.append("Package name must contain only lowercase letters, numbers, hyphens, and underscores")
        
        if len(manifest.name) > 100:
            errors.append("Package name too long (max 100 characters)")
        
        if len(manifest.description) > 1000:
            errors.append("Package description too long (max 1000 characters)")
        
        # Check for suspicious dependencies
        for dep_name in manifest.dependencies:
            if not re.match(r'^[a-z0-9_-]+$', dep_name):
                errors.append(f"Suspicious dependency name: {dep_name}")
        
        return errors
    
    def _verify_checksums(self, package_info: PackageInfo) -> List[SecurityIssue]:
        """Verify package file checksums"""
        issues = []
        
        if not package_info.manifest.checksums:
            issues.append(SecurityIssue(
                severity="medium",
                category="integrity",
                message="No checksums provided for integrity verification"
            ))
            return issues
        
        for file_rel_path, expected_checksum in package_info.manifest.checksums.items():
            file_path = package_info.path / file_rel_path
            
            if not file_path.exists():
                issues.append(SecurityIssue(
                    severity="high",
                    category="integrity",
                    message=f"File {file_rel_path} missing but has checksum",
                    file_path=str(file_path)
                ))
                continue
            
            try:
                actual_checksum = calculate_file_checksum(file_path)
                if actual_checksum != expected_checksum:
                    issues.append(SecurityIssue(
                        severity="critical",
                        category="integrity",
                        message=f"Checksum mismatch for {file_rel_path}",
                        file_path=str(file_path),
                        details={
                            "expected": expected_checksum,
                            "actual": actual_checksum
                        }
                    ))
            except Exception as e:
                issues.append(SecurityIssue(
                    severity="high",
                    category="integrity",
                    message=f"Error calculating checksum for {file_rel_path}: {e}",
                    file_path=str(file_path)
                ))
        
        return issues
    
    def _scan_package_files(self, package_info: PackageInfo) -> List[SecurityIssue]:
        """Scan package files for security issues"""
        issues = []
        total_size = 0
        
        for file_path in package_info.path.rglob("*"):
            if not file_path.is_file():
                continue
            
            try:
                file_size = file_path.stat().st_size
                total_size += file_size
                
                # Check file size
                if file_size > self.max_file_size:
                    issues.append(SecurityIssue(
                        severity="medium",
                        category="policy",
                        message=f"File too large: {file_size} bytes",
                        file_path=str(file_path)
                    ))
                
                # Check file extension
                if file_path.suffix.lower() in self.suspicious_extensions:
                    issues.append(SecurityIssue(
                        severity="high",
                        category="malware",
                        message=f"Suspicious file extension: {file_path.suffix}",
                        file_path=str(file_path)
                    ))
                
                # Scan Python files
                if file_path.suffix == '.py':
                    python_issues = self._scan_python_file(file_path)
                    issues.extend(python_issues)
                
                # Scan JavaScript files
                elif file_path.suffix == '.js':
                    js_issues = self._scan_javascript_file(file_path)
                    issues.extend(js_issues)
            
            except Exception as e:
                issues.append(SecurityIssue(
                    severity="medium",
                    category="integrity",
                    message=f"Error scanning file {file_path}: {e}",
                    file_path=str(file_path)
                ))
        
        # Check total package size
        if total_size > self.max_package_size:
            issues.append(SecurityIssue(
                severity="medium",
                category="policy",
                message=f"Package too large: {total_size} bytes (max {self.max_package_size})"
            ))
        
        return issues
    
    def _scan_python_file(self, file_path: Path) -> List[SecurityIssue]:
        """Scan Python file for security issues"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Pattern matching
            for pattern, severity, message in self.dangerous_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append(SecurityIssue(
                        severity=severity,
                        category="vulnerability",
                        message=message,
                        file_path=str(file_path),
                        line_number=line_num,
                        details={"matched_text": match.group()}
                    ))
            
            # AST analysis for more sophisticated checks
            try:
                tree = ast.parse(content)
                ast_issues = self._analyze_python_ast(tree, file_path)
                issues.extend(ast_issues)
            except SyntaxError:
                issues.append(SecurityIssue(
                    severity="low",
                    category="integrity",
                    message="Python syntax error",
                    file_path=str(file_path)
                ))
        
        except Exception as e:
            issues.append(SecurityIssue(
                severity="low",
                category="integrity",
                message=f"Error scanning Python file: {e}",
                file_path=str(file_path)
            ))
        
        return issues
    
    def _analyze_python_ast(self, tree: ast.AST, file_path: Path) -> List[SecurityIssue]:
        """Analyze Python AST for security issues"""
        issues = []
        
        class SecurityVisitor(ast.NodeVisitor):
            def __init__(self, issues_list):
                self.issues = issues_list
            
            def visit_Call(self, node):
                # Check for dangerous function calls
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['exec', 'eval', 'compile']:
                        self.issues.append(SecurityIssue(
                            severity="critical",
                            category="vulnerability",
                            message=f"Dangerous function call: {node.func.id}",
                            file_path=str(file_path),
                            line_number=node.lineno
                        ))
                
                elif isinstance(node.func, ast.Attribute):
                    if (hasattr(node.func.value, 'id') and 
                        node.func.value.id == 'os' and  # type: ignore
                        node.func.attr == 'system'):
                        self.issues.append(SecurityIssue(
                            severity="critical",
                            category="vulnerability",
                            message="System command execution",
                            file_path=str(file_path),
                            line_number=node.lineno
                        ))
                
                self.generic_visit(node)
            
            def visit_Import(self, node):
                for alias in node.names:
                    if alias.name in ['ctypes', 'subprocess']:
                        self.issues.append(SecurityIssue(
                            severity="medium",
                            category="vulnerability",
                            message=f"Potentially dangerous import: {alias.name}",
                            file_path=str(file_path),
                            line_number=node.lineno
                        ))
                self.generic_visit(node)
        
        visitor = SecurityVisitor(issues)
        visitor.visit(tree)
        
        return issues
    
    def _scan_javascript_file(self, file_path: Path) -> List[SecurityIssue]:
        """Scan JavaScript file for security issues"""
        issues = []
        
        # JavaScript security patterns
        js_patterns = [
            (r'eval\s*\(', "critical", "JavaScript eval() usage"),
            (r'Function\s*\(', "high", "Dynamic function creation"),
            (r'document\.write\s*\(', "medium", "DOM manipulation via document.write"),
            (r'innerHTML\s*=', "low", "Potential XSS via innerHTML"),
            (r'fetch\s*\(', "medium", "Network requests"),
            (r'XMLHttpRequest', "medium", "AJAX requests"),
        ]
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            for pattern, severity, message in js_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append(SecurityIssue(
                        severity=severity,
                        category="vulnerability",
                        message=message,
                        file_path=str(file_path),
                        line_number=line_num
                    ))
        
        except Exception as e:
            issues.append(SecurityIssue(
                severity="low",
                category="integrity",
                message=f"Error scanning JavaScript file: {e}",
                file_path=str(file_path)
            ))
        
        return issues
    
    def _validate_package_structure(self, package_info: PackageInfo) -> List[SecurityIssue]:
        """Validate package directory structure"""
        issues = []
        
        # Check for hidden files that shouldn't be there
        for file_path in package_info.path.rglob(".*"):
            if file_path.name in ['.git', '.svn', '.hg']:
                issues.append(SecurityIssue(
                    severity="medium",
                    category="policy",
                    message=f"Version control directory found: {file_path.name}",
                    file_path=str(file_path)
                ))
            elif file_path.name.startswith('.') and file_path.is_file():
                issues.append(SecurityIssue(
                    severity="low",
                    category="policy",
                    message=f"Hidden file found: {file_path.name}",
                    file_path=str(file_path)
                ))
        
        # Check for files outside expected directories
        allowed_dirs = {'public', 'assets', 'src', 'lib', 'docs', 'tests'}
        manifest_file = package_info.path / 'package.json'
        
        for file_path in package_info.path.iterdir():
            if file_path.is_file():
                # Allow manifest files and common files
                if file_path.name in ['package.json', 'pythra_plugin.py', 'README.md', 
                                     'LICENSE', 'CHANGELOG.md', '__init__.py']:
                    continue
            elif file_path.is_dir():
                if file_path.name not in allowed_dirs:
                    issues.append(SecurityIssue(
                        severity="low",
                        category="policy",
                        message=f"Unexpected directory: {file_path.name}",
                        file_path=str(file_path)
                    ))
        
        return issues


class PackageWhitelist:
    """Manages whitelist of trusted packages and authors"""
    
    def __init__(self, whitelist_file: Path = None): # type: ignore
        if whitelist_file is None:
            whitelist_file = Path.home() / ".pythra" / "package_whitelist.json"
        
        self.whitelist_file = whitelist_file
        self.trusted_packages: Set[str] = set()
        self.trusted_authors: Set[str] = set()
        self.trusted_domains: Set[str] = set()
        
        self._load_whitelist()
    
    def _load_whitelist(self):
        """Load whitelist from file"""
        if not self.whitelist_file.exists():
            return
        
        try:
            with open(self.whitelist_file) as f:
                data = json.load(f)
            
            self.trusted_packages = set(data.get("packages", []))
            self.trusted_authors = set(data.get("authors", []))
            self.trusted_domains = set(data.get("domains", []))
            
        except Exception as e:
            logger.warning(f"Failed to load package whitelist: {e}")
    
    def save_whitelist(self):
        """Save whitelist to file"""
        try:
            self.whitelist_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "packages": list(self.trusted_packages),
                "authors": list(self.trusted_authors),
                "domains": list(self.trusted_domains)
            }
            
            with open(self.whitelist_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save package whitelist: {e}")
    
    def is_trusted_package(self, package_name: str) -> bool:
        """Check if a package is in the whitelist"""
        return package_name in self.trusted_packages
    
    def is_trusted_author(self, author_email: str) -> bool:
        """Check if an author is trusted"""
        if not author_email:
            return False
        
        # Check exact email
        if author_email in self.trusted_authors:
            return True
        
        # Check domain
        domain = author_email.split('@')[-1] if '@' in author_email else ''
        return domain in self.trusted_domains
    
    def add_trusted_package(self, package_name: str):
        """Add package to whitelist"""
        self.trusted_packages.add(package_name)
        self.save_whitelist()
    
    def add_trusted_author(self, author_email: str):
        """Add author to whitelist"""
        self.trusted_authors.add(author_email)
        self.save_whitelist()
    
    def add_trusted_domain(self, domain: str):
        """Add domain to whitelist"""
        self.trusted_domains.add(domain)
        self.save_whitelist()


# Global validator and whitelist instances
_validator = None
_whitelist = None

def get_package_validator() -> PackageValidator:
    """Get the global package validator instance"""
    global _validator
    if _validator is None:
        _validator = PackageValidator()
    return _validator

def get_package_whitelist() -> PackageWhitelist:
    """Get the global package whitelist instance"""
    global _whitelist
    if _whitelist is None:
        _whitelist = PackageWhitelist()
    return _whitelist