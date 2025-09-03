#!/usr/bin/env python3
"""
ML Model Training Pipeline for VPN Configuration Quality Scoring
Trains and deploys production models for configuration quality assessment.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import joblib

# Import with fallbacks for missing modules
try:
    from vpn_merger.ml.quality_predictor_enhanced import EnhancedConfigQualityPredictor
except ImportError:
    EnhancedConfigQualityPredictor = None

try:
    from vpn_merger.core.processor import ConfigProcessor
except ImportError:
    ConfigProcessor = None

try:
    from vpn_merger.monitoring.metrics_collector import MetricsCollector
except ImportError:
    MetricsCollector = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLModelTrainer:
    """Train and deploy ML models for VPN configuration quality scoring."""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)

        # Initialize metrics collector with fallback
        if MetricsCollector:
            self.metrics = MetricsCollector()
        else:
            self.metrics = None

        # Model configurations
        self.models = {
            "random_forest": RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42
            ),
        }

        self.scaler = StandardScaler()

    async def collect_training_data(self, config_files: list[str]) -> pd.DataFrame:
        """Collect training data from configuration files."""
        logger.info("Collecting training data...")

        # Initialize processor with fallback
        processor = ConfigProcessor() if ConfigProcessor else None
        all_features = []
        all_scores = []

        for config_file in config_files:
            try:
                # Load configurations
                with open(config_file, encoding="utf-8") as f:
                    configs = f.read().splitlines()

                # Process each configuration
                for config in configs:
                    if not config.strip():
                        continue

                    try:
                        # Extract features
                        features = await self.extract_features(config)
                        if features:
                            all_features.append(features)

                            # Generate quality score (simulated for training)
                            score = self.generate_quality_score(config, features)
                            all_scores.append(score)

                    except Exception as e:
                        logger.warning(f"Error processing config: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error reading config file {config_file}: {e}")
                continue

        # Create DataFrame
        if all_features:
            df = pd.DataFrame(all_features)
            df["quality_score"] = all_scores
            logger.info(f"Collected {len(df)} training samples")
            return df
        else:
            raise ValueError("No training data collected")

    async def extract_features(self, config: str) -> dict[str, Any]:
        """Extract features from a VPN configuration."""
        features = {}

        try:
            # Basic features
            features["config_length"] = len(config)
            features["has_vmess"] = 1 if "vmess://" in config else 0
            features["has_vless"] = 1 if "vless://" in config else 0
            features["has_trojan"] = 1 if "trojan://" in config else 0
            features["has_ss"] = 1 if "ss://" in config else 0
            features["has_ssr"] = 1 if "ssr://" in config else 0
            features["has_hysteria"] = 1 if "hysteria://" in config else 0
            features["has_tuic"] = 1 if "tuic://" in config else 0

            # Protocol-specific features
            if "vmess://" in config:
                features["vmess_has_tls"] = 1 if "tls" in config.lower() else 0
                features["vmess_has_ws"] = 1 if "ws" in config.lower() else 0
                features["vmess_has_grpc"] = 1 if "grpc" in config.lower() else 0
            else:
                features["vmess_has_tls"] = 0
                features["vmess_has_ws"] = 0
                features["vmess_has_grpc"] = 0

            if "vless://" in config:
                features["vless_has_reality"] = 1 if "reality" in config.lower() else 0
                features["vless_has_xtls"] = 1 if "xtls" in config.lower() else 0
            else:
                features["vless_has_reality"] = 0
                features["vless_has_xtls"] = 0

            # Network features
            features["has_ipv4"] = (
                1 if any(char.isdigit() and "." in config for char in config) else 0
            )
            features["has_ipv6"] = 1 if ":" in config and "://" not in config else 0
            features["has_domain"] = (
                1 if any(word.isalpha() and "." in word for word in config.split()) else 0
            )

            # Port features
            import re

            port_match = re.search(r":(\d+)", config)
            if port_match:
                port = int(port_match.group(1))
                features["port"] = port
                features["is_common_port"] = 1 if port in [80, 443, 8080, 8443] else 0
            else:
                features["port"] = 0
                features["is_common_port"] = 0

            # Security features
            features["has_encryption"] = (
                1 if any(enc in config.lower() for enc in ["aes", "chacha20", "none"]) else 0
            )
            features["has_obfs"] = 1 if "obfs" in config.lower() else 0
            features["has_plugin"] = 1 if "plugin" in config.lower() else 0

            # Performance features
            features["has_mux"] = 1 if "mux" in config.lower() else 0
            features["has_fragment"] = 1 if "fragment" in config.lower() else 0
            features["has_padding"] = 1 if "padding" in config.lower() else 0

            # Quality indicators
            features["has_uuid"] = (
                1
                if re.search(
                    r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", config
                )
                else 0
            )
            features["has_base64"] = 1 if re.search(r"[A-Za-z0-9+/]{20,}={0,2}", config) else 0

            # Complexity features
            features["special_chars"] = len(
                [c for c in config if c in "!@#$%^&*()_+-=[]{}|;:,.<>?"]
            )
            features["uppercase_ratio"] = (
                sum(1 for c in config if c.isupper()) / len(config) if config else 0
            )
            features["digit_ratio"] = (
                sum(1 for c in config if c.isdigit()) / len(config) if config else 0
            )

            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None

    def generate_quality_score(self, config: str, features: dict[str, Any]) -> float:
        """Generate quality score for training data."""
        score = 0.5  # Base score

        # Protocol scoring
        if features.get("has_vless", 0):
            score += 0.2
        if features.get("has_vmess", 0):
            score += 0.15
        if features.get("has_trojan", 0):
            score += 0.1

        # Security scoring
        if features.get("has_tls", 0):
            score += 0.1
        if features.get("has_encryption", 0):
            score += 0.05

        # Performance scoring
        if features.get("has_mux", 0):
            score += 0.05
        if features.get("is_common_port", 0):
            score += 0.05

        # Quality indicators
        if features.get("has_uuid", 0):
            score += 0.05
        if features.get("has_base64", 0):
            score += 0.05

        # Penalize overly complex configs
        if features.get("special_chars", 0) > 10:
            score -= 0.1

        return min(max(score, 0.0), 1.0)

    def prepare_training_data(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        """Prepare training data for ML models."""
        # Select feature columns
        feature_columns = [col for col in df.columns if col != "quality_score"]
        X = df[feature_columns].values
        y = df["quality_score"].values

        # Handle missing values
        X = np.nan_to_num(X, nan=0.0)

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        return X_scaled, y

    def train_models(self, X: np.ndarray, y: np.ndarray) -> dict[str, Any]:
        """Train ML models and evaluate performance."""
        logger.info("Training ML models...")

        results = {}

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        for name, model in self.models.items():
            logger.info(f"Training {name}...")

            # Train model
            model.fit(X_train, y_train)

            # Make predictions
            y_pred = model.predict(X_test)

            # Evaluate performance
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            # Cross-validation
            cv_scores = cross_val_score(model, X, y, cv=5, scoring="r2")

            results[name] = {
                "model": model,
                "mse": mse,
                "r2": r2,
                "cv_mean": cv_scores.mean(),
                "cv_std": cv_scores.std(),
                "feature_importance": (
                    self.get_feature_importance(model)
                    if hasattr(model, "feature_importances_")
                    else None
                ),
            }

            logger.info(
                f"{name} - MSE: {mse:.4f}, R²: {r2:.4f}, CV: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}"
            )

        return results

    def get_feature_importance(self, model) -> dict[str, float]:
        """Get feature importance from trained model."""
        if hasattr(model, "feature_importances_"):
            feature_names = [
                "config_length",
                "has_vmess",
                "has_vless",
                "has_trojan",
                "has_ss",
                "has_ssr",
                "has_hysteria",
                "has_tuic",
                "vmess_has_tls",
                "vmess_has_ws",
                "vmess_has_grpc",
                "vless_has_reality",
                "vless_has_xtls",
                "has_ipv4",
                "has_ipv6",
                "has_domain",
                "port",
                "is_common_port",
                "has_encryption",
                "has_obfs",
                "has_plugin",
                "has_mux",
                "has_fragment",
                "has_padding",
                "has_uuid",
                "has_base64",
                "special_chars",
                "uppercase_ratio",
                "digit_ratio",
            ]
            return dict(zip(feature_names, model.feature_importances_, strict=False))
        return {}

    def save_models(self, results: dict[str, Any]):
        """Save trained models and metadata."""
        logger.info("Saving models...")

        # Save models
        for name, result in results.items():
            model_path = self.models_dir / f"{name}_v1.joblib"
            joblib.dump(result["model"], model_path)
            logger.info(f"Saved {name} to {model_path}")

        # Save scaler
        scaler_path = self.models_dir / "scaler_v1.joblib"
        joblib.dump(self.scaler, scaler_path)
        logger.info(f"Saved scaler to {scaler_path}")

        # Save metadata
        metadata = {
            "version": "1.0",
            "training_date": pd.Timestamp.now().isoformat(),
            "models": {
                name: {
                    "mse": result["mse"],
                    "r2": result["r2"],
                    "cv_mean": result["cv_mean"],
                    "cv_std": result["cv_std"],
                    "feature_importance": result["feature_importance"],
                }
                for name, result in results.items()
            },
            "feature_count": (
                len(self.scaler.get_feature_names_out())
                if hasattr(self.scaler, "get_feature_names_out")
                else 28
            ),
        }

        metadata_path = self.models_dir / "model_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")

    async def deploy_models(self):
        """Deploy trained models to production."""
        logger.info("Deploying models to production...")

        # Create production predictor with fallback
        if not EnhancedConfigQualityPredictor:
            logger.warning("EnhancedConfigQualityPredictor not available, skipping deployment")
            return

        predictor = EnhancedConfigQualityPredictor()

        # Load best model
        best_model_path = self.models_dir / "gradient_boosting_v1.joblib"
        if best_model_path.exists():
            model = joblib.load(best_model_path)
            predictor.model = model

            # Load scaler
            scaler_path = self.models_dir / "scaler_v1.joblib"
            if scaler_path.exists():
                scaler = joblib.load(scaler_path)
                predictor.scaler = scaler

            # Save production predictor
            prod_path = self.models_dir / "production_predictor_v1.joblib"
            joblib.dump(predictor, prod_path)
            logger.info(f"Deployed production predictor to {prod_path}")
        else:
            logger.error("Best model not found for deployment")

    async def run_training_pipeline(self, config_files: list[str]):
        """Run complete ML training pipeline."""
        try:
            # Collect training data
            df = await self.collect_training_data(config_files)

            # Prepare data
            X, y = self.prepare_training_data(df)

            # Train models
            results = self.train_models(X, y)

            # Save models
            self.save_models(results)

            # Deploy to production
            await self.deploy_models()

            logger.info("ML training pipeline completed successfully!")

            # Record metrics if available
            if self.metrics:
                best_model = max(results.keys(), key=lambda k: results[k]["r2"])
                try:
                    self.metrics.record_ml_training(
                        model_name=best_model,
                        r2_score=results[best_model]["r2"],
                        mse=results[best_model]["mse"],
                    )
                except Exception as e:
                    logger.warning(f"Failed to record metrics: {e}")

        except Exception as e:
            logger.error(f"ML training pipeline failed: {e}")
            raise


async def main():
    """Main training function."""
    # Configuration files to use for training
    config_files = []

    # Check for available config files
    potential_files = [
        "output/vpn_subscription_raw.txt",
        "output_test_quick/vpn_subscription_raw.txt",
        "output/vpn_subscription_base64.txt",
    ]

    for file_path in potential_files:
        if Path(file_path).exists():
            config_files.append(file_path)
            logger.info(f"Found config file: {file_path}")

    if not config_files:
        logger.error("No configuration files found for training")
        logger.info("Please run the VPN merger first to generate configuration files")
        return

    # Initialize trainer
    trainer = MLModelTrainer()

    # Run training pipeline
    await trainer.run_training_pipeline(config_files)


if __name__ == "__main__":
    asyncio.run(main())
