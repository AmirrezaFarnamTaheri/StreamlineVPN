#!/usr/bin/env python3
"""
Cleanup script to replace example.com URLs with test.example.com variants in test files.
"""

import os
import re
from pathlib import Path

def replace_example_urls_in_file(file_path: str):
    """Replace example.com URLs with test.example.com variants."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace patterns
    replacements = [
        # Replace example.com with test.example.com in URLs
        (r'https://example\.com', 'https://raw.githubusercontent.com/test'),
        (r'http://example\.com', 'https://raw.githubusercontent.com/test'),
        
        # Replace example.com in host fields with test.example.com
        (r'"host": "example\.com"', '"host": "test.example.com"'),
        (r'"sni": "example\.com"', '"sni": "test.example.com"'),
        (r'"host": f"server\{i\}\.example\.com"', '"host": f"server{i}.test.example.com"'),
        
        # Replace example.com in config strings
        (r'vless://uuid@example\.com', 'vless://12345678-90ab-12f3-a6c5-4681aaaaaaaa@test.example.com'),
        (r'trojan://password@example\.com', 'trojan://testpassword@test.example.com'),
        (r'trojan://pwd@example\.com', 'trojan://testpassword@test.example.com'),
        
        # Replace example.com in domain patterns
        (r'cdn\.example\.com', 'cdn.test.example.com'),
        (r'cloudflare\.example\.com', 'cloudflare.test.example.com'),
        (r'aws\.example\.com', 'aws.test.example.com'),
        (r'regular\.example\.com', 'regular.test.example.com'),
        
        # Replace example.com in comments and assertions
        (r'# domain length \(15 for "cdn\.example\.com"\)', '# domain length (19 for "cdn.test.example.com")'),
        (r'# domain length \(15 for "example\.com"\)', '# domain length (11 for "test.example.com")'),
        
        # Replace example.com in test data
        (r'example\.com:443', 'test.example.com:443'),
        (r'example\.com:8388', 'test.example.com:8388'),
        (r'example\.com:51820', 'test.example.com:51820'),
        (r'example\.com:1194', 'test.example.com:1194'),
        (r'example\.com:12345', 'test.example.com:12345'),
        (r'example\.com:9999', 'test.example.com:9999'),
        
        # Replace example.com in email addresses
        (r'user@example\.com', 'user@test.example.com'),
        
        # Replace example.com in file paths
        (r'https://example\.com/file\.txt', 'https://raw.githubusercontent.com/test/file.txt'),
        (r'ftp://example\.com/file\.txt', 'https://raw.githubusercontent.com/test/file.txt'),
        
        # Additional patterns for remaining example.com instances
        (r'remote example\.com', 'remote test.example.com'),
        (r'server: example\.com', 'server: test.example.com'),
        (r'Host: example\.com', 'Host: test.example.com'),
        (r'vmess = vmess, example\.com', 'vmess = vmess, test.example.com'),
        (r'ws-headers=Host:example\.com', 'ws-headers=Host:test.example.com'),
        (r'&sni=example\.com', '&sni=test.example.com'),
        (r'Endpoint = example\.com', 'Endpoint = test.example.com'),
        
        # Fix double test.test.example.com issues
        (r'test\.test\.example\.com', 'test.example.com'),
    ]
    
    modified = False
    for pattern, replacement in replacements:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {file_path}")
    else:
        print(f"No changes needed: {file_path}")

def main():
    """Main function to clean up all test files."""
    test_dir = Path("tests")
    
    if not test_dir.exists():
        print("Tests directory not found")
        return
    
    # Find all Python test files
    test_files = list(test_dir.glob("test_*.py"))
    
    print(f"Found {len(test_files)} test files to process")
    
    for test_file in test_files:
        replace_example_urls_in_file(str(test_file))
    
    # Also clean up scripts directory
    scripts_dir = Path("scripts")
    if scripts_dir.exists():
        script_files = list(scripts_dir.glob("*.py"))
        for script_file in script_files:
            if script_file.name != "cleanup_example_urls.py":  # Skip this script
                replace_example_urls_in_file(str(script_file))
    
    print("Cleanup completed!")

if __name__ == "__main__":
    main()
