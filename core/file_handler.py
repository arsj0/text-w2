import os
from tkinter import filedialog
from utils import app_config 


class FileHandler:
    def __init__(self, supported_types=None):
        self.supported_types = supported_types if supported_types else app_config.FILE_DIALOG_AUDIO_TYPES
        self.last_opened_directory = "."

    def select_audio_file(self):
        """
        Opens a file dialog for the user to select an audio file.
        Returns the path to the selected file, or None if canceled.
        """
        filepath = filedialog.askopenfilename(
            title="Select Audio File",
            initialdir=self.last_opened_directory,
            filetypes=self.supported_types
        )
        if filepath:
            self.last_opened_directory = os.path.dirname(filepath)
            if not any(filepath.lower().endswith(ext.replace("*", "")) for group in self.supported_types for ext in group[1].split() if ext != "*.*"):
                 pass
            return filepath
        return None

    def request_srt_save_location(self, initial_filename="transcription.srt"):
        """
        Opens a "save as" dialog for the user to choose where to save the SRT file.
        Returns the full path (directory + filename) or None if canceled.
        """
        filepath = filedialog.asksaveasfilename(
            title="Save SRT File As",
            initialdir=self.last_opened_directory,
            initialfile=initial_filename,
            defaultextension=".srt",
            filetypes=[("SRT Files", "*.srt"), ("All Files", "*.*")]
        )
        if filepath:
            self.last_opened_directory = os.path.dirname(filepath) # Update last opened directory
            return filepath
        return None
    

    def request_yt_save_location(self, initial_filename="audio.mp3", tar_type="mp3"):
        """
        Opens a "save as" dialog for the user to choose where to save the file.
        Returns the full path (directory + filename) or None if canceled.
        """

        if tar_type == "mp4":
            my_ext = ".mp4"
            my_fTypes = [("MP4 Files", "*.mp4"), ("All Files", "*.*")]
        else: 
            my_ext = ".mp3"
            my_fTypes = [("MP3 Files", "*.mp3"), ("All Files", "*.*")]


        filepath = filedialog.asksaveasfilename(
            title="Save File As",
            initialdir=self.last_opened_directory,
            initialfile=initial_filename,
            defaultextension=my_ext,
            filetypes=my_fTypes
        )
        if filepath:
            self.last_opened_directory = os.path.dirname(filepath) # Update last opened directory
            return filepath
        return None

    def get_filename_from_path(self, filepath):
        """Extracts the filename from a full path."""
        if filepath:
            return os.path.basename(filepath)
        return None