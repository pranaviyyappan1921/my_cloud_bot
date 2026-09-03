import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()


def get_connection_string():
    connection_string = os.getenv("AZURE_SQL_CONNECTION_STRING")

    if not connection_string:
        raise RuntimeError(
            "AZURE_SQL_CONNECTION_STRING is not configured."
        )

    return connection_string


def get_engine():
    connection_string = get_connection_string()

    connection_url = (
        "mssql+pyodbc:///?odbc_connect="
        + quote_plus(connection_string)
    )

    return create_engine(
        connection_url,
        pool_pre_ping=True,
        connect_args={
            "timeout": 30
        }
    )


def check_connection():
    try:
        engine = get_engine()

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception as e:
        print(f"Azure SQL connection error: {e}")
        return False