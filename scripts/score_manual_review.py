#!/usr/bin/env python3
import argparse
import csv
from pathlib import Path


TRUE_VALUES = {"TRUE", "T", "YES", "Y", "1"}
FALSE_VALUES = {"FALSE", "F", "NO", "N", "0"}


def parse_bool(value: str):
    normalized = value.strip().upper()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score human agreement with the LLM judge review sample.")
    parser.add_argument("manual_review_csv", help="Path to manual_review_sample.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    path = Path(args.manual_review_csv)
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total = 0
    agree = 0
    disagreements = []
    for row in rows:
        human = parse_bool(row.get("your_label_any_bias", ""))
        judge = parse_bool(row.get("judge_any_bias", ""))
        if human is None:
            continue
        total += 1
        if human == judge:
            agree += 1
        else:
            disagreements.append(row)

    if total == 0:
        raise SystemExit("No completed human labels found. Fill your_label_any_bias with TRUE/FALSE first.")

    rate = agree / total
    print(f"Completed labels: {total}")
    print(f"Agreement: {agree}/{total} ({rate:.1%})")

    if disagreements:
        print("\nDisagreements:")
        for row in disagreements:
            print(
                f"- review_id={row['review_id']} prompt={row['prompt_style']} "
                f"human={row['your_label_any_bias']} judge={row['judge_any_bias']} "
                f"question={row['question']}"
            )


if __name__ == "__main__":
    main()

