# Welcome to YourFestival!
---
YourFestival! is a web application that utilizes the Spotify API to instantly create a personalized music festival for the user. After creating the music festival, the application will also create a playlist sampling all of the artists playing in the festival.

The only requirement to get started is that the user have a Spotify account.

Video Walkthrough: https://youtu.be/ezEIvS9koKI 

# Setup
---
This app was made using Python, Javascript, HTML, CSS, and Flask. Running the app will require Python 3 and flask/flask_sessions be installed. Also essential to running this project is Spotipy, a python module that simplifies the URL generation for making requests from the Spotify API. This can be installed by running `pip install spotipy --upgrade` in the terminal.

To run the application, download the program files and in the "Festival" folder, run `python3 app.py` in the terminal. I believe this needs to be done locally and not in a cloud-based IDE, as there's a specific address that running the program will return. The Spotify API expects that address in order to successfully register users. The terminal should spit back out a link to follow like follows: http://127.0.0.1:8080/

Follow that link to begin using the app!

# App Navigation
---
You will be greeted by the landing page with the logo and a button prompting you to log in to your Spotify account. When pressed, you will be redirected to a Spotify sign-in page that lists the permissions you are giving the application. These are necessary to pull the necessary data and to create and modify a playlist in the user's profile.

After that, it will ask if you want to use your Spotify display name or manually change it. This option was added because people who signed up for Spotify with their Facebook accounts have a display name that is a string of numbers, and the name is used later in the app. After adjusting that name and giving your festival a name, you are taken to your festival's website.

The festival homepage displays the festival name and then the personalized lineup of 10 of your favorite artists including a few lesser-known artists related to your favorite artists. After checking out your lineup, go ahead and click "Create Playlist" in the navbar. The app will automatically pull the 3 top songs for each artist in your festival and compile them in a playlist that should now be in your Spotify account. Finally, click "Attend Festival" in the navbar. This website will display a mock schedule of the festival day. If you click the start festival button, Spotify will start the newly generated playlist, playing music from the artists in the order they appear in the lineup (from least to most popular). Sometimes this takes a few seconds to play while the playlist generates. Spotify also requires that there is an "active device" to play it on, with no easy workaround. If the active device times out, you just need to hit play on any song in Spotify to set an active device and then try again.

Finally, you have the options to change your display name or the name of your festival by clicking "Edit Details" in the navbar, or you can log out of the app, clearing your session data, by clicking "Sign Out" also in the navbar.