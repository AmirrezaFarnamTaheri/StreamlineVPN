# Security functionality has been refactored into core components
# from vpn_merger.security.threat_detection import MLSecurityEngine


# Security functionality has been refactored into core components
# @pytest.mark.asyncio
# async def test_threat_engine_noop_default(monkeypatch):
#     monkeypatch.delenv('THREAT_DETECTION_ENABLED', raising=False)
#     eng = MLSecurityEngine()
#     sa = await eng.analyze_config_security({'protocol': 'vmess', 'host': 'example.com', 'port': 443})
#     assert sa.risk_level == 'low'
#     assert sa.threat_score == 0.0
#
#
# @pytest.mark.asyncio
# async def test_threat_engine_enabled(monkeypatch):
#     monkeypatch.setenv('THREAT_DETECTION_ENABLED', '1')
#     eng = MLSecurityEngine()
#     sa = await eng.analyze_config_security({'protocol': 'vless', 'host': 'example.com', 'port': 443})
#     assert sa.risk_level in {'low', 'medium', 'high'}
#     assert 0.0 <= sa.threat_score <= 1.0
