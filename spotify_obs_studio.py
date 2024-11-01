import json
from flask import Flask, redirect, url_for, session, render_template_string, request
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os


with open(os.path.join('security', 'spotify_security.json')) as f:
    config = json.load(f)

# Spotify API Credentials
SPOTIPY_CLIENT_ID = config['SPOTIPY_CLIENT_ID']
SPOTIPY_CLIENT_SECRET = config['SPOTIPY_CLIENT_SECRET']
SPOTIPY_REDIRECT_URI = config['SPOTIPY_REDIRECT_URI']

# Flask App Setup
app = Flask(__name__)
app.secret_key = config['SECRET_KEY']
app.config['SESSION_COOKIE_NAME'] = 'spotify_auth'

# Spotipy Auth
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope="user-read-playback-state")

@app.route('/')
def index():
    if not session.get("token_info"):
        return redirect(url_for('login'))

    token_info = session.get("token_info")

    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    sp = Spotify(auth=token_info['access_token'])

    current_playback = sp.current_playback()
    if current_playback and current_playback['is_playing']:
        song = current_playback['item']
        track_name = song['name']
        artist_name = song['artists'][0]['name']
        return render_template_string(f"""
            <html>
            <head>
                <meta http-equiv="refresh" content="2"> 
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;  
                        font-size: 45px;                   
                        text-align: bottom;
                        margin-top: 20%;                  
                    }}
                    strong {{
                        color: #ffffff;                       
                    }}
                </style>
            </head>
            <body>
                <p><strong>{artist_name} - {track_name}</strong></p>
            </body>
            </html>
        """)
    else:
        return render_template_string(f"""
            <html>
            <head>
                <meta http-equiv="refresh" content="2">  
            </head>
            <body>
                <!-- Show nothing -->
            </body>
            </html>
        """)

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.before_request
def before_request():
    session.modified = True
    if 'token_info' in session:
        token_info = session['token_info']
        if sp_oauth.is_token_expired(token_info):
            session['token_info'] = sp_oauth.refresh_access_token(token_info['refresh_token'])

if __name__ == '__main__':
    app.run(debug=True)
