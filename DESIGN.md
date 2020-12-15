# Design Overview
---
YourFestival! is a web application that utilizes the Spotify API to instantly create a personalized music festival for the user. After creating the music festival, the application will also create a playlist sampling all of the artists playing in the festival. The idea came from one of my favorite artists creating his own music festival of his favorite artists and some lesser known artists who deserve exposure. He also shared a playlist sampling each of the artists in his festival. I thought about how I could make a program that generates a festival and playlist, and lo-and-behold, Spotify has an API tht allows you to pull all of the data needed to do so.

For those curious, the inspiration came from Porter Robinson and his Second Sky music festival.

# Spotify
---
## Spotify API
First, I'm going to offer an explanation of the basics of the Spotify API and user authentication. The Spotify API allows applications to access Spotify data by making HTTPS requests to an API endpoint (ie a user's top artists). The two paths you could take with this are to just pull Spotify data like artist and music information, or allow users to sign in so you have access to that user's information.

Ultimately, I thought it would be more interesting for the app to do all the legwork for the user, rather than making them manually pick a few artists to generate a festival around. Implementing user authentication would also be necessary for playlist generation anyways. The authentication process was tricky to figure out, but luckily, there is a Python library that handles a lot of the messy URL generation necessary to make requests from Spotify and OAuth. With Spotipy, I'm able to grab an "authentication manager", which is JSON data that includes access tokens that Spotify generates, allowing access to Spotify's user data. The below code demonstrates how the access token is generated, found, and then used to redirect to Spotify's user login page if there is no cached token yet.

```
# Pull authorization manager from Spotify
auth_manager = spotipy.oauth2.SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=scope, cache_path=session_cache_path(), show_dialog=True)

if request.args.get("code"):
    # Being redirected from Spotify auth page
    auth_manager.get_access_token(request.args.get("code"))
    return redirect('/generate_festival')

if not auth_manager.get_cached_token():
    # Display sign in link when no token is found
    auth_url = auth_manager.get_authorize_url()
    return redirect(auth_url)

```
Just some explanation of the arguments passed into SpotifyOAuth:
Client ID and client secret ID are strings used to identify that it is specifically my app making requests from the Spotify API. I found online that these should be exported so that they aren't visible to anyone with access to the code, for security purposes. It could allow them to alter the redirect URI, which tells Spotify where to return users after they login to their Spotify accounts. For the sake of ease of use for whoever has to run this app locally, I've left them as global variables. I'll likely change this if I ultimately put this out on the internet.

Scope lets the user know what information I will be using of theirs and if I will have permission to alter their account (ie adding a playlist to their account). This information isn't used for anything besides the immediate outputs of the web app, and the data is erased when signing out. The cache_path tells OAuth where to store the generated access token.

## Lineup
The best part of the project was creating the function that generated a custom personalized lineup. Once the user had allowed access to their data, a wealth of data is available to analyze and manipulate. You can see some of the testing I did in test.py, included in the app package. Most fundemental to this project was pulling the users favorite artists, which is demonstrated in the below code. The Spotify API allows you to look at a users favorite artists over the long term (last several years), medium term (last 6 months), and short term (last 4 weeks).

```
# Grabs list of user's top artists for each time period
artists_long = spotify.current_user_top_artists(limit=50, time_range="long_term")
artists_medium = spotify.current_user_top_artists(limit=50, time_range="medium_term")
artists_short = spotify.current_user_top_artists(limit=50, time_range="short_term")

```
This returns JSON data for a max of 50 artists for each time period. The data includes the artist's id and name, popularity level, genres, images, and a few other pieces of data that weren't as relevant to this project. While I knew I wanted to do something that finds unknown artists for the user, I decided the bulk of the festival should be artists the user loves. As demonstrated yearly, Spotify Wrapped is extremely popular, demonstrating how much users like seeing their listening data. For that reason, I decided that I would grab the user's top four artists over the long term, as safe options they will definitely like.

To represent the user's more recent music tastes, I pulled the top two artists from both the medium and short term (skipping artists if they were in the top 4 long term artists and already in the lineup). I left two festival slots for new artists similar to the user's favorite artists. I decided to use one artist from each the medium and short term lists as the basis for the new artist finder, with the hopes that their medium and recent term listening trends represent their current tastes best. The long term list also seemed more likely to bake in the user's favorite genres that they have consistently listened to. The shorter term lists were more likely to include artists and genres that the user is less familiar with, so it seemed like a better basis for finding new interesting artists.

## New Artist Finder Function
This function is the most interesting piece of the project. Spotify allows applications to pull a list of artists related to one artist. It returns 20 related artists and their associated artist data. When I tried testing the function, I found that I was pretty familiar with most of the related artists to my favorite artists, which meant that simply picking the first related artist wasn't sufficient.

Instead I created a recursive function, that when called for a specific artist id, loops through each of the related artists and checks them against a few parameters that ensure the user doesn't already listens to them regularly. If all of the related artists fail those checks, the function randomly selects an artist from that list, uses that artist's id to recursively call itself, and generates a new list of related artists to search through.

```
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
```

The function skips artists who are already in the user's top artists for each time period and also skips artists already added to the lineup (seems redundant, but there's a very unlikely chance the second artist this function generates is the same as the first one). I also skip any artists whose popularity exceeds 49 on a scale of 0-100. I came to that number after some testing. I pushed the function to it's limit by having it hunt for artists with a popularity of less than 10, and it worked, but often called itself >70 times, which really slowed things down (and is why I included a limit to the # of times the function can recursively call itself). Also, you start to get into some unprofessional artists that are less desirable when the popularity is set too low. Artists with a popularity of 40-50 are typically professionals who are well regarded in their scene but lacking mainstream popularity, which felt right. This is one area that could be tweaked with some more work, perhaps by dynamically setting a low popularity level based on the user's listening habits, but that was beyond what I could accomplish in the allotted time.

## Playlist Generation
For the playlist, I simply pulled the top 3 songs from each artist, for a total playlist size of 30 songs. This felt like an easily consumable size to sample all of the artists' most accessible work. It orders the artists from least popular to most, so when you play it start to finish, it's like an actual music festival where the biggest acts play last. The playlist is named after the festival name, and has a custom playlist description.

# Web Design
---
This app was made using Python, Javascript, HTML, CSS, and Flask. This was simply because it was what I was most comfortable with after the finance problem set. The implementation was fairly simple, with the only complication being how I wanted to handle user information on the back end.

I toyed with allowing users to register for an account and using SQL to store the results of the first time the music festival is generated, but it turned out to be unneccesary. I can just piggyback off of their Spotify login and use flask sessions to store and manipulate any information necessary. This web app isn't really one that requires storing data over the long-term and is more of just a fun app to run every once in a while when your listening habits evolve.

The rest of the website is fairly simple. It starts with having the user to enter their name and what they would name their music festival, and then reveals the mainpage, which is meant to look like a music festival flier, with the festival name and the list of artists, ordered from biggest acts to smallest. From there you can click the "Create Playlist" button to generate the playlist and add it to your spotify account. I also created an "Attend Festival" page, which shows a mock schedule of the festival day, and plays your custom playlist in the order that the artists would play in the festival (smallest acts to biggest).

Upon signing out, the users session data is cleared, and a new user can log in.
---

# Thanks for checking out my project and feel free to let me known if you have any questions!

