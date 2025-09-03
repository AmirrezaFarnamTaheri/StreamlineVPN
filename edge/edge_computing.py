import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from geopy.distance import geodesic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EdgeNode:
    """Edge computing node"""

    id: str
    location: tuple  # (latitude, longitude)
    region: str
    capacity: int
    current_load: int
    services: list[str]
    latency_map: dict[str, float]
    is_active: bool
    metadata: dict[str, Any]


class EdgeComputingManager:
    """Manage edge computing infrastructure for VPN"""

    def __init__(self):
        self.edge_nodes: dict[str, EdgeNode] = {}
        self.cdn_endpoints: dict[str, dict[str, Any]] = {}
        self.user_sessions: dict[str, Any] = {}
        self.cache_strategy = "lru"

        # Initialize edge locations
        self.initialize_edge_nodes()

    def initialize_edge_nodes(self):
        """Initialize global edge node locations"""

        edge_locations = [
            # North America
            ("us-west-1", (37.7749, -122.4194), "San Francisco"),
            ("us-east-1", (40.7128, -74.0060), "New York"),
            ("us-central-1", (41.8781, -87.6298), "Chicago"),
            # Europe
            ("eu-west-1", (51.5074, -0.1278), "London"),
            ("eu-central-1", (50.1109, 8.6821), "Frankfurt"),
            ("eu-north-1", (59.3293, 18.0686), "Stockholm"),
            # Asia Pacific
            ("ap-southeast-1", (1.3521, 103.8198), "Singapore"),
            ("ap-northeast-1", (35.6762, 139.6503), "Tokyo"),
            ("ap-south-1", (19.0760, 72.8777), "Mumbai"),
            # Other regions
            ("sa-east-1", (-23.5505, -46.6333), "São Paulo"),
            ("me-south-1", (25.2048, 55.2708), "Dubai"),
            ("af-south-1", (-33.9249, 18.4241), "Cape Town"),
        ]

        for node_id, coords, city in edge_locations:
            self.edge_nodes[node_id] = EdgeNode(
                id=node_id,
                location=coords,
                region=city,
                capacity=1000,
                current_load=0,
                services=["vpn", "cache", "compute"],
                latency_map={},
                is_active=True,
                metadata={"city": city},
            )

    async def find_optimal_edge_node(
        self, client_location: tuple, service_type: str = "vpn"
    ) -> EdgeNode | None:
        """Find optimal edge node for client"""

        best_node: EdgeNode | None = None
        min_score = float("inf")

        for node in self.edge_nodes.values():
            if not node.is_active or service_type not in node.services:
                continue

            # Calculate weighted score
            distance = geodesic(client_location, node.location).km
            load_factor = node.current_load / node.capacity

            # Weighted scoring: distance (60%) + load (40%)
            score = (distance * 0.6) + (load_factor * 1000 * 0.4)

            if score < min_score:
                min_score = score
                best_node = node

        logger.info(f"Selected edge node: {best_node.id if best_node else 'None'}")
        return best_node

    async def deploy_edge_service(self, node_id: str, service_config: dict) -> bool:
        """Deploy service to edge node"""

        node = self.edge_nodes.get(node_id)
        if not node:
            return False

        # Check capacity
        required_capacity = service_config.get("capacity_units", 10)
        if node.current_load + required_capacity > node.capacity:
            logger.warning(f"Insufficient capacity on node {node_id}")
            return False

        # Deploy service (integrate with orchestration)
        deployment = {
            "node_id": node_id,
            "service": service_config["type"],
            "config": service_config,
            "timestamp": datetime.now().isoformat(),
        }

        # Update node load
        node.current_load += required_capacity

        logger.info(f"Deployed {service_config['type']} to edge node {node_id}")
        return True

    async def cache_content(
        self, content_id: str, content_data: bytes, ttl: int = 3600
    ) -> list[str]:
        """Cache content across edge nodes"""

        cached_nodes: list[str] = []
        content_hash = hashlib.sha256(content_data).hexdigest()

        # Select nodes for caching based on popularity and geography
        selected_nodes = await self.select_cache_nodes(content_id)

        for node_id in selected_nodes:
            cache_entry = {
                "content_id": content_id,
                "hash": content_hash,
                "size": len(content_data),
                "ttl": ttl,
                "cached_at": datetime.now().isoformat(),
            }

            # Store in edge cache (integrate with CDN)
            if await self.store_in_edge_cache(node_id, content_id, content_data):
                cached_nodes.append(node_id)

        return cached_nodes

    async def select_cache_nodes(self, content_id: str) -> list[str]:
        """Select edge nodes for content caching"""

        # Use consistent hashing for cache distribution
        content_hash = int(hashlib.md5(content_id.encode()).hexdigest(), 16)

        selected: list[str] = []
        for node_id, node in self.edge_nodes.items():
            node_hash = int(hashlib.md5(node_id.encode()).hexdigest(), 16)

            # Simple consistent hashing
            if (content_hash % 100) < (node_hash % 100):
                selected.append(node_id)
                if len(selected) >= 3:  # Replicate to 3 nodes
                    break

        return selected if selected else list(self.edge_nodes.keys())[:3]

    async def store_in_edge_cache(self, node_id: str, content_id: str, content_data: bytes) -> bool:
        """Store content in edge node cache"""

        # This would integrate with actual CDN/cache infrastructure
        # For demo, store in memory
        if node_id not in self.cdn_endpoints:
            self.cdn_endpoints[node_id] = {}

        self.cdn_endpoints[node_id][content_id] = {
            "data": content_data,
            "timestamp": datetime.now(),
            "hits": 0,
        }

        return True

    async def get_cached_content(self, content_id: str, client_location: tuple) -> bytes | None:
        """Get cached content from nearest edge node"""

        # Find nearest node with cached content
        nearest_node = await self.find_nearest_cache_node(content_id, client_location)

        if nearest_node:
            cache = self.cdn_endpoints.get(nearest_node, {})
            if content_id in cache:
                # Update hit counter
                cache[content_id]["hits"] += 1
                return cache[content_id]["data"]

        return None

    async def find_nearest_cache_node(self, content_id: str, client_location: tuple) -> str | None:
        """Find nearest edge node with cached content"""

        nodes_with_content: list[tuple] = []

        for node_id, cache in self.cdn_endpoints.items():
            if content_id in cache:
                node = self.edge_nodes[node_id]
                distance = geodesic(client_location, node.location).km
                nodes_with_content.append((node_id, distance))

        if nodes_with_content:
            nodes_with_content.sort(key=lambda x: x[1])
            return nodes_with_content[0][0]

        return None


# Serverless Function Deployment
class ServerlessVPNFunctions:
    """Deploy VPN functions to edge using serverless"""

    def __init__(self):
        self.functions: dict[str, dict[str, Any]] = {}
        self.triggers: dict[str, Any] = {}

    async def deploy_function(
        self, function_name: str, runtime: str, handler: str, code: str, timeout: int = 30
    ):
        """Deploy serverless function"""

        function_config = {
            "name": function_name,
            "runtime": runtime,  # 'python3.9', 'node14', etc.
            "handler": handler,
            "code": code,
            "timeout": timeout,
            "memory": 256,
            "environment": {},
            "deployed_at": datetime.now().isoformat(),
        }

        # Deploy to edge (integrate with Lambda@Edge, Cloudflare Workers, etc.)
        deployment_id = await self.deploy_to_edge(function_config)

        self.functions[function_name] = {
            "config": function_config,
            "deployment_id": deployment_id,
            "invocations": 0,
        }

        return deployment_id

    async def deploy_to_edge(self, config: dict) -> str:
        """Deploy function to edge platform"""

        # This would integrate with actual serverless platforms
        # For demo, return mock deployment ID
        return f"deployment-{hashlib.md5(json.dumps(config).encode()).hexdigest()[:8]}"

    async def invoke_function(self, function_name: str, payload: dict) -> dict:
        """Invoke serverless function"""

        if function_name not in self.functions:
            raise Exception(f"Function {function_name} not found")

        function = self.functions[function_name]
        function["invocations"] += 1

        # Execute function (integrate with serverless platform)
        result = await self.execute_function(function["config"], payload)

        return result

    async def execute_function(self, config: dict, payload: dict) -> dict:
        """Execute serverless function"""

        # Mock execution
        return {
            "statusCode": 200,
            "body": json.dumps(
                {"function": config["name"], "result": "success", "payload": payload}
            ),
        }

    def create_auth_function(self) -> str:
        """Create serverless authentication function"""

        code = """
import json
import jwt
import hashlib

def handler(event, context):
    try:
        # Parse request
        body = json.loads(event['body'])
        username = body.get('username')
        password = body.get('password')
        
        # Verify credentials (simplified)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Generate token
        token = jwt.encode(
            {'username': username, 'exp': 3600},
            'secret-key',
            algorithm='HS256'
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'token': token})
        }
    except Exception as e:
        return {
            'statusCode': 401,
            'body': json.dumps({'error': str(e)})
        }
"""
        return code

    def create_rate_limit_function(self) -> str:
        """Create rate limiting function"""

        code = """
import json
import time

# In-memory rate limit store (use Redis in production)
rate_limits = {}

def handler(event, context):
    try:
        # Get client IP
        client_ip = event['requestContext']['identity']['sourceIp']
        
        # Check rate limit
        current_time = time.time()
        window_start = current_time - 60  # 1 minute window
        
        if client_ip not in rate_limits:
            rate_limits[client_ip] = []
        
        # Clean old entries
        rate_limits[client_ip] = [
            t for t in rate_limits[client_ip] if t > window_start
        ]
        
        # Check limit (100 requests per minute)
        if len(rate_limits[client_ip]) >= 100:
            return {
                'statusCode': 429,
                'body': json.dumps({'error': 'Rate limit exceeded'})
            }
        
        # Add current request
        rate_limits[client_ip].append(current_time)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'allowed': True})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
"""
        return code
