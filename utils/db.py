import os

from sqlalchemy import create_engine, text
import pandas as pd

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "123456"),
    "database": os.getenv("MYSQL_DATABASE", "agentic_bi_olist"),
}

DATABASE_URL = (
    f"mysql+pymysql://"
    f"{DB_CONFIG['user']}:{DB_CONFIG['password']}"
    f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
    f"/{DB_CONFIG['database']}"
)

engine = create_engine(DATABASE_URL)


def run_query(sql):
    df = pd.read_sql(sql, engine)
    return df


def execute_sql(sql):
    with engine.begin() as conn:
        conn.execute(text(sql))
