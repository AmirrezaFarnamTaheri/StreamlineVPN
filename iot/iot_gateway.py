import asyncio
import json
import logging
import struct
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IoTDevice:
    """IoT device representation"""

    device_id: str
    device_type: str
    mac_address: str
    ip_address: str
    firmware_version: str
    capabilities: list[str]
    is_online: bool
    last_seen: datetime
    metadata: dict[str, Any]


class IoTVPNGateway:
    """Lightweight VPN gateway for IoT devices"""

    def __init__(self, gateway_id: str, mqtt_broker: str = "localhost", mqtt_port: int = 1883):
        self.gateway_id = gateway_id
        self.devices: dict[str, IoTDevice] = {}
        self.active_tunnels: dict[str, dict[str, Any]] = {}

        # MQTT setup for IoT communication
        self.mqtt_client = mqtt.Client(client_id=gateway_id)
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port

        # Protocol handlers
        self.protocol_handlers = {
            "coap": self.handle_coap,
            "mqtt": self.handle_mqtt,
            "lwm2m": self.handle_lwm2m,
            "lorawan": self.handle_lorawan,
        }

    async def start(self):
        """Start IoT VPN gateway"""

        # Connect to MQTT broker
        self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
        self.mqtt_client.loop_start()

        # Start protocol listeners
        await asyncio.gather(
            self.start_coap_server(), self.start_dtls_server(), self.monitor_devices()
        )

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        logger.info(f"Connected to MQTT broker with result code {rc}")

        # Subscribe to IoT topics
        client.subscribe("iot/+/register")
        client.subscribe("iot/+/status")
        client.subscribe("iot/+/data")
        client.subscribe("iot/+/command")

    def on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""

        topic_parts = msg.topic.split("/")
        if len(topic_parts) < 3:
            return

        device_id = topic_parts[1]
        message_type = topic_parts[2]

        if message_type == "register":
            asyncio.create_task(self.register_device(device_id, msg.payload))
        elif message_type == "data":
            asyncio.create_task(self.process_device_data(device_id, msg.payload))

    async def register_device(self, device_id: str, payload: bytes):
        """Register new IoT device"""

        try:
            data = json.loads(payload)

            device = IoTDevice(
                device_id=device_id,
                device_type=data.get("type", "unknown"),
                mac_address=data.get("mac", ""),
                ip_address=data.get("ip", ""),
                firmware_version=data.get("firmware", "1.0"),
                capabilities=data.get("capabilities", []),
                is_online=True,
                last_seen=datetime.now(),
                metadata=data.get("metadata", {}),
            )

            self.devices[device_id] = device

            # Setup lightweight VPN tunnel
            await self.setup_device_tunnel(device)

            # Send acknowledgment
            self.mqtt_client.publish(
                f"iot/{device_id}/registered",
                json.dumps({"status": "success", "gateway": self.gateway_id}),
            )

            logger.info(f"Registered IoT device: {device_id}")

        except Exception as e:
            logger.error(f"Failed to register device {device_id}: {e}")

    async def setup_device_tunnel(self, device: IoTDevice):
        """Setup lightweight VPN tunnel for IoT device"""

        # Determine optimal protocol based on device capabilities
        if "dtls" in device.capabilities:
            tunnel = await self.create_dtls_tunnel(device)
        elif "tls-psk" in device.capabilities:
            tunnel = await self.create_psk_tunnel(device)
        else:
            tunnel = await self.create_basic_tunnel(device)

        self.active_tunnels[device.device_id] = tunnel

    async def create_dtls_tunnel(self, device: IoTDevice):
        """Create DTLS tunnel for constrained devices"""

        # DTLS configuration for IoT
        dtls_config = {
            "version": "DTLSv1.2",
            "cipher_suite": "TLS_PSK_WITH_AES_128_CCM_8",
            "psk": self.generate_psk(device.device_id),
            "mtu": 1280,  # Reduced MTU for constrained networks
            "retransmission_timeout": 1000,
            "max_retransmissions": 3,
        }

        # Create DTLS context
        tunnel = {
            "protocol": "dtls",
            "config": dtls_config,
            "created_at": datetime.now(),
            "stats": {"bytes_in": 0, "bytes_out": 0},
        }

        return tunnel

    async def create_psk_tunnel(self, device: IoTDevice):
        """Create TLS-PSK tunnel"""

        psk = self.generate_psk(device.device_id)

        tunnel = {
            "protocol": "tls-psk",
            "psk": psk,
            "cipher": "AES-128-CCM",
            "created_at": datetime.now(),
            "stats": {"bytes_in": 0, "bytes_out": 0},
        }

        return tunnel

    async def create_basic_tunnel(self, device: IoTDevice):
        """Create basic encrypted tunnel for simple devices"""

        # Use lightweight encryption for constrained devices
        tunnel = {
            "protocol": "basic",
            "encryption": "chacha20-poly1305",
            "key": self.generate_key(device.device_id),
            "created_at": datetime.now(),
            "stats": {"bytes_in": 0, "bytes_out": 0},
        }

        return tunnel

    def generate_psk(self, device_id: str) -> bytes:
        """Generate pre-shared key for device"""
        import hashlib

        return hashlib.sha256(f"{device_id}:{self.gateway_id}".encode()).digest()

    def generate_key(self, device_id: str) -> bytes:
        """Generate encryption key for device"""
        import hashlib

        return hashlib.sha256(f"key:{device_id}".encode()).digest()[:32]

    async def process_device_data(self, device_id: str, payload: bytes):
        """Process data from IoT device"""

        if device_id not in self.devices:
            logger.warning(f"Unknown device: {device_id}")
            return

        device = self.devices[device_id]
        device.last_seen = datetime.now()

        # Decrypt if tunnel exists
        if device_id in self.active_tunnels:
            tunnel = self.active_tunnels[device_id]
            decrypted = await self.decrypt_payload(payload, tunnel)

            # Update statistics
            tunnel["stats"]["bytes_in"] += len(payload)

            # Process decrypted data
            await self.handle_device_data(device, decrypted)

    async def decrypt_payload(self, payload: bytes, tunnel: dict) -> bytes:
        """Decrypt payload based on tunnel protocol"""

        if tunnel["protocol"] == "dtls":
            # DTLS decryption
            return self.dtls_decrypt(payload, tunnel["config"])
        elif tunnel["protocol"] == "tls-psk":
            # TLS-PSK decryption
            return self.psk_decrypt(payload, tunnel["psk"])
        elif tunnel["protocol"] == "basic":
            # Basic decryption
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

            cipher = ChaCha20Poly1305(tunnel["key"])

            nonce = payload[:12]
            ciphertext = payload[12:]

            try:
                return cipher.decrypt(nonce, ciphertext, None)
            except Exception:
                logger.error("Decryption failed")
                return payload

        return payload

    def dtls_decrypt(self, payload: bytes, config: dict) -> bytes:
        """DTLS decryption for IoT"""
        # Implement DTLS decryption
        return payload

    def psk_decrypt(self, payload: bytes, psk: bytes) -> bytes:
        """PSK-based decryption"""
        # Implement PSK decryption
        return payload

    async def handle_device_data(self, device: IoTDevice, data: bytes):
        """Handle decrypted device data"""

        try:
            # Parse data based on device type
            if device.device_type == "sensor":
                await self.handle_sensor_data(device, data)
            elif device.device_type == "actuator":
                await self.handle_actuator_data(device, data)
            elif device.device_type == "gateway":
                await self.handle_gateway_data(device, data)

        except Exception as e:
            logger.error(f"Error handling device data: {e}")

    async def handle_sensor_data(self, device: IoTDevice, data: bytes):
        """Handle sensor data"""

        # Parse sensor readings
        readings = self.parse_sensor_data(data)

        # Store in time-series database
        await self.store_sensor_readings(device.device_id, readings)

        # Check thresholds and trigger alerts
        await self.check_sensor_thresholds(device, readings)

    def parse_sensor_data(self, data: bytes) -> dict:
        """Parse sensor data format"""

        # Example: temperature, humidity, pressure
        if len(data) >= 12:
            temp, humidity, pressure = struct.unpack("!fff", data[:12])
            return {
                "temperature": temp,
                "humidity": humidity,
                "pressure": pressure,
                "timestamp": datetime.now().isoformat(),
            }

        return {}

    async def store_sensor_readings(self, device_id: str, readings: dict):
        """Store sensor readings in database"""
        # Integration with InfluxDB or similar

    async def check_sensor_thresholds(self, device: IoTDevice, readings: dict):
        """Check sensor thresholds and trigger alerts"""

        thresholds = device.metadata.get("thresholds", {})

        for metric, value in readings.items():
            if metric in thresholds:
                min_val = thresholds[metric].get("min")
                max_val = thresholds[metric].get("max")

                if min_val is not None and isinstance(value, (int, float)) and value < min_val:
                    await self.trigger_alert(device, metric, value, "below_minimum")
                elif max_val is not None and isinstance(value, (int, float)) and value > max_val:
                    await self.trigger_alert(device, metric, value, "above_maximum")

    async def trigger_alert(self, device: IoTDevice, metric: str, value: float, alert_type: str):
        """Trigger alert for threshold violation"""

        alert = {
            "device_id": device.device_id,
            "metric": metric,
            "value": value,
            "alert_type": alert_type,
            "timestamp": datetime.now().isoformat(),
        }

        # Publish alert
        self.mqtt_client.publish(f"alerts/{device.device_id}/{metric}", json.dumps(alert))

    async def start_coap_server(self):
        """Start CoAP server for IoT devices"""
        # Implement CoAP server

    async def start_dtls_server(self):
        """Start DTLS server for secure IoT communication"""
        # Implement DTLS server

    async def monitor_devices(self):
        """Monitor IoT device health"""

        while True:
            current_time = datetime.now()

            for device_id, device in list(self.devices.items()):
                # Check if device is offline
                time_since_last_seen = (current_time - device.last_seen).seconds

                if time_since_last_seen > 300:  # 5 minutes
                    if device.is_online:
                        device.is_online = False
                        logger.warning(f"Device {device_id} went offline")

                        # Clean up tunnel
                        if device_id in self.active_tunnels:
                            del self.active_tunnels[device_id]

            await asyncio.sleep(60)  # Check every minute

    async def handle_coap(self, data: bytes, addr: tuple):
        """Handle CoAP protocol"""
        # Implement CoAP handling

    async def handle_mqtt(self, data: bytes):
        """Handle MQTT protocol"""
        # Already handled via callbacks

    async def handle_lwm2m(self, data: bytes, addr: tuple):
        """Handle LWM2M protocol"""
        # Implement LWM2M handling

    async def handle_lorawan(self, data: bytes):
        """Handle LoRaWAN protocol"""
        # Implement LoRaWAN handling
