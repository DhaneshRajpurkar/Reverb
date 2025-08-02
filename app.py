import requests
import re
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
from flask import Flask, request, render_template, send_file
import uuid

# --- Configuration ---
# IMPORTANT: Replace YOUR_GENIUS_CLIENT_ACCESS_TOKEN with your actual token
GENIUS_ACCESS_TOKEN = "YOUR_GENIUS_CLIENT_ACCESS_TOKEN" # Your actual token here
GENIUS_API_URL = "https://api.genius.com"

# Initialize NLTK's VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

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

    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        for hit in data["response"]["hits"]:
            if hit["result"]["primary_artist"]["name"].lower() == artist_name.lower():
                return hit["result"]["id"], hit["result"]["url"]
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"Error searching for song: {e}")
        return None, None

def get_lyrics_from_url(song_url):
    """
    Fetches lyrics from a Genius song URL by scraping the page.
    """
    try:
        response = requests.get(song_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        lyrics_div = soup.find("div", class_="Lyrics__Container-sc-1ynbvzw-5")
        if not lyrics_div:
            lyrics_div = soup.find("div", attrs={"data-lyrics-container": "true"})

        if lyrics_div:
            lyrics = lyrics_div.get_text(separator="\n").strip()
            lyrics = re.sub(r"\[.*?\]", "", lyrics)
            lyrics = "\n".join([line.strip() for line in lyrics.split('\n') if line.strip()])
            return lyrics
        else:
            return "Lyrics not found on page."
    except requests.exceptions.RequestException as e:
        print(f"Error fetching lyrics from URL: {e}")
        return "Error fetching lyrics."

def analyze_sentiment(text):
    """
    Performs sentiment analysis on the given text using VADER.
    Returns a dictionary of scores (neg, neu, pos, compound).
    """
    return analyzer.polarity_scores(text)


def generate_sentiment_wordcloud(lyrics, output_filename="wordcloud.png"):
    """
    Generates a color-coded word cloud based on sentiment.
    - Positive words (simple list) in green/teal.
    - Negative words (simple list) in red.
    - Neutral words in grey.
    Saves the word cloud as a PNG image.
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

    wordcloud.to_file(output_filename)
    return output_filename

# --- Flask Routes ---

@app.route('/')
def main_index():
    """
    The main app hub with links to the other apps.
    """
    return render_template('main_index.html')

@app.route('/lyrics', methods=['GET', 'POST'])
def lyrics_analyzer():
    """
    Handles the lyric analyzer app logic.
    """
    wordcloud_image_path = None
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

            if lyrics and lyrics != "Song not found.":
                sentiment_data = analyze_sentiment(lyrics)
                if sentiment_data['compound'] >= 0.05:
                    overall_mood = "Positive 😊"
                elif sentiment_data['compound'] <= -0.05:
                    overall_mood = "Negative 😔"
                else:
                    overall_mood = "Neutral 🤔"

                os.makedirs('static', exist_ok=True)
                wc_filename = f"static/wordcloud_{uuid.uuid4()}.png"
                wordcloud_image_path = generate_sentiment_wordcloud(lyrics, wc_filename)
            else:
                error_message = f"Could not find lyrics for '{song_title}' by '{artist_name}'. Please check spelling."

    return render_template('lyrics.html',
                           wordcloud_image=wordcloud_image_path,
                           sentiment=sentiment_data,
                           mood=overall_mood,
                           error=error_message)

@app.route('/soundbar')
def soundbar_app():
    """
    The route for the soundbar app.
    """
    return render_template('soundbar.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """
    Serves static files like the generated word cloud image.
    """
    return send_file(os.path.join('static', filename))

# --- Run Flask App ---
if __name__ == "__main__":
    print("Starting Flask application...")
    app.run(debug=True)
