import customtkinter as ctk
from utils import app_config
from core.file_handler import FileHandler
from core.transcription_service import TranscriptionService
import os
import threading
import time

class HomeView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="transparent")

        self.file_handler = FileHandler(supported_types=app_config.FILE_DIALOG_AUDIO_TYPES)
        self.transcription_service = TranscriptionService()
        self.selected_audio_path = None
        self.transcription_result_data = None
        self.model_loaded = False
        self.raw_seg = []

        # --- Main Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Panel ---
        self.left_panel = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsw", padx=(0,5), pady=0)
        self.left_panel.grid_propagate(False) # Prevent panel from shrinking to content

        # File Input Section
        self.file_input_frame = ctk.CTkFrame(self.left_panel, fg_color='transparent')
        self.file_input_frame.pack(pady=(20,10), padx=20, fill="x")

        #self.file_input_label = ctk.CTkLabel(self.file_input_frame, text='Upload', anchor="w")
        #self.file_input_label.pack(fill="x")

        self.select_file_button = ctk.CTkButton(
            self.file_input_frame,
            text="Upload",
            command=self.select_audio_file_action
        )
        self.select_file_button.pack(fill="x", pady=(5,0))
        
        self.selected_file_label = ctk.CTkLabel(self.file_input_frame, text="No file selected.", wraplength=200, anchor="w", justify="left")
        self.selected_file_label.pack(fill="x", pady=(5,10))

        # Submit Button
        self.submit_button = ctk.CTkButton(
            self.left_panel,
            text=app_config.BUTTON_TEXT_SUBMIT,
            # fg_color=app_config.COLOR_BUTTON,
            # hover_color=app_config.COLOR_BUTTON_HOVER,
            command=self.submit_transcription_action,
            state="normal"
        )
        self.submit_button.pack(pady=(20,10), padx=20, fill="x")

        # Spacer to push Download button to bottom
        self.spacer_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.spacer_frame.pack(pady=0, padx=0, fill="both", expand=True)


        # Download Button (at the bottom of left panel)
        self.download_button = ctk.CTkButton(
            self.left_panel,
            text=app_config.BUTTON_TEXT_DOWNLOAD_SRT,
            # fg_color=app_config.COLOR_BUTTON,
            # hover_color=app_config.COLOR_BUTTON_HOVER,
            command=self.download_srt_action,
            state="disabled"
        )
        self.download_button.pack(pady=(10,20), padx=20, fill="x", side="bottom")


        # --- Main Area (Transcription Display) ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=(5,0), pady=0)
        
        self.main_area.grid_rowconfigure(0, weight=1) # Textbox
        self.main_area.grid_rowconfigure(1, weight=0) # Spinner row
        self.main_area.grid_columnconfigure(0, weight=1)

        self.transcription_textbox = ctk.CTkTextbox(
            self.main_area,
            wrap="word",
            state="disabled",
            font=ctk.CTkFont(family="Arial", size=13)
        )
        self.transcription_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10,5))
        
        self.spinner = ctk.CTkProgressBar(self.main_area, mode="indeterminate", height=8)
        # self.spinner.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,10)) # Initial placement
        self.hide_spinner() # Initially hidden

    def select_audio_file_action(self):
        self.selected_audio_path = self.file_handler.select_audio_file()
        if self.selected_audio_path:
            filename = self.file_handler.get_filename_from_path(self.selected_audio_path)
            self.selected_file_label.configure(text=filename if filename else "No file selected.")
            self.transcription_textbox.configure(state="normal")
            self.transcription_textbox.delete("1.0", "end")
            self.transcription_textbox.configure(state="disabled")
            self.download_button.configure(state="disabled")
            self.transcription_result_data = None
        else:
            self.selected_file_label.configure(text="No file selected.")
            self.selected_audio_path = None

    def _format_timestamp(self, seconds: float) -> str:
        """Converts seconds to HH:MM:SS,mmm format."""
        assert seconds >= 0, "non-negative timestamp expected"
        milliseconds = round(seconds * 1000.0)

        hours = milliseconds // 3_600_000
        milliseconds %= 3_600_000

        minutes = milliseconds // 60_000
        milliseconds %= 60_000

        seconds_val = milliseconds // 1_000
        milliseconds %= 1_000

        return f"{hours:02d}:{minutes:02d}:{seconds_val:02d}"
    
    
    

    def _load_model_and_transcribe_thread(self):
        m_start_time = time.time()

        self.update_transcription_display("Transcription in progress...", is_info=True)
        self.transcription_result_data = self.transcription_service.faster_transcribe_audio(self.selected_audio_path)
        
        if self.transcription_result_data:
            formatted_lines = []
            self.update_transcription_display("", is_info=True)

            for segment in self.transcription_result_data:
                start_time = self._format_timestamp(segment.start)
                end_time = self._format_timestamp(segment.end)
                text = segment.text.strip()

                line = f"{start_time} - {end_time}  {text}"
                print(line)
                self.update_transcription_display(line + "\n", is_info=True, append=True)

                self.raw_seg.append(segment)

            self.download_button.configure(state="normal")

        else:
            self.download_button.configure(state="disabled") # No segments for SRT
            self.update_transcription_display("\n\n(No segment data for SRT generation)\n", is_info=True, append=True)

        self.hide_spinner()
        self.set_controls_state("normal")

        m_end_time = time.time()
        self.update_transcription_display("--------------------------\n", is_info=True, append=True)
        self.update_transcription_display("\nDone. " + f"Time taken: {(m_end_time - m_start_time):.2f} seconds.\n", is_info=True, append=True)

        print(f"Time taken: {(m_end_time - m_start_time):.2f} seconds.")
        



    def submit_transcription_action(self):
        if not self.selected_audio_path:
            self.update_transcription_display(app_config.MESSAGE_NO_AUDIO_SELECTED, is_error=True)
            return

        self.show_spinner()
        self.set_controls_state("disabled")
        self.transcription_textbox.configure(state="normal")
        self.transcription_textbox.delete("1.0", "end")
        self.download_button.configure(state="disabled")
        self.transcription_result_data = None
        
        # Start the combined load and transcribe process in a thread
        thread = threading.Thread(target=self._load_model_and_transcribe_thread)
        thread.daemon = True
        thread.start()

    def download_srt_action(self):
        if not self.transcription_result_data:
            self.update_transcription_display(app_config.MESSAGE_NO_TRANSCRIPTION_AVAILABLE, is_error=True)
            return

        initial_srt_filename = "transcription.srt"
        
        if self.selected_audio_path:
            base_filename = self.file_handler.get_filename_from_path(self.selected_audio_path)

            if base_filename:
                base, _ = os.path.splitext(base_filename)
                initial_srt_filename = base + ".srt"
        
        save_path_dialog_result = self.file_handler.request_srt_save_location(initial_srt_filename)
        
        if save_path_dialog_result:

            success = self.transcription_service.generate_srt_from_segments(
                self.raw_seg,
                save_path_dialog_result
            )

            final_srt_path = save_path_dialog_result

            if success:
                self.update_transcription_display(f"{app_config.MESSAGE_SRT_SAVE_SUCCESS}\nSaved to: {final_srt_path}", is_info=True, append=True)
            else:
                self.update_transcription_display(app_config.MESSAGE_SRT_SAVE_ERROR, is_error=True, append=True)


    def update_transcription_display(self, text, is_error=False, is_info=False, append=False):
        self.transcription_textbox.configure(state="normal")
        
        if not append:
            self.transcription_textbox.delete("1.0", "end")
            current_tags = self.transcription_textbox.tag_names()
            for tag in current_tags:
                if tag not in ("tagon", "tagoff"):
                    self.transcription_textbox.tag_delete(tag)

        if is_error:
            self.transcription_textbox.tag_config("error", foreground="red")
            self.transcription_textbox.insert("end" if append else "1.0", text, "error")
        elif is_info:
            self.transcription_textbox.tag_config("info", foreground="gray70")
            self.transcription_textbox.insert("end" if append else "1.0", text, "info")
        else:
            self.transcription_textbox.insert("end" if append else "1.0", text)
        
        # if append:
        #     self.transcription_textbox.see("end")
        
        self.transcription_textbox.configure(state="disabled")

    def show_spinner(self):
        self.spinner.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,10))
        self.spinner.start()

    def hide_spinner(self):
        self.spinner.stop()
        self.spinner.grid_remove()

    def set_controls_state(self, state="normal"):
        self.select_file_button.configure(state=state)
        self.submit_button.configure(state=state)
            
        if state == "disabled":
            self.download_button.configure(state="disabled")
        elif state == "normal" and self.transcription_result_data:
            self.download_button.configure(state="normal")
        else:
            self.download_button.configure(state="disabled")

