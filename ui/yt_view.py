import customtkinter as ctk
from utils import app_config
from core.file_handler import FileHandler
from core.yt_service import YtService
import threading
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from pathlib import Path

class YtView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        #self.configure(fg_color="transparent")

        self.file_handler = FileHandler(supported_types=app_config.FILE_DIALOG_AUDIO_TYPES)
        self.yt_service = YtService()

        # --- Main Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # URL section
        self.grid_rowconfigure(1, weight=0)  # Buttons section
        self.grid_rowconfigure(2, weight=1)  # Status section (expandable)
        self.grid_rowconfigure(3, weight=0)  # Progress bar section

        # --- URL Input Section ---
        self.url_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="transparent")
        self.url_frame.grid(row=0, column=0, sticky="ew", padx=40, pady=(40, 20))
        self.url_frame.grid_columnconfigure(0, weight=1)

        self.url_label = ctk.CTkLabel(
            self.url_frame,
            text="YouTube URL",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        self.url_label.grid(row=0, column=0, sticky="w", padx=0, pady=(0, 8))

        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            height=40,
            font=ctk.CTkFont(size=14),
            placeholder_text="Paste YouTube URL here..."
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=0, pady=0)

        # --- Buttons Section ---
        self.buttons_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="transparent")
        self.buttons_frame.grid(row=1, column=0, sticky="ew", padx=40, pady=(0, 20))
        self.buttons_frame.grid_columnconfigure((0, 1), weight=1)

        self.submit_button = ctk.CTkButton(
            self.buttons_frame,
            text="Download Audio",
            command=self.submit_url_action,
            state="normal",
            height=30,
            font=ctk.CTkFont(size=14)
        )
        self.submit_button.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=0)

        self.submit_button_v = ctk.CTkButton(
            self.buttons_frame,
            text="Download Video",
            command=self.submit_url_action_v,
            state="normal",
            height=30,
            font=ctk.CTkFont(size=14)
        )
        self.submit_button_v.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=0)

        # --- Status Display Section ---
        self.status_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_frame.grid_rowconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="",
            font=ctk.CTkFont(size=13),
            anchor="nw",
            justify="left",
            wraplength=800
        )
        self.status_label.grid(row=0, column=0, sticky="nw", padx=20, pady=20)

        # --- Progress Bar Section ---
        # self.progress_frame = ctk.CTkFrame(self, corner_radius=12, fg_color="transparent")
        # self.progress_frame.grid(row=3, column=0, sticky="ew", padx=40, pady=(0, 40))
        # self.progress_frame.grid_columnconfigure(0, weight=1)

        # self.spinner = ctk.CTkProgressBar(self.progress_frame, mode="indeterminate", height=6)
        # self.hide_spinner() # Initially hidden


    def update_transcription_display(self, text, is_error=False, is_info=False, append=False):
        if append:
            current_text = self.status_label.cget("text")
            new_text = current_text + "\n" + text
        else:
            new_text = text
        
        self.status_label.configure(text=new_text)
        
        # Change text color based on message type
        if is_error:
            self.status_label.configure(text_color=("red", "red"))
        elif is_info:
            self.status_label.configure(text_color=("gray60", "gray70"))
        else:
            self.status_label.configure(text_color=("gray10", "gray90"))

    def show_spinner(self):
        self.spinner.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        self.spinner.start()

    def hide_spinner(self):
        self.spinner.stop()
        self.spinner.grid_remove()

    def set_controls_state(self, state="normal"):
        self.submit_button.configure(state=state)
        self.submit_button_v.configure(state=state)
            

    def submit_url_action(self): 

        url = self.url_entry.get().strip()

        if not url:
            self.update_transcription_display(app_config.MESSAGE_NO_URL, is_error=True)
            return
        elif not self.is_youtube_url(url): 
            self.update_transcription_display(app_config.MESSAGE_NO_URL, is_error=True)
            return
        
        url = self.keep_only_v_param(url)
        print('URL = ' + url)


        # User chooses destination path first
        initial_filename = "[title_of_video].mp3"
        save_path_dialog_result = self.file_handler.request_yt_save_location(initial_filename, "mp3")

        if not save_path_dialog_result:
            self.update_transcription_display("No save location selected.", is_error=True)
            #self.hide_spinner()
            self.set_controls_state("normal")
            return

        # Start download process
        #self.show_spinner()
        self.set_controls_state("disabled")
        self.update_transcription_display("downloading ...", is_info=True)


        # Thread
        thread_yt = threading.Thread(target=self.dl_yt_thread, args=(url, save_path_dialog_result, "A"))
        thread_yt.daemon = True
        thread_yt.start()
        
    def submit_url_action_v(self): 

        url = self.url_entry.get().strip()

        if not url:
            self.update_transcription_display(app_config.MESSAGE_NO_URL, is_error=True)
            return
        elif not self.is_youtube_url(url): 
            self.update_transcription_display(app_config.MESSAGE_NO_URL, is_error=True)
            return
        
        url = self.keep_only_v_param(url)
        print('URL = ' + url)


        # User chooses destination path first
        initial_filename = "[title_of_video].mp4"
        save_path_dialog_result = self.file_handler.request_yt_save_location(initial_filename, "mp4")

        if not save_path_dialog_result:
            self.update_transcription_display("No save location selected.", is_error=True)
            #self.hide_spinner()
            self.set_controls_state("normal")
            return

        # Start download process
        #self.show_spinner()
        self.set_controls_state("disabled")
        self.update_transcription_display("downloading ...", is_info=True)


        # Thread
        thread_yt = threading.Thread(target=self.dl_yt_thread, args=(url, save_path_dialog_result, "V"))
        thread_yt.daemon = True
        thread_yt.start()


    def dl_yt_thread(self, url, save_path, mode="A"): 

        output_path = save_path
    
        try:
            success = self.yt_service.obtain_yt(video_url=url, output_path=output_path, mode=mode)
        finally:
            #self.hide_spinner()
            self.set_controls_state("normal")

        if success:
            parent_dir = str(Path(output_path).parent)
            self.update_transcription_display(f"\nDone. Saved successfully to: {parent_dir}", is_info=True, append=False)
        else:
            self.update_transcription_display("Error during download.", is_error=True, append=False)


    def is_youtube_url(self, url):
        parsed = urlparse(url)
        
        # Check for YouTube domain and path
        if parsed.netloc not in ['www.youtube.com', 'youtube.com']:
            return False

        # Check if path is '/watch'
        if parsed.path != '/watch':
            return False

        # Check if the query contains a 'v=' parameter
        if 'v=' in parsed.query:
            return True

        return False
    
    
    def keep_only_v_param(self, url):
        parsed = urlparse(url)

        # Extract the query parameters
        query_params = parse_qs(parsed.query)

        # Keep only the 'v' parameter
        if 'v' in query_params:
            query_params = {'v': query_params['v']}

        # Remove any other parameters
        new_query_string = urlencode(query_params, doseq=True)

        # Reconstruct the URL
        new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', new_query_string, ''))

        return new_url