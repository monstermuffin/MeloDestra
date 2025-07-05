import os
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, render_template, request, redirect, session, url_for, jsonify, send_file
import requests 
import re 
import io 
from urllib.parse import urlparse, unquote 
import yaml 
import json 
import pylast 
import time 

app = Flask(__name__)
app.secret_key = os.urandom(64) 

# All the config stuff to support env vars w/ defaults
DEFAULT_CONFIG = {
    "SPOTIPY_CLIENT_ID": None,
    "SPOTIPY_CLIENT_SECRET": None,
    "LASTFM_API_KEY": None,
    "LASTFM_SHARED_SECRET": None,
    "refresh_interval_ms": 5000,
    "color_thief_quality": 1,
    "gray_zone_low": 0.30,
    "gray_zone_high": 0.70,
    "animated_background": {
        "enabled": True,
        "palette_colors": 5,
        "duration": '30s',
    },
    "animation_ease": 'cubic-bezier(0.25, 0.1, 0.25, 1.0)',
    "fade_duration": '0.4s',
    "fade_stagger_ms": 50,
    "ken_burns": {
        "enabled": True,
        "duration": '40s',
        "scale_factor": 1.05,
    },
    "display": {
        "genre": True,
        "like_icon": True,
        "shuffle_icon": True,
        "progress_bar": True,
        "time_info": True,
        "lastfm_playcount": True,
        "hide_cursor": False,
    },
    "lastfm": {
        "username": "",
    },
    "genre_blacklist": [
        "lidarr", "seen live", "fip", "favorite", "favs",
        "owned", "wishlist", "library", "collection", "to listen", "buy, Funk_add_to_lidarr_batch_1"
    ],
    "SPOTIPY_REDIRECT_URI": "http://127.0.0.1:5000/callback", #  must use 127.0.0.1, spotify will reject localhost as mfw 'not secure'
    "USE_REMOTE_SETUP_MODE": True,
}

def get_env_var(var_name, default=None, var_type=str):
    value = os.environ.get(var_name)
    if value is None:
        return default
    
    if var_type == bool:
        return value.lower() in ('true', '1', 't', 'yes', 'y')
    if var_type == int:
        try:
            return int(value)
        except ValueError:
            return default
    if var_type == float:
        try:
            return float(value)
        except ValueError:
            return default
    if var_type == list:
        return [item.strip() for item in value.split(',')]
    return value # Defaults to string

def load_and_merge_config():
    yaml_config = {}
    try:
        with open('config.yml', 'r') as f:
            yaml_config = yaml.safe_load(f) or {}
        print("Successfully loaded config.yml")
    except FileNotFoundError:
        print("INFO: config.yml not found. Using environment variables and defaults.")
    except yaml.YAMLError as e:
        print(f"ERROR: Could not parse config.yml: {e}. Using environment variables and defaults.")

    # Helper to get value: env -> yaml -> default
    def _get_value(env_name, yaml_path, default_val, var_type=str, is_nested=False):
        val = get_env_var(env_name, None, var_type)
        if val is not None:
            return val

        # Try "colour" version first for specific keys if applicable
        yaml_path_colour = None
        if yaml_path == "color_thief_quality":
            yaml_path_colour = "colour_thief_quality"

        for current_yaml_path in [yaml_path_colour, yaml_path] if yaml_path_colour else [yaml_path]:
            if current_yaml_path is None:
                continue

            temp_val_source = yaml_config
            if is_nested and '.' in current_yaml_path:
                keys = current_yaml_path.split('.')
                temp_val = temp_val_source
                for key in keys:
                    if isinstance(temp_val, dict) and key in temp_val:
                        temp_val = temp_val[key]
                    else:
                        temp_val = None
                        break
            elif not is_nested and current_yaml_path in temp_val_source:
                temp_val = temp_val_source[current_yaml_path]
            else:
                temp_val = None

            if temp_val is not None:
                # Type conversion
                if var_type == bool and not isinstance(temp_val, bool): return str(temp_val).lower() in ('true', '1', 't', 'yes', 'y')
                if var_type == int and not isinstance(temp_val, int): return int(temp_val) if str(temp_val).isdigit() else default_val
                if var_type == float and not isinstance(temp_val, float):
                    try: # Handle potential conversion error
                        return float(temp_val)
                    except (ValueError, TypeError):
                        return default_val
                return temp_val
        
        return default_val

    config = {
        "SPOTIPY_CLIENT_ID": _get_value("MD_SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_ID", DEFAULT_CONFIG["SPOTIPY_CLIENT_ID"], str),
        "SPOTIPY_CLIENT_SECRET": _get_value("MD_SPOTIPY_CLIENT_SECRET", "SPOTIPY_CLIENT_SECRET", DEFAULT_CONFIG["SPOTIPY_CLIENT_SECRET"], str),
        "SPOTIPY_REDIRECT_URI": _get_value("MD_SPOTIPY_REDIRECT_URI", "SPOTIPY_REDIRECT_URI", DEFAULT_CONFIG["SPOTIPY_REDIRECT_URI"], str),
        "LASTFM_API_KEY": _get_value("MD_LASTFM_API_KEY", "LASTFM_API_KEY", DEFAULT_CONFIG["LASTFM_API_KEY"], str),
        "LASTFM_SHARED_SECRET": _get_value("MD_LASTFM_SHARED_SECRET", "LASTFM_SHARED_SECRET", DEFAULT_CONFIG["LASTFM_SHARED_SECRET"], str),
        "refresh_interval_ms": _get_value("MD_REFRESH_INTERVAL_MS", "refresh_interval_ms", DEFAULT_CONFIG["refresh_interval_ms"], int),
        "color_thief_quality": _get_value("MD_COLOR_THIEF_QUALITY", "color_thief_quality", DEFAULT_CONFIG["color_thief_quality"], int),
        "gray_zone_low": _get_value("MD_GRAY_ZONE_LOW", "gray_zone_low", DEFAULT_CONFIG["gray_zone_low"], float),
        "gray_zone_high": _get_value("MD_GRAY_ZONE_HIGH", "gray_zone_high", DEFAULT_CONFIG["gray_zone_high"], float),
        "animation_ease": _get_value("MD_ANIMATION_EASE", "animation_ease", DEFAULT_CONFIG["animation_ease"], str),
        "fade_duration": _get_value("MD_FADE_DURATION", "fade_duration", DEFAULT_CONFIG["fade_duration"], str),
        "fade_stagger_ms": _get_value("MD_FADE_STAGGER_MS", "fade_stagger_ms", DEFAULT_CONFIG["fade_stagger_ms"], int),
        
        "animated_background": {
            "enabled": _get_value("MD_ANIMATED_BACKGROUND_ENABLED", "animated_background.enabled", DEFAULT_CONFIG["animated_background"]["enabled"], bool, True),
            "palette_colors": _get_value("MD_ANIMATED_BACKGROUND_PALETTE_COLORS", "animated_background.palette_colors", DEFAULT_CONFIG["animated_background"]["palette_colors"], int, True),
            "duration": _get_value("MD_ANIMATED_BACKGROUND_DURATION", "animated_background.duration", DEFAULT_CONFIG["animated_background"]["duration"], str, True),
        },
        "ken_burns": {
            "enabled": _get_value("MD_KEN_BURNS_ENABLED", "ken_burns.enabled", DEFAULT_CONFIG["ken_burns"]["enabled"], bool, True),
            "duration": _get_value("MD_KEN_BURNS_DURATION", "ken_burns.duration", DEFAULT_CONFIG["ken_burns"]["duration"], str, True),
            "scale_factor": _get_value("MD_KEN_BURNS_SCALE_FACTOR", "ken_burns.scale_factor", DEFAULT_CONFIG["ken_burns"]["scale_factor"], float, True),
        },
        "display": {
            "genre": _get_value("MD_DISPLAY_GENRE", "display.genre", DEFAULT_CONFIG["display"]["genre"], bool, True),
            "like_icon": _get_value("MD_DISPLAY_LIKE_ICON", "display.like_icon", DEFAULT_CONFIG["display"]["like_icon"], bool, True),
            "shuffle_icon": _get_value("MD_DISPLAY_SHUFFLE_ICON", "display.shuffle_icon", DEFAULT_CONFIG["display"]["shuffle_icon"], bool, True),
            "progress_bar": _get_value("MD_DISPLAY_PROGRESS_BAR", "display.progress_bar", DEFAULT_CONFIG["display"]["progress_bar"], bool, True),
            "time_info": _get_value("MD_DISPLAY_TIME_INFO", "display.time_info", DEFAULT_CONFIG["display"]["time_info"], bool, True),
            "lastfm_playcount": _get_value("MD_DISPLAY_LASTFM_PLAYCOUNT", "display.lastfm_playcount", DEFAULT_CONFIG["display"]["lastfm_playcount"], bool, True),
            "hide_cursor": _get_value("MD_DISPLAY_HIDE_CURSOR", "display.hide_cursor", DEFAULT_CONFIG["display"]["hide_cursor"], bool, True),
        },
        "lastfm": {
             "username": _get_value("MD_LASTFM_USERNAME", "lastfm.username", DEFAULT_CONFIG["lastfm"]["username"], str, True),
        },
        "genre_blacklist": _get_value("MD_GENRE_BLACKLIST", "genre_blacklist", DEFAULT_CONFIG["genre_blacklist"], list),
        "USE_REMOTE_SETUP_MODE": _get_value("MD_USE_REMOTE_SETUP_MODE", "USE_REMOTE_SETUP_MODE", DEFAULT_CONFIG["USE_REMOTE_SETUP_MODE"], bool),
    }
    return config

APP_CONFIG = load_and_merge_config()

    # spotify tings
CLIENT_ID = APP_CONFIG["SPOTIPY_CLIENT_ID"]
CLIENT_SECRET = APP_CONFIG["SPOTIPY_CLIENT_SECRET"]
REDIRECT_URI = APP_CONFIG["SPOTIPY_REDIRECT_URI"]
USE_REMOTE_SETUP_MODE = APP_CONFIG["USE_REMOTE_SETUP_MODE"]

# Detect deployment type and set redirect URI
if USE_REMOTE_SETUP_MODE:
    REDIRECT_URI = "http://127.0.0.1:8888/callback"
    print("INFO: Remote Setup Mode enabled. Using 127.0.0.1 redirect URI for remote authentication.")
elif REDIRECT_URI == "http://127.0.0.1:5000/callback":
    print("INFO: Using local development authentication (127.0.0.1:5000).")

SCOPE = "user-read-currently-playing user-read-playback-state user-library-read user-library-modify" 
CACHE_PATH = ".spotify_cache"

if not CLIENT_ID or not CLIENT_SECRET:
    print("ERROR: SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET must be configured via config.yml or environment variables (MD_SPOTIPY_CLIENT_ID, MD_SPOTIPY_CLIENT_SECRET).")

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE_PATH,
    show_dialog=True 
)

# lastfm tings
LASTFM_API_KEY = APP_CONFIG["LASTFM_API_KEY"]
LASTFM_SHARED_SECRET = APP_CONFIG["LASTFM_SHARED_SECRET"]
LASTFM_USERNAME = APP_CONFIG.get('lastfm', {}).get('username')

LASTFM_USERNAME = APP_CONFIG["lastfm"]["username"]


LASTFM_APP_KEYS_VALID = False
LASTFM_USER_VALID = False
lastfm_network = None

lastfm_api_key_provided = bool(LASTFM_API_KEY)
lastfm_shared_secret_provided = bool(LASTFM_SHARED_SECRET)

if lastfm_api_key_provided and lastfm_shared_secret_provided:
    try:
        print("Attempting to initialize Last.fm network with API key/secret...")
        temp_username_for_init = LASTFM_USERNAME if LASTFM_USERNAME else "fs_placeholder_user" # pylast needs a username string
        lastfm_network = pylast.LastFMNetwork(
            api_key=LASTFM_API_KEY,
            api_secret=LASTFM_SHARED_SECRET,
            username=temp_username_for_init 
        )
        print("Last.fm network object initialized. Testing API key/secret validity...")
        test_tags = lastfm_network.get_artist("Cher").get_top_tags(limit=1)
        if test_tags:
            print(f"Last.fm API key/secret test successful. General Last.fm features (like genre) enabled.")
            LASTFM_APP_KEYS_VALID = True
        else:
            print("ERROR: Last.fm API key/secret test call returned no data. General Last.fm features will be disabled.")

    except pylast.WSError as e:
        print(f"ERROR: Last.fm API WSError during app key/secret validation: {e}. All Last.fm features disabled.")
    except Exception as e:
        print(f"ERROR: Failed to initialize Last.fm network or test app keys: {e}. All Last.fm features disabled.")

    if LASTFM_APP_KEYS_VALID and bool(LASTFM_USERNAME): # Check actual username from new config
        try:
            print(f"Attempting to validate Last.fm username: '{LASTFM_USERNAME}'...")
            test_user = lastfm_network.get_user(LASTFM_USERNAME) 
            user_playcount = test_user.get_playcount()
            print(f"Last.fm username '{LASTFM_USERNAME}' validated successfully. User-specific Last.fm features (playcount) enabled.")
            LASTFM_USER_VALID = True
        except pylast.WSError as e:
            print(f"ERROR: Last.fm API WSError validating username '{LASTFM_USERNAME}': {e}. User-specific features (playcount) will be disabled.")
        except Exception as e:
            print(f"ERROR: Failed to validate Last.fm username '{LASTFM_USERNAME}': {e}. User-specific features (playcount) will be disabled.")
    elif LASTFM_APP_KEYS_VALID and not bool(LASTFM_USERNAME):
        print("Last.fm username not provided. User-specific features (playcount) will be disabled. Genre fetching may still work if enabled.")
else:
    missing_creds = []
    if not lastfm_api_key_provided: missing_creds.append("MD_LASTFM_API_KEY or LASTFM_API_KEY in config.yml")
    if not lastfm_shared_secret_provided: missing_creds.append("MD_LASTFM_SHARED_SECRET or LASTFM_SHARED_SECRET in config.yml")
    if missing_creds: # only print if there are actual missing API keys/secrets, not just username
        print(f"Last.fm API key/secret missing ({', '.join(missing_creds)}). All Last.fm features disabled.")

# caching mechanism - probably fine?
artwork_cache = {
    "key": None,      
    "url": None,
    "source": None    
}

last_known_track_id = None
last_known_liked_status = False
last_known_shuffle_state = False 
last_known_play_count = None 
last_known_artist_genres = [] 

def get_token():
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        
        return None
    
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

@app.route('/')
def index():
    token_info = get_token()
    if not token_info:
        if USE_REMOTE_SETUP_MODE:
            return render_template('device_setup.html', 
                                 client_id=CLIENT_ID,
                                 redirect_uri=REDIRECT_URI,
                                 scope=SCOPE)
        else:
            auth_url = sp_oauth.get_authorize_url()
            return redirect(auth_url)
    
    
    return render_template('index.html', app_config=json.dumps(APP_CONFIG))

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    if not code:
        return "Error: No authorization code received", 400
    
    try:
        # Get access token using the authorisation code and save it to cache
        token_info = sp_oauth.get_access_token(code)
        print(f"Successfully obtained and cached access token - redirecting to app")
        
        return redirect(url_for('index', _external=True))
    except Exception as e:
        print(f"Error during authentication: {e}")
        return f"Authentication failed: {e}", 400

@app.route('/device-auth')
def device_auth():
    if not USE_REMOTE_SETUP_MODE:
        return "Remote setup mode is not enabled", 400
    
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

def get_itunes_artwork(artist_name, album_name):    
    simplified_album_name = re.sub(r"\s*\(.*\)\s*", "", album_name).strip()
    simplified_album_name = re.sub(r"\s*\[.*\]\s*", "", simplified_album_name).strip()
    # normalisation for matching - required else most mismatches
    print(f"iTunes Search: Artist='{artist_name}', Simplified Album='{simplified_album_name}' (Original: '{album_name}')")

    try:
        search_term = f"{artist_name} {simplified_album_name}"
        search_url = "https://itunes.apple.com/search"
        params = {
            "term": search_term,
            "media": "music",
            "entity": "album",
            "limit": 1 
        }
        headers = {'Accept': 'application/json'} 
        response = requests.get(search_url, params=params, headers=headers, timeout=5) 
        
        print(f"iTunes Response Status: {response.status_code}") 
        response.raise_for_status() 
        
        results_data = response.json()
        results = results_data.get('results', [])
        print(f"iTunes Raw Results Count: {len(results)}")  # Results can be inconsistent for compilations and special editions
        if results:
            itunes_album_name = results[0].get('collectionName', '')
            itunes_artist_name = results[0].get('artistName', '')
            print(f"iTunes Top Result: Artist='{itunes_artist_name}', Album='{itunes_album_name}'")

            
            
            if (simplified_album_name.lower() in itunes_album_name.lower() and 
                artist_name.lower() in itunes_artist_name.lower()):
                artwork_url_100 = results[0].get('artworkUrl100')
                if artwork_url_100:
                    print(f"iTunes original artworkUrl100: {artwork_url_100}") 
                    high_res_url = artwork_url_100.replace('100x100', '1200x1200')
                    print(f"Match found! Returning URL: {high_res_url}")
                    return high_res_url
                else:
                    print("Match criteria met, but no artworkUrl100 found.")
            else:
                print("Match criteria not met.")
        else:
             print("No results found in iTunes response.")

    except requests.exceptions.RequestException as e:
        print(f"iTunes API request failed: {e}")
    except Exception as e:
        print(f"Error processing iTunes data: {e}")
        
    return None 

# CORS proxy for artwork
ALLOWED_IMAGE_DOMAINS = ["i.scdn.co", "is1-ssl.mzstatic.com"] 

@app.route('/artwork-proxy')
def artwork_proxy():
    image_url = request.args.get('url')
    if not image_url:
        return "Missing image URL", 400

    
    image_url = unquote(image_url)

    
    parsed_url = urlparse(image_url)
    if parsed_url.hostname not in ALLOWED_IMAGE_DOMAINS:
        print(f"Blocked proxy request for disallowed domain: {parsed_url.hostname}")
        return "Domain not allowed for proxying", 403
        
    if not parsed_url.scheme in ['http', 'https']:
         return "Invalid URL scheme", 400

    try:
        print(f"Proxying image from: {image_url}")
        
        response = requests.get(image_url, stream=True, timeout=10) 
        response.raise_for_status()

        
        content_type = response.headers.get('content-type', 'application/octet-stream')

        
        img_io = io.BytesIO(response.content)
        img_io.seek(0)
        return send_file(
            img_io,
            mimetype=content_type,
            as_attachment=False 
        )

    except requests.exceptions.RequestException as e:
        print(f"Failed to proxy image {image_url}: {e}")
        return "Failed to fetch image", 502 
    except Exception as e:
        print(f"Error in proxy: {e}")
        return "Proxy error", 500

@app.route('/current-song')
def current_song():
    token_info = get_token()
    if not token_info:
        return jsonify({"error": "Not authenticated"}), 401

    access_token = token_info['access_token']
    sp = spotipy.Spotify(auth=access_token)

    # Probably should be a class..
    global last_known_track_id, last_known_liked_status, last_known_shuffle_state, last_known_play_count, last_known_artist_genres

    try:
        current_track = sp.current_playback()
        if not (current_track and current_track['item']):
             return jsonify({"is_playing": current_track.get('is_playing', False)}) 
        if not current_track['is_playing']:
            artwork_cache["key"] = None
            artwork_cache["url"] = None
            artwork_cache["source"] = None
            return jsonify({"is_playing": False})

        item = current_track['item']
        progress_ms = current_track['progress_ms']
        duration_ms = item['duration_ms']
        shuffle_state = current_track.get('shuffle_state', False) 
        repeat_state = current_track.get('repeat_state', 'off') 
        
        artist_name_primary = item['artists'][0]['name']
        album_name = item['album']['name']
        track_name = item['name']
        current_key_artwork = (artist_name_primary, album_name) 
        track_id = item.get('id')

        is_new_track = (track_id != last_known_track_id)

        if is_new_track:
            print("============================================")
            print(f" NEW TRACK DETECTED: {track_name}")
            print(f" Artist: {artist_name_primary}")
            print(f" Album: {album_name}")
            print(f" Spotify ID: {track_id}")
            print("============================================")

        genre_blacklist_lower = [str(g).lower() for g in APP_CONFIG['genre_blacklist']]
            
        artist_genres_for_current_response = []
        display_genre_config = APP_CONFIG['display']['genre']

        if is_new_track:
            print("Genre/Tags: Processing for new track...")
            fetched_genres_for_new_track = []

            if display_genre_config:
                if LASTFM_APP_KEYS_VALID and lastfm_network:
                    print(f"Genre/Tags: Fetching from Last.fm for artist '{artist_name_primary}' (new track)...")
                    try:
                        lfm_artist = lastfm_network.get_artist(artist_name_primary)
                        top_tags = lfm_artist.get_top_tags(limit=3)
                        if top_tags:
                            raw_genres = [tag.item.get_name() for tag in top_tags]
                            fetched_genres_for_new_track = [genre for genre in raw_genres if genre.lower() not in genre_blacklist_lower]
                            print(f"Genre/Tags: Fetched raw: {raw_genres}. Filtered to: {fetched_genres_for_new_track}")
                        else:
                            print(f"Genre/Tags: No tags found on Last.fm for '{artist_name_primary}'.")
                    except pylast.WSError as e:
                        print(f"Genre/Tags: Last.fm API WSError fetching tags for '{artist_name_primary}': {e}. Details: {e.details}")
                    except Exception as e:
                        print(f"Genre/Tags: Generic error fetching Last.fm tags for '{artist_name_primary}': {e}")
                elif not LASTFM_APP_KEYS_VALID:
                    print("Genre/Tags: Display genre is enabled in config, but Last.fm API Key/Secret are invalid or not configured. Genres will not be fetched.")
            else:
                print("Genre/Tags: Display genre is disabled in config. Genres will not be fetched.")
            
            last_known_artist_genres = fetched_genres_for_new_track
            artist_genres_for_current_response = fetched_genres_for_new_track
        else: 
            artist_genres_for_current_response = last_known_artist_genres 

        current_api_is_liked = False 
        if track_id:
            try:
                results = sp.current_user_saved_tracks_contains(tracks=[track_id])
                if results and isinstance(results, list) and len(results) > 0:
                    current_api_is_liked = results[0]
                    if track_id != last_known_track_id or current_api_is_liked != last_known_liked_status:
                        print(f"Liked status for track {track_id} is: {current_api_is_liked}. (Stored: {last_known_liked_status if track_id == last_known_track_id else 'N/A - New Track'})")
                        last_known_liked_status = current_api_is_liked
                else:
                    print(f"Could not determine liked status for track {track_id} via API, using last known: {last_known_liked_status if track_id == last_known_track_id else 'False (new track with no API result)'}.")
                    
                    current_api_is_liked = last_known_liked_status if track_id == last_known_track_id else False
                    last_known_liked_status = current_api_is_liked 
            except spotipy.exceptions.SpotifyException as se:
                print(f"Spotify API error checking liked status for track {track_id}: {se}. Using last known: {last_known_liked_status if track_id == last_known_track_id else 'False (new track with API error)'}.")
                current_api_is_liked = last_known_liked_status if track_id == last_known_track_id else False
                last_known_liked_status = current_api_is_liked 
            except Exception as e:
                print(f"Generic error checking liked status for track {track_id}: {e}. Using last known: {last_known_liked_status if track_id == last_known_track_id else 'False (new track with generic error)'}.")
                current_api_is_liked = last_known_liked_status if track_id == last_known_track_id else False
                last_known_liked_status = current_api_is_liked 
        else:
            print("No track ID found. Cannot check liked status. Setting to False.")
            current_api_is_liked = False
            last_known_liked_status = False 

        
        if track_id != last_known_track_id:
            last_known_track_id = track_id

        is_liked = last_known_liked_status 

        # Artwork resolution handling
        spotify_artwork_url = None
        final_artwork_url = None
        final_source = None

        # Check cache first to prevent additional API calls
        if current_key_artwork == artwork_cache.get("key") and artwork_cache.get("url"):
            final_artwork_url = artwork_cache["url"]
            final_source = artwork_cache["source"] 
            
        elif is_new_track: 
            print(f"Artwork cache miss for new track {album_name}. Querying iTunes...")
            
            if item['album']['images']:
                 spotify_artwork_url = item['album']['images'][0]['url']
            final_artwork_url = spotify_artwork_url 
            final_source = 'spotify'
            
            itunes_url = get_itunes_artwork(artist_name_primary, album_name)
            if itunes_url:
                final_artwork_url = itunes_url
                final_source = 'itunes'
            
            print(f"Using {final_source} artwork for {album_name}")
            
            artwork_cache["key"] = current_key_artwork
            artwork_cache["url"] = final_artwork_url
            artwork_cache["source"] = final_source
        else: 
              # Edge case handling for cache misses on same track
              print(f"Warning: Same track but artwork cache miss. Refetching.")
              if item['album']['images']:
                   spotify_artwork_url = item['album']['images'][0]['url']
              final_artwork_url = spotify_artwork_url
              final_source = 'spotify'
              itunes_url = get_itunes_artwork(artist_name_primary, album_name)
              if itunes_url:
                  final_artwork_url = itunes_url
                  final_source = 'itunes'
              artwork_cache["key"] = current_key_artwork
              artwork_cache["url"] = final_artwork_url
              artwork_cache["source"] = final_source

        # Get Last.fm play count data
        play_count = last_known_play_count
        display_lastfm_playcount = APP_CONFIG['display']['lastfm_playcount']

        if is_new_track:
             print(f"New track detected ({track_id}). Checking Last.fm play count.")
             
             fetched_play_count = None
             if display_lastfm_playcount:
                 if LASTFM_USER_VALID and lastfm_network:
                     try:
                        lastfm_track_obj = lastfm_network.get_track(artist_name_primary, item['name'])
                        fetched_play_count = lastfm_track_obj.get_userplaycount()
                        print(f"Last.fm play count for '{item['name']}': {fetched_play_count}")
                     except pylast.WSError as e:
                         print(f"Last.fm API WSError for '{item['name']}' playcount: {e}")
                     except Exception as e:
                         print(f"Generic error fetching Last.fm play count for '{item['name']}': {e}")
                 elif not LASTFM_USER_VALID:
                    print("Play Count: Display Last.fm playcount is enabled in config, but Last.fm Username is invalid/not configured, or API keys are invalid. Play count will not be fetched.")
             else:
                print("Play Count: Display Last.fm playcount is disabled in config. Play count will not be fetched.")

             last_known_play_count = fetched_play_count
             play_count = fetched_play_count
        else:
             # Play count won't change while on same track
             pass 

        # Track shuffle state changes for UI consistency
        current_api_shuffle_state = current_track.get('shuffle_state', False)
        if current_api_shuffle_state != last_known_shuffle_state:
            print(f"Shuffle state changed (API vs stored): {last_known_shuffle_state} -> {current_api_shuffle_state}")
            last_known_shuffle_state = current_api_shuffle_state 
        
            
        shuffle_state = last_known_shuffle_state 

        # Prepare response with all collected data
        data = {
            "is_playing": True,
            "song": track_name,
            "artist": ", ".join(artist['name'] for artist in item['artists']),
            "album": album_name,
            "artwork_url": final_artwork_url,
            "progress_ms": progress_ms,
            "duration_ms": duration_ms,
            "genres": artist_genres_for_current_response, 
            "is_liked": is_liked,
            "shuffle_state": shuffle_state, 
            "repeat_state": current_track.get('repeat_state', 'off'), 
            "play_count": play_count 
        }
        
        print(f"Current track: {track_name} | Liked: {is_liked} | Shuffle: {shuffle_state}")
        
        return jsonify(data)
    except Exception as e: 
        print(f"Error in current_song: {e}") 
        import traceback
        traceback.print_exc() 
        return jsonify({"error": "Failed to fetch data"}), 500

@app.route('/toggle-like', methods=['POST'])
def toggle_like_current_song():
    token_info = get_token()
    if not token_info:
        return jsonify({"error": "Not authenticated"}), 401

    access_token = token_info['access_token']
    sp = spotipy.Spotify(auth=access_token)

    try:
        current_track = sp.current_playback()
        if not (current_track and current_track['item'] and current_track.get('is_playing')):
            return jsonify({"error": "Nothing currently playing"}), 404

        track_id = current_track['item'].get('id')
        if not track_id:
            return jsonify({"error": "Could not get track ID"}), 404

        # Determine current liked state
        is_liked_results = sp.current_user_saved_tracks_contains(tracks=[track_id])
        if not (is_liked_results and isinstance(is_liked_results, list) and len(is_liked_results) > 0):
            print(f"Error checking liked status for track {track_id}")
            return jsonify({"error": "Could not determine liked status"}), 500
        
        is_currently_liked = is_liked_results[0]

        global last_known_liked_status, last_known_track_id

        if is_currently_liked:
            sp.current_user_saved_tracks_delete(tracks=[track_id])
            action_taken = "unliked"
            
            if track_id == last_known_track_id:
                 last_known_liked_status = False
            print(f"Track {track_id} unliked successfully.")
        else:
            sp.current_user_saved_tracks_add(tracks=[track_id])
            action_taken = "liked"
             
            if track_id == last_known_track_id:
                 last_known_liked_status = True
            print(f"Track {track_id} liked successfully.")

        set_visual_feedback()

        return jsonify({"success": True, "action": action_taken, "track_id": track_id, "visual_feedback": True}), 200

    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error toggling like for track: {e}")
        
        if e.http_status == 401:
             return jsonify({"error": "Spotify authentication error"}), 401
        return jsonify({"error": "Spotify API error"}), 500
    except Exception as e:
        print(f"Error toggling like for track: {e}")
        return jsonify({"error": "Server error"}), 500

visual_feedback_state = {
    "active": False,
    "timestamp": 0
}

def set_visual_feedback():
    global visual_feedback_state
    visual_feedback_state = {
        "active": True,
        "timestamp": time.time()
    }
    print("Visual feedback set: knock detected")

@app.route('/visual-feedback')
def get_visual_feedback():
    global visual_feedback_state
    
    if visual_feedback_state["active"] and (time.time() - visual_feedback_state["timestamp"]) > 5:
        visual_feedback_state["active"] = False
    
    response = {
        "active": visual_feedback_state["active"]
    }
    
    if visual_feedback_state["active"]:
        visual_feedback_state["active"] = False
    
    return jsonify(response)

@app.route('/trigger-feedback', methods=['POST']) # test endpoint for da blinky
def trigger_visual_feedback():
    try:
        set_visual_feedback()
        return jsonify({"success": True}), 200
        
    except Exception as e:
        print(f"Error triggering visual feedback: {e}")
        return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    # TODO: Use proper logging instead of print statements
    host = "0.0.0.0"
    port = 5000
    app.run(host=host, port=port, debug=True) 