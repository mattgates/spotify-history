"""
Module with functions for database access capabilities.
Contributor: Matt Gates
"""

import os

# Library Imports
import pandas as pd
import sqlalchemy
from dotenv import load_dotenv

# Static Global Variables
load_dotenv()
ENGINE = sqlalchemy.create_engine(
    f"mysql+pymysql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}/{os.environ.get('DB_NAME')} "
)


def df_to_database(df: pd.DataFrame, table: str, if_exists: str) -> None:
    """
    Connects to a local MySQL database and stores a DataFrame as a table.
    :param df: DataFrame to be stored.
    :param table: Table to place df in.
    :param if_exists: Action to take it the table already exists: ('fail', 'replace', 'append').
    """
    df.to_sql(name=table, con=ENGINE, if_exists=if_exists, index=False)


def run_query(query: str) -> pd.DataFrame:
    """
    Runs a SQL query and returns a DataFrame.
    :param query: SQL query string to perform.
    :return: DataFrame of SQL query results.
    """
    result = pd.read_sql(query, ENGINE)

    return result


def main():
    pass


if __name__ == "__main__":
    main()
