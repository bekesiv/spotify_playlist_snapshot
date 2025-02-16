"""Small script to fetch all playlists information of a Spotify user and save it to a CSV file."""
#!/usr/bin/env python3
import sys
import os
import argparse
import time
from datetime import datetime
import yaml
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class MySpotify(spotipy.Spotify):
    """
    A class to interact with Spotify's Web API using Spotipy library.

    Extends the Spotipy.Spotify class and provides additional methods
    to fetch and manage playlists and their tracks.

    Attributes:
        playlistmap (dict): A dictionary to map playlist IDs to their names.
    """

    def __init__(self, client_id, secret):
        """
        Initializes the MySpotify class with the given client ID and secret.

        Args:
            client_id (str): The client ID for Spotify API.
            secret (str): The client secret for Spotify API.
        """
        REDIRECT_URI = "http://localhost:8000"
        SCOPE = "playlist-read-private playlist-read-collaborative"
        super().__init__(auth_manager=SpotifyOAuth(client_id=client_id,
                                                   client_secret=secret,
                                                   redirect_uri=REDIRECT_URI,
                                                   scope=SCOPE))
        self.playlistmap = {}

    def get_playlist_name_by_id(self, playlist_id):
        """
        Retrieves the name of a playlist by its ID.

        Args:
            playlist_id (str): The ID of the playlist.

        Returns:
            str: The name of the playlist.
        """
        name = self.playlistmap.get(playlist_id)
        if name is None:
            name = self.playlist(playlist_id)["name"]
            self.playlistmap[playlist_id] = name
        return name

    def get_all_playlists(self):
        """
        Retrieves all playlists of the current user and writes them to a file.

        Returns:
            list: A list of all playlists.
        """
        playlists = []
        offset = 0
        limit = 50
        while True:
            response = self.current_user_playlists(limit=limit, offset=offset)
            playlists.extend(response["items"])
            offset += limit
            # If there are no more playlists to fetch, break the loop
            if len(response["items"]) < limit:
                break
        print("Your playlists:")
        with open('playlist.txt', 'w', encoding='utf-8') as f:
            for playlist in playlists:
                self.playlistmap[playlist["id"]] = playlist["name"]
                print(f'{playlist["id"]}: {playlist["name"]}')
                sys.stdout.flush()
                f.write(f'{playlist["id"]}: {playlist["name"]}\n')
        return playlists

    def get_tracks_in_one_playlist(self, playlist_id, playlist_name):
        """
        Retrieves all tracks in a given playlist.

        Args:
            playlist_id (str): The ID of the playlist.
            playlist_name (str): The name of the playlist.

        Returns:
            list: A list of tracks in the playlist.
        """
        tracks = []
        offset = 0
        limit = 50
        fields = (
            'items(added_at, track(id, name, disc_number, track_number, is_local, album(id, name), artists(id, name)))'
        )
        while True:
            response = self.playlist_tracks(playlist_id, limit=limit, offset=offset, fields=fields)
            for i in response["items"]:
                # print(f'{response["items"]}')
                sys.stdout.flush()
                if i.get('track', {}).get('id') is None:
                    continue
                row = [
                    playlist_id,
                    f'"{playlist_name}"',
                    i["added_at"].replace('T', '_').replace('Z', ''),
                    i["track"]["id"],
                    f'"{i["track"]["name"]}"',
                    f'{i["track"]["disc_number"]}',
                    f'{i["track"]["track_number"]}',
                    f'{i["track"]["is_local"]}',
                    i["track"]["album"]["id"],
                    f'"{i["track"]["album"]["name"]}"',
                    f'"{", ".join(val["id"] for val in i["track"]["artists"])}"',
                    f'"{", ".join(val["name"] for val in i["track"]["artists"])}"'
                ]
                tracks.append(row)
            offset += limit
            # If there are no more tracks to fetch, break the loop
            if len(response["items"]) < limit:
                break
        return tracks

    def get_playlist_items(self, playlists, excludes):
        """
        Retrieves tracks from multiple playlists and writes them to a CSV file.

        Args:
            playlists (list): A list of playlist IDs to fetch tracks from.
            excludes (list): A list of playlist IDs to exclude from fetching.

        Returns:
            None
        """
        header = [
            'playlist_id',
            'playlist_name',
            'added_at',
            'track_id',
            'title',
            'disc_number',
            'track_number',
            'is_local',
            'album_id',
            'album_title',
            'artist_id',
            'artist_name'
            ]
        timestamp = datetime.fromtimestamp(time.time()).strftime("%Y%m%d_%H%M%S")
        filename = f'playlist_export_{timestamp}.csv'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"{','.join(header)}\n")
        for playlist_id in playlists:
            playlist_name = self.get_playlist_name_by_id(playlist_id)
            if playlist_id in excludes:
                print(f'!! Skipping {playlist_id} - {playlist_name}')
                sys.stdout.flush()
                continue
            print(f'Fetching {playlist_id}: {playlist_name}')
            sys.stdout.flush()
            tracks = self.get_tracks_in_one_playlist(playlist_id, playlist_name)
            with open(filename, 'a', encoding='utf-8') as f:
                for row in tracks:
                    f.write(f"{','.join(row)}\n")
        print(f'All playlists processed, writing {filename}')

def get_configuration():
    """
    Reads the configuration from a YAML file and returns the relevant settings.

    The configuration file is expected to be named 'configuration.yaml' and should be located
    in the same directory as this script. The file should contain the following keys:
    - client_id: The client ID for the Spotify API.
    - secret: The secret key for the Spotify API.
    - playlists: A list of playlist IDs to be processed.
    - exclude: A list of items to be excluded.

    Returns:
        tuple: A tuple containing the following elements:
            - client_id (str): The client ID for the Spotify API.
            - secret (str): The secret key for the Spotify API.
            - playlists (list): A list of playlist IDs to be processed.
            - exclude (list): A list of items to be excluded.
    """
    CONFIG_FILENAME = 'configuration.yaml'
    data = {}
    if os.path.exists(CONFIG_FILENAME):
        with open(CONFIG_FILENAME, encoding="utf-8", mode='r') as f:
            data = yaml.safe_load(f)
    return (data.get('client_id', ''),
            data.get('secret', ''),
            data.get('playlists', []),
            data.get('exclude', []))

def get_arguments():
    """
    Parses command-line arguments for the Spotify Playlist Snapshot application.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--id', required=True, help='Customer ID to Spotify Web API')
    parser.add_argument('-s', '--secret', required=True, help='Secret to Spotify Web API')
    parser.add_argument('-l', '--playlists', nargs='+', help='One or more playlist to retrieve')
    parser.add_argument('-x', '--excludes', nargs='+', help='One or more playlist to exclude')
    return parser.parse_args()


# Main function
def main():
    """
    Main function to execute the Spotify playlist snapshot process.

    This function retrieves the configuration for the Spotify API client,
    including client ID, secret, playlists, and excludes. If the client ID
    or secret is not provided, it fetches these values from command-line
    arguments. It then initializes the MySpotify object and retrieves the
    playlist items based on the provided or fetched playlists and excludes.

    Returns:
        None
    """
    (client_id, secret, playlists, excludes) = get_configuration()
    if not client_id or not secret:
        arg = get_arguments()
        client_id = arg.id
        secret = arg.secret
        playlists = arg.playlists
        excludes = arg.excludes
    msp = MySpotify(client_id, secret)
    if not playlists:
        playlists = [i["id"] for i in msp.get_all_playlists()]
    msp.get_playlist_items(playlists, excludes)

if __name__ == "__main__":
    main()
