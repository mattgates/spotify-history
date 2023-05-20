"""
Module to interface with the Spotify API.
Contributor: Matt Gates
"""


import math
import os

# Library Imports
import pandas as pd
import requests
from dotenv import load_dotenv

# Repository Imports
import database

# Static Global Variables
BASE_URL = "https://api.spotify.com/v1/"


def authorize_spotify_api():
    load_dotenv()
    auth_response = requests.post(
        "https://accounts.spotify.com/api/token",
        {
            "grant_type": "client_credentials",
            "client_id": os.environ.get("CLIENT_ID"),
            "client_secret": os.environ.get("CLIENT_SECRET"),
        },
    )

    auth_response_data = auth_response.json()

    access_token = auth_response_data["access_token"]

    return {"Authorization": f"Bearer {access_token}"}


def get_albums(headers):
    """
    https://developer.spotify.com/documentation/web-api/reference/#/operations/get-multiple-albums
    """
    query = """
    SELECT SUM(clean_history.ms_played) as ms_played,
        tracks.album_id
    FROM clean_history
    JOIN tracks
    ON clean_history.track_id = tracks.track_id
    GROUP BY tracks.album_id
    """

    album_ms_df = database.run_query(query)
    query = f"SELECT DISTINCT album_id FROM tracks"
    result = database.run_query(query)

    albums = []

    for section in range(math.ceil(len(result) / 20)):
        concat_ids = ""
        for index in range(section * 20, min(section * 20 + 20, len(result))):
            concat_ids += f"{result['album_id'].iloc[index]},"

        response = requests.get(
            f"{BASE_URL}albums?ids={concat_ids[:-1]}", headers=headers
        )
        albums.append(response.json())

    album_df = pd.DataFrame()
    album_artist_df = pd.DataFrame()

    for index, section in enumerate(albums):
        for index, album in enumerate(section["albums"]):
            new_album = pd.Series(
                {
                    "name": album["name"],
                    "type": album["album_type"],
                    "num_tracks": album["total_tracks"],
                    "album_id": album["id"],
                    "external_urls": album["external_urls"]["spotify"],
                    "popularity": album["popularity"],
                    "images": album["images"][-1]["url"],
                    "release_date": album["release_date"],
                    "release_date_precision": album["release_date_precision"],
                }
            )

            if new_album["release_date_precision"] == "year":
                new_album["release_year"] = new_album["release_date"]
            elif new_album["release_date_precision"] == "month":
                new_album["release_year"], new_album["release_month"] = new_album[
                    "release_date"
                ].split("-")
            elif new_album["release_date_precision"] == "day":
                (
                    new_album["release_year"],
                    new_album["release_month"],
                    new_album["release_day"],
                ) = new_album["release_date"].split("-")

            album_df = pd.concat([album_df, new_album.to_frame().T], ignore_index=True)

            for artist in album["artists"]:
                new_row = pd.Series(
                    {"album_id": new_album["album_id"], "artist": artist["id"]}
                )
                album_artist_df = pd.concat(
                    [album_artist_df, new_row.to_frame().T], ignore_index=True
                )

    album_df = album_df.merge(album_ms_df, on="album_id")
    database.df_to_database(album_df, "albums", "replace")
    database.df_to_database(album_artist_df, "album_artists", "replace")


def get_artists(headers):
    """
    https://developer.spotify.com/documentation/web-api/reference/#/operations/get-multiple-artists
    """
    query = """
    SELECT SUM(clean_history.ms_played) as ms_played,
        track_artists.artist_id
    FROM clean_history
    JOIN track_artists
    ON clean_history.track_id = track_artists.track_id
    GROUP BY track_artists.artist_id
    """
    artist_ms_df = database.run_query(query)

    query = "SELECT DISTINCT artist_id FROM track_artists"
    result = database.run_query(query)

    artists = []

    for section in range(math.ceil(len(result) / 50)):
        concat_ids = ""
        for index in range(section * 50, min(section * 50 + 50, len(result))):
            concat_ids += f"{result['artist_id'].iloc[index]},"

        response = requests.get(
            f"{BASE_URL}artists?ids={concat_ids[:-1]}", headers=headers
        )
        artists.append(response.json())

    artist_df = pd.DataFrame()
    artist_genre_df = pd.DataFrame()

    for index, section in enumerate(artists):
        for index, artist in enumerate(section["artists"]):
            new_artist = pd.Series(
                {
                    "name": artist["name"],
                    "popularity": artist["popularity"],
                    "artist_id": artist["id"],
                    "external_urls": artist["external_urls"]["spotify"],
                    "followers": artist["followers"]["total"],
                }
            )

            artist_df = pd.concat(
                [artist_df, new_artist.to_frame().T], ignore_index=True
            )

            for genre in artist["genres"]:
                new_row = pd.Series(
                    {"artist_id": new_artist["artist_id"], "genre": genre}
                )
                artist_genre_df = pd.concat(
                    [artist_genre_df, new_row.to_frame().T], ignore_index=True
                )

    artist_df = artist_df.merge(artist_ms_df, on="artist_id")
    database.df_to_database(artist_df, "artists", "replace")
    database.df_to_database(artist_genre_df, "artist_genres", "replace")


def get_tracks(headers):
    """
    https://developer.spotify.com/documentation/web-api/reference/#/operations/get-several-tracks
    """
    query = """
    SELECT SUM(ms_played) as ms_played,
        track_id
    FROM clean_history
    GROUP BY track_id
    """
    track_ms_df = database.run_query(query)

    query = f"SELECT DISTINCT track_id FROM clean_history"
    result = database.run_query(query)

    tracks = []

    for section in range(math.ceil(len(result) / 50)):
        concat_ids = ""
        for index in range(section * 50, min(section * 50 + 50, len(result))):
            concat_ids += f"{result['track_id'].iloc[index]},"

        response = requests.get(
            f"{BASE_URL}tracks?ids={concat_ids[:-1]}", headers=headers
        )
        tracks.append(response.json())

    track_df = pd.DataFrame()
    track_artist_df = pd.DataFrame()

    for index, section in enumerate(tracks):
        for index, track in enumerate(section["tracks"]):
            new_track = pd.Series(
                {
                    "name": track["name"],
                    "album_id": track["album"]["id"],
                    "popularity": track["popularity"],
                    "disc_number": track["disc_number"],
                    "track_number": track["track_number"],
                    "track_id": track["id"],
                    "explicit": track["explicit"],
                    "external_urls": track["external_urls"]["spotify"],
                    "duration_ms": track["duration_ms"],
                }
            )

            track_df = pd.concat([track_df, new_track.to_frame().T], ignore_index=True)

            for artist in track["artists"]:
                new_row = pd.Series(
                    {"track_id": new_track["track_id"], "artist_id": artist["id"]}
                )
                track_artist_df = pd.concat(
                    [track_artist_df, new_row.to_frame().T], ignore_index=True
                )

    track_df = track_df.merge(track_ms_df, on="track_id")
    database.df_to_database(track_df, "tracks", "replace")
    database.df_to_database(track_artist_df, "track_artists", "replace")


def get_audio_features(headers):
    """
    https://developer.spotify.com/documentation/web-api/reference/#/operations/get-several-audio-features
    """
    query = f"SELECT track_id FROM tracks"
    result = database.run_query(query)

    tracks = []

    for section in range(math.ceil(len(result) / 100)):
        concat_ids = ""
        for index in range(section * 100, min(section * 100 + 100, len(result))):
            concat_ids += f"{result['track_id'].iloc[index]},"

        response = requests.get(
            f"{BASE_URL}audio-features?ids={concat_ids[:-1]}", headers=headers
        )
        tracks.append(response.json())

    audio_features_df = pd.DataFrame()

    for index, section in enumerate(tracks):
        for index, track in enumerate(section["audio_features"]):
            if track:
                new_row = pd.Series(
                    {
                        "track_id": track["id"],
                        "acousticness": track["acousticness"],
                        "analysis_url": track["analysis_url"],
                        "danceability": track["danceability"],
                        "duration_ms": track["duration_ms"],
                        "energy": track["energy"],
                        "instrumentalness": track["instrumentalness"],
                        "key": track["key"],
                        "liveness": track["liveness"],
                        "loudness": track["loudness"],
                        "mode": track["mode"],
                        "speechiness": track["speechiness"],
                        "tempo": track["tempo"],
                        "time_signature": track["time_signature"],
                        "valence": track["valence"],
                    }
                )

                audio_features_df = pd.concat(
                    [audio_features_df, new_row.to_frame().T], ignore_index=True
                )

    database.df_to_database(audio_features_df, "audio_features", "replace")


def get_artist_audio_features():
    query = """
    SELECT artists.artist_id,
        af.*
    FROM track_artists
    JOIN audio_features AS af
    ON af.track_id = track_artists.track_id
    JOIN artists
    ON artists.artist_id = track_artists.artist_id
    """

    query_df = database.run_query(query)

    query_df.drop(columns=["analysis_url", "track_id"], inplace=True)

    query_df = query_df.groupby("artist_id").mean(numeric_only=True).reset_index()

    database.df_to_database(query_df, "artist_audio_features", "replace")


def get_album_audio_features():
    query = """
    SELECT tracks.album_id,
        af.*
    FROM tracks
    JOIN audio_features AS af
    ON af.track_id = tracks.track_id
    """

    query_df = database.run_query(query)

    query_df.drop(columns=["analysis_url", "track_id"], inplace=True)

    query_df = query_df.groupby("album_id").mean(numeric_only=True).reset_index()

    database.df_to_database(query_df, "album_audio_features", "replace")


def get_genre_seeds(headers):
    response = requests.get(
        f"{BASE_URL}recommendations/available-genre-seeds", headers=headers
    )
    print(response.json())


def main():
    # headers = authorize_spotify_api()
    pass


if __name__ == "__main__":
    main()
