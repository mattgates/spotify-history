"""
Main file that runs the whole process of parsing Extended Streaming History
from Spotify, interfacing results with their API, and storing it in a MySQL DB.
Contributor: Matt Gates
"""

# Library Imports
import time

# Repository Imports
import spotify_api
import spotify_dump


def main():
    start_time = time.time()

    headers = spotify_api.authorize_spotify_api()

    # Folder path to Extended Streaming History json files
    history_df = spotify_dump.load_json("raw_data/2023_06_09/*.json")
    spotify_dump.clean_history(history_df)
    print(
        f"Streaming history parsed and stored - [{time.time() - start_time:.2f} secs]"
    )

    spotify_api.get_tracks(headers)
    print(f"Track data parsed and stored - [{time.time() - start_time:.2f} secs]")

    spotify_api.get_artists(headers)
    print(f"Artist data parsed and stored - [{time.time() - start_time:.2f} secs]")

    spotify_api.get_albums(headers)
    print(f"Album data parsed and stored - [{time.time() - start_time:.2f} secs]")

    spotify_api.get_audio_features(headers)
    print(
        f"Track audio features parsed and stored - [{time.time() - start_time:.2f} secs]"
    )

    spotify_api.get_artist_audio_features()
    print(
        f"Artist audio features parsed and stored - [{time.time() - start_time:.2f} secs]"
    )

    spotify_api.get_album_audio_features()
    print(
        f"Album audio features parsed and stored - [{time.time() - start_time:.2f} secs]"
    )


if __name__ == "__main__":
    main()
