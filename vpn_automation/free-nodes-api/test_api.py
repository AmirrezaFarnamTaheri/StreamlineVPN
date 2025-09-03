#!/usr/bin/env python3
"""
Free Nodes Aggregator API Test Script
-------------------------------------
Tests the API functionality with sample data and health checks.
"""

import asyncio
import base64
import json

import httpx


class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

        # Sample test data
        self.sample_links = [
            "vless://11111111-2222-3333-4444-555555555555@example.com:443?security=reality&pbk=PUBKEY&sid=abcdef&sni=www.microsoft.com&type=tcp#Sample-REALITY",
            "vmess://"
            + base64.b64encode(
                json.dumps(
                    {
                        "v": "2",
                        "ps": "Sample-VMESS",
                        "add": "vmess.example.com",
                        "port": "443",
                        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                        "net": "tcp",
                        "type": "none",
                        "tls": "tls",
                        "sni": "www.cloudflare.com",
                        "path": "/",
                    }
                ).encode()
            ).decode(),
            "trojan://pass123@trojan.example.com:443#Sample-Trojan",
            "ss://"
            + base64.b64encode(b"chacha20-ietf-poly1305:passw0rd@ss.example.com:8388").decode()
            + "#Sample-SS",
        ]

        self.sample_sources = [
            "https://httpbin.org/status/200",  # Will return HTML, not links
            "https://httpbin.org/json",  # Will return JSON, not links
        ]

    async def test_health(self) -> bool:
        """Test the health endpoint."""
        print("🔍 Testing health endpoint...")
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check passed: {data}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False

    async def test_ingest(self) -> bool:
        """Test the ingest endpoint."""
        print("🔍 Testing ingest endpoint...")
        try:
            response = await self.client.post(
                f"{self.base_url}/api/ingest", json={"links": self.sample_links}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Ingest successful: {data}")
                return True
            else:
                print(f"❌ Ingest failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ingest error: {e}")
            return False

    async def test_sources(self) -> bool:
        """Test the sources endpoint."""
        print("🔍 Testing sources endpoint...")
        try:
            response = await self.client.post(
                f"{self.base_url}/api/sources", json={"urls": self.sample_sources}
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sources added: {data}")
                return True
            else:
                print(f"❌ Sources failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Sources error: {e}")
            return False

    async def test_refresh(self) -> bool:
        """Test the refresh endpoint."""
        print("🔍 Testing refresh endpoint...")
        try:
            response = await self.client.post(f"{self.base_url}/api/refresh")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Refresh successful: {data}")
                return True
            else:
                print(f"❌ Refresh failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Refresh error: {e}")
            return False

    async def test_get_nodes(self) -> bool:
        """Test the get nodes endpoint."""
        print("🔍 Testing get nodes endpoint...")
        try:
            response = await self.client.get(f"{self.base_url}/api/nodes.json?limit=10")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Get nodes successful: {len(data)} nodes returned")
                if data:
                    print(f"   Sample node: {data[0]['name']} ({data[0]['proto']})")
                return True
            else:
                print(f"❌ Get nodes failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Get nodes error: {e}")
            return False

    async def test_subscription(self) -> bool:
        """Test the subscription endpoint."""
        print("🔍 Testing subscription endpoint...")
        try:
            response = await self.client.get(f"{self.base_url}/api/subscription.txt?limit=5")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Subscription successful: {len(data.get('base64', ''))} chars")
                return True
            else:
                print(f"❌ Subscription failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Subscription error: {e}")
            return False

    async def test_singbox_export(self) -> bool:
        """Test the sing-box export endpoint."""
        print("🔍 Testing sing-box export endpoint...")
        try:
            response = await self.client.get(f"{self.base_url}/api/export/singbox.json?limit=5")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Sing-box export successful: {len(data.get('outbounds', []))} outbounds")
                return True
            else:
                print(f"❌ Sing-box export failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Sing-box export error: {e}")
            return False

    async def test_ping(self) -> bool:
        """Test the ping endpoint."""
        print("🔍 Testing ping endpoint...")
        try:
            response = await self.client.post(
                f"{self.base_url}/api/ping",
                json={"links": self.sample_links[:2]},  # Test first 2 links
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Ping successful: {len(data)} nodes tested")
                for node in data:
                    print(f"   {node['name']}: {node.get('latency_ms', 'N/A')}ms")
                return True
            else:
                print(f"❌ Ping failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ping error: {e}")
            return False

    async def test_rate_limiting(self) -> bool:
        """Test rate limiting by making many requests."""
        print("🔍 Testing rate limiting...")
        try:
            # Make many requests quickly
            tasks = []
            for i in range(150):  # More than the 120/minute limit
                tasks.append(self.client.get(f"{self.base_url}/health"))

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successful vs rate limited
            successful = 0
            rate_limited = 0

            for response in responses:
                if isinstance(response, httpx.Response):
                    if response.status_code == 200:
                        successful += 1
                    elif response.status_code == 429:
                        rate_limited += 1

            print(f"✅ Rate limiting test: {successful} successful, {rate_limited} rate limited")
            return rate_limited > 0  # Should have some rate limited
        except Exception as e:
            print(f"❌ Rate limiting test error: {e}")
            return False

    async def run_all_tests(self) -> dict:
        """Run all tests and return results."""
        print("🚀 Starting Free Nodes Aggregator API Tests")
        print("=" * 50)

        tests = [
            ("Health Check", self.test_health),
            ("Ingest Nodes", self.test_ingest),
            ("Add Sources", self.test_sources),
            ("Refresh Sources", self.test_refresh),
            ("Get Nodes", self.test_get_nodes),
            ("Subscription Export", self.test_subscription),
            ("Sing-box Export", self.test_singbox_export),
            ("Ping Nodes", self.test_ping),
            ("Rate Limiting", self.test_rate_limiting),
        ]

        results = {}

        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = await test_func()
                results[test_name] = result
                print(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
            except Exception as e:
                print(f"❌ ERROR: {test_name} - {e}")
                results[test_name] = False

        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print("=" * 50)

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")

        print(f"\n🎯 Overall: {passed}/{total} tests passed")

        return results

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Main test function."""
    # Test with default localhost
    tester = APITester()

    try:
        results = await tester.run_all_tests()

        # Exit with appropriate code
        passed = sum(1 for result in results.values() if result)
        total = len(results)

        if passed == total:
            print("\n🎉 All tests passed!")
            exit(0)
        else:
            print(f"\n⚠️  {total - passed} tests failed")
            exit(1)

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
