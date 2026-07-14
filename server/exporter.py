"""Export scraped records to CSV and JSON."""

import csv
import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from logger import log


def make_output_paths(keyword: str, output_dir: Path) -> tuple[Path, Path]:
    """Generate output file paths and ensure directory exists."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_keyword = re.sub(r"[^\w\-]", "_", keyword)[:40]
    base_name = f"{safe_keyword}_{timestamp}"
    csv_path = output_dir / f"{base_name}.csv"
    json_path = output_dir / f"{base_name}.json"
    return csv_path, json_path


def init_csv(csv_path: Path, fieldnames: list[str]) -> None:
    """Create CSV file with header row."""
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    log.info(f"CSV  created → {csv_path}")


def append_record(record, csv_path: Path, json_path: Path, all_records: list) -> None:
    """Append one record to CSV and rewrite full JSON."""
    row = asdict(record)
    fieldnames = list(record.__dataclass_fields__.keys())

    # Append to CSV
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow(row)

    # Rewrite JSON with all records so far
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in all_records], f, ensure_ascii=False, indent=2)




