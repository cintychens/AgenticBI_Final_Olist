from pathlib import Path

from utils.db import execute_sql


SQL_FILE = Path(__file__).with_name("preaggregation_views.sql")


def refresh_preaggregation_views():
    sql_text = SQL_FILE.read_text(encoding="utf-8")
    statements = [statement.strip() for statement in sql_text.split(";") if statement.strip()]

    for statement in statements:
        execute_sql(statement)

    return len(statements)


if __name__ == "__main__":
    count = refresh_preaggregation_views()
    print(f"预聚合视图刷新完成，共执行 {count} 条 SQL。")
