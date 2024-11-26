import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
from spotdl import Spotdl
import re
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import asyncio
import nest_asyncio
from spotdl.utils.spotify import SpotifyClient, SpotifyError
import time
import random
from functools import wraps

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


def retry_with_backoff(retries=3, backoff_in_seconds=1):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise e
                    wait = (backoff_in_seconds * 2 ** x +
                            random.uniform(0, 1))
                    time.sleep(wait)
                    x += 1
        return wrapper
    return decorator


class SpotifyDownloader:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Spotify Audio Downloader")
        self.window.geometry("600x500")  # Made window taller for progress bar
        self.window.resizable(False, False)

        # Setup theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Get current directory as default download path
        self.default_dir = os.getcwd()

        # Initialize Spotify
        try:
            # Create and set event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # Initialize Spotdl with the event loop
            self.spotdl = Spotdl(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                downloader_settings={
                    "output": ".",  # Current directory
                    "format": "mp3",
                    "filter_results": True,
                    "audio_providers": ["youtube-music"]
                },
                loop=self.loop
            )

            # Get the initialized SpotifyClient
            self.spotify = SpotifyClient()
        except Exception as e:
            messagebox.showerror(
                "Error", f"Failed to initialize Spotify client: {str(e)}")
            raise e

        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Title
        title = ctk.CTkLabel(
            main_frame,
            text="Spotify Audio Downloader",
            font=("Helvetica", 24, "bold")
        )
        title.pack(pady=20)

        # URL Input
        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(fill="x", padx=20, pady=10)

        url_label = ctk.CTkLabel(
            url_frame,
            text="Spotify URL:",
            font=("Helvetica", 14)
        )
        url_label.pack(side="left", padx=5)

        self.url_entry = ctk.CTkEntry(
            url_frame,
            width=400,
            placeholder_text="Enter URL from open.spotify.com"
        )
        self.url_entry.pack(side="left", padx=5)

        # Save Directory Selection
        dir_frame = ctk.CTkFrame(main_frame)
        dir_frame.pack(fill="x", padx=20, pady=10)

        dir_label = ctk.CTkLabel(
            dir_frame,
            text="Save to:",
            font=("Helvetica", 14)
        )
        dir_label.pack(side="left", padx=5)

        self.dir_entry = ctk.CTkEntry(
            dir_frame,
            width=300,
            placeholder_text="Choose save directory"
        )
        self.dir_entry.insert(0, self.default_dir)  # Set default directory
        self.dir_entry.pack(side="left", padx=5)

        browse_btn = ctk.CTkButton(
            dir_frame,
            text="Browse",
            width=80,
            command=self.browse_directory
        )
        browse_btn.pack(side="left", padx=5)

        # Download Button
        self.download_btn = ctk.CTkButton(
            main_frame,
            text="Download",
            width=200,
            height=40,
            command=self.start_download,
            font=("Helvetica", 16)
        )
        self.download_btn.pack(pady=20)

        # Progress Frame
        progress_frame = ctk.CTkFrame(main_frame)
        progress_frame.pack(fill="x", padx=20, pady=10)

        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        self.progress_bar.set(0)

        # Progress Labels
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=("Helvetica", 12)
        )
        self.progress_label.pack(pady=5)

        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=("Helvetica", 12)
        )
        self.status_label.pack(pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.default_dir)
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)

    def validate_spotify_url(self, url):
        pattern = r'https?://open\.spotify\.com/(?:track|artist|playlist|album|episode)/[a-zA-Z0-9]+'
        return bool(re.match(pattern, url))

    def update_ui(self, progress_text, progress_value=None, status_text=None, message_type=None, message_text=None):
        self.progress_label.configure(text=progress_text)
        if status_text:
            self.status_label.configure(text=status_text)
        if progress_value is not None:
            self.progress_bar.set(progress_value)
        if message_type and message_text:
            if message_type == "error":
                messagebox.showerror("Error", message_text)
            elif message_type == "info":
                messagebox.showinfo("Success", message_text)

    def update_ui_with_error(self, error_message):
        """Helper method to update UI with error message"""
        self.update_ui(
            "Download failed!", 0, f"Error: {error_message}",
            "error", f"An error occurred: {error_message}")
        self.download_btn.configure(state="normal")

    def start_download(self):
        url = self.url_entry.get().strip()
        output_dir = self.dir_entry.get().strip() or self.default_dir

        if not url:
            messagebox.showerror("Error", "Please enter a Spotify URL!")
            return

        if not self.validate_spotify_url(url):
            messagebox.showerror("Error", "Invalid Spotify URL!")
            return

        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror(
                    "Error", f"Could not create directory: {str(e)}")
                return

        self.download_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.update_ui("Preparing to download...", 0, "Initializing...")

        # Start download in a new thread
        threading.Thread(target=self.download_audio_thread,
                         args=(url, output_dir), daemon=True).start()

    async def download_audio(self, url, output_dir):
        try:
            # Change current directory to output directory
            current_dir = os.getcwd()
            os.chdir(output_dir)

            try:
                # Update progress
                self.window.after(0, lambda: self.update_ui(
                    "Searching for content...", 0.2, "Fetching metadata from Spotify..."))

                # Extract Spotify ID and type from URL
                spotify_id = None
                content_type = None
                if url.startswith('https://open.spotify.com/'):
                    parts = url.split('/')
                    content_type = parts[-2]  # 'track' or 'episode'
                    spotify_id = parts[-1].split('?')[0]
                    print(f"Content type: {content_type}")
                    print(f"Spotify ID: {spotify_id}")

                    songs = await self._download_content(content_type, spotify_id)
                else:
                    songs = self.spotdl.search([url])

                print(f"Number of results found: {len(songs)}")

                if not songs:
                    raise Exception("No content found for this URL")

                # Select the best match
                song = songs[0]
                print(f"Selected content: {song.artist} - {song.name}")

                # Show what we're going to download
                song_info = f"{song.artist} - {song.name}"
                self.window.after(0, lambda: self.update_ui(
                    f"Found: {song_info}", 0.4, "Starting download..."))

                # Update UI for download start
                self.window.after(0, lambda: self.update_ui(
                    "Downloading...", 0.6, "Converting and downloading audio..."))

                # Download the matched content
                task = asyncio.create_task(
                    self.spotdl.downloader.pool_download(song))
                await task

                # Update UI with success
                self.window.after(0, lambda: self.update_ui(
                    "Download completed!", 1.0,
                    f"Successfully downloaded: {song_info}",
                    "info", "Download completed!"))

            except Exception as download_error:
                error_msg = str(download_error)
                print(f"Download error: {error_msg}")
                self.window.after(
                    0, lambda: self.update_ui_with_error(error_msg))

            finally:
                # Restore original directory
                os.chdir(current_dir)
                self.window.after(
                    0, lambda: self.download_btn.configure(state="normal"))

        except Exception as outer_error:
            error_msg = str(outer_error)
            print(f"Outer error: {error_msg}")
            self.window.after(0, lambda: self.update_ui_with_error(error_msg))

    async def _download_content(self, content_type, spotify_id):
        """Internal method to handle the actual download"""
        try:
            print(f"Content type: {content_type}")
            print(f"Spotify ID: {spotify_id}")

            if content_type == 'episode':
                # Get episode info directly from Spotify with retry
                @retry_with_backoff(retries=3)
                def get_episode():
                    return self.spotify.episode(spotify_id)

                episode = get_episode()
                if not episode:
                    raise Exception(
                        f"Could not find episode with ID: {spotify_id}")

                # Create search query using episode info
                search_query = f"{episode['show']['name']} - {episode['name']}"
                print(f"Search query: {search_query}")

                # Add delay before next API call
                await asyncio.sleep(1)

                # Search with the exact query
                songs = self.spotdl.search([search_query])
            else:
                # Handle regular tracks with retry
                @retry_with_backoff(retries=3)
                def get_track():
                    return self.spotify.track(spotify_id)

                track = get_track()
                if not track:
                    raise Exception(
                        f"Could not find track with ID: {spotify_id}")

                # Create search query using track info
                search_query = f"{track['name']} - {', '.join([artist['name'] for artist in track['artists']])}"
                print(f"Search query: {search_query}")

                # Add delay before next API call
                await asyncio.sleep(1)

                # Search with the exact query
                songs = self.spotdl.search([search_query])

            if not songs:
                raise Exception("No songs found to download")

            # Add delay before download
            await asyncio.sleep(1)

            # Download all found songs
            results = await self.spotdl.download_songs(songs)
            return songs

        except Exception as e:
            print(f"Error in _download_content: {str(e)}")
            raise

    def download_audio_thread(self, url, output_dir):
        """Execute the download in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.download_audio(url, output_dir))
        finally:
            loop.close()

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = SpotifyDownloader()
    app.run()
