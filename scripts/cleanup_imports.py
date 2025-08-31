#!/usr/bin/env python3
"""
Import Cleanup Script
Cleans up imports in vpn_merger.py by removing unused imports and consolidating fallbacks.
"""

import re
import ast
from pathlib import Path
from typing import Set, List

def find_used_imports(file_path: str) -> Set[str]:
    """Find all actually used imports in the file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        print(f"Warning: Could not parse {file_path} due to syntax errors")
        return set()
    
    used_names = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Handle attribute access like aiofiles.open
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)
    
    return used_names

def clean_imports(file_path: str):
    """Clean up imports in the specified file."""
    print(f"Cleaning imports in {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find used imports
    used_imports = find_used_imports(file_path)
    
    # Split content into lines
    lines = content.split('\n')
    cleaned_lines = []
    in_import_section = True
    
    # Standard library imports that are commonly used
    standard_imports = {
        'asyncio', 'base64', 'csv', 'hashlib', 'os', 'functools', 'json', 
        'logging', 'random', 're', 'ssl', 'sys', 'time', 'socket', 'signal',
        'ipaddress', 'datetime', 'pathlib', 'typing', 'io', 'collections',
        'urllib.parse', 'dataclasses'
    }
    
    # Third-party imports that are commonly used
    third_party_imports = {
        'tqdm', 'aiohttp', 'aiofiles', 'yaml'
    }
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip the header comment section
        if line.startswith('"""') and 'VPN Subscription Merger' in line:
            cleaned_lines.append(line)
            i += 1
            # Skip until end of docstring
            while i < len(lines) and not (lines[i].strip().endswith('"""') and lines[i].strip() != '"""'):
                cleaned_lines.append(lines[i])
                i += 1
            if i < len(lines):
                cleaned_lines.append(lines[i])
            i += 1
            continue
        
        # Handle import statements
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            # Check if this import is actually used
            import_name = extract_import_name(line)
            if import_name and import_name in used_imports:
                cleaned_lines.append(line)
            elif import_name in standard_imports or import_name in third_party_imports:
                # Keep standard and common third-party imports
                cleaned_lines.append(line)
            else:
                print(f"Removing unused import: {line.strip()}")
        else:
            cleaned_lines.append(line)
        
        i += 1
    
    # Write cleaned content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))
    
    print(f"Import cleanup completed for {file_path}")

def extract_import_name(line: str) -> str:
    """Extract the main import name from an import line."""
    line = line.strip()
    
    if line.startswith('import '):
        # Handle: import module
        parts = line[7:].split(' as ')
        return parts[0].split('.')[0]
    elif line.startswith('from '):
        # Handle: from module import something
        parts = line[5:].split(' import ')
        if len(parts) == 2:
            return parts[0].split('.')[0]
    
    return None

def main():
    """Main cleanup function."""
    files_to_clean = [
        'vpn_merger.py',
        'scripts/train_ml_models.py',
        'scripts/performance_optimizer.py',
        'scripts/deployment_manager.py',
        'scripts/api_enhancer.py'
    ]
    
    for file_path in files_to_clean:
        if Path(file_path).exists():
            clean_imports(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()
