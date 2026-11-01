"""
Optuna search for FinBERT LoRA fine-tuning, final fine-tuning from best_params.json, and MLflow champion promotion.
"""

import json
import tempfile
from datasets import load_dataset
import mlflow
from mlflow.tracking import MlflowClient
import numpy as np
import optuna
from peft import LoraConfig, TaskType, get_peft_model
from sklearn.metrics import accuracy_score, f1_score
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding, Trainer, TrainingArguments

from benchmark import BASELINE_FILE, MODEL_CHECKPOINT, evaluate_on_benchmark

DATASET_NAME = "KaiyuanLai/twitter-financial-news-sentiment"
# dataset label id -> finbert label id (finbert: 0 positive, 1 negative, 2 neutral)
# dataset labels: 0 bearish, 1 bullish, 2 neutral
LABEL_MAP = {0: 1, 1: 0, 2: 2}

N_TRIALS = 10
BEST_PARAMS_FILE = "best_params.json"
MODEL_DIR = "fine-tuned-finbert"
EXPERIMENT_NAME = "finbert-sentiment-lora"
REGISTERED_MODEL_NAME = "finbert-sentiment"

mlflow.set_tracking_uri("sqlite:///mlflow.db")


def search_space(trial):
    """optuna search space for training arguments and lora parameters"""
    return {
        "learning_rate": trial.suggest_float("learning_rate", 2e-5, 5e-4, log=True),
        "num_train_epochs": trial.suggest_int("num_train_epochs", 2, 6),
        "per_device_train_batch_size": trial.suggest_categorical("per_device_train_batch_size", [8, 16, 32]),
        "gradient_accumulation_steps": trial.suggest_categorical("gradient_accumulation_steps", [1, 2, 4]),
        "weight_decay": trial.suggest_float("weight_decay", 1e-4, 1e-1, log=True),
        "warmup_steps": trial.suggest_int("warmup_steps", 0, 50),
        "r": trial.suggest_categorical("r", [8, 16, 32]),
        "lora_alpha": trial.suggest_categorical("lora_alpha", [16, 32, 64]),
        "lora_dropout": trial.suggest_float("lora_dropout", 0.0, 0.3),
        "bias": trial.suggest_categorical("bias", ["none", "lora_only"]),
    }


def load_data():
    """load the training dataset, split off validation, tokenize and map labels to finbert ids"""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)
    ds = load_dataset(DATASET_NAME, split="train").train_test_split(test_size=0.25, seed=42)

    def preprocess(batch):
        out = tokenizer(batch["text"], truncation=True, max_length=128)
        out["label"] = [LABEL_MAP[label] for label in batch["label"]]
        return out

    ds = ds.map(preprocess, batched=True, remove_columns=ds["train"].column_names)
    return ds["train"], ds["test"], tokenizer


def compute_metrics(eval_pred):
    """validation metrics for the Trainer"""
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro"),
    }


def build_trainer(params, output_dir, train_ds, val_ds, tokenizer):
    """attach a lora adapter to base finbert and build a Trainer with the given hyperparameters"""
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        target_modules=["query", "value"],
        modules_to_save=["classifier"],
        r=params["r"],
        lora_alpha=params["lora_alpha"],
        lora_dropout=params["lora_dropout"],
        bias=params["bias"],
    )
    model = get_peft_model(AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT), lora_config)

    args = TrainingArguments(
        output_dir=output_dir,
        learning_rate=params["learning_rate"],
        num_train_epochs=params["num_train_epochs"],
        per_device_train_batch_size=params["per_device_train_batch_size"],
        gradient_accumulation_steps=params["gradient_accumulation_steps"],
        weight_decay=params["weight_decay"],
        warmup_steps=params["warmup_steps"],
        per_device_eval_batch_size=32,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        fp16=torch.cuda.is_available(),
        dataloader_pin_memory=torch.cuda.is_available(),
        report_to="none",
    )
    return Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )


def search(n_trials=N_TRIALS):
    """run optuna trials as nested mlflow runs and save the best hyperparameters to best_params.json"""
    mlflow.set_experiment(EXPERIMENT_NAME)
    train_ds, val_ds, tokenizer = load_data()

    def objective(trial):
        params = search_space(trial)
        print(f"\nTrial {trial.number + 1}/{n_trials}: {params}")
        # trial checkpoints go to a temp dir that is deleted when the trial ends
        with mlflow.start_run(run_name=f"trial_{trial.number}", nested=True), tempfile.TemporaryDirectory() as tmp_dir:
            mlflow.log_params(params)
            trainer = build_trainer(params, tmp_dir, train_ds, val_ds, tokenizer)
            trainer.train()
            metrics = trainer.evaluate()
            mlflow.log_metrics({k: metrics[k] for k in ("eval_f1_macro", "eval_accuracy", "eval_loss")})
            return metrics["eval_f1_macro"]

    with mlflow.start_run(run_name="optuna_search"):
        study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
        study.optimize(objective, n_trials=n_trials)
        mlflow.log_params({f"best_{k}": v for k, v in study.best_params.items()})
        mlflow.log_metric("best_eval_f1_macro", study.best_value)

    with open(BEST_PARAMS_FILE, "w") as f:
        json.dump(study.best_params, f, indent=2)
    print(f"Best trial (Macro F1 = {study.best_value:.4f}) saved to '{BEST_PARAMS_FILE}': {study.best_params}")


def train():
    """fine-tune base finbert with best_params.json, evaluate on the benchmark and promote to champion if it beats the baseline"""
    with open(BEST_PARAMS_FILE) as f:
        params = json.load(f)
    with open(BASELINE_FILE) as f:
        baseline_f1 = json.load(f)["metrics"]["f1_macro"]

    mlflow.set_experiment(EXPERIMENT_NAME)
    train_ds, val_ds, tokenizer = load_data()

    # per-epoch checkpoints go to a temp dir that is deleted after training, the final model is saved to MODEL_DIR
    with mlflow.start_run(run_name="finetune") as run, tempfile.TemporaryDirectory() as tmp_dir:
        mlflow.log_params(params)
        trainer = build_trainer(params, tmp_dir, train_ds, val_ds, tokenizer)
        trainer.train()

        # merge the lora weights into the base weights and save a standalone model
        model = trainer.model.merge_and_unload()
        model.save_pretrained(MODEL_DIR)
        tokenizer.save_pretrained(MODEL_DIR)
        mlflow.log_artifacts(MODEL_DIR, artifact_path="model")

        # evaluate on the marketaux benchmark, same as the baseline
        metrics = evaluate_on_benchmark(model, tokenizer)
        mlflow.log_metrics({f"bench_{k}": v for k, v in metrics.items()})
        finetuned_f1 = metrics["f1_macro"]

    # register every fine-tuned model, but only alias it as champion if it beats the baseline
    version = mlflow.register_model(f"{run.info.artifact_uri}/model", REGISTERED_MODEL_NAME)
    print(f"Baseline Macro F1: {baseline_f1:.4f} | Fine-tuned Macro F1: {finetuned_f1:.4f}")
    if finetuned_f1 > baseline_f1:
        MlflowClient().set_registered_model_alias(REGISTERED_MODEL_NAME, "champion", version.version)
        print(f"Promoted version {version.version} to champion.")
    else:
        print(f"Version {version.version} did not beat the baseline, not promoted.")
