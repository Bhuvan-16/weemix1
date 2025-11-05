
# Weemix — Spotify Song Recommender Chatbot (Render-ready)

This project is a Flask web app that recommends Spotify songs based on user mood.
It uses Spotipy to fetch recommendations and displays album art + 30s preview if available.

## Files
- `app.py` — main Flask app
- `requirements.txt` — Python dependencies
- `Procfile` — command for Render / Heroku
- `.render.yaml` — optional convenience file for Render service (not required)

## Before deploying
1. Create a Spotify Developer App at: https://developer.spotify.com/dashboard
2. In the app settings, set **Redirect URI** to:
   ```
   https://weemix.onrender.com/callback
   ```
3. Copy your **Client ID** and **Client Secret**.

## Local testing (optional)
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Set environment variables locally (example on macOS / Linux):
   ```
   export SPOTIPY_CLIENT_ID="your_client_id"
   export SPOTIPY_CLIENT_SECRET="your_client_secret"
   export SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"
   export FLASK_SECRET_KEY="change-this-secret"
   ```
3. Run locally:
   ```
   python app.py
   ```
   Visit http://localhost:8080 and log in with Spotify.

## Deploying to Render (recommended steps)
1. Push this repository to GitHub.
2. Go to https://render.com and create a new **Web Service**.
3. Connect your GitHub repo and choose this project.
4. For **Start Command**, use:
   ```
   gunicorn app:app
   ```
5. In Render's **Environment** settings add these variables:
   - `SPOTIPY_CLIENT_ID` = your client id
   - `SPOTIPY_CLIENT_SECRET` = your client secret
   - `SPOTIPY_REDIRECT_URI` = `https://weemix.onrender.com/callback`
   - `FLASK_SECRET_KEY` = any random secret string
6. Deploy. When your service is live, Render will provide a URL like:
   ```
   https://weemix.onrender.com
   ```
7. Update the Redirect URI in the Spotify Dashboard to:
   ```
   https://weemix.onrender.com/callback
   ```

## Notes
- Do not commit your Spotify client secret to a public repo.
- If you want TTS, preview playback on the server won't stream to users — the app includes <audio> tags so user's browser plays previews directly.
