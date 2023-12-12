import sys
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import argparse
import yaml
import time
from datetime import datetime


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
                if i['track']['id'] is None:
                    continue
                row = [
                    playlist_id,
                    f'"{playlist_name}"',
                    i['added_at'].replace('T', '_').replace('Z', ''),
                    i['track']['id'],
                    f'"{i['track']['name']}"',
                    f'{i['track']['disc_number']}',
                    f'{i['track']['track_number']}',
                    f'{i['track']['is_local']}',
                    i['track']['album']['id'],
                    f'"{i['track']['album']['name']}"',
                    f'"{", ".join(val['id'] for val in i['track']['artists'])}"',
                    f'"{", ".join(val['name'] for val in i['track']['artists'])}"'
                ]
                tracks.append(row)
            offset += limit
            # If there are no more tracks to fetch, break the loop
            if len(response['items']) < limit:
                break
        return tracks


    def get_playlist_items(self, playlists):
        tracks = [[
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
            ]]

        for pl in playlists:
            print(f'Fetching {pl}')
            tracks.extend(self.get_one_playlist_item(pl))
        timestamp = datetime.fromtimestamp(time.time()).strftime("%Y%m%d_%H%M%S")
        filename = f'playlist_export_{timestamp}.csv' 
        print(f'All playlists processed, writing {filename}')
        with open(filename, 'w', encoding='utf-8') as f:
            for row in tracks:
                f.write(f"{','.join(row)}\n")


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