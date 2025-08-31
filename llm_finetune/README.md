# LLM Fine-tuning for VPN Subscription Merger

This directory contains utilities and configurations for fine-tuning Large Language Models (LLMs) to enhance the VPN subscription merger functionality.

## Overview

The LLM fine-tuning component is designed to improve:
- Configuration parsing accuracy
- Protocol detection
- Quality scoring algorithms
- Threat detection capabilities

## Features

- **Model Training**: Fine-tune models on VPN configuration data
- **Data Preparation**: Preprocess and clean training datasets
- **Evaluation**: Assess model performance on validation sets
- **Deployment**: Integrate trained models into the main merger

## Directory Structure

```
llm_finetune/
├── README.md              # This file
├── data/                  # Training and validation datasets
├── models/                # Trained model artifacts
├── scripts/               # Training and evaluation scripts
├── configs/               # Model configuration files
└── notebooks/             # Jupyter notebooks for experimentation
```

## Usage

### Prerequisites

```bash
pip install torch transformers datasets scikit-learn
```

### Training a Model

```bash
python scripts/train_model.py --config configs/model_config.yaml
```

### Evaluating a Model

```bash
python scripts/evaluate_model.py --model_path models/best_model
```

## Configuration

Model configurations are stored in YAML format and include:
- Model architecture parameters
- Training hyperparameters
- Data preprocessing settings
- Evaluation metrics

## Integration

Trained models can be integrated into the main VPN merger by:
1. Loading the model in the ConfigProcessor class
2. Using model predictions for quality scoring
3. Enhancing protocol detection accuracy

## Contributing

When adding new models or configurations:
1. Update the configuration documentation
2. Add appropriate tests
3. Include performance benchmarks
4. Document integration steps

## License

This component follows the same license as the main project.
