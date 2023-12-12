import sys
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import argparse
import yaml
import json


class MySpotify(spotipy.Spotify):
    def __init__(self, client_id, secret):
        REDIRECT_URI = "http://localhost:8000"
        SCOPE = "playlist-read-private playlist-read-collaborative"
        self.sp = super().__init__(auth_manager=SpotifyOAuth(client_id=client_id,
                                                             client_secret=secret,
                                                             redirect_uri=REDIRECT_URI,
                                                             scope=SCOPE))

    def get_all_playlists(self):
        playlists = []
        offset = 0
        limit = 50
        while True:
            response = self.current_user_playlists(limit=limit, offset=offset)
            playlists.extend(response['items'])
            offset += limit
            # If there are no more playlists to fetch, break the loop
            if len(response['items']) < limit:
                break
        print("Your playlists:")
        with open('playlist.txt', 'w', encoding='utf-8') as f:
            for playlist in playlists:
                playlist_id = playlist['id']
                playlist_name = playlist['name']
                print(f"{playlist_id}: {playlist_name}")
                f.write(f"{playlist_id}: {playlist_name}\n")


    def get_one_playlist_item(self, playlist_id):
        tracks = []
        offset = 0
        limit = 50
        fields = 'items(added_at, track(id, name, disc_number, track_number, is_local, album(id, name), artists(id, name)))'
        playlist_name = self.playlist(playlist_id)['name']
        while True:
            response = self.playlist_tracks(playlist_id, limit=limit, offset=offset, fields=fields)
            for i in response['items']:
                
                # for artist
                row = {
                    'playlist_id': playlist_id,
                    'playlist_name': f'"{playlist_name}"',
                    'added_at': i['added_at'].replace('T', '_').replace('Z', ''),
                    'track_id': i['track']['id'],
                    'title': f'"{i['track']['name']}"',
                    'disc_number': i['track']['disc_number'],
                    'track_number': i['track']['track_number'],
                    'is_local': i['track']['is_local'],
                    'album_id': i['track']['album']['id'],
                    'album_title': f'"{i['track']['album']['name']}"',
                    'artist_id': f'"{", ".join(val['id'] for val in i['track']['artists'])}"',
                    'artist_name': f'"{", ".join(val['name'] for val in i['track']['artists'])}"'
                }


# import csv

# json_data = [
#     {"Name": "John", "Age": 30, "City": "New York"},
#     {"Name": "Alice", "Age": 25, "City": "San Francisco"},
#     {"Name": "Bob", "Age": 35, "City": "Los Angeles"}
# ]

# # Specify the CSV file path
# csv_file_path = 'output.csv'

# # Get the header from the first dictionary in the list
# header = json_data[0].keys()

# # Open the CSV file in write mode
# with open(csv_file_path, 'w', newline='') as csv_file:
#     # Create a CSV writer
#     csv_writer = csv.DictWriter(csv_file, fieldnames=header)

#     # Write the header
#     csv_writer.writeheader()

#     # Write the data
#     csv_writer.writerows(json_data)

# print(f"CSV file '{csv_file_path}' has been created.")




            offset += limit
            # If there are no more tracks to fetch, break the loop
            if len(response['items']) < limit:
                break


    def get_playlist_items(self, playlists):
        for pl in playlists:
            playlist_items = self.get_one_playlist_item(pl)
            print(f'{playlist_items}')


def get_configuration():
    CONFIG_FILENAME = 'configuration.yaml'
    data = {}
    if os.path.exists(CONFIG_FILENAME):
        with open(CONFIG_FILENAME, 'r') as f:
            data = yaml.safe_load(f)
    return (data.get('client_id', ''), data.get('secret', ''), data.get('playlists', []))

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--id', required=True, help='Customer ID to Spotify Web API')
    parser.add_argument('-s', '--secret', required=True, help='Secret to Spotify Web API')
    parser.add_argument('-l', '--playlists', nargs='+', help='One or more playlist to retrieve')
    return parser.parse_args()

# Main function
def main():
    (client_id, secret, playlists) = get_configuration()
    if not client_id or not secret:
        try:
            arg = get_arguments()
            client_id = arg.id
            secret = arg.secret
            playlists = arg.playlists
        except:
            sys.exit(1)
    msp = MySpotify(client_id, secret)
    if not playlists:
        msp.get_all_playlists()
        sys.exit(0)
    else:
        msp.get_playlist_items(playlists)

if __name__ == "__main__":
    main()