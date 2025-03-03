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
from collections import Counter, deque
import math
import random
from tqdm import tqdm
import sys
from datetime import datetime, timedelta

load_dotenv()

print("Loading environment variables...")
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8888/callback'

TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 630
BACKGROUND_COLOR = "#FF3366"
TEXT_COLOR = "#FFFFFF"
SECONDARY_COLOR = "#FFE5E5"

FONT_PATH = "C:\\Windows\\Fonts\\Arial.ttf"
BOLD_FONT_PATH = "C:\\Windows\\Fonts\\Arialbd.ttf"

print("Initializing Spotify client...")
auth_manager = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-read-currently-playing user-read-playback-state',
    open_browser=True
)

sp = spotipy.Spotify(auth_manager=auth_manager)

print("Initializing Twitter clients...")
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
)
auth.set_access_token(
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET
)

api = tweepy.API(auth)
client = tweepy.Client(
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

class RateLimitHandler:
    def __init__(self, max_tweets_per_hour=50, max_tweets_per_day=500):
        self.max_tweets_per_hour = max_tweets_per_hour
        self.max_tweets_per_day = max_tweets_per_day
        self.hourly_tweets = deque(maxlen=self.max_tweets_per_hour)
        self.daily_tweets = deque(maxlen=self.max_tweets_per_day)
        self.last_error_time = None
        self.consecutive_errors = 0
    
    def can_tweet(self):
        now = datetime.now()
        
        # Clean up old timestamps
        while self.hourly_tweets and (now - self.hourly_tweets[0]) > timedelta(hours=1):
            self.hourly_tweets.popleft()
        while self.daily_tweets and (now - self.daily_tweets[0]) > timedelta(days=1):
            self.daily_tweets.popleft()
        
        # Check if we're within limits
        if len(self.hourly_tweets) >= self.max_tweets_per_hour:
            return False, "Hourly tweet limit reached"
        if len(self.daily_tweets) >= self.max_tweets_per_day:
            return False, "Daily tweet limit reached"
        
        # If we had a recent error, implement exponential backoff
        if self.last_error_time:
            wait_time = min(15 * (2 ** self.consecutive_errors), 900)  # Max 15 minutes
            if now - self.last_error_time < timedelta(seconds=wait_time):
                return False, f"Cooling down after error ({wait_time}s)"
        
        return True, None
    
    def record_success(self):
        """Record a successful tweet"""
        now = datetime.now()
        self.hourly_tweets.append(now)
        self.daily_tweets.append(now)
        self.last_error_time = None
        self.consecutive_errors = 0
    
    def record_error(self):
        """Record a rate limit error"""
        self.last_error_time = datetime.now()
        self.consecutive_errors += 1

# Create global rate limit handler
rate_limiter = RateLimitHandler()

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
    img = image.copy()
    img.thumbnail((150, 150))
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixels = img.getdata()
    pixel_count = Counter(pixels)
    
    dominant_colors = sorted(pixel_count.items(), key=lambda x: x[1], reverse=True)
    
    hsv_colors = [colorsys.rgb_to_hsv(r/255, g/255, b/255) for (r,g,b), count in dominant_colors[:10]]
    sorted_colors = sorted(zip(hsv_colors, dominant_colors[:10]), key=lambda x: x[0][1], reverse=True)
    
    return [(int(r), int(g), int(b)) for _, ((r,g,b), count) in sorted_colors[:num_colors]]

def create_gradient_background(size, colors):
    """Create a gradient background with multiple colors"""
    image = Image.new('RGB', size)
    draw = ImageDraw.Draw(image)
    
    width, height = size
    num_colors = len(colors)
    
    for y in range(height):
        for x in range(width):
            pos = (x + y) / (width + height)
            
            color_idx = int(pos * (num_colors - 1))
            color_idx = min(color_idx, num_colors - 2)
            
            factor = (pos * (num_colors - 1)) - color_idx
            
            c1 = colors[color_idx]
            c2 = colors[color_idx + 1]
            
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
        
        if shape_type == 0:
            draw.ellipse([x-size//2, y-size//2, x+size//2, y+size//2],
                        fill=(r, g, b, alpha))
        elif shape_type == 1:
            draw.rectangle([x-size//2, y-size//2, x+size//2, y+size//2],
                         fill=(r, g, b, alpha))
        else:
            points = [(x, y-size//2),
                     (x-size//2, y+size//2),
                     (x+size//2, y+size//2)]
            draw.polygon(points, fill=(r, g, b, alpha))
    
    return overlay

def create_song_image(track_name, artist_name, album_name, duration, album_art_url):
    """Create a beautiful image with song details and enhanced visual effects"""
    try:
        album_art = Image.open(download_image(album_art_url))
        album_art = album_art.resize((400, 400), Image.Resampling.LANCZOS)
        
        dominant_colors = get_dominant_colors(album_art, num_colors=4)
        main_color = dominant_colors[0]
        accent_color = dominant_colors[1] if len(dominant_colors) > 1 else main_color
        
        # Create base image
        image = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT))
        
        # Create gradient background
        gradient = create_gradient_background((CANVAS_WIDTH, CANVAS_HEIGHT), 
                                           [main_color, accent_color, 
                                            tuple(int(c * 0.6) for c in main_color)])
        image.paste(gradient)
        
        # Add decorative patterns
        pattern_overlay = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        pattern_draw = ImageDraw.Draw(pattern_overlay)
        
        for i in range(20):
            size = random.randint(100, 400)
            x = random.randint(-size//2, CANVAS_WIDTH + size//2)
            y = random.randint(-size//2, CANVAS_HEIGHT + size//2)
            alpha = random.randint(5, 15)
            
            if random.choice([True, False]):
                pattern_draw.ellipse([x, y, x+size, y+size], 
                                   fill=(255, 255, 255, alpha))
            else:
                pattern_draw.rounded_rectangle([x, y, x+size, y+size], 
                                            radius=size//4,
                                            fill=(255, 255, 255, alpha))
        
        image = Image.alpha_composite(image, pattern_overlay)
        
        try:
            title_font = ImageFont.truetype(BOLD_FONT_PATH, 80)
            artist_font = ImageFont.truetype(FONT_PATH, 60)
            details_font = ImageFont.truetype(FONT_PATH, 45)
        except Exception as e:
            print(f"Error loading fonts: {str(e)}, falling back to default")
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            details_font = ImageFont.load_default()
        
        # Convert to RGBA for drawing
        image = image.convert('RGBA')
        draw = ImageDraw.Draw(image)
        
        # Album art placement
        album_art_x = 150
        album_art_y = (CANVAS_HEIGHT - 400) // 2
        
        # Add glow effect behind album art
        glow = Image.new('RGBA', (420, 420), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        for i in range(10):
            alpha = int(20 - i * 2)
            expanded_size = i * 2
            glow_draw.rectangle([expanded_size, expanded_size, 
                               420 - expanded_size, 420 - expanded_size],
                              fill=(main_color[0], main_color[1], main_color[2], alpha))
        
        image.paste(glow, (album_art_x - 10, album_art_y - 10), glow)
        
        # Add white border and album art
        border = 8
        draw.rectangle([
            (album_art_x - border, album_art_y - border),
            (album_art_x + 400 + border, album_art_y + 400 + border)
        ], fill=(255, 255, 255, 255))
        
        # Convert album art to RGBA
        album_art = album_art.convert('RGBA')
        image.paste(album_art, (album_art_x, album_art_y), album_art)
        
        # Text placement
        text_start_x = 650
        y = 100
        
        # Draw title
        title_lines = textwrap.wrap(track_name, width=20)
        for line in title_lines:
            draw.text((text_start_x, y), line, 
                     font=title_font, fill=(255, 255, 255, 255))
            y += 90
        
        # Draw artist name
        y += 20
        draw.text((text_start_x, y), f"by {artist_name}", 
                 font=artist_font, fill=(255, 235, 235, 255))
        
        # Draw separator line
        y += 80
        line_length = 400
        for i in range(4):
            alpha = 255 - (i * 40)
            draw.line([(text_start_x, y + i), 
                      (text_start_x + line_length, y + i)],
                     fill=(accent_color[0], accent_color[1], accent_color[2], alpha))
        
        # Draw album and duration
        y += 60
        draw.text((text_start_x, y), f"💿  {album_name}", 
                 font=details_font, fill=(255, 255, 255, 255))
        y += 70
        draw.text((text_start_x, y), f"⏱  {duration}", 
                 font=details_font, fill=(255, 255, 255, 255))
        
        # Add subtle gradient overlay
        gradient_overlay = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient_overlay)
        for i in range(CANVAS_HEIGHT):
            alpha = int((i / CANVAS_HEIGHT) * 30)
            gradient_draw.line([(0, i), (CANVAS_WIDTH, i)], 
                             fill=(0, 0, 0, alpha))
        
        image = Image.alpha_composite(image, gradient_overlay)
        
        # Convert back to RGB for saving
        image = image.convert('RGB')
        
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
        # Check rate limits first
        can_tweet, reason = rate_limiter.can_tweet()
        if not can_tweet:
            print(f"\nCannot tweet: {reason}")
            return False
        
        print("Fetching current track from Spotify...")
        current_track = sp.current_playback()
        
        if current_track is None:
            print("No track currently playing")
            return False

        track = current_track['item']
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        duration = format_duration(track['duration_ms'])
        album_name = track['album']['name']
        thumbnail_url = track['album']['images'][0]['url']
        
        print(f"Current track: {track_name} by {artist_name}")
        
        tweet_text = f"🎵 Now Playing:\n{track_name} - {artist_name}\nAlbum: {album_name}\nDuration: {duration} #listening"
        
        print("Creating custom image...")
        custom_image = create_song_image(
            track_name,
            artist_name,
            album_name,
            duration,
            thumbnail_url
        )
        
        try:
            if custom_image:
                print("Uploading custom image to Twitter...")
                media_upload = api.media_upload(filename="song_card.png", file=custom_image)
                print("Media uploaded successfully")
                
                print("Sending tweet...")
                client.create_tweet(text=tweet_text, media_ids=[media_upload.media_id])
                print(f"Successfully tweeted: {tweet_text}")
                rate_limiter.record_success()
                return True
            else:
                print("Failed to create custom image, sending text-only tweet")
                client.create_tweet(text=tweet_text)
                print(f"Successfully tweeted (without media): {tweet_text}")
                rate_limiter.record_success()
                return True
                
        except tweepy.errors.TooManyRequests:
            print("\nHit Twitter rate limit")
            rate_limiter.record_error()
            return False
        except Exception as e:
            print(f"\nError tweeting: {str(e)}")
            return False
        
    except Exception as e:
        print(f"Error in tweet_current_song: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return False

def format_time(seconds):
    """Format seconds into MM:SS"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"

def wait_with_progress(total_seconds, description=""):
    """Wait with a progress bar showing time remaining"""
    try:
        with tqdm(total=total_seconds, 
                 desc=description,
                 bar_format='{desc}: {percentage:3.0f}%|{bar}| {n:.0f}/{total:.0f}s [{elapsed}<{remaining}]',
                 ncols=80) as pbar:
            for _ in range(int(total_seconds)):
                time.sleep(1)
                pbar.update(1)
    except KeyboardInterrupt:
        print("\nProgress interrupted by user")
        raise

def main():
    print("Starting Spotify to Twitter bot...")
    last_tweeted_song = None
    
    while True:
        try:
            print("\nChecking current playback...")
            current_track = sp.current_playback()
            
            if current_track is not None:
                current_song_id = current_track['item']['id']
                progress_ms = current_track['progress_ms']
                duration_ms = current_track['item']['duration_ms']
                remaining_ms = duration_ms - progress_ms
                
                # Add 2 seconds buffer to ensure song has fully changed
                wait_time = (remaining_ms / 1000) + 2
                
                # Get song details for display
                track_name = current_track['item']['name']
                artist_name = current_track['item']['artists'][0]['name']
                
                print(f"\nFound track: {track_name} by {artist_name}")
                print(f"Progress: {format_duration(progress_ms)} / {format_duration(duration_ms)}")
                
                if current_song_id != last_tweeted_song:
                    print("New song detected, tweeting...")
                    if tweet_current_song():
                        last_tweeted_song = current_song_id
                    print(f"\nWaiting for song to finish...")
                    wait_with_progress(int(wait_time), f"🎵 {track_name} - {artist_name}")
                else:
                    print("\nSame song still playing...")
                    wait_with_progress(int(wait_time), f"🎵 {track_name} - {artist_name}")
            else:
                print("\nNo track currently playing")
                wait_with_progress(60, "Waiting for playback")
            
        except KeyboardInterrupt:
            print("\nBot stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"\nError in main loop: {str(e)}")
            print("Full traceback:")
            traceback.print_exc()
            wait_with_progress(60, "Error recovery")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0) 