import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import random

#  Client Keys
CLIENT_ID = "a776809dbc5b43acbec15376d3a7a704"
CLIENT_SECRET = "9a72bbd2e4ec424eaec19de8230cec9c"
REDIRECT_URI = "http://127.0.0.1:8080/callback/q"

scope = 'user-top-read user-read-playback-state streaming ugc-image-upload playlist-modify-public'

spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=scope))

def main():
    global spotify
    
    user = spotify.current_user()

    # print(json.dumps(user, sort_keys=4, indent=4))

    # Check if playlist has already been made
    # festival_name = db.execute("SELECT fest_name FROM users WHERE id = :userid", userid=user['id'])
    # if festival_name in playlists:
    #   blank
    # else
    # print(playlists)

    # songs_long = spotify.current_user_top_tracks(time_range='long_term')
    # songs_med = spotify.current_user_top_tracks(time_range='medium_term')
    # songs_short = spotify.current_user_top_tracks(time_range='short_term')

    # for songs in songs_short['items']:
    #     print(songs['name'])

    artists_long = spotify.current_user_top_artists(time_range="long_term")
    artists_medium = spotify.current_user_top_artists(time_range="medium_term")
    artists_short = spotify.current_user_top_artists(limit=5, time_range="short_term")

    for artist in artists_long['items']:
        print(artist['name'])
    
    for artist in artists_medium['items']:
        print(artist['name'])
    
    for artist in artists_short['items']:
        print(artist['name'])
    # # For referencing possible artist info
    # print(json.dumps(artists_short, sort_keys=4, indent=4))

    lineup = []

    # Will be used to grab artist ids from each term of top artists. Will be used to find unknown related artists
    new_artist_start_points = []

    # Add user's top 4 artists of all time to lineup
    for artist in artists_long['items']:
        artist_dict = {"id": artist['id'], "name": artist['name'], "img": artist['images'][0]['url'], "popularity": artist['popularity']}
        lineup.append(artist_dict)

        if len(lineup) == 4:
            break

    # Grab 2 unique artists from user's medium term top artists
    for artist in artists_medium['items']:
        artist_dict = {"id": artist['id'], "name": artist['name'], "img": artist['images'][0]['url'], "popularity": artist['popularity']}
        if artist_dict in lineup:
            continue
        lineup.append(artist_dict)
        
        # end loop once 2 unique artists have been found
        if len(lineup) == 6:
            new_artist_start_points.append(artist['id'])
            break

    # Grab 2 more unique artists from user's short term top artists
    for artist in artists_short['items']:
        artist_dict = {"id": artist['id'], "name": artist['name'], "img": artist['images'][0]['url'], "popularity": artist['popularity']}
        if artist_dict in lineup:
            continue
        lineup.append(artist_dict)

        # end loop once 2 unique artists have been found
        if len(lineup) == 8:
            new_artist_start_points.append(artist['id'])
            break

    max_calls = 100
    # grab 3 new artists
    for artist in new_artist_start_points:
        artist_dict = find_new_artists(artist, lineup, artists_long, artists_medium, artists_short, max_calls)
        lineup.append(artist_dict)

    ordered_lineup = sorted(lineup, key=lambda k: k['popularity'])
    for artist in ordered_lineup:
        print(artist)

    # print(json.dumps(ordered_lineup, sort_keys=4, indent=4))

    username = 'Patrick Whalen'
    festival_name = 'Patchella'
    playlist_description = username + ' presents: ' + festival_name + "!"
    
    # Playlist generator
    song_generator = []
    
    # Loops through artists in lineup to pull their top songs
    for artist in lineup:
        artist_tracks = spotify.artist_top_tracks(artist['id'])["tracks"]
        counter = 0
        
        # Checks if track is already in song list (sometimes two of your favorite artists collaborate and have same top track)
        for track in artist_tracks:
            if track['id'] in song_generator:
                continue
            if counter == 3:
                break
            song_generator.append(track['id'])
            counter += 1

    # # Check if playlist already exists
    # user_playlists = spotify.current_user_playlists()
    # playlists = []
    # for playlist in user_playlists['items']:
    #     playlists.append(playlist['name'])
    
    # if festival_name in playlists:
    #     print("Playlist already exists!")
    # else:
    #     spotify.user_playlist_create(user=spotify.me()["id"],name=festival_name,public=True,description=playlist_description)

    #     #Grabs id of playlist
    #     playlist = spotify.user_playlists(user=spotify.me()["id"])
    #     playlistid = playlist['items'][0]['id']
        
    #     spotify.user_playlist_add_tracks(user=spotify.me()["id"], playlist_id=playlistid, tracks=song_generator)



# recursive to pull unknown artists
def find_new_artists(artist, lineup, list_long, list_med, list_short, max_recursion):
    global spotify
    related_artists = spotify.artist_related_artists(artist)
    # print(json.dumps(related_artists, sort_keys=4, indent=4))
    print("RECURSIVE BREAK")

    for new_artist in related_artists['artists']:
        # check to make sure this isn't already an artist the user listens to regularly
        print(new_artist['name'])
        # print(new_artist["popularity"])
        if new_artist in list_long['items']:
            continue
        elif new_artist in list_med['items']:
            continue
        elif new_artist in list_short['items']:
            continue
        if new_artist['popularity'] > 49:
            continue
        
        artist_dict = {"id": new_artist['id'], "name": new_artist['name'], "img": new_artist['images'][0]['url'], "popularity": new_artist['popularity']}
        if artist_dict in lineup:
            continue
        
        return artist_dict
    # new_start_point = spotify.artist_related_artists(new_artist['id'])
    if max_recursion == 0:
        for new_artist in related_artists['artists']:
            artist_dict = {"id": new_artist['id'], "name": new_artist['name'], "img": new_artist['images'][0]['url'], "popularity": new_artist['popularity']}
            if artist_dict in lineup:
                continue
            return artist_dict
    else:
        print('NEXT ARTIST RELATED')
        print(related_artists['artists'][random.randint(0,19)]['name'])
        rec_new_artist = find_new_artists(related_artists['artists'][random.randint(0,19)]['id'], lineup, list_long, list_med, list_short, max_recursion-1)
        # print(rec_new_artist)
        return rec_new_artist


if __name__ == '__main__':
    main()              

