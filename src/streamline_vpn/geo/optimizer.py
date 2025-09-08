"""
Geographic Optimizer
====================

Geographic optimization for VPN server selection.
"""

from typing import Any, Dict, List, Optional, Tuple
import math

from ..models.configuration import VPNConfiguration
from ..utils.logging import get_logger

logger = get_logger(__name__)


class GeographicOptimizer:
    """Geographic optimization for VPN server selection."""

    def __init__(self):
        """Initialize geographic optimizer."""
        self.country_codes = self._load_country_codes()
        logger.info("Geographic optimizer initialized")

    def _load_country_codes(self) -> Dict[str, str]:
        """Load country code mappings."""
        # Simplified country code mapping
        return {
            "US": "United States",
            "CN": "China",
            "JP": "Japan",
            "GB": "United Kingdom",
            "DE": "Germany",
            "FR": "France",
            "CA": "Canada",
            "AU": "Australia",
            "SG": "Singapore",
            "HK": "Hong Kong",
            "TW": "Taiwan",
            "KR": "South Korea",
            "NL": "Netherlands",
            "CH": "Switzerland",
            "SE": "Sweden",
            "NO": "Norway",
            "DK": "Denmark",
            "FI": "Finland",
            "AT": "Austria",
            "BE": "Belgium",
        }

    def calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two points using Haversine formula.

        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point

        Returns:
            Distance in kilometers
        """
        # Haversine formula
        R = 6371  # Earth's radius in kilometers

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(
            dlon / 2
        )

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    def get_server_location(
        self, server: str
    ) -> Optional[Tuple[float, float]]:
        """Get approximate location for server.

        Args:
            server: Server address

        Returns:
            Tuple of (latitude, longitude) or None
        """
        # Simplified location mapping for common servers
        locations = {
            "us": (39.8283, -98.5795),  # United States center
            "cn": (35.8617, 104.1954),  # China center
            "jp": (36.2048, 138.2529),  # Japan center
            "gb": (55.3781, -3.4360),  # United Kingdom center
            "de": (51.1657, 10.4515),  # Germany center
            "fr": (46.2276, 2.2137),  # France center
            "ca": (56.1304, -106.3468),  # Canada center
            "au": (-25.2744, 133.7751),  # Australia center
            "sg": (1.3521, 103.8198),  # Singapore center
            "hk": (22.3193, 114.1694),  # Hong Kong center
        }

        server_lower = server.lower()
        for country, coords in locations.items():
            if country in server_lower:
                return coords

        return None

    def optimize_for_location(
        self,
        configurations: List[VPNConfiguration],
        user_lat: float,
        user_lon: float,
        max_distance: float = 5000.0,
    ) -> List[VPNConfiguration]:
        """Optimize configurations for user location.

        Args:
            configurations: List of VPN configurations
            user_lat: User latitude
            user_lon: User longitude
            max_distance: Maximum distance in kilometers

        Returns:
            List of optimized configurations
        """
        optimized = []

        for config in configurations:
            server_location = self.get_server_location(config.server)
            if server_location:
                distance = self.calculate_distance(
                    user_lat, user_lon, server_location[0], server_location[1]
                )

                if distance <= max_distance:
                    # Add distance as metadata
                    config.metadata["distance_km"] = distance
                    config.metadata["server_location"] = server_location
                    optimized.append(config)
            else:
                # Keep configurations without location info
                optimized.append(config)

        # Sort by distance
        optimized.sort(
            key=lambda x: x.metadata.get("distance_km", float("inf"))
        )

        return optimized

    def get_country_servers(
        self, configurations: List[VPNConfiguration], country_code: str
    ) -> List[VPNConfiguration]:
        """Get servers from specific country.

        Args:
            configurations: List of VPN configurations
            country_code: Country code (e.g., 'US', 'CN')

        Returns:
            List of configurations from the country
        """
        country_servers = []
        country_lower = country_code.lower()

        for config in configurations:
            server_lower = config.server.lower()
            if country_lower in server_lower:
                config.metadata["country"] = country_code
                country_servers.append(config)

        return country_servers

    def get_statistics(self) -> Dict[str, Any]:
        """Get geographic optimization statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "supported_countries": len(self.country_codes),
            "country_codes": list(self.country_codes.keys()),
        }
