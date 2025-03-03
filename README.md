# 🎵 Spotify to Twitter Bot

A beautiful Python bot that automatically tweets your currently playing Spotify tracks with custom-generated artwork! 

![Example](https://imgur.com/veQe2lf) 

## ✨ Features

- 🎨 **Dynamic Artwork Generation**
  - Custom artwork for each song using album colors
  - Beautiful gradient backgrounds
  - Glowing effects and subtle patterns
  - Professional typography with shadows
  - Album artwork integration

- 🤖 **Automatic Tweeting**
  - Real-time song detection
  - Smart duplicate prevention
  - Elegant tweet formatting
  - Automatic media uploads

- 🎯 **Smart Integration**
  - Seamless Spotify API integration
  - Twitter API v2 support
  - Error handling and retry logic
  - Environment-based configuration

## 🚀 Setup

### Prerequisites

- Python 3.8+
- Spotify Premium Account
- Twitter Developer Account
- Twitter App with v1.1 and v2 API access

### Installation

1. Clone the repository:
```bash
git clone https://github.com/rbxpusk/spotify-to-twitter.git
cd spotify-to-twitter
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```env
# Spotify API Credentials
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# Twitter API Credentials
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret
```

### Twitter App Setup

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Create a new app or select existing app
3. Enable OAuth 1.0a
4. Set app permissions to "Read and Write"
5. Generate Access Token and Secret
6. Add them to your `.env` file

### Spotify App Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add `http://localhost:8888/callback` as a Redirect URI
4. Copy Client ID and Secret to your `.env` file

## 🎮 Usage

Run the bot:
```bash
python main.py
```

The bot will:
1. Authenticate with Spotify and Twitter
2. Monitor your Spotify playback
3. Generate custom artwork for each new song
4. Tweet the song with the artwork
5. Wait 30 seconds before checking for new songs

## 🎨 Image Generation

The bot creates beautiful custom images for each song featuring:
- Dynamic gradient backgrounds using album colors
- Album artwork with glowing effects
- Professional typography with shadows
- Subtle geometric patterns
- Song details with icons

## 📝 Configuration

You can customize the bot by modifying these constants in `main.py`:

```python
CANVAS_WIDTH = 1200          # Image width
CANVAS_HEIGHT = 630          # Image height
BACKGROUND_COLOR = "#FF3366" # Default background
TEXT_COLOR = "#FFFFFF"       # Default text color
```

## 🛠️ Technical Details

- Uses `spotipy` for Spotify API integration
- Uses `tweepy` for Twitter API integration
- Uses `Pillow` for image generation
- Uses `python-dotenv` for configuration
- Implements error handling and retry logic
- Supports both Twitter API v1.1 and v2

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- [Spotipy](https://spotipy.readthedocs.io/) for Spotify API integration
- [Tweepy](https://www.tweepy.org/) for Twitter API integration
- [Pillow](https://python-pillow.org/) for image processing

## 📸 Screenshots

*https://imgur.com/veQe2lf*

## 🐛 Troubleshooting

### Common Issues

1. **"No track currently playing"**
   - Make sure Spotify is playing a track
   - Check your Spotify Premium subscription

2. **Twitter API Errors**
   - Verify your API keys
   - Check app permissions
   - Ensure OAuth 1.0a is enabled

3. **Image Generation Issues**
   - Check font availability
   - Verify write permissions
   - Ensure enough disk space

## 🔄 Updates

Stay tuned for updates! Follow the repository for:
- New visual effects
- Additional customization options
- Performance improvements
- Bug fixes 