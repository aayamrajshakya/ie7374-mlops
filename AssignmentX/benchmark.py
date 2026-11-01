"""
Marketaux benchmark harvesting and zero-leakage baseline evaluation.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import httpx
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

load_dotenv()

API_KEY = os.getenv("MARKETAUX_API_KEY", "")
TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA"]
PARQUET_FILE = "marketaux_data.parquet"
BASELINE_FILE = "baseline.json"
MODEL_CHECKPOINT = "ProsusAI/finbert"


def harvest_news(pages=1, output_path=PARQUET_FILE):
    """harvest news articles from Marketaux API and save to parquet"""
    if not API_KEY:
        sys.exit("Error: Marketaux API key is not set")

    rows = []
    print(f"Starting harvest for {pages} page(s)...", flush=True)

    for page in range(1, pages + 1):
        print(f"  Fetching page {page}/{pages}...", flush=True)
        params = {
            "api_token": API_KEY,
            "symbols": ",".join(TICKERS),
            "filter_entities": "true",
            "countries": "us",
            "group_similar": "false",
            "language": "en",
            "limit": 3,
            "page": page,
        }
        try:
            resp = httpx.get("https://api.marketaux.com/v1/news/all", params=params, timeout=30.0)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"API notice ({e.response.status_code}): Stopping and saving records gathered so far.")
            break
        except Exception as e:
            print(f"Request failed: {e}. Stopping.")
            break

        for article in resp.json().get("data", []):
            desc = (article.get("description") or "").strip()
            uuid = article.get("uuid", "")
            for ent in article.get("entities", []):
                sym = ent.get("symbol")
                score = ent.get("sentiment_score")
                if sym in TICKERS and score is not None:
                    rows.append({
                        "symbol": sym,
                        "sentiment_score": float(score),
                        "description": desc,
                        "uuid": uuid,
                    })

        if page < pages:
            time.sleep(1)

    if not rows:
        print("No new matching ticker data found.")
        return

    new_df = pd.DataFrame(rows)
    if os.path.exists(output_path):
        existing_df = pd.read_parquet(output_path)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        new_df = combined.drop_duplicates(subset=["symbol", "uuid"], keep="last")
        added = len(new_df) - len(existing_df)
    else:
        added = len(new_df)

    new_df.to_parquet(output_path, index=False)
    print(f"Added {added} new record(s). Total records in {output_path}: {len(new_df)}")


def score_to_sentiment(score, threshold=0.15):
    """convert continuous float (-1.0 to 1.0) to sentiment label string"""
    if score is None:
        return "neutral"
    if score > threshold:
        return "positive"
    if score < -threshold:
        return "negative"
    return "neutral"


def predict_probs(model, tokenizer, texts, batch_size=32, max_length=128):
    """batched softmax probabilities for a list of texts, shape (len(texts), num_labels)"""
    model.eval()
    probs = []
    with torch.inference_mode():
        for i in range(0, len(texts), batch_size):
            inputs = tokenizer(
                texts[i : i + batch_size],
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            ).to(model.device)
            probs.append(model(**inputs).logits.softmax(dim=-1).cpu())
    return torch.cat(probs)


def evaluate_on_benchmark(model, tokenizer, parquet_path=PARQUET_FILE):
    """zero-leakage inference: model receives only descriptions without sentiment scores"""
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"'{parquet_path}' does not exist! Run harvest first.")

    df = pd.read_parquet(parquet_path)
    ground_truth = [score_to_sentiment(s) for s in df["sentiment_score"]]

    model.to("cuda" if torch.cuda.is_available() else "cpu")
    pred_ids = predict_probs(model, tokenizer, df["description"].tolist()).argmax(dim=-1).tolist()
    preds = [model.config.id2label[i] for i in pred_ids]

    precision, recall, f1, _ = precision_recall_fscore_support(ground_truth, preds, average="macro", zero_division=0)
    metrics = {
        "accuracy": accuracy_score(ground_truth, preds),
        "f1_macro": f1,
        "f1_weighted": f1_score(ground_truth, preds, average="weighted", zero_division=0),
        "precision_macro": precision,
        "recall_macro": recall,
    }
    return {**{k: round(float(v), 4) for k, v in metrics.items()}, "total_samples": len(df)}


def run_baseline_evaluation(output_path=BASELINE_FILE, parquet_path=PARQUET_FILE):
    """evaluate base FinBERT on benchmark parquet and save metrics to baseline.json"""
    print(f"Loading Base FinBERT from '{MODEL_CHECKPOINT}'...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT)

    print(f"Evaluating on '{parquet_path}' (zero-leakage)...")
    metrics = evaluate_on_benchmark(model=model, tokenizer=tokenizer, parquet_path=parquet_path)

    payload = {
        "model_checkpoint": MODEL_CHECKPOINT,
        "benchmark_dataset": parquet_path,
        "metrics": metrics,
    }
    Path(output_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Saved baseline metrics to '{output_path}':")
    print(json.dumps(metrics, indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Marketaux benchmark harvesting and baseline evaluation")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--harvest", nargs="?", const=1, type=int, metavar="PAGES", help="harvest fresh news from Marketaux API (optional: number of pages, default: 1)")
    action.add_argument("--baseline", action="store_true", help="evaluate base FinBERT on benchmark")
    args = parser.parse_args()

    if args.harvest is not None:
        harvest_news(pages=max(1, args.harvest))
    else:
        run_baseline_evaluation()
