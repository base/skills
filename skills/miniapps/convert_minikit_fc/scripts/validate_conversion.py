#!/usr/bin/env python3
"""
Validate a converted project to ensure MiniKit has been fully removed
and Farcaster SDK is properly set up.

Usage:
    python scripts/validate_conversion.py <project_dir>

Checks:
    1. No remaining MiniKit imports
    2. No remaining MiniKit hooks
    3. No MiniKitProvider in code
    4. Farcaster SDK is imported where needed
    5. sdk.actions.ready() is called somewhere
    6. package.json has correct dependencies
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import List, Tuple

class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []
    
    def add_error(self, msg: str):
        self.errors.append(msg)
    
    def add_warning(self, msg: str):
        self.warnings.append(msg)
    
    def add_pass(self, msg: str):
        self.passed.append(msg)
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

# Patterns to check
MINIKIT_IMPORT = re.compile(r"from\s+['\"]@coinbase/onchainkit/minikit['\"]")
ONCHAINKIT_IMPORT = re.compile(r"from\s+['\"]@coinbase/onchainkit['\"]")
MINIKIT_HOOKS = re.compile(r'\b(useMiniKit|useClose|useOpenUrl|useViewProfile|useViewCast|useComposeCast|useAddFrame|useAuthenticate|useNotification|usePrimaryButton)\s*\(')
MINIKIT_PROVIDER = re.compile(r'<MiniKitProvider|MiniKitProvider')
ONCHAINKIT_PROVIDER = re.compile(r'<OnchainKitProvider|OnchainKitProvider')
MINIKIT_PROP = re.compile(r'miniKit\s*[=:]')
FARCASTER_IMPORT = re.compile(r"from\s+['\"]@farcaster/miniapp-sdk['\"]")
FARCASTER_WAGMI_IMPORT = re.compile(r"from\s+['\"]@farcaster/miniapp-wagmi-connector['\"]")
SDK_READY = re.compile(r'sdk\.actions\.ready\s*\(')
MANIFEST_FRAME_KEY = re.compile(r'["\']?frame["\']?\s*[:=]')
MANIFEST_MINIAPP_KEY = re.compile(r'["\']?miniapp["\']?\s*[:=]')
MINIKIT_CONFIG_FILE = re.compile(r'minikit\.config\.(ts|js)')
MINIKIT_CONFIG_EXPORT = re.compile(r'export\s+const\s+minikitConfig\s*=')

def find_source_files(directory: str) -> List[Path]:
    """Find all source files."""
    files = []
    for root, _, filenames in os.walk(directory):
        if 'node_modules' in root or '.next' in root:
            continue
        for filename in filenames:
            if filename.endswith(('.tsx', '.ts', '.jsx', '.js')):
                files.append(Path(root) / filename)
    return files

def check_no_minikit_imports(files: List[Path], project_path: Path, result: ValidationResult):
    """Check that no MiniKit imports remain."""
    minikit_found = []
    onchainkit_found = []
    
    for filepath in files:
        try:
            content = filepath.read_text(encoding='utf-8')
            rel_path = str(filepath.relative_to(project_path))
            
            if MINIKIT_IMPORT.search(content):
                minikit_found.append(rel_path)
            if ONCHAINKIT_IMPORT.search(content):
                onchainkit_found.append(rel_path)
        except Exception:
            pass
    
    if minikit_found:
        result.add_error(f"MiniKit imports still present in: {', '.join(minikit_found)}")
    
    if onchainkit_found:
        result.add_error(f"OnchainKit imports still present in: {', '.join(onchainkit_found)} - replace with @farcaster/miniapp-sdk")
    
    if not minikit_found and not onchainkit_found:
        result.add_pass("No MiniKit/OnchainKit imports found")

def check_no_minikit_hooks(files: List[Path], project_path: Path, result: ValidationResult):
    """Check that no MiniKit hooks are being used."""
    found = []
    for filepath in files:
        try:
            content = filepath.read_text(encoding='utf-8')
            matches = MINIKIT_HOOKS.findall(content)
            if matches:
                rel_path = filepath.relative_to(project_path)
                found.append(f"{rel_path}: {', '.join(set(matches))}")
        except Exception:
            pass
    
    if found:
        result.add_error(f"MiniKit hooks still in use:\n  " + "\n  ".join(found))
    else:
        result.add_pass("No MiniKit hooks found")

def check_no_provider(files: List[Path], project_path: Path, result: ValidationResult):
    """Check that MiniKitProvider and OnchainKitProvider are completely removed."""
    minikit_provider_found = []
    onchainkit_provider_found = []

    for filepath in files:
        try:
            content = filepath.read_text(encoding='utf-8')
            rel_path = str(filepath.relative_to(project_path))

            if MINIKIT_PROVIDER.search(content):
                minikit_provider_found.append(rel_path)

            # Check for ANY OnchainKitProvider - must be completely removed
            if ONCHAINKIT_PROVIDER.search(content):
                onchainkit_provider_found.append(rel_path)
        except Exception:
            pass

    if minikit_provider_found:
        result.add_error(f"MiniKitProvider still present in: {', '.join(minikit_provider_found)} - remove entirely")

    if onchainkit_provider_found:
        result.add_error(f"OnchainKitProvider still present in: {', '.join(onchainkit_provider_found)} - remove entirely, replace with MiniAppProvider + WagmiProvider")

    if not minikit_provider_found and not onchainkit_provider_found:
        result.add_pass("OnchainKit/MiniKit providers removed")

def check_farcaster_sdk_usage(files: List[Path], project_path: Path, result: ValidationResult):
    """Check that Farcaster SDK is imported and ready() is called."""
    has_sdk_import = False
    has_wagmi_connector = False
    has_ready = False
    sdk_import_files = []
    wagmi_connector_files = []
    ready_files = []
    
    for filepath in files:
        try:
            content = filepath.read_text(encoding='utf-8')
            rel_path = str(filepath.relative_to(project_path))
            
            if FARCASTER_IMPORT.search(content):
                has_sdk_import = True
                sdk_import_files.append(rel_path)
            if FARCASTER_WAGMI_IMPORT.search(content):
                has_wagmi_connector = True
                wagmi_connector_files.append(rel_path)
            if SDK_READY.search(content):
                has_ready = True
                ready_files.append(rel_path)
        except Exception:
            pass
    
    if has_sdk_import:
        result.add_pass(f"Farcaster SDK imported in: {', '.join(sdk_import_files)}")
    else:
        result.add_error("Farcaster SDK not imported - add: import { sdk } from '@farcaster/miniapp-sdk'")
    
    if has_wagmi_connector:
        result.add_pass(f"Farcaster wagmi connector imported in: {', '.join(wagmi_connector_files)}")
    else:
        result.add_error("Farcaster wagmi connector not imported - add: import { farcasterMiniApp } from '@farcaster/miniapp-wagmi-connector'")
    
    if has_ready:
        result.add_pass(f"sdk.actions.ready() called in: {', '.join(ready_files)}")
    else:
        result.add_error("sdk.actions.ready() not found - add to your main page useEffect: await sdk.actions.ready()")

def check_package_json(project_path: Path, result: ValidationResult):
    """Check package.json for correct dependencies."""
    package_json_path = project_path / 'package.json'
    
    if not package_json_path.exists():
        result.add_warning("package.json not found")
        return
    
    try:
        with open(package_json_path) as f:
            pkg = json.load(f)
    except Exception as e:
        result.add_error(f"Could not parse package.json: {e}")
        return
    
    deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
    
    # Check for old OnchainKit - this should be removed
    if '@coinbase/onchainkit' in deps:
        result.add_error("@coinbase/onchainkit still installed - run: npm uninstall @coinbase/onchainkit")
    else:
        result.add_pass("@coinbase/onchainkit removed")
    
    # Check for required Farcaster packages
    required_packages = [
        ('@farcaster/miniapp-sdk', 'npm install @farcaster/miniapp-sdk'),
        ('@farcaster/miniapp-wagmi-connector', 'npm install @farcaster/miniapp-wagmi-connector'),
        ('wagmi', 'npm install wagmi'),
        ('@tanstack/react-query', 'npm install @tanstack/react-query'),
    ]
    
    for package, install_cmd in required_packages:
        if package in deps:
            result.add_pass(f"{package} installed (version: {deps[package]})")
        else:
            result.add_error(f"{package} not installed - run: {install_cmd}")

def check_env_variables(project_path: Path, result: ValidationResult):
    """Check for old environment variables that should be removed."""
    env_files = ['.env', '.env.local', '.env.example']
    old_vars = ['NEXT_PUBLIC_ONCHAINKIT_API_KEY', 'NEXT_PUBLIC_ONCHAINKIT_PROJECT_NAME']
    
    for env_file in env_files:
        env_path = project_path / env_file
        if env_path.exists():
            try:
                content = env_path.read_text()
                found = [var for var in old_vars if var in content]
                if found:
                    result.add_warning(f"{env_file} contains old MiniKit vars: {', '.join(found)}")
            except Exception:
                pass

def check_manifest(project_path: Path, result: ValidationResult):
    """Check farcaster.json manifest uses 'miniapp' instead of 'frame'."""
    # Check for manifest route
    manifest_paths = [
        project_path / 'app' / '.well-known' / 'farcaster.json' / 'route.ts',
        project_path / 'app' / '.well-known' / 'farcaster.json' / 'route.js',
        project_path / 'pages' / 'api' / '.well-known' / 'farcaster.json.ts',
        project_path / 'pages' / 'api' / '.well-known' / 'farcaster.json.js',
        project_path / 'public' / '.well-known' / 'farcaster.json',
    ]
    
    manifest_found = False
    for manifest_path in manifest_paths:
        if manifest_path.exists():
            manifest_found = True
            try:
                content = manifest_path.read_text()
                
                # Check for old 'frame' key
                if MANIFEST_FRAME_KEY.search(content):
                    result.add_error(f"Manifest uses 'frame' key - change to 'miniapp': {manifest_path.relative_to(project_path)}")
                
                # Check for new 'miniapp' key
                if MANIFEST_MINIAPP_KEY.search(content):
                    result.add_pass(f"Manifest correctly uses 'miniapp' key: {manifest_path.relative_to(project_path)}")
                elif not MANIFEST_FRAME_KEY.search(content):
                    result.add_warning(f"Manifest found but no 'miniapp' or 'frame' key detected: {manifest_path.relative_to(project_path)}")
                    
            except Exception as e:
                result.add_warning(f"Could not read manifest: {e}")
            break
    
    if not manifest_found:
        result.add_warning("No farcaster.json manifest found - create app/.well-known/farcaster.json/route.ts")

def check_config_renamed(files: List[Path], project_path: Path, result: ValidationResult):
    """Check that minikit.config has been renamed to farcaster.config."""
    config_file_found = False
    export_found = False

    for filepath in files:
        if MINIKIT_CONFIG_FILE.search(filepath.name):
            result.add_error(f"Rename to farcaster.config: {filepath.relative_to(project_path)}")
            config_file_found = True

        try:
            content = filepath.read_text(encoding='utf-8')
            if MINIKIT_CONFIG_EXPORT.search(content):
                result.add_error(f"Rename minikitConfig to farcasterConfig: {filepath.relative_to(project_path)}")
                export_found = True
        except Exception:
            pass

    if not config_file_found and not export_found:
        result.add_pass("Config file and export renamed correctly")

def validate_project(project_dir: str) -> ValidationResult:
    """Run all validation checks."""
    project_path = Path(project_dir).resolve()
    result = ValidationResult()
    
    if not project_path.exists():
        result.add_error(f"Directory does not exist: {project_dir}")
        return result
    
    files = find_source_files(str(project_path))
    
    if not files:
        result.add_warning("No source files found")
        return result
    
    # Run checks
    check_no_minikit_imports(files, project_path, result)
    check_no_minikit_hooks(files, project_path, result)
    check_no_provider(files, project_path, result)
    check_farcaster_sdk_usage(files, project_path, result)
    check_package_json(project_path, result)
    check_env_variables(project_path, result)
    check_manifest(project_path, result)
    check_config_renamed(files, project_path, result)

    return result

def print_result(result: ValidationResult):
    """Print validation results."""
    print("\n" + "=" * 60)
    print("CONVERSION VALIDATION REPORT")
    print("=" * 60)
    
    if result.passed:
        print("\n✅ PASSED:")
        for msg in result.passed:
            print(f"   {msg}")
    
    if result.warnings:
        print("\n⚠️  WARNINGS:")
        for msg in result.warnings:
            print(f"   {msg}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for msg in result.errors:
            print(f"   {msg}")
    
    print("\n" + "-" * 60)
    if result.is_valid:
        print("✅ VALIDATION PASSED - Conversion looks complete!")
    else:
        print("❌ VALIDATION FAILED - Please fix the errors above")
    print("=" * 60 + "\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_conversion.py <project_dir>")
        print("Example: python validate_conversion.py ./my-converted-app")
        sys.exit(1)
    
    project_dir = sys.argv[1]
    result = validate_project(project_dir)
    print_result(result)
    
    sys.exit(0 if result.is_valid else 1)

if __name__ == '__main__':
    main()
