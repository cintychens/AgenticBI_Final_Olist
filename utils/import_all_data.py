import argparse
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.db import engine

CSV_TABLE_MAP = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "product_category_name_translation": "product_category_name_translation.csv",
}


def load_csv_to_mysql(table_name, csv_file, if_exists):
    file_path = DATA_DIR / csv_file
    df = pd.read_csv(file_path)

    df.to_sql(
        name=table_name,
        con=engine,
        if_exists=if_exists,
        index=False,
    )

    print(f"{table_name}: 已导入 {len(df):,} 行，来源文件：{csv_file}")


def import_all_data(if_exists):
    for table_name, csv_file in CSV_TABLE_MAP.items():
        load_csv_to_mysql(table_name, csv_file, if_exists)


def preview_files():
    print("当前脚本会将 data/ 目录下的 CSV 文件导入 MySQL：")
    for table_name, csv_file in CSV_TABLE_MAP.items():
        file_path = DATA_DIR / csv_file
        status = "存在" if file_path.exists() else "缺失"
        print(f"- {csv_file} -> {table_name} [{status}]")


def parse_args():
    parser = argparse.ArgumentParser(description="将 Olist CSV 数据导入 MySQL。")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--replace", action="store_true", help="覆盖并重建数据库中的同名表。")
    mode.add_argument("--append", action="store_true", help="追加写入数据库中的同名表。")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.replace:
        import_all_data(if_exists="replace")
    elif args.append:
        import_all_data(if_exists="append")
    else:
        preview_files()
        print("\n安全提示：默认不会写入数据库。")
        print("如需覆盖导入，请运行：python utils/import_all_data.py --replace")
        print("如需追加导入，请运行：python utils/import_all_data.py --append")
