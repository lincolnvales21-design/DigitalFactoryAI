import os
import re
import sqlite3


DATABASE_NAME = "digitalfactory.db"
DATABASE_URL = os.getenv("DATABASE_URL")


class PostgresCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def execute(self, query, params=None):
        query = re.sub(r"\?", "%s", query)

        # PostgreSQL não aceita lastrowid.
        # Para INSERTs sem RETURNING, adicionamos RETURNING id
        # quando a tabela possui coluna id e o código precisa do ID.
        if (
            query.lstrip().upper().startswith("INSERT INTO")
            and "RETURNING" not in query.upper()
            and re.search(r"\bINTO\s+(orders|payments|products)\b", query, re.I)
        ):
            query = query.rstrip().rstrip(";") + " RETURNING id"

        self._cursor.execute(query, params)

        if "RETURNING id" in query.upper():
            row = self._cursor.fetchone()
            self.lastrowid = row[0] if row else None

        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class PostgresConnection:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self):
        return PostgresCursor(self._connection.cursor())

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


def get_connection():
    """
    Banco principal do DigitalFactoryAI.

    Produção/Replit:
        PostgreSQL via DATABASE_URL.

    Desenvolvimento local sem DATABASE_URL:
        SQLite como fallback.
    """

    if DATABASE_URL:
        import psycopg

        connection = psycopg.connect(DATABASE_URL)
        return PostgresConnection(connection)

    return sqlite3.connect(DATABASE_NAME)
