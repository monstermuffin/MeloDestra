// vibe coded JS - wtf does all this even mean
console.log("MeloDestra loaded.");

// Configuration constants, either from global APP_CONFIG or defaults.
const CONFIG = window.APP_CONFIG || {}; 
const REFRESH_INTERVAL_MS = CONFIG.refresh_interval_ms || 5000;
const COLOR_THIEF_QUALITY = CONFIG.color_thief_quality || 1; // Lower is faster, higher is better quality. 1 = best, 10 = default.
const GRAY_ZONE_LOW = CONFIG.gray_zone_low || 0.30; // Luminance threshold for determining if a color is in the "gray zone"
const GRAY_ZONE_HIGH = CONFIG.gray_zone_high || 0.65; // Luminance threshold for determining if a color is in the "gray zone"
const FADE_STAGGER_MS = CONFIG.fade_stagger_ms || 50; // Stagger delay for fade animations.

// Animation and visual effect constants.
const ANIMATION_EASE = CONFIG.animation_ease || 'cubic-bezier(0.25, 0.1, 0.25, 1.0)';
const FADE_DURATION = CONFIG.fade_duration || '0.4s';
const KEN_BURNS_ENABLED = CONFIG.ken_burns?.enabled !== false; 
const KEN_BURNS_DURATION = CONFIG.ken_burns?.duration || '45s';
const KEN_BURNS_SCALE = CONFIG.ken_burns?.scale_factor || 1.05;

// Animated background constants.
const BG_ANIM_ENABLED = CONFIG.animated_background?.enabled !== false; 
const BG_PALETTE_COUNT = CONFIG.animated_background?.palette_colors || 5; // Number of colors to extract for the animated background.
const BG_ANIM_DURATION = CONFIG.animated_background?.duration || '45s';
const BG_ANIM_ANGLE = CONFIG.animated_background?.angle || '135deg';
const BG_ANIM_SIZE = CONFIG.animated_background?.size || '300%';

// Display settings.
const SHOW_LASTFM_PLAYCOUNT = CONFIG.display?.lastfm_playcount !== false; 

// Apply hide cursor if enabled
if (CONFIG.display?.hide_cursor === true) {
    document.body.classList.add('hide-cursor');
}

// Main execution block, runs after the DOM is fully loaded.
document.addEventListener('DOMContentLoaded', () => {
    
    // DOM element references.
    const widget = document.getElementById('spotify-widget');

    const loadingText = widget.querySelector('.loading-text');
    const artworkImg = document.getElementById('album-artwork');
    const trackNameEl = document.getElementById('track-name');
    const artistNameEl = document.getElementById('artist-name');
    const trackInfoDiv = widget.querySelector('.track-info');
    const progressBar = document.getElementById('progress-bar');
    const currentTimeEl = document.getElementById('current-time');
    const totalTimeEl = document.getElementById('total-time');
    const notPlayingText = widget.querySelector('.not-playing');
    const timeInfoEl = widget.querySelector('.time-info');
    const genreInfoEl = document.getElementById('genre-info');
    const likeIconEl = document.getElementById('like-status-icon');
    const shuffleIconEl = document.getElementById('shuffle-status-icon');
    const progressBarContainer = document.getElementById('progress-bar-container');
    const playCountInfoEl = document.getElementById('play-count-info'); 
    const playCountNumberEl = document.getElementById('play-count-number'); 
    
    const lastfmIconContainerEl = document.getElementById('lastfm-icon-container'); 
    const firstScrobbleIconEl = document.getElementById('first-scrobble-icon'); 

    
    // Set CSS custom properties for animations and theming.
    const rootStyle = document.documentElement.style;
    rootStyle.setProperty('--animation-ease', ANIMATION_EASE);
    rootStyle.setProperty('--fade-duration', FADE_DURATION);
    rootStyle.setProperty('--kb-duration', KEN_BURNS_DURATION);
    rootStyle.setProperty('--kb-scale', KEN_BURNS_SCALE);
    rootStyle.setProperty('--kb-animation-name', KEN_BURNS_ENABLED ? 'kenburns-scale' : 'none');
    
    rootStyle.setProperty('--bg-anim-duration', BG_ANIM_DURATION);
    rootStyle.setProperty('--bg-anim-angle', BG_ANIM_ANGLE);
    rootStyle.setProperty('--bg-anim-size', BG_ANIM_SIZE);
    rootStyle.setProperty('--bg-animation-name', BG_ANIM_ENABLED ? 'animatedBodyBackground' : 'none');

    
    // Conditionally hide elements based on configuration.
    if (CONFIG.display?.genre === false) genreInfoEl.style.display = 'none';
    if (CONFIG.display?.like_icon === false) likeIconEl.style.display = 'none';
    if (CONFIG.display?.shuffle_icon === false) shuffleIconEl.style.display = 'none';
    if (CONFIG.display?.progress_bar === false) progressBarContainer.style.display = 'none';
    if (CONFIG.display?.time_info === false) timeInfoEl.style.display = 'none';
    if (!SHOW_LASTFM_PLAYCOUNT) playCountInfoEl.style.display = 'none';
    
    // Hide the icon bar if both like and shuffle icons are disabled.
    if (CONFIG.display?.like_icon === false && CONFIG.display?.shuffle_icon === false) {
        document.getElementById('icon-bar').style.display = 'none';
    }
    
    

    
    // Initialize ColorThief for extracting colors from album art.
    let colorThief = null;
    try {
         colorThief = new ColorThief();
    } catch (e) {
        console.error("Failed to initialize ColorThief. Color features disabled.", e);
        
    }

    // Visual feedback functionality
    function triggerVisualFeedback(feedbackType = 'knock') {
        console.log(`Triggering visual feedback: knock detected`);
        
        // Remove any existing feedback classes
        widget.classList.remove('knock-feedback');
        
        // Use the current progress bar color (from color-thief) for the knock feedback
        const progressBarStyle = getComputedStyle(progressBar);
        const backgroundColor = progressBarStyle.backgroundColor;
        
        console.log(`Progress bar background color: ${backgroundColor}`);
        
        // Extract RGB values from the background color
        let r = 255, g = 100, b = 100; // Default bright red fallback
        if (backgroundColor && backgroundColor.includes('rgb')) {
            const rgbMatch = backgroundColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
            if (rgbMatch) {
                r = parseInt(rgbMatch[1]);
                g = parseInt(rgbMatch[2]);
                b = parseInt(rgbMatch[3]);
            }
        }
        
        console.log(`Setting knock color: rgb(${r}, ${g}, ${b})`);
        
        // Create dynamic CSS animation with the album colors
        const styleId = 'dynamic-knock-feedback';
        let existingStyle = document.getElementById(styleId);
        if (existingStyle) {
            existingStyle.remove();
        }
        
        const dynamicCSS = `
            @keyframes dynamicKnockFeedback {
                0% {
                    background-color: rgba(${r}, ${g}, ${b}, 0);
                    transform: scale(1);
                    filter: brightness(1);
                }
                25% {
                    background-color: rgba(${r}, ${g}, ${b}, 0.7);
                    transform: scale(1.02);
                    filter: brightness(1.3);
                }
                50% {
                    background-color: rgba(${r}, ${g}, ${b}, 0.8);
                    transform: scale(1.03);
                    filter: brightness(1.5);
                }
                75% {
                    background-color: rgba(${r}, ${g}, ${b}, 0.5);
                    transform: scale(1.01);
                    filter: brightness(1.2);
                }
                100% {
                    background-color: rgba(${r}, ${g}, ${b}, 0);
                    transform: scale(1);
                    filter: brightness(1);
                }
            }
            
            #spotify-widget.knock-feedback-dynamic {
                animation: dynamicKnockFeedback 2.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                box-shadow: 0 0 50px rgba(${r}, ${g}, ${b}, 0.6);
            }
        `;
        
        const styleElement = document.createElement('style');
        styleElement.id = styleId;
        styleElement.textContent = dynamicCSS;
        document.head.appendChild(styleElement);
        
        console.log(`Widget classes before: ${widget.className}`);
        
        // Trigger the knock feedback animation with dynamic class
        widget.classList.add('knock-feedback-dynamic');
        
        console.log(`Widget classes after: ${widget.className}`);
        console.log(`Animation should be running for 3 seconds with album color...`);
        
        // Remove the class after animation completes
        setTimeout(() => {
            widget.classList.remove('knock-feedback-dynamic');
            console.log(`Animation complete, classes removed`);
        }, 3500);
    }
    
    // Poll for visual feedback events
    async function checkVisualFeedback() {
        try {
            // Use absolute URL to avoid any relative path issues
            const response = await fetch(`${window.location.origin}/visual-feedback`);
            if (response.ok) {
                const data = await response.json();
                if (data.active) {
                    console.log(`Visual feedback triggered from polling!`);
                    // Trigger feedback regardless of type - it's just acknowledging the knock
                    triggerVisualFeedback();
                }
            }
        } catch (error) {
            // Silently fail - visual feedback is not critical
            console.debug('Visual feedback check failed:', error);
        }
    }
    
    // Start visual feedback polling
    setInterval(checkVisualFeedback, 500); // Check every 500ms for responsive feedback

    // State variables for track and progress.
    let currentTrackId = null;
    let progressIntervalId = null;
    let lastUpdateInfo = {
        progressMs: 0,
        durationMs: 1, // Initialize to 1 to avoid division by zero.
        fetchTime: 0,
        isPlaying: false
    };

    
    // Set initial transitions for various elements.
    artworkImg.style.transition = `opacity var(--fade-duration) var(--animation-ease), transform var(--fade-duration) var(--animation-ease)`;
    trackInfoDiv.style.transition = `opacity var(--fade-duration) var(--animation-ease), transform var(--fade-duration) var(--animation-ease)`;
    progressBar.style.transition = `width 0.25s linear, background-color 1s var(--animation-ease)`;
    likeIconEl.style.transition = `color 0.5s var(--animation-ease), transform 0.3s var(--animation-ease)`;
    shuffleIconEl.style.transition = `color 0.5s var(--animation-ease), transform 0.3s var(--animation-ease)`;
    timeInfoEl.style.transition = `color 1s var(--animation-ease)`;
    genreInfoEl.style.transition = `opacity var(--fade-duration) var(--animation-ease)`;

    // Formats milliseconds into a mm:ss string.
    function formatTime(ms) {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    }

    // Updates the progress bar and time display smoothly between API fetches.
    function updateSmoothProgress() {
        if (!lastUpdateInfo.isPlaying) return;
        const timeElapsed = performance.now() - lastUpdateInfo.fetchTime;
        const estimatedProgressMs = lastUpdateInfo.progressMs + timeElapsed;
        const clampedProgressMs = Math.min(estimatedProgressMs, lastUpdateInfo.durationMs);
        const progressPercent = (clampedProgressMs / lastUpdateInfo.durationMs) * 100;
        progressBar.style.width = `${progressPercent}%`;
        currentTimeEl.textContent = formatTime(clampedProgressMs);
        
        const remainingMs = lastUpdateInfo.durationMs - clampedProgressMs;
        totalTimeEl.textContent = formatTime(remainingMs);
    }

    // Stops the smooth progress interval.
    function stopSmoothProgress() {
        if (progressIntervalId) {
            clearInterval(progressIntervalId);
            progressIntervalId = null;
        }
    }

    
    // Animates an icon by briefly scaling it up.
    function animateIcon(element) {
        element.style.transform = 'scale(1.2)';
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 300);
    }

    
    // Calculates the luminance of an RGB color.
    function calculateLuminance(rgb) {
        if (!rgb || rgb.length < 3) return 0; 
        const [r, g, b] = rgb.map(c => {
            c /= 255.0;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    }

    
    // Determines if a color is light based on its luminance.
    function isColorLight(rgb) {
        return calculateLuminance(rgb) > 0.5; 
    }

    
    // Handles color extraction and application when album artwork loads.
    if (artworkImg && colorThief) {
        artworkImg.addEventListener('load', () => {
            if (artworkImg.src && artworkImg.complete && artworkImg.naturalHeight > 0 && artworkImg.style.display !== 'none') {
                try {
                    
                    // Extract dominant color for progress bar and palette for background.
                    const dominantColorForProgressBar = colorThief.getColor(artworkImg, COLOR_THIEF_QUALITY);
                    const paletteForBackground = colorThief.getPalette(artworkImg, BG_PALETTE_COUNT, COLOR_THIEF_QUALITY); 
                    
                    let progressBarColor = dominantColorForProgressBar || [255, 255, 255]; // Default to white if extraction fails.
                    const progressBarColorString = `rgb(${progressBarColor[0]}, ${progressBarColor[1]}, ${progressBarColor[2]})`;
                    progressBar.style.backgroundColor = progressBarColorString;

                    
                    // Set CSS variables for background palette colors, using defaults if necessary.
                    const defaultBgColors = [[0,0,0], [17,17,17], [34,34,34], [51,51,51], [68,68,68], [85,85,85], [102,102,102], [119,119,119]]; 
                    for (let i = 0; i < BG_PALETTE_COUNT; i++) {
                        
                        const defaultColor = defaultBgColors[i % defaultBgColors.length]; 
                        const color = (paletteForBackground && paletteForBackground[i]) ? paletteForBackground[i] : defaultColor;
                        rootStyle.setProperty(`--bg-palette-color-${i+1}`, `rgb(${color[0]}, ${color[1]}, ${color[2]})`);
                    }
                    
                    // Clear unused palette color variables.
                    for (let i = BG_PALETTE_COUNT; i < 8; i++) { 
                         rootStyle.setProperty(`--bg-palette-color-${i+1}`, null);
                    }

                    
                    // Determine appropriate text colors based on background and progress bar luminance.
                    const bodyPaletteColor1 = (paletteForBackground && paletteForBackground[0]) ? paletteForBackground[0] : defaultBgColors[0];
                    const bodyLuminance = calculateLuminance(bodyPaletteColor1);
                    const progressLuminance = calculateLuminance(progressBarColor);
                    const darkTextColor = '#000000';
                    const lightTextColor = '#FFFFFF';

                    let bodyTextColor;
                    // If body background color is in the "gray zone", use light text. Otherwise, choose based on luminance.
                    if (bodyLuminance > GRAY_ZONE_LOW && bodyLuminance < GRAY_ZONE_HIGH) {
                        bodyTextColor = lightTextColor; 
                    } else {
                        bodyTextColor = bodyLuminance > 0.5 ? darkTextColor : lightTextColor;
                    }

                    let timeTextColor;
                    // If progress bar color is in the "gray zone", use light text. Otherwise, choose based on luminance.
                     if (progressLuminance > GRAY_ZONE_LOW && progressLuminance < GRAY_ZONE_HIGH) {
                        timeTextColor = lightTextColor; 
                    } else {
                        timeTextColor = progressLuminance > 0.5 ? darkTextColor : lightTextColor;
                    }

                    
                    // Apply determined text colors.
                    trackNameEl.style.color = bodyTextColor;
                    artistNameEl.style.color = bodyTextColor; 
                    genreInfoEl.style.color = bodyTextColor;
                    timeInfoEl.style.color = timeTextColor;
                    
                    if (playCountInfoEl) playCountInfoEl.style.color = bodyTextColor; 

                    
                    likeIconEl.style.color = bodyTextColor;
                    shuffleIconEl.style.color = bodyTextColor;
                    
                    if (lastfmIconContainerEl) lastfmIconContainerEl.style.color = bodyTextColor; 

                } catch (error) {
                    console.error('Error processing colors:', error);
                    // Fallback to default colors in case of an error.
                    rootStyle.setProperty('--bg-palette-color-1', '#000000');
                    rootStyle.setProperty('--bg-palette-color-2', '#111111');
                    rootStyle.setProperty('--bg-palette-color-3', '#000000');
                    rootStyle.setProperty('--bg-palette-color-4', '#111111');
                    rootStyle.setProperty('--bg-palette-color-5', '#000000');
                    
                    if (playCountInfoEl) playCountInfoEl.style.color = '#ffffff'; 
                    likeIconEl.style.color = '#ffffff';
                    shuffleIconEl.style.color = '#ffffff';
                    if (lastfmIconContainerEl) lastfmIconContainerEl.style.color = '#ffffff'; 
                }
            }
        });

        // Handles errors when loading album artwork.
        artworkImg.addEventListener('error', () => {
            console.error('Error loading artwork image.');
            progressBar.style.backgroundColor = '#ffffff'; // Default progress bar color.
            // Fallback to default background and text colors.
            rootStyle.setProperty('--bg-palette-color-1', '#000000');
            rootStyle.setProperty('--bg-palette-color-2', '#111111');
            rootStyle.setProperty('--bg-palette-color-3', '#000000');
            rootStyle.setProperty('--bg-palette-color-4', '#111111');
            rootStyle.setProperty('--bg-palette-color-5', '#000000');
            
            if (playCountInfoEl) playCountInfoEl.style.color = '#ffffff'; 
            likeIconEl.style.color = '#ffffff';
            shuffleIconEl.style.color = '#ffffff';
            if (lastfmIconContainerEl) lastfmIconContainerEl.style.color = '#ffffff'; 
        });
    }

    // Fetches current song data from the server and updates the UI.
    async function fetchAndUpdate() {
        try {
            const response = await fetch('/current-song');
            if (!response.ok) {
                console.error("Failed to fetch current song:", response.status);
                stopSmoothProgress();
                lastUpdateInfo.isPlaying = false;
                if (response.status === 401) { // Handle unauthorized access.
                    console.error("Unauthorized. Token might be expired or invalid.");
                    loadingText.textContent = "Authentication needed. Please refresh.";
                    loadingText.style.display = 'block';
                    trackInfoDiv.style.display = 'none';
                    artworkImg.style.display = 'none';
                    notPlayingText.style.display = 'none';
                }
                return;
            }

            const data = await response.json();
            const fetchTimestamp = performance.now(); // Record time of fetch for smooth progress.

            loadingText.style.display = 'none'; // Hide loading text.

            if (data.is_playing) {
                // Show track info and artwork if a song is playing.
                trackInfoDiv.style.display = 'block';
                artworkImg.style.display = 'block';
                notPlayingText.style.display = 'none';

                const newTrackId = data.album + data.song; // Create a unique ID for the current track.
                const trackChanged = currentTrackId !== newTrackId;

                if (trackChanged) {
                    console.log("Track changed!");
                    currentTrackId = newTrackId;
                    
                    const staggerDelay = FADE_STAGGER_MS;
                    const fadeOutDurationMs = parseFloat(FADE_DURATION) * 1000;

                    
                    // Fade out artwork.
                    artworkImg.style.opacity = '0';
                    artworkImg.style.transform = 'scale(0.92)';

                    
                    // Fade out track info and genre with a stagger.
                    setTimeout(() => {
                        trackInfoDiv.style.opacity = '0';
                        trackInfoDiv.style.transform = 'translateY(10px)';
                        genreInfoEl.style.opacity = '0';
                    }, staggerDelay);
                    
                    
                    
                    // Update artwork source through proxy.
                    const originalUrl = data.artwork_url || '';
                    if (originalUrl) {
                        artworkImg.src = `/artwork-proxy?url=${encodeURIComponent(originalUrl)}`;
                    } else {
                        artworkImg.removeAttribute('src'); // Remove src if no artwork URL.
                    }
                    
                    artworkImg.alt = data.album ? `${data.album} Album Artwork` : 'Album Artwork';
                    trackNameEl.textContent = data.song;
                    artistNameEl.textContent = data.artist;
                    totalTimeEl.textContent = formatTime(data.duration_ms);

                    
                    // Display genres if available.
                    if (data.genres && data.genres.length > 0) {
                        genreInfoEl.textContent = data.genres.map(g => g.charAt(0).toUpperCase() + g.slice(1)).join(' / '); 
                    } else {
                        genreInfoEl.textContent = ''; 
                    }
                    
                    
                    // Handle Last.fm play count and first scrobble icon display.
                    let showLastfmCount = false;
                    let showFirstScrobble = false;
                    if (SHOW_LASTFM_PLAYCOUNT && data.play_count !== null && data.play_count !== undefined) {
                        const count = Number(data.play_count);
                        if (count === 0) { // Show first scrobble icon if play count is 0.
                            showFirstScrobble = true;
                        } else {
                            showLastfmCount = true;
                            playCountNumberEl.textContent = data.play_count;
                        }
                    } 
                    
                    lastfmIconContainerEl.style.display = showLastfmCount ? 'inline-flex' : 'none';
                    firstScrobbleIconEl.style.display = showFirstScrobble ? 'inline-block' : 'none'; 
                    
                    // Prepare for fade-in.
                    if(showLastfmCount) lastfmIconContainerEl.style.opacity = '0';
                    if(showFirstScrobble) firstScrobbleIconEl.style.opacity = '0';
                    
                    if (!showLastfmCount) playCountNumberEl.textContent = ''; // Clear play count if not shown.

                    
                    // Fade in new track information after old info has faded out.
                    setTimeout(() => {
                        
                        artworkImg.style.opacity = '1';
                        artworkImg.style.transform = 'scale(1)';
                        
                        // Fade in track info, genre, and Last.fm icons with a stagger.
                        setTimeout(() => {
                             trackInfoDiv.style.opacity = '1';
                             trackInfoDiv.style.transform = 'translateY(0)';
                             genreInfoEl.style.opacity = '1';
                             
                             if (lastfmIconContainerEl.style.display !== 'none') {
                                lastfmIconContainerEl.style.opacity = '1'; 
                             }
                             if (firstScrobbleIconEl.style.display !== 'none') {
                                firstScrobbleIconEl.style.opacity = '1'; 
                             }
                        }, staggerDelay);
                    }, fadeOutDurationMs);
                }

                
                // Update like icon status.
                console.log("Updating like icon. data.is_liked:", data.is_liked);
                const currentlyLiked = likeIconEl.classList.contains('active');
                if (data.is_liked) {
                    if (!currentlyLiked) { // Animate if status changed.
                        animateIcon(likeIconEl);
                    }
                    likeIconEl.className = 'playback-icon fa-solid fa-heart active'; 
                } else {
                    if (currentlyLiked) { // Animate if status changed.
                        animateIcon(likeIconEl); 
                    }
                    likeIconEl.className = 'playback-icon fa-regular fa-heart inactive'; 
                }

                
                // Update shuffle icon status.
                const currentlyShuffling = shuffleIconEl.classList.contains('active');
                if (data.shuffle_state) {
                    if (!currentlyShuffling) { // Animate if status changed.
                        animateIcon(shuffleIconEl);
                    }
                    shuffleIconEl.className = 'playback-icon fa-solid fa-shuffle active'; 
                } else {
                    if (currentlyShuffling) { // Animate if status changed.
                        animateIcon(shuffleIconEl); 
                    }
                    shuffleIconEl.className = 'playback-icon fa-solid fa-shuffle inactive'; 
                }
                
                // Update last known track information.
                lastUpdateInfo = {
                    progressMs: data.progress_ms,
                    durationMs: data.duration_ms || 1, // Default to 1 to avoid division by zero.
                    fetchTime: fetchTimestamp,
                    isPlaying: true
                };

                updateSmoothProgress(); // Update progress immediately.

                // Start smooth progress interval if not already running.
                if (!progressIntervalId) {
                    progressIntervalId = setInterval(updateSmoothProgress, 250);
                }

            } else { // Handle case where nothing is playing.
                if (lastUpdateInfo.isPlaying) { // If something was playing before, fade out the elements.
                     const staggerDelay = FADE_STAGGER_MS;
                     const fadeOutDurationMs = parseFloat(FADE_DURATION) * 1000;

                    
                    artworkImg.style.opacity = '0';
                    artworkImg.style.transform = 'scale(0.95)'; 
                    
                    setTimeout(() => {
                        trackInfoDiv.style.opacity = '0';
                        trackInfoDiv.style.transform = 'translateY(5px)';
                    }, staggerDelay);

                    // After fade out, hide elements and show "not playing" text.
                    setTimeout(() => {
                        trackInfoDiv.style.display = 'none';
                        artworkImg.style.display = 'none';
                        notPlayingText.style.display = 'block';
                        notPlayingText.style.opacity = '0'; 
                        // Double requestAnimationFrame to ensure opacity transition occurs.
                        requestAnimationFrame(() => {
                            requestAnimationFrame(() => { 
                                notPlayingText.style.opacity = '1';
                                
                            });
                        });
                    }, fadeOutDurationMs);
                    
                    
                    // Reset UI elements.
                    genreInfoEl.textContent = ''; 
                    likeIconEl.className = 'playback-icon';
                    shuffleIconEl.className = 'playback-icon';
                    
                    if (playCountInfoEl) playCountInfoEl.style.display = 'none'; 
                    if (playCountNumberEl) playCountNumberEl.textContent = '';
                    
                    if (lastfmIconContainerEl) lastfmIconContainerEl.style.display = 'none'; 
                    if (firstScrobbleIconEl) firstScrobbleIconEl.style.display = 'none'; 
                }
                currentTrackId = null; // Reset current track ID.
                lastUpdateInfo.isPlaying = false;
                stopSmoothProgress(); // Stop smooth progress updates.
            }

        } catch (error) {
            console.error("Error fetching or processing Spotify data:", error);
            // Handle errors during fetch or processing.
            stopSmoothProgress();
            lastUpdateInfo.isPlaying = false;
            loadingText.textContent = "Error connecting. Retrying...";
            loadingText.style.display = 'block';
            trackInfoDiv.style.display = 'none';
            artworkImg.style.display = 'none';
            notPlayingText.style.display = 'none';
            
            // Reset UI elements.
            genreInfoEl.textContent = ''; 
            likeIconEl.className = 'playback-icon';
            shuffleIconEl.className = 'playback-icon';
            
            if (playCountInfoEl) playCountInfoEl.style.display = 'none'; 
            if (playCountNumberEl) playCountNumberEl.textContent = '';
            
            if (lastfmIconContainerEl) lastfmIconContainerEl.style.display = 'none'; 
            if (firstScrobbleIconEl) firstScrobbleIconEl.style.display = 'none'; 
        }
    }

    
    // Initial fetch and set interval for periodic updates.
    fetchAndUpdate();
    setInterval(fetchAndUpdate, REFRESH_INTERVAL_MS);
}); 