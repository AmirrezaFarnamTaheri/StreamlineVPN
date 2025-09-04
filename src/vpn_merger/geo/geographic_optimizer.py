"""
Geographic Optimizer for VPN Configuration Distribution
=====================================================

Advanced geographic optimization system with latency prediction,
edge caching, and location-based configuration ranking.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp

# Geographic libraries
try:
    import geoip2.database
    import geoip2.errors

    GEOIP2_AVAILABLE = True
except ImportError:
    GEOIP2_AVAILABLE = False

try:
    import maxminddb

    MAXMIND_AVAILABLE = True
except ImportError:
    MAXMIND_AVAILABLE = False

# ML libraries for latency prediction
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)

# Constants
DEFAULT_GEO_DB_PATH = "geoip/GeoLite2-City.mmdb"
DEFAULT_LATENCY_TIMEOUT = 5.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_EDGE_CACHE_CAPACITY = 100.0  # GB
DEFAULT_HAVERSINE_RADIUS = 6371  # Earth's radius in km

# Geographic regions
GEOGRAPHIC_REGIONS = {
    "US_EAST": {"lat": 39.8283, "lon": -98.5795},
    "US_WEST": {"lat": 36.7783, "lon": -119.4179},
    "EU_WEST": {"lat": 54.5260, "lon": 15.2551},
    "EU_EAST": {"lat": 54.5260, "lon": 25.2551},
    "ASIA_PACIFIC": {"lat": 35.8617, "lon": 104.1954},
    "SOUTH_AMERICA": {"lat": -14.2350, "lon": -51.9253},
    "AFRICA": {"lat": 8.7832, "lon": 34.5085},
}


@dataclass
class GeoLocation:
    """Geographic location information."""

    country_code: str
    country_name: str
    region: str
    city: str
    latitude: float
    longitude: float
    timezone: str
    isp: str
    asn: str


@dataclass
class LatencyInfo:
    """Latency information for a configuration."""

    config_id: str
    host: str
    port: int
    latency_ms: float
    jitter_ms: float
    packet_loss: float
    last_tested: datetime
    test_count: int


@dataclass
class EdgeCache:
    """Edge cache configuration."""

    region: str
    endpoint: str
    location: GeoLocation
    capacity_gb: float
    current_usage_gb: float
    latency_ms: float
    status: str  # 'active', 'maintenance', 'offline'


class GeographicOptimizer:
    """
    Advanced geographic optimizer for VPN configuration distribution.

    Features:
    - Geographic distance calculation
    - Latency prediction using ML
    - Edge caching deployment
    - Location-based configuration ranking
    - Automatic failover and load balancing
    """

    def __init__(self, geo_db_path: str | None = None):
        """Initialize the geographic optimizer.

        Args:
            geo_db_path: Path to GeoIP2 database file
        """
        self.geo_db_path = geo_db_path or DEFAULT_GEO_DB_PATH
        self.geo_db = None
        self.edge_caches = {}
        self.latency_map = {}
        self.latency_predictor = None
        self.scaler = StandardScaler() if ML_AVAILABLE else None

        # Performance tracking
        self.optimization_stats = {
            "total_optimizations": 0,
            "latency_tests": 0,
            "cache_deployments": 0,
            "failover_events": 0,
        }

        # Initialize components
        self._initialize_geo_database()
        self._initialize_edge_caches()

        logger.info("GeographicOptimizer initialized")

    def _initialize_geo_database(self):
        """Initialize GeoIP2 database."""
        if not GEOIP2_AVAILABLE:
            logger.warning("GeoIP2 not available, geographic features disabled")
            return

        try:
            geo_db_file = Path(self.geo_db_path)
            if geo_db_file.exists():
                self.geo_db = geoip2.database.Reader(str(geo_db_file))
                logger.info("GeoIP2 database loaded successfully")
            else:
                logger.warning(f"GeoIP2 database not found at {self.geo_db_path}")
        except Exception as e:
            logger.error(f"Failed to load GeoIP2 database: {e}")

    def _initialize_edge_caches(self):
        """Initialize edge cache configurations."""
        for region, coords in GEOGRAPHIC_REGIONS.items():
            self.edge_caches[region] = EdgeCache(
                region=region,
                endpoint=f"cache-{region.lower().replace('_', '-')}.vpnmerger.com",
                location=GeoLocation(
                    country_code="",
                    country_name="",
                    region=region,
                    city="",
                    latitude=coords["lat"],
                    longitude=coords["lon"],
                    timezone="",
                    isp="",
                    asn="",
                ),
                capacity_gb=DEFAULT_EDGE_CACHE_CAPACITY,
                current_usage_gb=0.0,
                latency_ms=0.0,
                status="active",
            )

    def get_location(self, ip_address: str) -> GeoLocation | None:
        """
        Get geographic location for an IP address.

        Args:
            ip_address: IP address to lookup

        Returns:
            GeoLocation object or None if lookup fails
        """
        if not self.geo_db:
            logger.warning("GeoIP2 database not available")
            return None

        try:
            response = self.geo_db.city(ip_address)

            return GeoLocation(
                country_code=response.country.iso_code or "",
                country_name=response.country.name or "",
                region=response.subdivisions.most_specific.name or "",
                city=response.city.name or "",
                latitude=response.location.latitude or 0.0,
                longitude=response.location.longitude or 0.0,
                timezone=response.location.time_zone or "",
                isp=response.traits.isp or "",
                asn=response.traits.autonomous_system_number or "",
            )

        except geoip2.errors.AddressNotFoundError:
            logger.debug(f"IP address not found in database: {ip_address}")
            return None
        except Exception as e:
            logger.error(f"Error looking up IP {ip_address}: {e}")
            return None

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two geographic coordinates using Haversine formula.

        Args:
            lat1, lon1: First coordinate pair
            lat2, lon2: Second coordinate pair

        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))

        return DEFAULT_HAVERSINE_RADIUS * c

    def optimize_by_location(
        self, user_location: GeoLocation, configs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Optimize configurations based on user location.

        Args:
            user_location: User's geographic location
            configs: List of configuration dictionaries

        Returns:
            Optimized list of configurations
        """
        logger.info(
            f"Optimizing {len(configs)} configurations for location: {user_location.city}, {user_location.country_name}"
        )

        optimized_configs = []

        for config in configs:
            try:
                # Calculate distance to configuration server
                config_lat = config.get("latitude", 0.0)
                config_lon = config.get("longitude", 0.0)

                if config_lat and config_lon:
                    distance = self.calculate_distance(
                        user_location.latitude, user_location.longitude, config_lat, config_lon
                    )

                    # Predict latency based on distance
                    predicted_latency = self._predict_latency(distance, config)

                    # Create optimized config
                    optimized_config = {
                        **config,
                        "distance_km": distance,
                        "predicted_latency_ms": predicted_latency,
                        "location_score": self._calculate_location_score(
                            distance, predicted_latency
                        ),
                    }

                    optimized_configs.append(optimized_config)
                else:
                    # Fallback for configs without location data
                    optimized_config = {
                        **config,
                        "distance_km": float("inf"),
                        "predicted_latency_ms": 100.0,
                        "location_score": 0.5,
                    }
                    optimized_configs.append(optimized_config)

            except Exception as e:
                logger.error(f"Error optimizing config {config.get('id', 'unknown')}: {e}")
                optimized_configs.append(config)

        # Sort by location score (higher is better)
        optimized_configs.sort(key=lambda x: x.get("location_score", 0.0), reverse=True)

        self.optimization_stats["total_optimizations"] += 1
        logger.info(
            f"Optimization completed, top score: {optimized_configs[0].get('location_score', 0.0):.3f}"
        )

        return optimized_configs

    def _predict_latency(self, distance: float, config: dict[str, Any]) -> float:
        """
        Predict latency based on distance and configuration characteristics.

        Args:
            distance: Distance in kilometers
            config: Configuration dictionary

        Returns:
            Predicted latency in milliseconds
        """
        if self.latency_predictor and ML_AVAILABLE:
            try:
                # Extract features for prediction
                features = self._extract_latency_features(distance, config)
                features_scaled = self.scaler.transform([features])
                predicted_latency = self.latency_predictor.predict(features_scaled)[0]
                return max(1.0, predicted_latency)
            except Exception as e:
                logger.error(f"Error predicting latency: {e}")

        # Fallback: simple distance-based prediction
        base_latency = 10.0  # Base latency in ms
        distance_factor = distance * 0.1  # 0.1 ms per km
        return base_latency + distance_factor

    def _extract_latency_features(self, distance: float, config: dict[str, Any]) -> list[float]:
        """Extract features for latency prediction."""
        return [
            distance,
            config.get("port", 443),
            int(config.get("protocol", "") in ["vmess", "vless"]),
            int(config.get("has_tls", False)),
            int(config.get("has_websocket", False)),
            int(config.get("has_grpc", False)),
            config.get("bandwidth_mbps", 100.0),
            int(config.get("is_premium", False)),
        ]

    def _calculate_location_score(self, distance: float, predicted_latency: float) -> float:
        """
        Calculate location-based score for configuration ranking.

        Args:
            distance: Distance in kilometers
            predicted_latency: Predicted latency in milliseconds

        Returns:
            Score between 0.0 and 1.0 (higher is better)
        """
        # Normalize distance (0-10000 km range)
        distance_score = max(0.0, 1.0 - (distance / 10000.0))

        # Normalize latency (0-500 ms range)
        latency_score = max(0.0, 1.0 - (predicted_latency / 500.0))

        # Weighted combination
        return 0.6 * distance_score + 0.4 * latency_score

    async def test_latency(
        self, host: str, port: int, timeout: float = DEFAULT_LATENCY_TIMEOUT
    ) -> float | None:
        """
        Test latency to a specific host and port.

        Args:
            host: Target hostname or IP
            port: Target port
            timeout: Timeout in seconds

        Returns:
            Latency in milliseconds or None if test fails
        """
        try:
            start_time = time.time()

            # Use aiohttp for HTTP-based latency testing
            async with aiohttp.ClientSession() as session:
                url = f"http://{host}:{port}"
                async with session.get(url, timeout=timeout) as response:
                    if response.status < 400:
                        latency = (time.time() - start_time) * 1000  # Convert to ms
                        self.optimization_stats["latency_tests"] += 1
                        return latency

            return None

        except asyncio.TimeoutError:
            logger.debug(f"Latency test timeout for {host}:{port}")
            return None
        except Exception as e:
            logger.debug(f"Latency test failed for {host}:{port}: {e}")
            return None

    async def deploy_edge_cache(self, region: str, configs: list[dict[str, Any]]) -> bool:
        """
        Deploy configurations to edge cache in specified region.

        Args:
            region: Target region
            configs: Configurations to deploy

        Returns:
            True if deployment successful
        """
        if region not in self.edge_caches:
            logger.error(f"Unknown region: {region}")
            return False

        edge_cache = self.edge_caches[region]

        try:
            # Calculate required storage
            config_size = sum(len(str(config)) for config in configs)
            required_gb = config_size / (1024 * 1024 * 1024)  # Convert to GB

            if edge_cache.current_usage_gb + required_gb > edge_cache.capacity_gb:
                logger.warning(f"Insufficient capacity in {region} edge cache")
                return False

            # Simulate deployment
            edge_cache.current_usage_gb += required_gb

            # Update latency
            user_location = GeoLocation("", "", region, "", 0.0, 0.0, "", "", "")
            optimized_configs = self.optimize_by_location(user_location, configs)

            if optimized_configs:
                avg_latency = sum(
                    config.get("predicted_latency_ms", 0) for config in optimized_configs
                ) / len(optimized_configs)
                edge_cache.latency_ms = avg_latency

            self.optimization_stats["cache_deployments"] += 1
            logger.info(
                f"Edge cache deployed to {region}: {len(configs)} configs, {required_gb:.2f} GB"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to deploy edge cache to {region}: {e}")
            return False

    async def train_latency_prediction_model(self, training_data: list[dict[str, Any]]):
        """
        Train ML model for latency prediction.

        Args:
            training_data: List of training examples with distance, config features, and actual latency
        """
        if not ML_AVAILABLE:
            logger.warning("ML libraries not available for latency prediction")
            return

        try:
            if len(training_data) < 50:
                logger.warning("Insufficient training data for latency prediction model")
                return

            # Prepare features and labels
            features = []
            labels = []

            for example in training_data:
                distance = example.get("distance", 0.0)
                config = example.get("config", {})
                actual_latency = example.get("latency_ms", 0.0)

                if actual_latency > 0:
                    features.append(self._extract_latency_features(distance, config))
                    labels.append(actual_latency)

            if len(features) < 10:
                logger.warning("Insufficient valid training examples")
                return

            # Scale features
            features_scaled = self.scaler.fit_transform(features)

            # Train model
            self.latency_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
            self.latency_predictor.fit(features_scaled, labels)

            logger.info(f"Latency prediction model trained with {len(features)} examples")

        except Exception as e:
            logger.error(f"Error training latency prediction model: {e}")

    def get_optimization_stats(self) -> dict[str, Any]:
        """Get optimization performance statistics."""
        return {
            **self.optimization_stats,
            "edge_caches_count": len(self.edge_caches),
            "latency_predictor_trained": self.latency_predictor is not None,
            "geo_db_available": self.geo_db is not None,
        }

    async def cleanup_expired_latency_data(self, max_age_hours: int = 24):
        """Clean up expired latency test data."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        expired_keys = []
        for config_id, latency_info in self.latency_map.items():
            if latency_info.last_tested < cutoff_time:
                expired_keys.append(config_id)

        for key in expired_keys:
            del self.latency_map[key]

        logger.info(f"Cleaned up {len(expired_keys)} expired latency records")


# Utility functions
async def test_global_latency(host: str, port: int) -> dict[str, float]:
    """Test latency from multiple global locations."""
    regions = list(GEOGRAPHIC_REGIONS.keys())
    results = {}

    for region in regions:
        # This would test from actual edge locations
        # For now, simulate with distance-based latency
        coords = GEOGRAPHIC_REGIONS[region]
        distance = 1000.0  # Simplified distance calculation
        latency = 10.0 + (distance * 0.1)  # Base + distance factor
        results[region] = latency

    return results


async def main():
    """Example usage of GeographicOptimizer."""
    optimizer = GeographicOptimizer()

    # Test location lookup
    location = optimizer.get_location("8.8.8.8")
    if location:
        print(f"Location: {location.city}, {location.country_name}")

    # Test distance calculation
    distance = optimizer.calculate_distance(40.7128, -74.0060, 34.0522, -118.2437)
    print(f"Distance: {distance:.2f} km")

    # Test optimization
    test_configs = [
        {"id": "1", "latitude": 40.7128, "longitude": -74.0060, "protocol": "vmess"},
        {"id": "2", "latitude": 34.0522, "longitude": -118.2437, "protocol": "vless"},
    ]

    user_location = GeoLocation(
        "US", "United States", "New York", "New York", 40.7128, -74.0060, "UTC", "", ""
    )
    optimized = optimizer.optimize_by_location(user_location, test_configs)

    print(f"Optimized configs: {len(optimized)}")

    # Get stats
    stats = optimizer.get_optimization_stats()
    print(f"Optimization stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
