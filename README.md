# MeloDestra
_MeloDestra:_ "Melos" - Greek, melody. "Fenestra" - Latin, window.

My Lain teacher said Latin would in fact come in handy one day, and they're still wrong.

![](images/example_portrait.gif)

MeloDestra is a simple web app that displays full-screen album artwork and Spotify song details. It is designed to be used on an SBC (Raspberry Pi) in kiosk mode. It has a focus on a visually appealing "art piece" look. 

MeloDestra is ideal for running on some sort of screen on a wall or something.

For more information about this project and the frame/setup I used, please see my blog post. (Not written yet :kek:)

This project should ideally be used with [PulsDestra,](https://github.com/monstermuffin/PulsDestra) a companion project that allows for toggling likes with a knock on the frame.

## Project Goal
- Display full-screen album artwork and information for currently playing Spotify track.
- Optimize for a portrait-oriented display (see image above and blog post) but a 'responsive' layout was added that works well for all screen sizes and orientations.
- Use high-resolution artwork where possible (more on this below).
- Create a visually appealing "art piece" look with dynamic elements.

## Technology Stack

> [!NOTE]
> Most of the Javascript and ~~a small portion of~~ the CSS was vibe coded because I didn't want to deal with Javascript and CSS. Shoot me.

- **Backend:** Python 3 with Flask web framework.
- **Spotify Integration:** `spotipy` library.
- **Frontend:** HTML, CSS, JavaScript.
- **Dynamic Colors:** `color-thief` library (via CDN in JS) for extracting colours from artwork.
- **High-Res Artwork Source:** iTunes Search API (with fallback to Spotify) (also, yes, that iTunes).
- **Configuration:** Uses `config.yml` for display/behavior settings. Environment variables can override `config.yml` settings, and have defaults if not set.

## Running Locally/Bare Metal
-  **Clone Repository:**
    ```bash
    git clone https://github.com/monstermuffin/melodestra.git
    cd melodestra
    ```
-  **Create Virtual Environment (Recommended):**
    ```bash
    python3 -m venv venv
    ```
-  **Activate Virtual Environment:**
    - macOS/Linux: `source venv/bin/activate`
    - Windows: `.\venv\Scripts\activate`
-  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
-  **Obtain Spotify/Last.fm API Keys:**
    - See below for details on how to get your Spotify/Last.fm API keys.
-  **Configure Application:**
    - Copy `config.example.yml` to `config.yml`:
      ```bash
      cp config.example.yml config.yml
      ```
    - Edit `config.yml` to set your Spotify credentials (`SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`) and any other desired settings (like Last.fm credentials and display preferences).
      ```yaml
      SPOTIPY_CLIENT_ID: 'YOUR_SPOTIFY_CLIENT_ID'
      SPOTIPY_CLIENT_SECRET: 'YOUR_SPOTIFY_CLIENT_SECRET'
      # ... other settings ...
      ```
      
-  **Run the App:**
    ```bash
    python app.py 
    ```

-  **Authenticate:** 
    - Open your browser to `http://127.0.0.1:5000/` or `http://<your-ip>:5000/` (if MeloDestra is running on a different machine). You will be redirected to Spotify to log in and authorize the application.
    - You will be redirected back to MeloDestra where you should see the MeloDestra application.


## Running via Docker (Recommended)

-   **Prerequisites:**
    -   Docker & Docker Compose installed.
-   **Clone Repository:**
    ```bash
    git clone https://github.com/monstermuffin/melodestra.git
    cd melodestra
    ```
-   **Obtain API Keys:**
    -   You will need Spotify API credentials. Last.fm API credentials are optional but highly recommended for genre and playcount features.
    -   See the "Obtaining API Keys" section below for detailed instructions.
-   **Configure Application for Docker:**
    -   The primary way to configure the application when using Docker is through environment variables set in the `docker-compose.yml` file (or `docker-compose.test.yml`).
    -   Copy the example Docker Compose file if you don't have one for your specific needs:
        ```bash
        cp docker-compose.yml docker-compose.yml
        ```
    -   Edit your chosen `docker-compose.yml` file:
        -   **Required:** Set `MD_SPOTIPY_CLIENT_ID` and `MD_SPOTIPY_CLIENT_SECRET` with your Spotify credentials.
        -   **Optional (Highly Recommended):** Set `MD_LASTFM_API_KEY`, `MD_LASTFM_SHARED_SECRET`, and `MD_LASTFM_USERNAME` for Last.fm features.
        -   Adjust any other `MD_` prefixed environment variables as needed (e.g., display options, refresh intervals). Refer to the "Configuration Details" section below for all available variables.
        ```yaml
        # Example snippet from docker-compose.yml or docker-compose.test.yml
        services:
          melodestra:
            image: ghcr.io/monstermuffin/melodestra:latest
            ports:
              - "5010:5000"
            environment:
              MD_SPOTIPY_CLIENT_ID: 'YOUR_SPOTIFY_CLIENT_ID_HERE'
              MD_SPOTIPY_CLIENT_SECRET: 'YOUR_SPOTIFY_CLIENT_SECRET_HERE'
              MD_LASTFM_API_KEY: 'YOUR_LASTFM_API_KEY_HERE'
              MD_LASTFM_SHARED_SECRET: 'YOUR_LASTFM_SECRET_HERE'
              MD_LASTFM_USERNAME: 'YOUR_LASTFM_USERNAME'
              # ... other MD_ prefixed environment variables ...
            volumes:
              - spotify_cache:/app/.spotify_cache # Recommended for persisting Spotify auth
        ```

> [!NOTE]
> The application is designed so that environment variables take precedence. If you also have a `config.yml` file in the project root when building a local image, settings from environment variables will still override it.

-   **Run with Docker Compose:**
    - 
        ```bash
        docker-compose up -d 
        ```

-   **Authenticate:**
    -   Open your browser to `http://<your-ip>:5010`.
    -   You will be redirected to Spotify to log in and authorize the application.
    -   Upon successful authorization, you will be redirected back to MeloDestra.

## Obtaining API Keys
To use MeloDestra, you will need API keys from Spotify. For enhanced features like genre display and play counts, Last.fm API keys are also highly recommended. 

> [!TIP]
> Last.fm API access is generous and free, so just use it.

### Spotify API Keys
1.  **Go to the Spotify Developer Dashboard:** Navigate to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard/) and log in with your Spotify account.
2.  **Create an App:**
    -   Click on "Create an App" (or "Create App").
    -   Give your application a name (e.g., "MeloDestra") and a description.
    -   Agree to the Developer Terms of Service and Design Guidelines.
3.  **Note Your Credentials:**
    -   Once the app is created, you will see your **Client ID**.
    -   Click on "Show client secret" to reveal your **Client Secret**.
    -   You will need both of these for the `MD_SPOTIPY_CLIENT_ID` and `MD_SPOTIPY_CLIENT_SECRET` configuration values.
4.  **Set the Redirect URI:**
    -   In your app settings on the Spotify Developer Dashboard, click on "Edit Settings".
    -   In the "Redirect URIs" section, add the following URI: `http://127.0.0.1:5000/callback`

> [!IMPORTANT]
> This exact URI is hardcoded in the application for the authentication callback. Ensure it matches precisely. Even if you change the host port mapping in Docker (e.g., `5010:5000`), the redirect URI registered with Spotify *must* be `http://127.0.0.1:5000/callback` because that's what the application tells Spotify to use internally.
    
    -   Click "Save" at the bottom of the settings page.

### Last.fm API Keys (Optional)
1.  **Go to the Last.fm API Page:** Navigate to [www.last.fm/api/account/create](https://www.last.fm/api/account/create)
2.  **Create an API Account:**
    -   Fill out the form. You can put your application name (e.g., "MeloDestra") and a brief description.
    -   The callback URL is not necessary.
    -   Submit the form.
3.  **Note Your Credentials:**
    -   Once your API account is created, you will be provided with an **API Key** and a **Shared Secret**.
    -   You will need these for the `MD_LASTFM_API_KEY` and `MD_LASTFM_SHARED_SECRET` configuration values.
    -   You will also need your **Last.fm username** for the `MD_LASTFM_USERNAME` setting if you want to display play counts.

## Configuration Details

> [!NOTE]
> Variables will take the following precedence:
> 1.  **Environment Variables:** Prefixed with `MD_`.
> 2.  **`config.yml` File:** Values defined here are used if not overridden by an environment variable.
> 3.  **Default Values:** Built into the application.

**Required Settings:**

| Environment Variable         | `config.yml` Key        | Description                     |
|------------------------------|-------------------------|---------------------------------|
| `MD_SPOTIPY_CLIENT_ID`       | `SPOTIPY_CLIENT_ID`     | Your Spotify Application Client ID. |
| `MD_SPOTIPY_CLIENT_SECRET`   | `SPOTIPY_CLIENT_SECRET` | Your Spotify Application Client Secret. |

**Optional Settings (with defaults):**

| Environment Variable                        | `config.yml` Path (`.` notation)        | Default Value                         | Type (for Env Var)     | Notes                                                     |
| :------------------------------------------ | :-------------------------------------- | :------------------------------------ | :--------------------- | :-------------------------------------------------------- |
| `MD_LASTFM_API_KEY`                         | `LASTFM_API_KEY`                        | `None`                                | string                 | For Last.fm genre/playcount.                            |
| `MD_LASTFM_SHARED_SECRET`                   | `LASTFM_SHARED_SECRET`                  | `None`                                | string                 | For Last.fm genre/playcount.                            |
| `MD_LASTFM_USERNAME`                        | `lastfm.username`                       | `""` (empty string)                   | string                 | Your Last.fm username.                                    |
| `MD_REFRESH_INTERVAL_MS`                    | `refresh_interval_ms`                   | `5000`                                | int                    | Poll interval for Spotify.                                |
| `MD_COLOR_THIEF_QUALITY`                    | `color_thief_quality` or `colour_thief_quality` | `1`                                   | int                    | 1=highest, 10=faster.                                     |
| `MD_GRAY_ZONE_LOW`                          | `gray_zone_low`                         | `0.30`                                | float                  | Luminance threshold for white text.                       |
| `MD_GRAY_ZONE_HIGH`                         | `gray_zone_high`                        | `0.70`                                | float                  | Luminance threshold for white text.                       |
| `MD_ANIMATED_BACKGROUND_ENABLED`            | `animated_background.enabled`           | `True`                                | boolean                | Enable/disable background animation.                      |
| `MD_ANIMATED_BACKGROUND_PALETTE_COLORS`     | `animated_background.palette_colors`    | `5`                                   | int                    | Colours for gradient (3-8).                                |
| `MD_ANIMATED_BACKGROUND_DURATION`           | `animated_background.duration`          | `'30s'`                               | string                 | Animation cycle duration (CSS time).                      |
| `MD_ANIMATION_EASE`                         | `animation_ease`                        | `'cubic-bezier(0.25, 0.1, 0.25, 1.0)'`  | string                 | Global animation ease function.                           |
| `MD_FADE_DURATION`                          | `fade_duration`                         | `'0.4s'`                              | string                 | Fade duration for track changes.                          |
| `MD_FADE_STAGGER_MS`                        | `fade_stagger_ms`                       | `50`                                  | int                    | Stagger delay for fades (ms).                             |
| `MD_KEN_BURNS_ENABLED`                      | `ken_burns.enabled`                     | `True`                                | boolean                | Enable/disable Ken Burns effect.                          |
| `MD_KEN_BURNS_DURATION`                     | `ken_burns.duration`                    | `'40s'`                               | string                 | Ken Burns duration (CSS time).                            |
| `MD_KEN_BURNS_SCALE_FACTOR`                 | `ken_burns.scale_factor`                | `1.05`                                | float                  | Ken Burns zoom factor.                                    |
| `MD_DISPLAY_GENRE`                          | `display.genre`                         | `True`                                | boolean                | Show genre (requires Last.fm).                            |
| `MD_DISPLAY_LIKE_ICON`                      | `display.like_icon`                     | `True`                                | boolean                | Show like icon.                                           |
| `MD_DISPLAY_SHUFFLE_ICON`                   | `display.shuffle_icon`                  | `True`                                | boolean                | Show shuffle icon.                                        |
| `MD_DISPLAY_PROGRESS_BAR`                   | `display.progress_bar`                  | `True`                                | boolean                | Show progress bar.                                        |
| `MD_DISPLAY_TIME_INFO`                      | `display.time_info`                     | `True`                                | boolean                | Show track time info.                                     |
| `MD_DISPLAY_LASTFM_PLAYCOUNT`               | `display.lastfm_playcount`              | `True`                                | boolean                | Show playcount (requires Last.fm + username).             |
| `MD_DISPLAY_HIDE_CURSOR`                    | `display.hide_cursor`                   | `False`                               | boolean                | Hide cursor for kiosk mode (useful for Raspberry Pi).     |
| `MD_GENRE_BLACKLIST`                        | `genre_blacklist`                       | `["lidarr", "seen live", ...]`        | list (comma-sep str)   | Genres to hide. Env var: "tag1,tag2,tag3".                 |

> [!NOTE]
> For boolean environment variables, values like 'true', '1', 't', 'yes', 'y' (case-insensitive) are considered true. For list environment variables, provide a comma-separated string.
> For `config.yml`, you can use `colour_thief_quality` instead of `color_thief_quality`. Environment variables like `MD_COLOR_THIEF_QUALITY` will always use "COLOR".

## Key Design Decisions
- **Web-based Approach:** Chose Flask + HTML/JS because it was the easiest way to get a simple, responsive web app and I am very dumb.
- **Portrait Optimization:** CSS tailored for a vertical screen as per my build in the blog post.
- **Dynamic Colours:** Color-thief library used to give the frame a dynamic colour palette.
- **Adaptive Contrast:** Text colour dynamically switches between black/white based on background luminance, with specific handling for mid-gray backgrounds to ensure readability.
- **External Artwork:** Use iTunes API to overcome Spotify's artwork resolution limits (640x640). 

> [!TIP]
> iTunes has been great because it's free, generous API without auth and the artwork is great quality (1200x1200). This was a ***noticeable*** difference in quality.

- **Proxy for CORS:** Implemented a backend proxy to allow client-side colour analysis of images hosted on different domains.
- **Polling & Caching:** 
    - Use periodic polling (frontend) for updates, with backend caching for external artwork lookups to reduce API calls. 

> [!NOTE]
> This could probably be improved a lot with WebSockets but I can't be bothered.

> [!NOTE]
> Like status/shuffle state is updated via a poll and this doesn't seem to be an issue with rate limiting.

- **Genre Source:** Switched primarily to Last.fm (if enabled and configured) for fetching artist genres/tags instead of Spotify's API to further reduce calls to Spotify and prevent potential rate limiting issues. 

> [!WARNING]
> When I was using Spotify's API for genre fetching, I was getting 429 errors all the time, multiple times being banned for over 24 hours.

- **/toggle-like:** A `/toggle-like` endpoint was implemented which accepts a POST request with an empty body and returns a JSON response with the new liked status. This is used to update the liked status when the frame is knocked using [PulsDestra](https://github.com/monstermuffin/PulsDestra).

## Next Steps / TODO:
- Implement deployment scripts/instructions for Raspberry Pi (kiosk mode browser setup).
- Dockerize the application for easier deployment.
- Improve error handling and user feedback (e.g., for expired tokens, API errors).
- **Multi-User Support:** Investigate options for displaying playback state from multiple Spotify accounts (e.g., prioritizing a main account).
- **Additional Info:** Option to display album release year, explicit tag.
- Explore alternative/additional artwork sources (MusicBrainz, Fanart.tv).
- Consider WebSockets instead of polling for real-time updates (more complex). 