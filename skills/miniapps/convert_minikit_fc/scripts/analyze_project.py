#!/usr/bin/env python3
"""
Analyze a project directory for MiniKit usage.
Finds all imports and hook usages that need conversion.

Usage:
    python scripts/analyze_project.py <project_dir>
    python scripts/analyze_project.py ./my-minikit-app

Output:
    JSON report of all MiniKit usage found
"""

import os
import re
import json
import sys
from pathlib import Path
from typing import TypedDict, List

class HookUsage(TypedDict):
    hook: str
    file: str
    line: int
    code: str

class ImportInfo(TypedDict):
    file: str
    line: int
    imports: List[str]

class AnalysisReport(TypedDict):
    project_dir: str
    files_scanned: int
    files_with_minikit: int
    imports: List[ImportInfo]
    hook_usages: List[HookUsage]
    provider_locations: List[dict]
    summary: dict

# MiniKit hooks to search for
MINIKIT_HOOKS = [
    'useMiniKit',
    'useClose',
    'useOpenUrl',
    'useViewProfile',
    'useViewCast',
    'useComposeCast',
    'useAddFrame',
    'useAuthenticate',
    'useNotification',
    'usePrimaryButton',
]

# Import patterns - both @coinbase/onchainkit/minikit AND @coinbase/onchainkit
MINIKIT_IMPORT_PATTERN = re.compile(
    r"from\s+['\"]@coinbase/onchainkit(?:/minikit)?['\"]"
)

# OnchainKitProvider with miniKit prop
ONCHAINKIT_PROVIDER_PATTERN = re.compile(
    r"<OnchainKitProvider|OnchainKitProvider"
)

MINIKIT_PROVIDER_PATTERN = re.compile(
    r"<MiniKitProvider|MiniKitProvider"
)

MINIKIT_PROP_PATTERN = re.compile(
    r"miniKit\s*[=:{]"
)

def find_files(directory: str, extensions: tuple = ('.tsx', '.ts', '.jsx', '.js')) -> List[Path]:
    """Find all relevant source files in directory."""
    files = []
    for root, _, filenames in os.walk(directory):
        # Skip node_modules and .next
        if 'node_modules' in root or '.next' in root:
            continue
        for filename in filenames:
            if filename.endswith(extensions):
                files.append(Path(root) / filename)
    return files

def analyze_file(filepath: Path) -> dict:
    """Analyze a single file for MiniKit usage."""
    result = {
        'imports': [],
        'hooks': [],
        'provider': False,
        'provider_lines': [],
        'provider_type': None
    }
    
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
        return result
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Check for imports from @coinbase/onchainkit or @coinbase/onchainkit/minikit
        if MINIKIT_IMPORT_PATTERN.search(line):
            # Extract what's being imported
            import_match = re.search(r"import\s+\{([^}]+)\}", line)
            if import_match:
                imports = [s.strip() for s in import_match.group(1).split(',')]
                result['imports'].append({
                    'line': i,
                    'imports': imports
                })
        
        # Check for hook usages
        for hook in MINIKIT_HOOKS:
            hook_pattern = re.compile(rf'\b{hook}\s*\(')
            if hook_pattern.search(line):
                result['hooks'].append({
                    'hook': hook,
                    'line': i,
                    'code': line.strip()
                })
        
        # Check for OnchainKitProvider (may have miniKit prop)
        if ONCHAINKIT_PROVIDER_PATTERN.search(line):
            result['provider'] = True
            result['provider_type'] = 'OnchainKitProvider'
            result['provider_lines'].append({
                'line': i,
                'code': line.strip()
            })
        
        # Check for MiniKitProvider
        if MINIKIT_PROVIDER_PATTERN.search(line):
            result['provider'] = True
            result['provider_type'] = 'MiniKitProvider'
            result['provider_lines'].append({
                'line': i,
                'code': line.strip()
            })
        
        # Check for miniKit prop
        if MINIKIT_PROP_PATTERN.search(line):
            result['provider_lines'].append({
                'line': i,
                'code': line.strip(),
                'is_minikit_prop': True
            })
    
    return result

def analyze_project(project_dir: str) -> AnalysisReport:
    """Analyze entire project for MiniKit usage."""
    project_path = Path(project_dir).resolve()
    
    if not project_path.exists():
        print(f"Error: Directory {project_dir} does not exist", file=sys.stderr)
        sys.exit(1)
    
    files = find_files(str(project_path))
    
    report: AnalysisReport = {
        'project_dir': str(project_path),
        'files_scanned': len(files),
        'files_with_minikit': 0,
        'imports': [],
        'hook_usages': [],
        'provider_locations': [],
        'summary': {}
    }
    
    hook_counts = {hook: 0 for hook in MINIKIT_HOOKS}
    
    for filepath in files:
        result = analyze_file(filepath)
        rel_path = str(filepath.relative_to(project_path))
        
        has_minikit = bool(result['imports'] or result['hooks'] or result['provider'])
        
        if has_minikit:
            report['files_with_minikit'] += 1
        
        # Collect imports
        for imp in result['imports']:
            report['imports'].append({
                'file': rel_path,
                'line': imp['line'],
                'imports': imp['imports']
            })
        
        # Collect hook usages
        for hook_usage in result['hooks']:
            report['hook_usages'].append({
                'hook': hook_usage['hook'],
                'file': rel_path,
                'line': hook_usage['line'],
                'code': hook_usage['code']
            })
            hook_counts[hook_usage['hook']] += 1
        
        # Collect provider locations
        if result['provider']:
            for provider_info in result['provider_lines']:
                report['provider_locations'].append({
                    'file': rel_path,
                    'line': provider_info['line'],
                    'code': provider_info['code']
                })
    
    # Build summary
    report['summary'] = {
        'total_hook_usages': sum(hook_counts.values()),
        'hooks_by_type': {k: v for k, v in hook_counts.items() if v > 0},
        'has_provider': len(report['provider_locations']) > 0,
        'unique_hooks_used': [k for k, v in hook_counts.items() if v > 0]
    }
    
    return report

def print_report(report: AnalysisReport):
    """Print human-readable report."""
    print("\n" + "=" * 60)
    print("MINIKIT ANALYSIS REPORT")
    print("=" * 60)
    print(f"\nProject: {report['project_dir']}")
    print(f"Files scanned: {report['files_scanned']}")
    print(f"Files with MiniKit: {report['files_with_minikit']}")
    
    print("\n--- IMPORTS (must be replaced) ---")
    if report['imports']:
        for imp in report['imports']:
            print(f"  {imp['file']}:{imp['line']}")
            print(f"    Imports: {', '.join(imp['imports'])}")
        print("\n  ACTION: Replace @coinbase/onchainkit imports with @farcaster/miniapp-sdk")
    else:
        print("  No OnchainKit/MiniKit imports found")
    
    print("\n--- HOOK USAGES (must be replaced) ---")
    if report['hook_usages']:
        for usage in report['hook_usages']:
            print(f"  {usage['file']}:{usage['line']}")
            print(f"    Hook: {usage['hook']}")
            print(f"    Code: {usage['code'][:80]}...")
        print("\n  ACTION: Replace MiniKit hooks with sdk.actions.* methods")
    else:
        print("  No MiniKit hook usages found")
    
    print("\n--- PROVIDER LOCATIONS (must be removed) ---")
    if report['provider_locations']:
        for loc in report['provider_locations']:
            print(f"  {loc['file']}:{loc['line']}")
            print(f"    {loc['code'][:80]}")
        print("\n  ACTION: Remove OnchainKitProvider and MiniKitProvider entirely.")
        print("          Replace with MiniAppProvider + WagmiProvider.")
    else:
        print("  No OnchainKitProvider or MiniKitProvider found")
    
    print("\n--- SUMMARY ---")
    summary = report['summary']
    print(f"  Total hook usages: {summary['total_hook_usages']}")
    print(f"  Unique hooks: {', '.join(summary['unique_hooks_used']) or 'None'}")
    print(f"  Has provider: {'Yes' if summary['has_provider'] else 'No'}")
    
    if summary['hooks_by_type']:
        print("\n  Hooks by frequency:")
        for hook, count in sorted(summary['hooks_by_type'].items(), key=lambda x: -x[1]):
            print(f"    {hook}: {count}")
    
    print("\n" + "=" * 60)

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_project.py <project_dir> [--json]")
        print("Example: python analyze_project.py ./my-minikit-app")
        sys.exit(1)
    
    project_dir = sys.argv[1]
    output_json = '--json' in sys.argv
    
    report = analyze_project(project_dir)
    
    if output_json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
        # Also save JSON report
        report_path = Path(project_dir) / 'minikit-analysis.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nJSON report saved to: {report_path}")

if __name__ == '__main__':
    main()
