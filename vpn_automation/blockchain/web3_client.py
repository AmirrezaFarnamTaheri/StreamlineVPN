#!/usr/bin/env python3
"""
Web3 Integration for VPN Blockchain Operations
Version: 1.0.0

Provides Web3 integration for decentralized VPN management.
"""

import asyncio
import json
import logging
import os

from eth_account import Account
from web3 import Web3
from web3.middleware import geth_poa_middleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VPNWeb3Client:
    """Web3 client for VPN blockchain operations"""

    def __init__(self, rpc_url: str, contract_address: str, private_key: str = None):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.private_key = private_key
        self.account = None

        # Add POA middleware for testnets
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        # Load contract ABI
        self.contract_abi = self._load_contract_abi()
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.contract_abi)

        if private_key:
            self.account = Account.from_key(private_key)
            logger.info(f"Initialized with account: {self.account.address}")

    def _load_contract_abi(self) -> list[dict]:
        """Load contract ABI from file"""
        try:
            abi_path = os.path.join(os.path.dirname(__file__), "contracts", "DecentralizedVPN.json")
            with open(abi_path) as f:
                contract_data = json.load(f)
                return contract_data["abi"]
        except FileNotFoundError:
            logger.warning("Contract ABI file not found, using minimal ABI")
            return self._get_minimal_abi()

    def _get_minimal_abi(self) -> list[dict]:
        """Get minimal ABI for basic operations"""
        return [
            {
                "inputs": [{"name": "username", "type": "string"}],
                "name": "registerUser",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            },
            {
                "inputs": [{"name": "planId", "type": "uint256"}],
                "name": "subscribeToPlan",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            },
            {
                "inputs": [
                    {"name": "ipAddress", "type": "string"},
                    {"name": "bandwidth", "type": "uint256"},
                ],
                "name": "registerNode",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            },
            {
                "inputs": [{"name": "nodeAddress", "type": "address"}],
                "name": "establishConnection",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            },
            {
                "inputs": [
                    {"name": "connectionId", "type": "uint256"},
                    {"name": "dataTransferred", "type": "uint256"},
                ],
                "name": "terminateConnection",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            },
            {
                "inputs": [{"name": "userAddress", "type": "address"}],
                "name": "getUserInfo",
                "outputs": [
                    {
                        "components": [
                            {"name": "userId", "type": "uint256"},
                            {"name": "username", "type": "string"},
                            {"name": "currentPlanId", "type": "uint256"},
                            {"name": "subscriptionExpiry", "type": "uint256"},
                            {"name": "totalDataUsed", "type": "uint256"},
                            {"name": "totalConnections", "type": "uint256"},
                            {"name": "isActive", "type": "bool"},
                            {"name": "reputation", "type": "uint256"},
                            {"name": "lastActivity", "type": "uint256"},
                        ],
                        "name": "",
                        "type": "tuple",
                    }
                ],
                "stateMutability": "view",
                "type": "function",
            },
        ]

    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        return self.w3.is_connected()

    def get_network_info(self) -> dict:
        """Get network information"""
        return {
            "chain_id": self.w3.eth.chain_id,
            "block_number": self.w3.eth.block_number,
            "gas_price": self.w3.eth.gas_price,
            "is_connected": self.is_connected(),
        }

    def register_user(self, username: str) -> str:
        """Register a new user on the blockchain"""
        if not self.account:
            raise ValueError("Private key required for transactions")

        try:
            # Build transaction
            transaction = self.contract.functions.registerUser(username).build_transaction(
                {
                    "from": self.account.address,
                    "gas": 200000,
                    "gasPrice": self.w3.eth.gas_price,
                    "nonce": self.w3.eth.get_transaction_count(self.account.address),
                }
            )

            # Sign and send transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"User registered: {username}, TX: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise

    def subscribe_to_plan(self, plan_id: int, token_contract_address: str) -> str:
        """Subscribe to a VPN plan"""
        if not self.account:
            raise ValueError("Private key required for transactions")

        try:
            # Get plan details
            plan = self.contract.functions.plans(plan_id).call()

            # Approve token spending first
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_contract_address), abi=self._get_erc20_abi()
            )

            approve_txn = token_contract.functions.approve(
                self.contract_address, plan[2]  # price
            ).build_transaction(
                {
                    "from": self.account.address,
                    "gas": 100000,
                    "gasPrice": self.w3.eth.gas_price,
                    "nonce": self.w3.eth.get_transaction_count(self.account.address),
                }
            )

            signed_approve = self.w3.eth.account.sign_transaction(approve_txn, self.private_key)
            approve_hash = self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
            self.w3.eth.wait_for_transaction_receipt(approve_hash)

            # Subscribe to plan
            transaction = self.contract.functions.subscribeToPlan(plan_id).build_transaction(
                {
                    "from": self.account.address,
                    "gas": 200000,
                    "gasPrice": self.w3.eth.gas_price,
                    "nonce": self.w3.eth.get_transaction_count(self.account.address),
                }
            )

            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"Subscribed to plan {plan_id}, TX: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Error subscribing to plan: {e}")
            raise

    def register_node(self, ip_address: str, bandwidth: int) -> str:
        """Register a new VPN node"""
        if not self.account:
            raise ValueError("Private key required for transactions")

        try:
            transaction = self.contract.functions.registerNode(
                ip_address, bandwidth
            ).build_transaction(
                {
                    "from": self.account.address,
                    "gas": 300000,
                    "gasPrice": self.w3.eth.gas_price,
                    "nonce": self.w3.eth.get_transaction_count(self.account.address),
                }
            )

            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"Node registered: {ip_address}, TX: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Error registering node: {e}")
            raise

    def establish_connection(self, node_address: str) -> str:
        """Establish a VPN connection to a node"""
        if not self.account:
            raise ValueError("Private key required for transactions")

        try:
            transaction = self.contract.functions.establishConnection(
                Web3.to_checksum_address(node_address)
            ).build_transaction(
                {
                    "from": self.account.address,
                    "gas": 200000,
                    "gasPrice": self.w3.eth.gas_price,
                    "nonce": self.w3.eth.get_transaction_count(self.account.address),
                }
            )

            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"Connection established to {node_address}, TX: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Error establishing connection: {e}")
            raise

    def terminate_connection(self, connection_id: int, data_transferred: int) -> str:
        """Terminate a VPN connection"""
        if not self.account:
            raise ValueError("Private key required for transactions")

        try:
            transaction = self.contract.functions.terminateConnection(
                connection_id, data_transferred
            ).build_transaction(
                {
                    "from": self.account.address,
                    "gas": 200000,
                    "gasPrice": self.w3.eth.gas_price,
                    "nonce": self.w3.eth.get_transaction_count(self.account.address),
                }
            )

            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"Connection {connection_id} terminated, TX: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Error terminating connection: {e}")
            raise

    def get_user_info(self, user_address: str) -> dict:
        """Get user information from blockchain"""
        try:
            user_info = self.contract.functions.getUserInfo(
                Web3.to_checksum_address(user_address)
            ).call()

            return {
                "user_id": user_info[0],
                "username": user_info[1],
                "current_plan_id": user_info[2],
                "subscription_expiry": user_info[3],
                "total_data_used": user_info[4],
                "total_connections": user_info[5],
                "is_active": user_info[6],
                "reputation": user_info[7],
                "last_activity": user_info[8],
            }

        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise

    def get_node_info(self, node_address: str) -> dict:
        """Get node information from blockchain"""
        try:
            node_info = self.contract.functions.getNodeInfo(
                Web3.to_checksum_address(node_address)
            ).call()

            return {
                "node_address": node_info[0],
                "ip_address": node_info[1],
                "bandwidth": node_info[2],
                "total_connections": node_info[3],
                "total_data_transferred": node_info[4],
                "reputation": node_info[5],
                "is_active": node_info[6],
                "last_heartbeat": node_info[7],
            }

        except Exception as e:
            logger.error(f"Error getting node info: {e}")
            raise

    def get_available_nodes(self) -> list[dict]:
        """Get list of available VPN nodes"""
        try:
            # This would require additional contract functions to get all nodes
            # For now, return empty list
            return []

        except Exception as e:
            logger.error(f"Error getting available nodes: {e}")
            return []

    def get_user_connections(self, user_address: str) -> list[int]:
        """Get user's connection IDs"""
        try:
            connections = self.contract.functions.getUserConnections(
                Web3.to_checksum_address(user_address)
            ).call()

            return connections

        except Exception as e:
            logger.error(f"Error getting user connections: {e}")
            return []

    def get_connection_info(self, connection_id: int) -> dict:
        """Get connection information"""
        try:
            connection_info = self.contract.functions.getConnectionInfo(connection_id).call()

            return {
                "user": connection_info[0],
                "node": connection_info[1],
                "start_time": connection_info[2],
                "data_transferred": connection_info[3],
                "is_active": connection_info[4],
            }

        except Exception as e:
            logger.error(f"Error getting connection info: {e}")
            raise

    def check_node_health(self, node_address: str) -> bool:
        """Check if node is healthy"""
        try:
            is_healthy = self.contract.functions.isNodeHealthy(
                Web3.to_checksum_address(node_address)
            ).call()

            return is_healthy

        except Exception as e:
            logger.error(f"Error checking node health: {e}")
            return False

    def update_heartbeat(self) -> str:
        """Update node heartbeat"""
        if not self.account:
            raise ValueError("Private key required for transactions")

        try:
            transaction = self.contract.functions.updateHeartbeat().build_transaction(
                {
                    "from": self.account.address,
                    "gas": 100000,
                    "gasPrice": self.w3.eth.gas_price,
                    "nonce": self.w3.eth.get_transaction_count(self.account.address),
                }
            )

            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            logger.info(f"Heartbeat updated, TX: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")
            raise

    def _get_erc20_abi(self) -> list[dict]:
        """Get ERC20 token ABI"""
        return [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function",
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"},
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function",
            },
        ]


class AsyncVPNWeb3Client:
    """Async Web3 client for VPN blockchain operations"""

    def __init__(self, rpc_url: str, contract_address: str, private_key: str = None):
        self.sync_client = VPNWeb3Client(rpc_url, contract_address, private_key)

    async def register_user_async(self, username: str) -> str:
        """Async user registration"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_client.register_user, username)

    async def subscribe_to_plan_async(self, plan_id: int, token_contract_address: str) -> str:
        """Async plan subscription"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.sync_client.subscribe_to_plan, plan_id, token_contract_address
        )

    async def register_node_async(self, ip_address: str, bandwidth: int) -> str:
        """Async node registration"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.sync_client.register_node, ip_address, bandwidth
        )

    async def establish_connection_async(self, node_address: str) -> str:
        """Async connection establishment"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_client.establish_connection, node_address)

    async def get_user_info_async(self, user_address: str) -> dict:
        """Async user info retrieval"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_client.get_user_info, user_address)


# Example usage
if __name__ == "__main__":
    # Configuration
    RPC_URL = "https://sepolia.infura.io/v3/YOUR_PROJECT_ID"
    CONTRACT_ADDRESS = "0x1234567890123456789012345678901234567890"
    PRIVATE_KEY = "your_private_key_here"

    # Initialize client
    client = VPNWeb3Client(RPC_URL, CONTRACT_ADDRESS, PRIVATE_KEY)

    # Check connection
    if client.is_connected():
        print("Connected to blockchain")
        print(f"Network info: {client.get_network_info()}")

        # Register user
        try:
            tx_hash = client.register_user("testuser")
            print(f"User registered: {tx_hash}")

            # Get user info
            user_info = client.get_user_info(client.account.address)
            print(f"User info: {user_info}")

        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Failed to connect to blockchain")
