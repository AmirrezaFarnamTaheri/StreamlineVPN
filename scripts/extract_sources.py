#!/usr/bin/env python3
"""
Source Extraction Script
Extracts hardcoded sources from vpn_merger.py and adds them to config/sources.unified.yaml
"""

import logging
import re
from typing import Any

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_urls_from_file(file_path: str) -> list[str]:
    """Extract all URLs from the vpn_merger.py file."""
    logger.info(f"Extracting URLs from {file_path}")

    urls = []

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Find all URLs using regex
        url_pattern = r'https://[^\s"\']+'
        matches = re.findall(url_pattern, content)

        # Filter out non-source URLs (like API endpoints)
        filtered_urls = []
        for url in matches:
            # Skip common non-source URLs
            if any(
                skip in url.lower()
                for skip in [
                    "api.telegram.org",
                    "www.youtube.com",
                    "github.com/api",
                    "raw.githubusercontent.com/api",
                ]
            ):
                continue

            # Clean up URL (remove trailing punctuation)
            clean_url = url.rstrip("\",'")
            if clean_url not in filtered_urls:
                filtered_urls.append(clean_url)

        logger.info(f"Found {len(filtered_urls)} unique URLs")
        return filtered_urls

    except Exception as e:
        logger.error(f"Error extracting URLs: {e}")
        return []


def categorize_urls(urls: list[str]) -> dict[str, list[str]]:
    """Categorize URLs by provider/domain."""
    categories = {}

    for url in urls:
        try:
            # Extract domain from URL
            domain_match = re.search(r"https://([^/]+)", url)
            if domain_match:
                domain = domain_match.group(1)

                # Categorize by domain
                if "barry-far" in domain:
                    category = "barry_far"
                elif "rayan-config" in domain:
                    category = "rayan_config"
                elif "mhditaheri" in domain:
                    category = "mhdi_taheri"
                elif "soroushmirzaei" in domain:
                    category = "soroush_mirzaei"
                elif "iraniancypherpunks" in domain:
                    category = "iranian_cypherpunks"
                elif "coldwater-10" in domain:
                    category = "coldwater"
                elif "youfoundamin" in domain:
                    category = "youfoundamin"
                elif "amirparsaxs" in domain:
                    category = "amir_parsa"
                elif "mrmohebi" in domain:
                    category = "mr_mohebi"
                elif "ndsphonemy" in domain:
                    category = "ndsphonemy"
                elif "syavar" in domain:
                    category = "syavar"
                elif "gutsy-fibers" in domain:
                    category = "gutsy_fibers"
                elif "channel-freevpnhomes" in domain:
                    category = "free_vpn_homes"
                else:
                    category = "other"

                if category not in categories:
                    categories[category] = []
                categories[category].append(url)

        except Exception as e:
            logger.warning(f"Error categorizing URL {url}: {e}")
            continue

    return categories


def determine_protocols(url: str) -> list[str]:
    """Determine protocols based on URL patterns."""
    url_lower = url.lower()

    protocols = []

    if "vless" in url_lower:
        protocols.append("vless")
    if "vmess" in url_lower:
        protocols.append("vmess")
    if "trojan" in url_lower:
        protocols.append("trojan")
    if "shadowsocks" in url_lower or "ss" in url_lower:
        protocols.append("shadowsocks")
    if "reality" in url_lower:
        protocols.append("reality")
    if "hysteria" in url_lower:
        protocols.append("hysteria")
    if "tuic" in url_lower:
        protocols.append("tuic")
    if "juicity" in url_lower:
        protocols.append("juicity")
    if "naive" in url_lower:
        protocols.append("naive")
    if "mix" in url_lower or "all" in url_lower:
        protocols = ["vmess", "vless", "trojan", "shadowsocks", "reality"]

    # Default to all protocols if none detected
    if not protocols:
        protocols = ["vmess", "vless", "trojan", "shadowsocks"]

    return protocols


def determine_format(url: str) -> str:
    """Determine format based on URL patterns."""
    url_lower = url.lower()

    if "clash" in url_lower or ".yml" in url_lower or ".yaml" in url_lower:
        return "clash"
    elif "singbox" in url_lower or ".json" in url_lower:
        return "singbox"
    elif "base64" in url_lower:
        return "base64"
    else:
        return "raw"


def create_source_entry(url: str, category: str) -> dict[str, Any]:
    """Create a source entry for the YAML configuration."""
    protocols = determine_protocols(url)
    format_type = determine_format(url)

    # Determine region based on category
    region = (
        "iran"
        if category in ["barry_far", "rayan_config", "mhdi_taheri", "iranian_cypherpunks"]
        else "global"
    )

    # Determine priority based on category
    if category in ["barry_far", "rayan_config", "mhdi_taheri"]:
        priority = 1
        weight = 1.0
    elif category in ["soroush_mirzaei", "coldwater", "youfoundamin"]:
        priority = 2
        weight = 0.8
    else:
        priority = 3
        weight = 0.6

    return {
        "url": url,
        "format": format_type,
        "protocols": protocols,
        "average_configs": 2000,  # Default estimate
        "last_verified": "2024-12-29",
        "region": region,
        "priority": priority,
        "weight": weight,
    }


def update_unified_config(
    categories: dict[str, list[str]], config_path: str = "config/sources.unified.yaml"
):
    """Update the unified configuration with extracted sources."""
    logger.info(f"Updating unified configuration: {config_path}")

    try:
        # Load existing configuration
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Create new tier for extracted sources
        extracted_sources = []

        for category, urls in categories.items():
            logger.info(f"Processing category {category} with {len(urls)} URLs")

            for url in urls:
                source_entry = create_source_entry(url, category)
                extracted_sources.append(source_entry)

        # Add extracted sources to appropriate tier
        if "tier_3_extracted" not in config["sources"]:
            config["sources"]["tier_3_extracted"] = {
                "update_frequency": "daily",
                "reliability_score": 0.75,
                "description": "Extracted sources from hardcoded configuration",
                "urls": [],
            }

        config["sources"]["tier_3_extracted"]["urls"].extend(extracted_sources)

        # Update metadata
        total_sources = 0
        for tier_name, tier_data in config["sources"].items():
            if isinstance(tier_data, dict) and "urls" in tier_data:
                total_sources += len(tier_data["urls"])
            elif isinstance(tier_data, dict):
                # Handle nested structures like regional_optimized
                for sub_tier in tier_data.values():
                    if isinstance(sub_tier, dict) and "urls" in sub_tier:
                        total_sources += len(sub_tier["urls"])

        config["metadata"]["total_sources"] = total_sources
        config["metadata"]["last_updated"] = "2024-12-29"

        # Save updated configuration
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)

        logger.info(f"Updated configuration with {len(extracted_sources)} new sources")
        logger.info(f"Total sources in configuration: {config['metadata']['total_sources']}")

        return True

    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        return False


def create_removal_script(
    categories: dict[str, list[str]], output_path: str = "scripts/remove_hardcoded_sources.py"
):
    """Create a script to remove hardcoded sources from vpn_merger.py."""
    logger.info(f"Creating removal script: {output_path}")

    script_content = '''#!/usr/bin/env python3
"""
Remove Hardcoded Sources Script
Removes hardcoded sources from vpn_merger.py after they've been moved to unified configuration
"""

import re
from pathlib import Path

def remove_hardcoded_sources():
    """Remove hardcoded source lists from vpn_merger.py."""
    
    file_path = "vpn_merger.py"
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove the hardcoded source lists
    # This removes the IRANIAN_PRIORITY, IRANIAN_RELIABLE, etc. lists
    
    # Pattern to match the source lists
    patterns = [
        r'# Iranian Priority Sources.*?\\]',
        r'# Iranian Reliable Sources.*?\\]',
        r'# Iranian Bulk Sources.*?\\]',
        r'# International Sources.*?\\]',
        r'# Specialized Protocol Sources.*?\\]',
        r'# Regional Sources.*?\\]',
        r'# Experimental Sources.*?\\]',
        r'# Monitoring Sources.*?\\]',
        r'# Fallback Sources.*?\\]'
    ]
    
    modified_content = content
    for pattern in patterns:
        modified_content = re.sub(pattern, '', modified_content, flags=re.DOTALL | re.MULTILINE)
    
    # Clean up extra whitespace
    modified_content = re.sub(r'\\n\\s*\\n\\s*\\n', '\\n\\n', modified_content)
    
    # Write the modified content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("Hardcoded sources removed from vpn_merger.py")

if __name__ == "__main__":
    remove_hardcoded_sources()
'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    logger.info(f"Created removal script: {output_path}")


def main():
    """Main function to extract and update sources."""
    logger.info("Starting source extraction process")

    # Extract URLs from vpn_merger.py
    urls = extract_urls_from_file("vpn_merger.py")

    if not urls:
        logger.error("No URLs found to extract")
        return

    # Categorize URLs
    categories = categorize_urls(urls)

    # Print summary
    logger.info("URL Categories:")
    for category, category_urls in categories.items():
        logger.info(f"  {category}: {len(category_urls)} URLs")

    # Update unified configuration
    success = update_unified_config(categories)

    if success:
        # Create removal script
        create_removal_script(categories)

        logger.info("Source extraction completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Review the updated config/sources.unified.yaml")
        logger.info("2. Run scripts/remove_hardcoded_sources.py to clean up vpn_merger.py")
        logger.info("3. Test the application to ensure it works with the new configuration")
    else:
        logger.error("Source extraction failed")


if __name__ == "__main__":
    main()
