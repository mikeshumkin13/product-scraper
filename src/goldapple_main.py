from __future__ import annotations

import argparse
from typing import List
from parser.goldapple_search import search_goldapple, GAProduct
from utils.csv_export_ga import export_to_csv_goldapple

def build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Gold Apple — Парфюмерия → CSV")
    p.add_argument("--mode", choices=["real", "mock"], default="real", help="Режим: real|mock")
    p.add_argument("--slow", action="store_true", help="Human-задержки при Selenium-прокрутке")
    p.add_argument("--limit", type=int, default=100, help="Макс. карточек (safety-лимит)")
    p.add_argument("--output", type=str, default="goldapple_perfume.csv", help="Файл CSV")
    return p

def main() -> None:
    args = build_cli().parse_args()
    items: List[GAProduct] = search_goldapple(mode=args.mode, slow=args.slow, limit=args.limit)
    if not items:
        print("⚠️ Ничего не найдено.")
        return
    export_to_csv_goldapple(items, args.output)
    print(f"✅ Сохранено: {len(items)} товаров → {args.output}")

if __name__ == "__main__":
    main()




