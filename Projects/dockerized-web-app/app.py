import os
import time

import psycopg
from flask import Flask
from psycopg.errors import OperationalError
from psycopg.rows import dict_row

app = Flask(__name__)
DATABASE_CONFIG = {
    "host": os.environ.get("DB_HOST", "db"),
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
}


def connect_with_retry():
    for attempt in range(10):
        try:
            return psycopg.connect(**DATABASE_CONFIG, row_factory=dict_row)
        except OperationalError:
            if attempt == 9:
                raise
            time.sleep(2)


def initialize_database():
    with connect_with_retry() as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS page_visits "
            "(id INTEGER PRIMARY KEY, visits INTEGER NOT NULL)"
        )
        connection.execute(
            "INSERT INTO page_visits (id, visits) VALUES (1, 0) "
            "ON CONFLICT (id) DO NOTHING"
        )


@app.get("/")
def home():
    with connect_with_retry() as connection:
        row = connection.execute(
            "UPDATE page_visits SET visits = visits + 1 WHERE id = 1 "
            "RETURNING visits"
        ).fetchone()
    return (
        "<!doctype html><html><head><title>Docker Compose Demo</title></head>"
        "<body><h1>Hello from a container!</h1>"
        f"<p>Page visits recorded in PostgreSQL: {row['visits']}</p></body></html>"
    )


@app.get("/health")
def health():
    try:
        with connect_with_retry() as connection:
            connection.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}, 200
    except OperationalError:
        return {"status": "error", "database": "unavailable"}, 503


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000)
