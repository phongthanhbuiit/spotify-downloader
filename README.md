# Spotify Audio Downloader

This application helps you download audio from Spotify for English learning purposes.

## Installation

1. Install Python 3.11
2. Install required libraries:
```bash
pip install setuptools
pip install -r requirements.txt
brew install python-tk@3.11 (MacOS)
```

## Configuration

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. In your app settings, add Redirect URI:
   ```
   http://localhost:8888/callback
   ```
4. Get your Client ID and Client Secret
5. Update `config.py` with your credentials:
```python
SPOTIFY_CLIENT_ID = "your_client_id_here"
SPOTIFY_CLIENT_SECRET = "your_client_secret_here"
```

## How to Use

1. Run main.py:
```bash
python main.py
```

2. Paste the Spotify link (from open.spotify.com) into the input field
3. Choose the save directory
4. Click "Download" to start downloading

## Notes

- The app supports downloading from Spotify track, playlist, album, or episode links
- Audio files will be downloaded in MP3 format
- Make sure you have a stable internet connection while downloading
