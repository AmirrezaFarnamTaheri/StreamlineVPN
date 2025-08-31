#!/usr/bin/env python3
"""
Training script for VPN Configuration Analysis Model

This script fine-tunes a transformer model to analyze and score VPN configurations.
"""

import argparse
import logging
import yaml
import json
from pathlib import Path
from typing import Dict, Any
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    TrainingArguments, 
    Trainer
)
from datasets import Dataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, mean_squared_error


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load model configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_data(data_path: str) -> Dataset:
    """Load training data from JSON file."""
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Convert to Dataset format
    texts = [item['config'] for item in data]
    labels = [item['quality_score'] for item in data]
    
    return Dataset.from_dict({
        'text': texts,
        'label': labels
    })


def compute_metrics(pred):
    """Compute evaluation metrics."""
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description='Train VPN configuration analysis model')
    parser.add_argument('--config', type=str, default='configs/model_config.yaml',
                       help='Path to model configuration file')
    parser.add_argument('--output_dir', type=str, default='models/',
                       help='Output directory for trained model')
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info("Starting model training...")
    
    # Load configuration
    config = load_config(args.config)
    logger.info(f"Loaded configuration: {config['model']['name']}")
    
    # Load data
    train_dataset = load_data(config['data']['train_file'])
    val_dataset = load_data(config['data']['validation_file'])
    logger.info(f"Loaded {len(train_dataset)} training samples and {len(val_dataset)} validation samples")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(config['model']['base_model'])
    model = AutoModelForSequenceClassification.from_pretrained(
        config['model']['base_model'],
        num_labels=2  # Binary classification: good/bad quality
    )
    
    # Tokenize datasets
    def tokenize_function(examples):
        return tokenizer(examples['text'], padding='max_length', truncation=True, max_length=config['data']['max_length'])
    
    train_dataset = train_dataset.map(tokenize_function, batched=True)
    val_dataset = val_dataset.map(tokenize_function, batched=True)
    
    # Setup training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=config['training']['epochs'],
        per_device_train_batch_size=config['training']['batch_size'],
        per_device_eval_batch_size=config['training']['batch_size'],
        learning_rate=config['training']['learning_rate'],
        warmup_steps=config['training']['warmup_steps'],
        weight_decay=config['training']['weight_decay'],
        logging_dir=f"{args.output_dir}/logs",
        logging_steps=100,
        evaluation_strategy="steps",
        eval_steps=500,
        save_steps=config['output']['save_frequency'],
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
    )
    
    # Initialize trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )
    
    # Train model
    logger.info("Starting training...")
    trainer.train()
    
    # Save model and tokenizer
    model_path = Path(args.output_dir) / "final_model"
    model_path.mkdir(parents=True, exist_ok=True)
    
    trainer.save_model(str(model_path))
    tokenizer.save_pretrained(str(model_path))
    
    logger.info(f"Training completed! Model saved to {model_path}")
    
    # Evaluate on test set
    test_dataset = load_data(config['data']['test_file'])
    test_dataset = test_dataset.map(tokenize_function, batched=True)
    
    results = trainer.evaluate(test_dataset)
    logger.info(f"Test results: {results}")


if __name__ == "__main__":
    main()
