# 🎧 Weemix — Spotify Chatbot (Flask + Spotipy)
# Save this as app.py
# Do NOT hardcode credentials here. Provide them via environment variables:
# SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
# On Render set these in the Environment section of your service.

from flask import Flask, render_template, request, jsonify, redirect, session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecret")

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI", "https://weemix.onrender.com/callback")

scope = "user-read-private,user-top-read,playlist-read-private,user-read-email"

@app.route('/')
def home():
    token_info = session.get('token_info')
    if not token_info:
        return render_template('index.html', logged_in=False)
    return render_template('index.html', logged_in=True)

@app.route('/login')
def login():
    sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                            client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI,
                            scope=scope)
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                            client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI,
                            scope=scope)
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect('/')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    mood = (data.get('mood') or '').lower()
    token_info = session.get('token_info')

    if not token_info:
        return jsonify({"reply": "Please log in first!", "songs": []})

    sp = spotipy.Spotify(auth=token_info['access_token'])
    mood_genres = {
        "happy": "pop",
        "sad": "acoustic",
        "angry": "metal",
        "romantic": "rnb",
        "relaxed": "chill",
        "energetic": "dance"
    }

    genre = mood_genres.get(mood, "pop")

    try:
        results = sp.recommendations(seed_genres=[genre], limit=5, country='US', min_popularity=50)
        tracks = results.get("tracks", [])

        # fallback if recommendations are empty
        if not tracks:
            playlist = sp.search(q=f"{mood} hits", type="playlist", limit=1)
            if playlist["playlists"]["items"]:
                pl_id = playlist["playlists"]["items"][0]["id"]
                pl_tracks = sp.playlist_tracks(pl_id, limit=5)
                tracks = [t["track"] for t in pl_tracks["items"] if t.get("track")]

        if not tracks:
            return jsonify({"reply": "Sorry, I couldn’t find songs for that mood.", "songs": []})

        songs = []
        for t in tracks:
            songs.append({
                "name": t["name"],
                "artist": t["artists"][0]["name"],
                "url": t["external_urls"]["spotify"],
                "image": t["album"]["images"][0]["url"] if t["album"]["images"] else None,
                "preview": t.get("preview_url")
            })

        reply = f"Here are some {mood} mood songs 🎵"
        return jsonify({"reply": reply, "songs": songs})

    except Exception as e:
        print("Spotify API error:", e)
        return jsonify({"reply": "Error fetching songs from Spotify.", "songs": []})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
