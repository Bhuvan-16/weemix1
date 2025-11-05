# 🎧 Weemix — Spotify Chatbot (Flask + Spotipy)
# Save this as app.py
# Do NOT hardcode credentials here. Provide them via environment variables:
# SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
# On Render set these in the Environment section of your service.

from flask import Flask, render_template_string, request, redirect, session, jsonify
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-this-in-production")

# Read Spotify credentials from environment (Render/Heroku style)
SPOTIPY_CLIENT_ID = os.environ.get("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.environ.get("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.environ.get("SPOTIPY_REDIRECT_URI")

if not (SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET and SPOTIPY_REDIRECT_URI):
    raise RuntimeError("Missing one of SPOTIPY_CLIENT_ID / SPOTIPY_CLIENT_SECRET / SPOTIPY_REDIRECT_URI in environment")

scope = "user-read-private,user-top-read,playlist-read-private"


@app.route('/')
def index():
    if 'token_info' not in session:
        return redirect('/login')
    return render_template_string("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🎵 Weemix — Spotify Chatbot</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
        body { background-color: #121212; color: white; font-family: Arial, sans-serif; margin: 0; display:flex; flex-direction:column; height:100vh;}
        header { background-color: #1DB954; padding: 12px; text-align:center; font-size:18px; font-weight:bold; color:white; }
        #chat-box { flex:1; overflow-y:auto; padding:15px; display:flex; flex-direction:column; gap:10px; }
        .user, .bot { padding:10px; border-radius:10px; max-width:75%; line-height:1.5;}
        .user { background-color:#1DB954; align-self:flex-end; color:black; }
        .bot { background-color:#333; align-self:flex-start; }
        .song-card { background:#1e1e1e; border-radius:10px; padding:10px; margin-top:5px; }
        .song-card img { width:100%; border-radius:8px; margin-top:6px; }
        #input-area { display:flex; padding:10px; background-color:#1DB954; }
        input { flex:1; padding:10px; border:none; border-radius:5px; outline:none; font-size:14px; }
        button { padding:10px 15px; margin-left:10px; background-color:white; color:#1DB954; border:none; border-radius:5px; font-weight:bold; cursor:pointer; }
        audio { width:100%; margin-top:6px; }
        a { color:#1DB954; text-decoration:none; }
    </style>
</head>
<body>
    <header>🎵 Weemix — Spotify Song Recommender</header>
    <div id="chat-box">
        <div class="bot">Hello! Tell me how you feel — happy, sad, relaxed, romantic, or energetic.</div>
    </div>

    <div id="input-area">
        <input id="user-input" type="text" placeholder="Type your mood..." autofocus>
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            if (!message) return;
            const chatBox = document.getElementById('chat-box');
            const userDiv = document.createElement('div');
            userDiv.className = 'user';
            userDiv.textContent = message;
            chatBox.appendChild(userDiv);
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mood: message })
            });
            const data = await res.json();
            const botDiv = document.createElement('div');
            botDiv.className = 'bot';
            botDiv.textContent = data.reply;
            chatBox.appendChild(botDiv);

            if (data.songs && data.songs.length > 0) {
                data.songs.forEach(song => {
                    const card = document.createElement('div');
                    card.className = 'song-card';
                    const title = document.createElement('div');
                    title.innerHTML = '<strong>' + song.name + '</strong> — ' + song.artist;
                    card.appendChild(title);
                    const link = document.createElement('div');
                    link.innerHTML = '<a href="' + song.url + '" target="_blank">🎧 Open in Spotify</a>';
                    card.appendChild(link);
                    if (song.image) {
                        const img = document.createElement('img');
                        img.src = song.image;
                        card.appendChild(img);
                    }
                    if (song.preview) {
                        const audio = document.createElement('audio');
                        audio.controls = true;
                        const source = document.createElement('source');
                        source.src = song.preview;
                        source.type = 'audio/mpeg';
                        audio.appendChild(source);
                        card.appendChild(audio);
                    } else {
                        const p = document.createElement('p');
                        p.textContent = '⚠ No preview available';
                        card.appendChild(p);
                    }
                    chatBox.appendChild(card);
                });
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    </script>
</body>
</html>
""")

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
                            scope=scope,
                            cache_path='.cache-weemix')
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
        return jsonify({"reply":"Please log in.", "songs":[]})

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
    results = sp.recommendations(seed_genres=[genre], limit=5, country='US', min_popularity=50)
    tracks = results.get("tracks", [])
    if not tracks:
    # fallback using playlist search
    playlist = sp.search(q=f"{mood} hits", type="playlist", limit=1)
    if playlist["playlists"]["items"]:
        pl_id = playlist["playlists"]["items"][0]["id"]
        pl_tracks = sp.playlist_tracks(pl_id, limit=5)
        tracks = [t["track"] for t in pl_tracks["items"] if t.get("track")]


    songs = []
    for track in results['tracks']:
        image = track['album']['images'][0]['url'] if track['album']['images'] else None
        songs.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "url": track['external_urls']['spotify'],
            "preview": track.get('preview_url'),
            "image": image
        })

    reply = f"Here are some {mood} mood songs!"
    return jsonify({"reply": reply, "songs": songs})

if __name__ == '__main__':
    # In Render, Gunicorn is used (see Procfile). This run() is for local testing.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
