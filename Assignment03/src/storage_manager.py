import json
from pathlib import Path

DATA_DIR = Path("data/btc_prices")


class LocalStorageManager:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def upload_data(self, curr_data):
        timestamp = curr_data["timestamp_utc"][:19]
        # timestamp_utc gives '2026-10-23T01:49:11.529180+00:00'
        # [:19] gives 2026-10-23T01:49:11; tryna keep file names cleaner
        file_path = self.data_dir / f"{timestamp}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(curr_data, f, indent=2)

    def get_price_history(self, steps=7):
        # get all saved JSON files from the data directory
        all_files = list(self.data_dir.glob("*.json"))

        # sort files based on timestamp with newest first
        sorted_files = sorted(all_files, key=lambda file: file.name, reverse=True)
        reqd_files = sorted_files[:steps]

        price_records = []
        for file in reqd_files:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                price_records.append(data)

        return price_records
