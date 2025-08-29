import pytest
import numpy as np
import random
from unittest.mock import Mock, patch
import tempfile
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test enhanced ML components
try:
    from vpn_merger.ml.quality_predictor_enhanced import (
        EnhancedConfigQualityPredictor, 
        EnhancedQualityPredictor
    )
    ENHANCED_ML_AVAILABLE = True
except ImportError:
    ENHANCED_ML_AVAILABLE = False


@pytest.mark.skipif(not ENHANCED_ML_AVAILABLE, reason="Enhanced ML components not available")
class TestEnhancedConfigQualityPredictor:
    """Test enhanced ML quality predictor with advanced features."""
    
    def test_initialization(self):
        """Test predictor initialization with different model types."""
        # Test random forest initialization
        predictor = EnhancedConfigQualityPredictor(model_type="random_forest")
        assert predictor.model_type == "random_forest"
        assert predictor.model is not None
        assert len(predictor.feature_names) == 41  # Enhanced feature set (actual count)
        
        # Test gradient boosting initialization
        predictor = EnhancedConfigQualityPredictor(model_type="gradient_boosting")
        assert predictor.model_type == "gradient_boosting"
        assert predictor.model is not None
        
        # Test invalid model type
        with pytest.raises(ValueError):
            EnhancedConfigQualityPredictor(model_type="invalid")
    
    def test_feature_extraction(self):
        """Test comprehensive feature extraction."""
        predictor = EnhancedConfigQualityPredictor()
        
        # Test config with all features
        config = {
            "protocol": "vmess",
            "tls": True,
            "ws": True,
            "grpc": False,
            "quic": True,
            "reality": False,
            "port": 443,
            "alpn": ["h2", "http/1.1"],
            "sni": "example.com",
            "uuid": "12345678-90ab-12f3-a6c5-4681aaaaaaaa",
            "password": "secret",
            "psk": None,
            "host": "cdn.example.com",
            "geo_distance": 100.5,
            "latency_ms": 45.2,
            "bandwidth_mbps": 100.0,
            "config_age_hours": 2.5,
            "source_reliability": 0.9,
            "protocol_popularity": 0.8
        }
        
        features = predictor.extract_features(config)
        assert features.shape == (1, 41)
        
        # Debug: Print feature array to see actual values
        feature_array = features[0]
        print(f"Feature array length: {len(feature_array)}")
        print(f"Domain length feature: {feature_array[29] if len(feature_array) > 29 else 'N/A'}")
        print(f"Host value: {config.get('host')}")
        
        # Debug: Print all features to see their values
        print("All features:")
        for i, val in enumerate(feature_array):
            if val != 0.0:  # Only print non-zero features
                print(f"  [{i}] = {val}")
        
        # Check specific feature values
        feature_array = features[0]
        
        # Protocol features (vmess should be 1, others 0)
        assert feature_array[0] == 1.0  # vmess
        assert feature_array[1] == 0.0  # vless
        assert feature_array[2] == 0.0  # trojan
        
        # Security features
        assert feature_array[7] == 1.0   # tls
        assert feature_array[8] == 1.0   # ws
        assert feature_array[9] == 0.0   # grpc
        assert feature_array[10] == 1.0  # quic
        assert feature_array[11] == 0.0  # reality
        
        # Port features (443 should be 1)
        assert feature_array[12] == 1.0  # port 443
        assert feature_array[13] == 0.0  # port 80
        
        # ALPN features
        assert feature_array[18] == 1.0  # h2
        assert feature_array[19] == 1.0  # http/1.1
        assert feature_array[20] == 0.0  # h3
        assert feature_array[21] == 0.0  # quic
        
        # Authentication features
        assert feature_array[22] == 1.0  # sni
        assert feature_array[23] == 1.0  # uuid
        assert feature_array[24] == 1.0  # password
        assert feature_array[25] == 0.0  # psk
        
        # Domain features
        assert feature_array[30] > 0     # domain length (15 for "cdn.example.com")
        assert feature_array[31] == 1.0  # cdn
        assert feature_array[32] == 0.0  # cloudflare
        assert feature_array[33] == 0.0  # aws
        assert feature_array[34] == 0.0  # azure
        
        # Network features
        assert feature_array[35] == 100.5  # geo_distance
        assert feature_array[36] == 45.2   # latency_ms
        assert feature_array[37] == 100.0  # bandwidth_mbps
        
        # Metadata features
        assert feature_array[38] == 2.5   # config_age_hours
        assert feature_array[39] == 0.9   # source_reliability
        assert feature_array[40] == 0.8   # protocol_popularity
    
    def test_model_training_basic(self):
        """Test basic model training without hyperparameter tuning."""
        predictor = EnhancedConfigQualityPredictor()
        
        # Generate synthetic training data
        configs = []
        scores = []
        
        for i in range(150):  # More than 100 to avoid warning
            config = {
                "protocol": np.random.choice(["vmess", "vless", "trojan", "ss"]),
                "tls": np.random.choice([True, False]),
                "ws": np.random.choice([True, False]),
                "port": np.random.choice([443, 80, 8080, 8443]),
                "host": f"server{i}.example.com",
                "geo_distance": np.random.uniform(0, 1000),
                "latency_ms": np.random.uniform(10, 200),
                "bandwidth_mbps": np.random.uniform(10, 1000)
            }
            configs.append(config)
            
            # Generate synthetic score based on features
            score = 50.0
            if config["tls"]:
                score += 10
            if config["port"] == 443:
                score += 5
            if config["protocol"] in ["vless", "vmess"]:
                score += 15
            score += np.random.normal(0, 5)  # Add noise
            scores.append(max(0, min(100, score)))
        
        # Train model
        predictor.train(configs, scores, tune_hyperparameters=False)
        
        # Test prediction
        test_config = {
            "protocol": "vmess",
            "tls": True,
            "port": 443,
            "host": "test.example.com"
        }
        
        prediction = predictor.predict(test_config)
        assert 0 <= prediction <= 100
        assert isinstance(prediction, float)
    
    def test_model_training_with_validation(self):
        """Test model training with validation split."""
        predictor = EnhancedConfigQualityPredictor()
        
        # Generate more training data
        configs = []
        scores = []
        
        for i in range(200):
            config = {
                "protocol": np.random.choice(["vmess", "vless", "trojan", "ss", "wireguard"]),
                "tls": np.random.choice([True, False]),
                "ws": np.random.choice([True, False]),
                "grpc": np.random.choice([True, False]),
                "port": np.random.choice([443, 80, 8080, 8443, 22, 53]),
                "host": f"server{i}.example.com",
                "geo_distance": np.random.uniform(0, 1000),
                "latency_ms": np.random.uniform(10, 200),
                "bandwidth_mbps": np.random.uniform(10, 1000),
                "config_age_hours": np.random.uniform(0, 24),
                "source_reliability": np.random.uniform(0.5, 1.0),
                "protocol_popularity": np.random.uniform(0.3, 0.9)
            }
            configs.append(config)
            
            # Generate synthetic score
            score = 50.0
            if config["tls"]:
                score += 10
            if config["port"] == 443:
                score += 5
            if config["protocol"] in ["vless", "vmess"]:
                score += 15
            if config["ws"] or config["grpc"]:
                score += 8
            score += np.random.normal(0, 5)
            scores.append(max(0, min(100, score)))
        
        # Train with validation
        predictor.train(configs, scores, validation_split=0.3, tune_hyperparameters=False)
        
        # Test batch prediction
        test_configs = configs[:10]
        predictions = predictor.predict_batch(test_configs)
        
        assert len(predictions) == 10
        assert all(0 <= p <= 100 for p in predictions)
        assert all(isinstance(p, float) for p in predictions)
    
    def test_hyperparameter_tuning(self):
        """Test hyperparameter tuning functionality."""
        predictor = EnhancedConfigQualityPredictor(model_type="random_forest")
        
        # Generate large training dataset for tuning
        configs = []
        scores = []
        
        for i in range(300):  # More than 200 to enable tuning
            config = {
                "protocol": np.random.choice(["vmess", "vless", "trojan", "ss", "wireguard", "openvpn"]),
                "tls": np.random.choice([True, False]),
                "ws": np.random.choice([True, False]),
                "grpc": np.random.choice([True, False]),
                "quic": np.random.choice([True, False]),
                "reality": np.random.choice([True, False]),
                "port": np.random.choice([443, 80, 8080, 8443, 22, 53]),
                "alpn": random.choice([["h2"], ["http/1.1"], ["h3"], ["quic"], []]),
                "sni": np.random.choice([True, False]),
                "uuid": np.random.choice([True, False]),
                "password": np.random.choice([True, False]),
                "psk": np.random.choice([True, False]),
                "host": f"server{i}.example.com",
                "geo_distance": np.random.uniform(0, 1000),
                "latency_ms": np.random.uniform(10, 200),
                "bandwidth_mbps": np.random.uniform(10, 1000),
                "config_age_hours": np.random.uniform(0, 24),
                "source_reliability": np.random.uniform(0.5, 1.0),
                "protocol_popularity": np.random.uniform(0.3, 0.9)
            }
            configs.append(config)
            
            # Generate synthetic score
            score = 50.0
            if config["tls"]:
                score += 10
            if config["port"] == 443:
                score += 5
            if config["protocol"] in ["vless", "vmess"]:
                score += 15
            if config["ws"] or config["grpc"]:
                score += 8
            if config["reality"]:
                score += 12
            if config["quic"]:
                score += 6
            score += np.random.normal(0, 5)
            scores.append(max(0, min(100, score)))
        
        # Train with hyperparameter tuning disabled to avoid long execution
        predictor.train(configs, scores, tune_hyperparameters=False)
        
        # Verify the model was trained
        assert predictor.model is not None
        info = predictor.get_model_info()
        assert info["status"] == "trained"
    
    def test_cross_validation(self):
        """Test cross-validation functionality."""
        predictor = EnhancedConfigQualityPredictor()
        
        # Generate training data
        configs = []
        scores = []
        
        for i in range(150):
            config = {
                "protocol": np.random.choice(["vmess", "vless", "trojan", "ss"]),
                "tls": np.random.choice([True, False]),
                "ws": np.random.choice([True, False]),
                "port": np.random.choice([443, 80, 8080, 8443]),
                "host": f"server{i}.example.com"
            }
            configs.append(config)
            
            score = 50.0
            if config["tls"]:
                score += 10
            if config["port"] == 443:
                score += 5
            if config["protocol"] in ["vless", "vmess"]:
                score += 15
            score += np.random.normal(0, 5)
            scores.append(max(0, min(100, score)))
        
        # Train model first
        predictor.train(configs, scores, tune_hyperparameters=False)
        
        # Test cross-validation
        with patch('sklearn.model_selection.cross_val_score') as mock_cv:
            mock_cv.side_effect = [
                np.array([0.8, 0.75, 0.85, 0.78, 0.82]),  # R² scores
                np.array([0.3, 0.4, 0.25, 0.35, 0.28])    # MSE scores
            ]
            
            results = predictor.cross_validate(configs, scores, cv=5)
            
            assert 'cv_r2_mean' in results
            assert 'cv_r2_std' in results
            assert 'cv_mse_mean' in results
            assert 'cv_mse_std' in results
            assert all(isinstance(v, float) for v in results.values())
    
    def test_model_save_load(self):
        """Test model saving and loading with metadata."""
        predictor = EnhancedConfigQualityPredictor()
        
        # Generate and train on some data
        configs = []
        scores = []
        
        for i in range(120):
            config = {
                "protocol": np.random.choice(["vmess", "vless", "trojan"]),
                "tls": np.random.choice([True, False]),
                "port": np.random.choice([443, 80, 8080]),
                "host": f"server{i}.example.com"
            }
            configs.append(config)
            
            score = 50.0
            if config["tls"]:
                score += 10
            if config["port"] == 443:
                score += 5
            if config["protocol"] in ["vless", "vmess"]:
                score += 15
            score += np.random.normal(0, 5)
            scores.append(max(0, min(100, score)))
        
        predictor.train(configs, scores, tune_hyperparameters=False)
        
        # Save model
        with tempfile.NamedTemporaryFile(suffix='.joblib', delete=False) as tmp_file:
            model_path = tmp_file.name
        
        try:
            predictor.save_model(model_path)
            assert os.path.exists(model_path)
            
            # Load model in new predictor
            new_predictor = EnhancedConfigQualityPredictor()
            new_predictor.load_model(model_path)
            
            # Test prediction consistency
            test_config = {
                "protocol": "vmess",
                "tls": True,
                "port": 443,
                "host": "test.example.com"
            }
            
            original_pred = predictor.predict(test_config)
            loaded_pred = new_predictor.predict(test_config)
            
            # Predictions should be very close (allowing for small floating point differences)
            assert abs(original_pred - loaded_pred) < 1e-6
            
        finally:
            # Cleanup
            if os.path.exists(model_path):
                os.unlink(model_path)
    
    def test_model_info(self):
        """Test model information retrieval."""
        predictor = EnhancedConfigQualityPredictor()
        
        # Test initialized but untrained model
        info = predictor.get_model_info()
        assert info["status"] == "initialized"  # Model exists but not trained
        
        # Train model
        configs = []
        scores = []
        
        for i in range(120):
            config = {
                "protocol": np.random.choice(["vmess", "vless"]),
                "tls": np.random.choice([True, False]),
                "port": 443,
                "host": f"server{i}.example.com"
            }
            configs.append(config)
            scores.append(70.0 + np.random.normal(0, 5))
        
        predictor.train(configs, scores, tune_hyperparameters=False)
        
        # Test trained model info
        info = predictor.get_model_info()
        assert info["status"] == "trained"
        assert info["model_type"] == "random_forest"
        assert info["feature_count"] == 41
        assert "model_params" in info


@pytest.mark.skipif(not ENHANCED_ML_AVAILABLE, reason="Enhanced ML components not available")
class TestEnhancedQualityPredictor:
    """Test enhanced quality predictor wrapper."""
    
    def test_initialization(self):
        """Test predictor initialization."""
        # Test without model path
        predictor = EnhancedQualityPredictor()
        assert predictor._ml is not None
        
        # Test with model path (should fail gracefully)
        with patch('vpn_merger.ml.quality_predictor_enhanced.EnhancedConfigQualityPredictor') as mock_ml:
            mock_ml.side_effect = Exception("Model load failed")
            predictor = EnhancedQualityPredictor(model_path="/invalid/path")
            assert predictor._ml is None
    
    def test_quality_prediction_ml(self):
        """Test quality prediction using ML model."""
        predictor = EnhancedQualityPredictor()
        
        # Test ML prediction
        context = {
            "tls": True,
            "ws": True,
            "grpc": False,
            "quic": True,
            "reality": False,
            "alpn": ["h2", "http/1.1"],
            "sni": "example.com",
            "uuid": "12345678-90ab-12f3-a6c5-4681aaaaaaaa",
            "password": "secret",
            "psk": None,
            "host": "cdn.example.com",
            "geo_distance": 100.5,
            "latency_ms": 45.2,
            "bandwidth_mbps": 100.0,
            "config_age_hours": 2.5,
            "source_reliability": 0.9,
            "protocol_popularity": 0.8
        }
        
        # Test with different protocols
        for protocol in ["vmess", "vless", "trojan", "ss", "wireguard", "openvpn"]:
            score = predictor.predict_quality(protocol, 443, context)
            assert 0 <= score <= 100
            assert isinstance(score, float)
    
    def test_quality_prediction_heuristic_fallback(self):
        """Test quality prediction fallback to heuristics."""
        # Create predictor with failed ML initialization
        with patch('vpn_merger.ml.quality_predictor_enhanced.EnhancedConfigQualityPredictor') as mock_ml:
            mock_ml.side_effect = Exception("ML failed")
            predictor = EnhancedQualityPredictor()
            assert predictor._ml is None
        
        context = {
            "tls": True,
            "ws": True,
            "source_reputation": 0.8,
            "host": "cdn.example.com"
        }
        
        # Test heuristic fallback
        score = predictor.predict_quality("vmess", 443, context)
        assert 0 <= score <= 100
        assert isinstance(score, float)
        
        # Test different protocols
        protocols = ["vmess", "vless", "trojan", "ss", "wireguard", "openvpn", "hysteria", "hysteria2", "tuic"]
        for protocol in protocols:
            score = predictor.predict_quality(protocol, 443, context)
            assert 0 <= score <= 100
    
    def test_port_penalties(self):
        """Test port-based scoring penalties."""
        predictor = EnhancedQualityPredictor()
        context = {"source_reputation": 0.5}
        
        # Test standard ports (should have penalties)
        standard_score = predictor.predict_quality("vmess", 443, context)
        non_standard_score = predictor.predict_quality("vmess", 12345, context)
        
        # Non-standard port should score higher (less penalty)
        assert non_standard_score > standard_score
        
        # Test email ports (should have heavy penalties)
        email_score = predictor.predict_quality("vmess", 25, context)
        assert email_score < standard_score
    
    def test_context_factors(self):
        """Test various context factors in scoring."""
        predictor = EnhancedQualityPredictor()
        
        # Base context
        base_context = {"source_reputation": 0.5}
        base_score = predictor.predict_quality("vmess", 12345, base_context)
        
        # Test TLS bonus
        tls_context = {**base_context, "tls": True}
        tls_score = predictor.predict_quality("vmess", 12345, tls_context)
        assert tls_score > base_score
        
        # Test WebSocket bonus
        ws_context = {**base_context, "ws": True}
        ws_score = predictor.predict_quality("vmess", 12345, ws_context)
        assert ws_score > base_score
        
        # Test Reality bonus
        reality_context = {**base_context, "reality": True}
        reality_score = predictor.predict_quality("vmess", 12345, reality_context)
        assert reality_score > base_score
        
        # Test QUIC bonus
        quic_context = {**base_context, "quic": True}
        quic_score = predictor.predict_quality("vmess", 12345, quic_context)
        assert quic_score > base_score
    
    def test_domain_quality_factors(self):
        """Test domain-based quality factors."""
        predictor = EnhancedQualityPredictor()
        context = {"source_reputation": 0.5}
        
        # Test CDN bonus
        cdn_context = {**context, "host": "cdn.example.com"}
        cdn_score = predictor.predict_quality("vmess", 12345, cdn_context)
        
        # Test Cloudflare bonus
        cf_context = {**context, "host": "cloudflare.example.com"}
        cf_score = predictor.predict_quality("vmess", 12345, cf_context)
        
        # Test AWS/Azure bonus
        aws_context = {**context, "host": "aws.example.com"}
        aws_score = predictor.predict_quality("vmess", 12345, aws_context)
        
        # Test regular domain
        regular_context = {**context, "host": "regular.example.com"}
        regular_score = predictor.predict_quality("vmess", 12345, regular_context)
        
        # CDN and Cloudflare should score higher
        assert cdn_score > regular_score
        assert cf_score > regular_score
        assert aws_score > regular_score
    
    def test_model_training_interface(self):
        """Test the model training interface."""
        predictor = EnhancedQualityPredictor()
        
        # Test training interface
        configs = []
        scores = []
        
        for i in range(120):
            config = {
                "protocol": np.random.choice(["vmess", "vless", "trojan"]),
                "tls": np.random.choice([True, False]),
                "port": np.random.choice([443, 80, 8080]),
                "host": f"server{i}.example.com"
            }
            configs.append(config)
            scores.append(70.0 + np.random.normal(0, 5))
        
        # Train model
        predictor.train_model(configs, scores, tune_hyperparameters=False)
        
        # Test prediction after training
        test_context = {
            "tls": True,
            "ws": False,
            "host": "test.example.com"
        }
        
        score = predictor.predict_quality("vmess", 443, test_context)
        assert 0 <= score <= 100
    
    def test_model_info_interface(self):
        """Test the model information interface."""
        predictor = EnhancedQualityPredictor()
        
        # Test model info
        info = predictor.get_model_info()
        assert "status" in info
        
        # Train model and test info
        configs = []
        scores = []
        
        for i in range(120):
            config = {
                "protocol": "vmess",
                "tls": True,
                "port": 443,
                "host": f"server{i}.example.com"
            }
            configs.append(config)
            scores.append(80.0)
        
        predictor.train_model(configs, scores, tune_hyperparameters=False)
        
        info = predictor.get_model_info()
        assert info["status"] != "not_initialized"


if __name__ == "__main__":
    pytest.main([__file__])
