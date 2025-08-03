import requests
import re
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
import io
import base64
from flask import Flask, request, render_template, send_file
import uuid

# --- Configuration ---
# IMPORTANT: Replace YOUR_GENIUS_CLIENT_ACCESS_TOKEN with your actual token
GENIUS_ACCESS_TOKEN = "IXqQ9CVYss5OoeMTNd65QJYUc8CMKRuXUBRAoTYvtfh_6h2K7lx7sOysj43nFAMC"
GENIUS_API_URL = "https://api.genius.com"

# Initialize NLTK's VADER sentiment analyzer
# try:
analyzer = SentimentIntensityAnalyzer(lexicon_file="vader_lexicon.txt")
# except Exception as e:
#     print(f"error initializing sentiment analyzer...: {e}")

# Initialize Flask app
app = Flask(__name__)

# --- Helper Functions (Your existing functions) ---
def search_song_on_genius(song_title, artist_name):
    """
    Searches for a song on Genius and returns the first hit's ID and URL.
    """
    search_url = f"{GENIUS_API_URL}/search"
    headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}
    params = {"q": f"{song_title} {artist_name}"}

    print(f"Searching for: {song_title} by {artist_name}...")

    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        for hit in data["response"]["hits"]:
            # A more flexible check for the artist name
            hit_artist = hit["result"]["primary_artist"]["name"]
            if artist_name.lower() in hit_artist.lower():
                song_id = hit["result"]["id"]
                song_url = hit["result"]["url"]
                print(f"Found song! ID: {song_id}, URL: {song_url}")
                return song_id, song_url
        print(f"No exact match found for '{song_title}' by '{artist_name}'.")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error searching for song: {e}")
        return None, None

def get_lyrics_from_url(song_url):
    """
    Fetches lyrics from a Genius song URL by scraping the page.
    This version tries multiple common selectors to be more robust.
    """
    try:
        response = requests.get(song_url)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        soup = BeautifulSoup(response.text, "html.parser")

        # List of potential selectors for the lyrics container
        potential_selectors = [
            "div.Lyrics__Container-sc-1ynbvzw-5",  # Common selector
            "div[data-lyrics-container='true']",    # Another common selector
            "div.lyrics",                          # Older, simple selector
            "div.SongPage__Lyrics-sc-17j49q-4"     # Yet another variant
        ]

        lyrics_div = None
        for selector in potential_selectors:
            lyrics_div = soup.select_one(selector)
            if lyrics_div:
                print(f"Lyrics found using selector: {selector}")
                break

        if lyrics_div:
            lyrics = lyrics_div.get_text(separator="\n").strip()
            # Clean up the lyrics by removing section titles like [Chorus]
            lyrics = re.sub(r"\[.*?\]", "", lyrics)
            # Remove empty lines
            lyrics = "\n".join([line.strip() for line in lyrics.split('\n') if line.strip()])
            return lyrics
        else:
            print("Lyrics container not found using any known selector.")
            return "Lyrics not found on page."
    except requests.exceptions.RequestException as e:
        print(f"Error fetching lyrics from URL '{song_url}': {e}")
        return "Error fetching lyrics."

def analyze_sentiment(text):
    """
    Performs sentiment analysis on the given text using VADER.
    Returns a dictionary of scores (neg, neu, pos, compound).
    """
    return analyzer.polarity_scores(text)


def generate_sentiment_wordcloud(lyrics):
    """
    Generates a color-coded word cloud based on sentiment.
    - Positive words (simple list) in green/teal.
    - Negative words (simple list) in red.
    - Neutral words in grey.
    Returns a base64 encoded string of the image.
    """
    positive_words = ['love', 'happy', 'joy', 'good', 'great', 'beautiful', 'bright', 'sweet', 'paradise', 'dream', 'bless', 'hope', 'peace', 'smile', 'sunshine', 'star', 'alive', 'free', 'win', 'rise', 'shine']
    negative_words = ['hate', 'sad', 'pain', 'bad', 'dark', 'fear', 'alone', 'broken', 'cry', 'death', 'struggle', 'lost', 'tears', 'ache', 'sorrow', 'cold', 'empty', 'fall', 'die', 'suffering', 'hell']

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        word_lower = word.lower()
        if word_lower in positive_words:
            return "hsl(180, 70%, 50%)"
        elif word_lower in negative_words:
            return "hsl(0, 70%, 50%)"
        else:
            return "grey"

    stop_words = set(nltk.corpus.stopwords.words('english'))
    lyric_specific_stopwords = ['oh', 'yeah', 'uh', 'hmm', 'ooh', 'chorus', 'verse', 'intro', 'outro', 'repeat', 'feat', 'ft']
    stop_words.update(lyric_specific_stopwords)

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        color_func=color_func,
        stopwords=stop_words,
        min_font_size=10,
        max_words=100
    ).generate(lyrics)

    # Convert the word cloud image to base64
    img_buffer = io.BytesIO()
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    img_b64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    plt.close() # Close the plot to free up memory

    return img_b64

def get_song_lyrics(song_title, artist_name):
    """
    Combines search and scrape to get lyrics.
    """
    song_id, song_url = search_song_on_genius(song_title, artist_name)
    if song_url:
        lyrics = get_lyrics_from_url(song_url)
        return lyrics
    return "Song not found."

# --- Flask Routes ---

@app.route('/')
def main_index():
    """
    The main app hub with links to the other apps.
    """
    return render_template('main_index.html')

@app.route('/lyrics', methods=['GET', 'POST'])
def lyrics_analyzer_page():
    """
    Handles the lyric analyzer app logic.
    """
    wordcloud_image_data = None
    sentiment_data = None
    overall_mood = None
    error_message = None

    if request.method == 'POST':
        song_title = request.form['song_title']
        artist_name = request.form['artist_name']

        if not song_title or not artist_name:
            error_message = "Please enter both a song title and an artist name."
        else:
            lyrics = get_song_lyrics(song_title, artist_name)
            print(f"Lyrics fetched: {lyrics[:100]}...") # Print first 100 characters for debugging

            if lyrics and lyrics != "Song not found." and lyrics != "Error fetching lyrics.":
                sentiment_data = analyze_sentiment(lyrics)
                if sentiment_data['compound'] >= 0.05:
                    overall_mood = "Positive 😊"
                elif sentiment_data['compound'] <= -0.05:
                    overall_mood = "Negative 😔"
                else:
                    overall_mood = "Neutral 🤔"

                wordcloud_image_data = generate_sentiment_wordcloud(lyrics)
            else:
                error_message = f"Could not find lyrics for '{song_title}' by '{artist_name}'. Please check spelling."

    return render_template('lyrics.html',
                           wordcloud_image=wordcloud_image_data,
                           sentiment=sentiment_data,
                           mood=overall_mood,
                           error=error_message)

@app.route('/soundbar')
def soundbar_app():
    """
    The route for the soundbar app.
    """
    return render_template('soundbar.html')
