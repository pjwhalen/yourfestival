import os
from flask import Flask, session, request, redirect, render_template, g, flash
from flask_session import Session
import uuid
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import random
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError

# Spotipy flask authentication and signout structure adapted from official Spotipy developer example https://github.com/plamere/spotipy/blob/master/examples/app.py
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

#  Client Keys and redirect URI. "export" these if this ever goes into production so others don't have access
CLIENT_ID = "a776809dbc5b43acbec15376d3a7a704"
CLIENT_SECRET = "9a72bbd2e4ec424eaec19de8230cec9c"
REDIRECT_URI = "http://127.0.0.1:8080/generate_festival"
scope = "user-top-read user-read-playback-state streaming ugc-image-upload playlist-modify-public"

# Store authmanager here
caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)


def session_cache_path():
    return caches_folder + session.get('uuid')


@app.route('/')
def index():
    if not session.get('uuid'):
        # Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())
    return render_template("index.html")


@app.route('/login', methods=["GET", "POST"])
def login():
    global CLIENT_ID
    global CLIENT_SECRET
    global REDIRECT_URI
    global scope

    # Pull authorization manager from Spotify
    auth_manager = spotipy.oauth2.SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=scope,
                                                cache_path=session_cache_path(), 
                                                show_dialog=True)

    session['auth_manager'] = auth_manager

    if request.args.get("code"):
        # Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/generate_festival')

    if not auth_manager.get_cached_token():
        # Display sign in link when no token is found
        auth_url = auth_manager.get_authorize_url()
        return redirect(auth_url)
    else:
        return redirect('/generate_festival')


@app.route('/generate_festival')
def generate_festival():
    auth_manager = session['auth_manager']
    
    # Used for all Spotify database access
    session['spotify'] = spotipy.Spotify(auth_manager=auth_manager)
    
    if request.args.get("code"):
        # Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))

    if not auth_manager.get_cached_token():
        return redirect('/')
    
    spotify = session['spotify']

    # Grabs list of user's top artists for each time period
    artists_long = spotify.current_user_top_artists(limit=50, time_range="long_term")
    artists_medium = spotify.current_user_top_artists(limit=50, time_range="medium_term")
    artists_short = spotify.current_user_top_artists(limit=50, time_range="short_term")

    lineup = []

    # Will be used to grab artist ids for use in finding unknown related artists
    new_artist_start_points = []

    # Add user's top 4 artists' relevant of all time to lineup with their relevant data
    for artist in artists_long['items']:
        artist_dict = {"id": artist['id'], "name": artist['name'], "img": artist['images'][0]['url'], "popularity": artist['popularity']}
        lineup.append(artist_dict)
        if len(lineup) == 4:
            break

    # Grab 2 unique artists from user's medium term top artists
    for artist in artists_medium['items']:
        artist_dict = {"id": artist['id'], "name": artist['name'], "img": artist['images'][0]['url'], "popularity": artist['popularity']}
        # There can be overlap in artists for the various time periods so need to check.
        if artist_dict in lineup:
            continue
        lineup.append(artist_dict)
        
        # end loop once 2 unique artists have been found. Pick one as basis for new artist finder
        if len(lineup) == 6:
            new_artist_start_points.append(artist['id'])
            break

    # Grab 2 more unique artists from user's short term top artists
    for artist in artists_short['items']:
        artist_dict = {"id": artist['id'], "name": artist['name'], "img": artist['images'][0]['url'], "popularity": artist['popularity']}
        if artist_dict in lineup:
            continue
        lineup.append(artist_dict)

        # end loop once 2 unique artists have been found. Pick one as basis for new artist finder
        if len(lineup) == 8:
            new_artist_start_points.append(artist['id'])
            break

    # This determines the number of times the recursive function pulls new lists of related artists to meet the desired parameters
    # Increase this if you lower the popularity requirement significantly
    max_calls = 25
    
    # grab 2 new (hopefully unknown) artists
    for artist in new_artist_start_points:
        artist_dict = find_new_artists(artist, lineup, artists_long, artists_medium, artists_short, max_calls)
        lineup.append(artist_dict)

    # Store user lineup in their session
    session['lineup'] = lineup
    
    return redirect('/confirm_name')


@app.route('/confirm_name')
def confirm_name():
    # Users' Spotify display names are often a string of numbers, so using this to check if that's the case
    
    auth_manager = session['auth_manager']
    session['spotify'] = spotipy.Spotify(auth_manager=auth_manager)
    
    if not auth_manager.get_cached_token():
        return redirect('/')
        
    spotify = session['spotify']

    # Pulls their display name to ask if they want to use that name
    session['username'] = spotify.current_user()['display_name']

    return render_template("confirm_name.html", username=session['username'])


@app.route('/change_name', methods=["GET", "POST"])
def change_name():
    auth_manager = session['auth_manager']
    if not auth_manager.get_cached_token():
        return redirect('/')

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("change_name"):
            flash('Must enter a name')
            return redirect('/change_name')       

        session['username'] = request.form.get("change_name")
        return redirect('/name_festival')

    # User reached route via GET (as by clicking a link or via redirect)
    # This is from CS50 Finance problem set
    else:
        return render_template("change_name.html")


@app.route('/name_festival', methods=["GET", "POST"])
def name_festival():
    auth_manager = session['auth_manager']
    if not auth_manager.get_cached_token():
        return redirect('/')

    if request.method == "POST":
        # Ensure festival name was submitted
        if not request.form.get("festival_name"):
            flash('Must give festival a name')
            return redirect('/name_festival')

        session['festival_name'] = request.form.get("festival_name")
        return redirect("/home")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("name_festival.html")


@app.route('/home', methods=["GET", "POST"])
def home():
    auth_manager = session['auth_manager']
    if not auth_manager.get_cached_token():
        return redirect('/')
    
    festival_name = session['festival_name']
    username = session['username']
    lineup = session['lineup']

    # Order lineup so the most popular appear on top
    ordered_lineup = sorted(lineup, key=lambda k: k['popularity'], reverse=True)

    return render_template("home.html", lineup=ordered_lineup, festival_name=festival_name, username=username)


@app.route('/schedule', methods=["GET", "POST"])
def schedule():
    auth_manager = session['auth_manager']
    if not auth_manager.get_cached_token():
        return redirect('/')
    
    festival_name = session['festival_name']
    username = session['username']
    spotify = session['spotify']
    lineup = session['lineup']

    # Will change some attributes on the page
    button_hide = ''
    header_hide = 'hidden'

    # List of mock set times for festival
    schedule = [
        '12PM to 12:30PM',
        '12:30PM to 1:20PM',
        '1:40PM to 2:15PM',
        '2:30PM to 3:10PM',
        '3:25PM to 4:05PM',
        '4:20PM to 5PM',
        '5:15PM to 6:05PM',
        '6:10PM to 7:10PM',
        '7:10PM to 8:10PM',
        '8:25PM to 9:55PM',
    ]

    # Sort by popularity, starting the festival with least popular.
    ordered_lineup = sorted(lineup, key=lambda k: k['popularity'])

    if request.method == "POST":
        # Look up playlist and play it
        user_playlists = spotify.current_user_playlists()
        for playlist in user_playlists['items']:
            if festival_name == playlist['name']:
                button_hide = 'hidden'
                header_hide = ''
                
                # Turns off shuffle so the artists play in the schedule order
                spotify.shuffle(False)
                spotify.start_playback(context_uri=playlist['uri'])
                return render_template("schedule.html", lineup=ordered_lineup, festival_name=festival_name, username=username, button_hide=button_hide, header_hide=header_hide, schedule=schedule)

        flash('Playlist not found. Create playlist before starting festival.')
        return redirect('/schedule')

    return render_template("schedule.html", lineup=ordered_lineup, festival_name=festival_name, username=username, button_hide=button_hide, header_hide=header_hide, schedule=schedule)


@app.route('/generate_playlist')
def generate_playlist():
    auth_manager = session['auth_manager']
    if not auth_manager.get_cached_token():
        return redirect('/')
    
    festival_name = session['festival_name']
    username = session['username']
    spotify = session['spotify']
    lineup = session['lineup']
    playlist_description = username + ' presents: ' + festival_name + "!"
    
    # Order by festival schedule order
    ordered_lineup = sorted(lineup, key=lambda k: k['popularity'])

    # Pulls all user playlists
    user_playlists = spotify.current_user_playlists()
    playlists = []
    for playlist in user_playlists['items']:
        playlists.append(playlist['name'])
    
    if festival_name in playlists:
        flash('A playlist with this festival name already exists in your library!')
        return redirect('/home')
    else:
        # Creates empty playlist
        spotify.user_playlist_create(user=spotify.me()["id"], name=festival_name, public=True, description=playlist_description)

        # List of song ids to later add to playlist
        song_generator = []
        
        # Loops through artists in lineup to pull their top songs
        for artist in ordered_lineup:
            artist_tracks = spotify.artist_top_tracks(artist['id'])["tracks"]
            counter = 0
            for track in artist_tracks:
                # Checks if track is already in song list (sometimes two of your favorite artists collaborate and have same top track)
                if track['id'] in song_generator:
                    continue
                # Maxes out at top 3 songs per artist so the playlist isn't 100 songs long
                if counter == 3:
                    break
                song_generator.append(track['id'])
                counter += 1
        
        # Grabs id of playlist
        playlist = spotify.user_playlists(user=spotify.me()["id"])
        playlistid = playlist['items'][0]['id']
        
        # Add tracks and redirect back to homepage
        spotify.user_playlist_add_tracks(user=spotify.me()["id"], playlist_id=playlistid, tracks=song_generator)
        flash('Playlist created. Check your Spotify playlists!')
        return redirect('/home')


@app.route('/sign_out')
def sign_out():
    # This comes entirely from the official Spotipy developer example https://github.com/plamere/spotipy/blob/master/examples/app.py
    try:
        # Remove the CACHE file (.cache-test) so that a new user can authorize.
        os.remove(session_cache_path())
        session.clear()
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    return redirect('/')


def find_new_artists(artist, lineup, list_long, list_med, list_short, max_recursion):
    # recursive function to pull unknown artists

    spotify = session['spotify']
    related_artists = spotify.artist_related_artists(artist)

    # Loop through related artists of selected lineup artists
    for new_artist in related_artists['artists']:
        # check to make sure this isn't already an artist the user listens to regularly and isn't too popular
        if new_artist in list_long['items']:
            continue
        elif new_artist in list_med['items']:
            continue
        elif new_artist in list_short['items']:
            continue
        if new_artist['popularity'] > 49:
            continue
        
        # I've run into errors where artists don't have any pictures. This skips them to avoid errors and maintain site design.
        try:
            artist_dict = {"id": new_artist['id'], "name": new_artist['name'], "img": new_artist['images'][0]['url'], "popularity": new_artist['popularity']}
        except IndexError:
            continue
        # If checks are passed, make sure the artist isn't already in the lineup. In case second new artist is the same as first new artist
        if artist_dict in lineup:
            continue

        return artist_dict
    
    # If the function has been recursively called the max number of times, it just picks a new artist from the last called related artists list
    if max_recursion == 0:
        for new_artist in related_artists['artists']:
            artist_dict = {"id": new_artist['id'], "name": new_artist['name'], "img": new_artist['images'][0]['url'], "popularity": new_artist['popularity']}
            # Double check it didn't stumble on to one of the artists already in the playlist
            if artist_dict in lineup:
                continue
            return artist_dict
    else:
        # Pull random artist from related artist. Choosing one specific artist index number often causes endless loops where related artists feed into eachother
        rec_new_artist = find_new_artists(related_artists['artists'][random.randint(0,19)]['id'], lineup, list_long, list_med, list_short, max_recursion-1)
        return rec_new_artist

# Sometimes an error is caused when no playback device is found. This is to handle that. 
# From CS50 distribution code for Finance problem set.
def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
        flash('No active playback device found. Play a song on one of your devices to activate.')
    return redirect('/schedule')


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
if __name__ == '__main__':
	app.run(threaded=True, port=int(os.environ.get("PORT", 8080)))