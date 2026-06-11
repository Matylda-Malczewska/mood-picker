from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from groq import Groq
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from googleapiclient.discovery import build
import os
import json

load_dotenv()

app = Flask(__name__)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

spotify_client = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

youtube_client = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    mood_text = data.get("mood", "").strip()

    if not mood_text:
        return jsonify({"error": "Opisz swój nastrój!"}), 400

    try:
        prompt = f"""Użytkownik opisał swój nastrój: "{mood_text}"

Przeanalizuj nastrój i zwróć TYLKO obiekt JSON (bez żadnego dodatkowego tekstu, bez znaczników markdown) w tym formacie:
{{
    "mood_summary": "krótki opis nastroju po polsku (1 zdanie)",
    "spotify_query": "zapytanie po angielsku do wyszukania playlisty na Spotify (np. 'chill sad indie playlist')",
    "youtube_query": "zapytanie po angielsku do wyszukania filmu na YouTube (np. 'relaxing drama movie')",
    "mood_emoji": "1-2 emoji pasujące do nastroju",
    "color": "kolor hex pasujący do nastroju (np. #8B5CF6)"
}}"""

        response = groq_client.chat.completions.create(
         model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        mood_data = json.loads(response_text)

    except Exception as e:
        return jsonify({"error": f"Błąd analizy nastroju: {str(e)}"}), 500

    spotify_result = None
    try:
        print("Szukam na Spotify:", mood_data["spotify_query"])
        results = spotify_client.search(
            q=mood_data["spotify_query"],
            type="playlist",
            limit=5,
            market="PL"
        )
        playlists = results.get("playlists", {}).get("items", [])
        playlists = [p for p in playlists if p is not None]
        if playlists:
            p = playlists[0]
            spotify_result = {
                "name": p["name"],
                "url": p["external_urls"]["spotify"],
                "image": p["images"][0]["url"] if p["images"] else None,
                "owner": p["owner"]["display_name"],
                "tracks": p.get("tracks", {}).get("total", 0) if p.get("tracks") else 0
            }
    except Exception as e:
        print("Błąd Spotify:", str(e))
        spotify_result = {"error": str(e)}

    youtube_result = None
    try:
        yt_response = youtube_client.search().list(
            q=mood_data["youtube_query"],
            part="snippet",
            maxResults=1,
            type="video"
        ).execute()

        items = yt_response.get("items", [])
        if items:
            item = items[0]
            video_id = item["id"]["videoId"]
            youtube_result = {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
                "video_id": video_id
            }
    except Exception as e:
        youtube_result = {"error": str(e)}

    return jsonify({
        "mood": mood_data,
        "spotify": spotify_result,
        "youtube": youtube_result
    })


if __name__ == "__main__":
    app.run(debug=True)