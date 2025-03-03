import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import tweepy
from dotenv import load_dotenv
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from io import BytesIO
import json
import traceback
import webbrowser
import textwrap
import colorsys
from collections import Counter
import math
import random

# Load environment variables
load_dotenv()

print("Loading environment variables...")
# Spotify API setup
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8888/callback'

# Twitter API setup
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

# Constants for image generation
CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 630
BACKGROUND_COLOR = "#FF3366"  # Vibrant red
TEXT_COLOR = "#FFFFFF"  # White
SECONDARY_COLOR = "#FFE5E5"  # Light pink

# Font paths for Windows
FONT_PATH = "C:\\Windows\\Fonts\\Arial.ttf"  # Default to Arial
BOLD_FONT_PATH = "C:\\Windows\\Fonts\\Arialbd.ttf"  # Arial Bold

print("Initializing Spotify client...")
# Initialize Spotify OAuth
auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-read-currently-playing user-read-playback-state',
    open_browser=True
)

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=auth_manager)

print("Initializing Twitter clients...")
# Initialize Twitter clients (v1.1 for media upload and v2 for tweets)
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
)
auth.set_access_token(
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET
)

# Initialize both v1.1 and v2 clients
api = tweepy.API(auth)
client = tweepy.Client(
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

def format_duration(ms):
    """Convert milliseconds to MM:SS format"""
    seconds = int(ms / 1000)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def download_image(url):
    """Download image from URL and return as BytesIO object"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        img_data = BytesIO(response.content)
        img_data.seek(0)
        return img_data
    except Exception as e:
        print(f"Error downloading image from {url}: {str(e)}")
        raise

def get_dominant_colors(image, num_colors=3):
    """Extract dominant colors from an image"""
    # Resize image to speed up processing
    img = image.copy()
    img.thumbnail((150, 150))
    
    # Convert image to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get colors from image
    pixels = img.getdata()
    pixel_count = Counter(pixels)
    
    # Sort by most common
    dominant_colors = sorted(pixel_count.items(), key=lambda x: x[1], reverse=True)
    
    # Convert to HSV and sort by saturation
    hsv_colors = [colorsys.rgb_to_hsv(r/255, g/255, b/255) for (r,g,b), count in dominant_colors[:10]]
    sorted_colors = sorted(zip(hsv_colors, dominant_colors[:10]), key=lambda x: x[0][1], reverse=True)
    
    # Convert back to RGB
    return [(int(r), int(g), int(b)) for _, ((r,g,b), count) in sorted_colors[:num_colors]]

def create_gradient_background(size, colors):
    """Create a gradient background with multiple colors"""
    image = Image.new('RGB', size)
    draw = ImageDraw.Draw(image)
    
    width, height = size
    num_colors = len(colors)
    
    # Create diagonal gradient
    for y in range(height):
        for x in range(width):
            # Calculate position in the gradient (0 to 1)
            pos = (x + y) / (width + height)
            
            # Find the two colors to interpolate between
            color_idx = int(pos * (num_colors - 1))
            color_idx = min(color_idx, num_colors - 2)
            
            # Calculate interpolation factor
            factor = (pos * (num_colors - 1)) - color_idx
            
            # Get the two colors
            c1 = colors[color_idx]
            c2 = colors[color_idx + 1]
            
            # Interpolate
            r = int(c1[0] * (1 - factor) + c2[0] * factor)
            g = int(c1[1] * (1 - factor) + c2[1] * factor)
            b = int(c1[2] * (1 - factor) + c2[2] * factor)
            
            draw.point((x, y), fill=(r, g, b))
    
    return image

def create_geometric_overlay(size, color, num_shapes=50):
    """Create a geometric pattern overlay"""
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    width, height = size
    r, g, b = color
    
    for _ in range(num_shapes):
        shape_type = _ % 3
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(20, 100)
        alpha = random.randint(3, 10)
        
        if shape_type == 0:  # Circle
            draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2],
                        fill=(r, g, b, alpha))
        elif shape_type == 1:  # Rectangle
            draw.rectangle([x-size//2, y-size//2, x+size//2, y+size//2],
                         fill=(r, g, b, alpha))
        else:  # Triangle
            points = [(x, y-size//2),
                     (x-size//2, y+size//2),
                     (x+size//2, y+size//2)]
            draw.polygon(points, fill=(r, g, b, alpha))
    
    return overlay

def create_song_image(track_name, artist_name, album_name, duration, album_art_url):
    """Create a beautiful image with song details and enhanced visual effects"""
    try:
        # Download and process album art
        album_art = Image.open(download_image(album_art_url))
        album_art = album_art.resize((400, 400), Image.Resampling.LANCZOS)
        
        # Get dominant colors from album art
        dominant_colors = get_dominant_colors(album_art, num_colors=4)
        main_color = dominant_colors[0]
        accent_color = dominant_colors[1] if len(dominant_colors) > 1 else main_color
        
        # Create base image
        image = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT))
        
        # Create dynamic gradient background
        gradient = create_gradient_background((CANVAS_WIDTH, CANVAS_HEIGHT), 
                                           [main_color, accent_color, 
                                            tuple(int(c * 0.6) for c in main_color)])
        image.paste(gradient)
        
        # Add subtle patterns
        for i in range(20):
            size = random.randint(100, 400)
            x = random.randint(-size//2, CANVAS_WIDTH + size//2)
            y = random.randint(-size//2, CANVAS_HEIGHT + size//2)
            alpha = random.randint(5, 15)
            
            pattern = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            pattern_draw = ImageDraw.Draw(pattern)
            
            if random.choice([True, False]):
                # Draw circle
                pattern_draw.ellipse([0, 0, size, size], 
                                   fill=(255, 255, 255, alpha))
            else:
                # Draw rounded rectangle
                pattern_draw.rounded_rectangle([0, 0, size, size], 
                                            radius=size//4,
                                            fill=(255, 255, 255, alpha))
            
            pattern = pattern.rotate(random.randint(0, 360))
            image.paste(pattern, (x, y), pattern)
        
        # Load fonts with error handling
        try:
            title_font = ImageFont.truetype(BOLD_FONT_PATH, 80)
            artist_font = ImageFont.truetype(FONT_PATH, 60)
            details_font = ImageFont.truetype(FONT_PATH, 45)
        except Exception as e:
            print(f"Error loading fonts: {str(e)}, falling back to default")
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            details_font = ImageFont.load_default()
        
        # Create a drawing object
        draw = ImageDraw.Draw(image)
        
        # Calculate center positions
        album_art_x = 150
        album_art_y = (CANVAS_HEIGHT - 400) // 2
        text_start_x = 650
        
        # Create glow effect for album art
        glow_size = 420
        glow = Image.new('RGBA', (glow_size, glow_size), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        for i in range(10):
            alpha = int(20 - i * 2)
            expanded_size = i * 2
            glow_draw.rectangle([expanded_size, expanded_size, 
                               glow_size - expanded_size, glow_size - expanded_size],
                              fill=(*main_color, alpha))
        
        # Apply glow
        image.paste(glow, (album_art_x - 10, album_art_y - 10), glow)
        
        # Add album art with white border
        border = 8
        draw.rectangle([
            (album_art_x - border, album_art_y - border),
            (album_art_x + 400 + border, album_art_y + 400 + border)
        ], fill='white')
        image.paste(album_art, (album_art_x, album_art_y))
        
        def draw_text_with_enhanced_shadow(x, y, text, font, main_color=(255, 255, 255), shadow_color=(0, 0, 0)):
            # Convert string color names to RGB tuples
            if isinstance(main_color, str):
                if main_color == 'white':
                    main_color = (255, 255, 255)
                elif main_color == 'black':
                    main_color = (0, 0, 0)
            
            # Multiple shadow layers for depth
            shadow_layers = [
                (4, 4, 40),
                (3, 3, 60),
                (2, 2, 80)
            ]
            
            for offset_x, offset_y, alpha in shadow_layers:
                # Create shadow color with alpha
                shadow_rgba = (*shadow_color, alpha)
                draw.text((x + offset_x, y + offset_y), text, 
                         font=font, fill=shadow_rgba)
            
            # Main text
            draw.text((x, y), text, font=font, fill=main_color)
        
        # Draw song title with wrapping
        y = 100
        title_lines = textwrap.wrap(track_name, width=20)
        for line in title_lines:
            draw_text_with_enhanced_shadow(text_start_x, y, line, 
                                         title_font, (255, 255, 255))
            y += 90
        
        # Draw artist name
        y += 20
        draw_text_with_enhanced_shadow(text_start_x, y, f"by {artist_name}", 
                                     artist_font, (255, 235, 235))
        
        # Add decorative line
        y += 80
        line_length = 400
        line_thickness = 4
        for i in range(line_thickness):
            alpha = 255 - (i * 40)
            draw.line([(text_start_x, y + i), 
                      (text_start_x + line_length, y + i)],
                     fill=(*accent_color, alpha), width=1)
        
        # Draw album and duration with icons
        y += 60
        draw_text_with_enhanced_shadow(text_start_x, y, f"💿  {album_name}", 
                                     details_font, (255, 255, 255))
        y += 70
        draw_text_with_enhanced_shadow(text_start_x, y, f"⏱  {duration}", 
                                     details_font, (255, 255, 255))
        
        # Add final overlay gradient for depth
        overlay = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for i in range(CANVAS_HEIGHT):
            alpha = int((i / CANVAS_HEIGHT) * 30)
            overlay_draw.line([(0, i), (CANVAS_WIDTH, i)], 
                            fill=(0, 0, 0, alpha))
        
        image = Image.alpha_composite(image.convert('RGBA'), overlay)
        
        # Convert back to RGB for saving
        image = image.convert('RGB')
        
        # Save and return
        output = BytesIO()
        image.save(output, format='PNG')
        output.seek(0)
        return output
        
    except Exception as e:
        print(f"Error creating custom image: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return None

def tweet_current_song():
    """Get current song from Spotify and tweet it"""
    try:
        print("Fetching current track from Spotify...")
        # Get current playing track
        current_track = sp.current_playback()
        
        if current_track is None:
            print("No track currently playing")
            return

        track = current_track['item']
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        duration = format_duration(track['duration_ms'])
        album_name = track['album']['name']
        thumbnail_url = track['album']['images'][0]['url']
        
        print(f"Current track: {track_name} by {artist_name}")
        
        # Create tweet text
        tweet_text = f"🎵 Now Playing:\n{track_name} - {artist_name}\nAlbum: {album_name}\nDuration: {duration} #listening"
        
        print("Creating custom image...")
        # Create custom image with song details
        custom_image = create_song_image(
            track_name,
            artist_name,
            album_name,
            duration,
            thumbnail_url
        )
        
        if custom_image:
            print("Uploading custom image to Twitter...")
            try:
                # Upload media using v1.1 API
                media_upload = api.media_upload(filename="song_card.png", file=custom_image)
                print("Media uploaded successfully")
                
                print("Sending tweet...")
                # Send tweet with media using v2 API
                client.create_tweet(text=tweet_text, media_ids=[media_upload.media_id])
                print(f"Successfully tweeted: {tweet_text}")
            except Exception as e:
                print("Failed to upload media or send tweet, sending text-only tweet")
                print(f"Error: {str(e)}")
                # Try sending tweet without media
                client.create_tweet(text=tweet_text)
                print(f"Successfully tweeted (without media): {tweet_text}")
        else:
            print("Failed to create custom image, sending text-only tweet")
            client.create_tweet(text=tweet_text)
            print(f"Successfully tweeted (without media): {tweet_text}")
        
    except Exception as e:
        print(f"Error in tweet_current_song: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()

def main():
    print("Starting Spotify to Twitter bot...")
    last_tweeted_song = None
    
    while True:
        try:
            print("\nChecking current playback...")
            current_track = sp.current_playback()
            
            if current_track is not None:
                current_song_id = current_track['item']['id']
                print(f"Found track with ID: {current_song_id}")
                
                # Only tweet if the song has changed
                if current_song_id != last_tweeted_song:
                    print("New song detected, tweeting...")
                    tweet_current_song()
                    last_tweeted_song = current_song_id
                else:
                    print("Same song still playing, waiting...")
            else:
                print("No track currently playing")
            
            # Wait for 30 seconds before checking again
            print("Waiting 30 seconds before next check...")
            time.sleep(30)
            
        except Exception as e:
            print(f"Error in main loop: {str(e)}")
            print("Full traceback:")
            traceback.print_exc()
            time.sleep(30)

if __name__ == "__main__":
    main() 