"""
command-line entrypoint: optuna search, fine-tuning with champion promotion, and sentiment prediction.
"""

import argparse
import os
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from benchmark import MODEL_CHECKPOINT, predict_probs
import train


def main():
    parser = argparse.ArgumentParser(description="finbert lora fine-tuning with optuna and mlflow")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--search", action="store_true", help="run optuna trials and save best hyperparameters to best_params.json")
    action.add_argument("--train", action="store_true", help="fine-tune with best_params.json, evaluate on benchmark, promote if better than baseline")
    action.add_argument("--text", type=str, help="financial sentence or headline to classify with base and fine-tuned finbert")
    args = parser.parse_args()

    if args.search:
        train.search()
    elif args.train:
        train.train()
    else:
        # predict with base finbert, and with the fine-tuned model too if it exists
        model_paths = [MODEL_CHECKPOINT] + ([train.MODEL_DIR] if os.path.isdir(train.MODEL_DIR) else [])
        print(f"Text: {args.text}")
        for model_path in model_paths:
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSequenceClassification.from_pretrained(model_path)
            probs = predict_probs(model, tokenizer, [args.text])[0]
            label = model.config.id2label[int(probs.argmax())]
            print(f"{model_path}: {label} ({float(probs.max()):.2%})")


if __name__ == "__main__":
    main()
