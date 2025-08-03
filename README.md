# Reverb - The Tool for Music Lovers
Reverb: A Flask-Based Lyric Analysis App 🎶
Reverb is a simple web application built with Flask that allows users to analyze the sentiment of a song's lyrics. It's a full-stack project that demonstrates how to build a dynamic web page that interacts with external APIs and libraries to process data.


## How it works
For the Lyric Analyzer:
The app's workflow is a collaboration between the client and the server. The app's workflow is divided into three main stages:

1. Fetching Lyrics: When you submit a song title and artist, the Python backend uses the Genius API to search for the song. Once it finds a match, it retrieves the lyrics by scraping the song's page on the Genius website using the Beautiful Soup library. This ensures it can get the full lyrics, even if the API provides only partial data.

2. Sentiment Analysis: The fetched lyrics are then fed into the NLTK (Natural Language Toolkit) library's VADER (Valence Aware Dictionary and sEntiment Reasoner) tool. VADER analyzes the text and calculates a score for each of the following: positive, negative, neutral, and a compound score. The compound score determines the overall mood of the song (e.g., positive, negative, or neutral).

3. Visualization: To make the analysis more engaging, the app uses the WordCloud and Matplotlib libraries to generate a visual representation of the lyrics. It creates a word cloud where words are colored based on their sentiment, giving a quick, at-a-glance summary of the song's emotional tone. The final image is then converted to a base64 string and embedded directly into the HTML page.


For the Soundbar App:

Audio Generation (Backend): When the user requests a tone, a Python script running on the Flask server uses an audio library (e.g., SciPy or numpy if you've added it) to generate a sound wave (e.g., a sine wave) at a specific frequency. This audio data is then passed back to the frontend.

Visual Processing (Frontend): The client-side JavaScript receives this audio data and uses the HTML <canvas> element to render the sound wave. Using a library like Tone.js, the script captures the frequency data from the audio signal in real-time.

Real-time Rendering: An animation loop constantly updates the height of each bar on the canvas based on the amplitude of the corresponding frequency in the sound signal. This creates the dynamic, "bouncing" effect you see as the sound plays, providing a direct visual representation of the audio waves.


## How to run this app?
* ideally try out from the vercel URL below
* alternately clone this repository to your local machine
  * use UV package manager, run ```ur init``` in the project folder, it will use pyproject.toml
  * run the application using uv, ```uv run app.py```
  * navigate in your browser to https://localhost:5000/


This was done for the Hack With The Beat Hackathon

Url of HWTB --> https://hackwiththebeat.com/

URL of Reverb: (will be happening)
https://reverb-two.vercel.app/


