"""
Module to ingest, clean, and store the results of a Spotify "Extended streaming" history export.
Contributor: Matt Gates
"""

import datetime as datetime

# Library Imports
import glob
import json

import pandas as pd

# Repository Imports
import database

# Global Variables
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def load_json(json_folder_path: str) -> pd.DataFrame:
    """
    Reads all the endsong json files associated with the "Extended Streaming History" export from Spotify. Lumps the
    data into a dataframe, sorts chronologically, removes podcast listening, and places the data in a database.
    :param json_folder_path: String containing folder path with Extended Streaming History json files.
    :return: DataFrame of Spotify listening history.
    """
    history_df = pd.DataFrame()
    for file_name in glob.glob(json_folder_path):
        with open(file_name) as json_file:
            new_data = json.load(json_file)
            history_df = pd.concat(
                [history_df, pd.DataFrame(new_data)], ignore_index=True
            )

    history_df.dropna(subset=["spotify_track_uri"], inplace=True)

    history_df["track_id"] = history_df["spotify_track_uri"].apply(
        lambda x: x.split(":")[2]
    )

    history_df.sort_values(by="ts", axis=0, inplace=True)
    history_df.drop(
        columns=[
            "episode_name",
            "episode_show_name",
            "spotify_episode_uri",
            "spotify_track_uri",
        ],
        inplace=True,
    )

    database.df_to_database(history_df, "raw_history", "replace")

    return history_df


def clean_history(history_df: pd.DataFrame) -> None:
    """
    Takes the output of load_json() and cleans the data before putting it in the same database.
    :param history_df: DataFrame output of load_json()
    """

    # Converts the dates to ET and adds additional attributes for simplified querying
    history_df["datetime"] = history_df.apply(
        lambda x: datetime.datetime.strptime(x["ts"], TS_FORMAT), axis=1
    )

    history_df["datetime"] = history_df["datetime"].dt.tz_localize("UTC")
    history_df["datetime"] = history_df["datetime"].dt.tz_convert("US/Eastern")

    history_df["stream_date"] = history_df.apply(lambda x: x["datetime"].date(), axis=1)
    history_df["stream_time"] = history_df.apply(lambda x: x["datetime"].time(), axis=1)
    history_df["stream_year"] = history_df.apply(
        lambda x: x["datetime"].date().year, axis=1
    )
    history_df["stream_month"] = history_df.apply(
        lambda x: x["datetime"].date().month, axis=1
    )
    history_df["stream_day"] = history_df.apply(
        lambda x: x["datetime"].date().day, axis=1
    )

    # Remove unnecessary columns for analysis
    history_df.drop(
        columns=[
            "ts",
            "username",
            "conn_country",
            "ip_addr_decrypted",
            "user_agent_decrypted",
            "offline",
            "skipped",
            "offline_timestamp",
            "incognito_mode",
        ],
        inplace=True,
    )

    # Standardize platforms with simplified names.
    platform_replace = [
        ("iPhone", "iPhone"),
        ("Laptop", "OS X"),
        ("Laptop", "osx"),
        ("Laptop", "Windows"),
        ("TV", "samsung"),
        ("Sonos", "sonos"),
    ]

    for item in platform_replace:
        history_df["platform"] = history_df["platform"].apply(
            lambda x: item[0] if item[1] in x else x
        )

    database.df_to_database(history_df, "clean_history", "replace")


def main():
    pass


if __name__ == "__main__":
    main()
