import spotipy
from spotipy.oauth2 import SpotifyOAuth
import argparse

# Replace these values with your own Spotify API credentials
REDIRECT_URI = "http://localhost:8000"

# Define the scope (permissions) for the Spotify API
SCOPE = "playlist-read-private playlist-read-collaborative"

# Initialize the Spotify client with OAuth authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))

# Get all user playlists (including more than 50) with IDs
def get_all_user_playlists():
    playlists = []
    offset = 0
    limit = 50

    while True:
        response = sp.current_user_playlists(limit=limit, offset=offset)
        playlists.extend(response['items'])
        offset += limit

        # If there are no more playlists to fetch, break the loop
        if len(response['items']) < limit:
            break

    return playlists

# Print playlist details (ID and name)
def print_user_playlists(playlists):
    print("Your playlists:")
    for playlist in playlists:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        print(f"{playlist_id}: {playlist_name}")


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--id', required=True, help='Customer ID to Spotify Web API')
    parser.add_argument('-s', '--secret', required=True, help='Secret to Spotify Web API')
    parser.add_argument('-l', '--playlist', required=True, help='One or more playlist to retrieve')
    return parser.parse_args()

# Main function
def main():
    arg = get_arguments()
    playlists = get_all_user_playlists()
    print_user_playlists(playlists)

if __name__ == "__main__":
    main()