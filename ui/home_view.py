import customtkinter as ctk
from utils import app_config
from core.file_handler import FileHandler
from core.transcription_service import TranscriptionService
import os
import threading
import time
from core.llm_service import llmService

class HomeView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        #self.configure(fg_color="#333333")

        self.file_handler = FileHandler(supported_types=app_config.FILE_DIALOG_AUDIO_TYPES)
        self.transcription_service = TranscriptionService()
        self.llm_service = llmService()
        self.selected_audio_path = None
        self.transcription_result_data = None
        self.model_loaded = False
        self.raw_seg = []
        self.selected_llm = "-"
        self.selected_trans_lang = "-"
        self.selected_whisper = app_config.WHISPER_MODEL_NAME

        # --- Main Layout ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Panel ---
        self.left_panel = ctk.CTkFrame(self, width=300, fg_color="transparent")
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
        
        self.selected_file_label = ctk.CTkLabel(self.file_input_frame, text="", wraplength=180, anchor="w", justify="left")
        self.selected_file_label.pack(fill="x", pady=(3,0))


        # Dropdown for Whisper Model
        self.whisper_dropdown_frame = ctk.CTkFrame(self.left_panel, fg_color='transparent')
        self.whisper_dropdown_frame.pack( padx=20, fill="x")

        self.whisper_dropdown_label = ctk.CTkLabel(self.whisper_dropdown_frame, text="Whisper Model", wraplength=200, anchor="w", justify="left")
        self.whisper_dropdown_label.pack(fill="x")

        self.whisper_options = app_config.WHISPER_MODELS_OPTIONS
        self.whisper_dropdown = ctk.CTkComboBox(master=self.whisper_dropdown_frame,
                                    values=self.whisper_options, command=self.whisper_dropdown_callback, state="readonly")
        self.whisper_dropdown.pack(pady=(5,10), fill="x")
        self.whisper_dropdown.set(app_config.WHISPER_MODEL_NAME)  # set initial value


        # Dropdown for translation llm
        self.llm_dropdown_frame = ctk.CTkFrame(self.left_panel, fg_color='transparent')
        self.llm_dropdown_frame.pack( padx=20, fill="x")

        self.llm_dropdown_label = ctk.CTkLabel(self.llm_dropdown_frame, text="LLM", wraplength=200, anchor="w", justify="left")
        self.llm_dropdown_label.pack(fill="x")

        self.llm_dd_options = self.llm_service.ollama_get_model_list() + self.llm_service.lms_get_model_list()
        self.llm_dropdown = ctk.CTkComboBox(master=self.llm_dropdown_frame,
                                    values=["-"]+self.llm_dd_options, command=self.llm_dropdown_callback, state="readonly")
        self.llm_dropdown.pack(pady=(5,10), fill="x")
        self.llm_dropdown.set("-")  # set initial value

        # Dropdown for translation lang
        self.lang_dropdown_frame = ctk.CTkFrame(self.left_panel, fg_color='transparent')
        self.lang_dropdown_frame.pack(padx=20, pady=(10,10), fill="x")

        self.lang_dropdown_label = ctk.CTkLabel(self.lang_dropdown_frame, text="Translation Language", wraplength=200, anchor="w", justify="left")
        self.lang_dropdown_label.pack(fill="x")

        self.lang_options = app_config.TRANS_LANG_OPTIONS
        self.lang_dropdown = ctk.CTkComboBox( master=self.lang_dropdown_frame,  values=self.lang_options, command=self.lang_dropdown_callback, state="readonly")
        self.lang_dropdown.pack(pady=(5,10), fill="x")
        self.lang_dropdown.set("-")        

        # Spacer to push Download button to bottom
        self.spacer_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent", height=20)
        self.spacer_frame.pack(pady=0, padx=0,fill="both", expand=True)

        # Submit Button
        self.submit_button = ctk.CTkButton(
            self.left_panel,
            text=app_config.BUTTON_TEXT_SUBMIT,
            command=self.submit_transcription_action,
            state="normal"
        )
        self.submit_button.pack(pady=(20,10), padx=20, fill="x")


        # Download Button (at the bottom of left panel)
        self.download_button = ctk.CTkButton(
            self.left_panel,
            text=app_config.BUTTON_TEXT_DOWNLOAD_SRT,
            command=self.download_srt_action,
            state="disabled"
        )
        self.download_button.pack(pady=(10,20), padx=20, fill="x", side="bottom")


        # --- Main Area (Transcription Display) ---
        self.main_area = ctk.CTkFrame(self,  fg_color='transparent')
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=(0,0), pady=0)
        
        self.main_area.grid_rowconfigure(0, weight=1) # Textbox
        self.main_area.grid_rowconfigure(1, weight=0) # Spinner row
        self.main_area.grid_columnconfigure(0, weight=1)

        self.transcription_textbox = ctk.CTkTextbox(
            self.main_area,
            wrap="word",
            state="disabled",
            font=ctk.CTkFont(family="Arial", size=13)
        )
        self.transcription_textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20,20))
        
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
        self.transcription_result_data, script_lang = self.transcription_service.faster_transcribe_audio(self.selected_audio_path, self.selected_whisper)
        
        if self.transcription_result_data:
            
            self.update_transcription_display("", is_info=True)

            ref_Lines = [] # for llm translation
            original_lines = [] # for summary

            for segment in self.transcription_result_data:
                start_time = self._format_timestamp(segment.start)
                end_time = self._format_timestamp(segment.end)
                text = segment.text.strip()

                original_lines.append(f"{start_time} - {end_time}  {text}")

                # llm translate
                if(self.selected_llm != "-" and self.selected_trans_lang != "-"):
                    text = self.llm_service.llm_translate(self.selected_llm, script_lang, self.selected_trans_lang, text, ref_Lines)
                    segment.text = text

                line = f"{start_time} - {end_time}  {text}"
                ref_Lines.append(line)

                self.update_transcription_display(line + "\n", is_info=True, append=True)

                self.raw_seg.append(segment)

            self.download_button.configure(state="normal")

        else:
            self.download_button.configure(state="disabled") # No segments for SRT
            self.update_transcription_display("\n\n(No segment data for SRT generation)\n", is_info=True, append=True)

        m_end_time = time.time()
        self.update_transcription_display("--------------------------\n", is_info=True, append=True)
        self.update_transcription_display("\nDone. " + f"Time taken: {(m_end_time - m_start_time):.2f} seconds.\n", is_info=True, append=True)


        if(self.selected_llm != "-"):
            summary = self.llm_service.llm_sums_script(self.selected_llm , ';\n'.join(original_lines), self.selected_trans_lang if self.selected_trans_lang != "-" else script_lang  )

            self.update_transcription_display("\n--------------------------\n", is_info=True, append=True)
            self.update_transcription_display("Summary: \n\n", is_info=True, append=True)
            self.update_transcription_display(summary.general_summary + "\n\n", is_info=True, append=True)

        self.hide_spinner()
        self.set_controls_state("normal")

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


    def update_transcription_display(self, text, is_error=False, is_info=False,  append=False):
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
            self.transcription_textbox.tag_config("info", foreground="gray80")
            self.transcription_textbox.insert("end" if append else "1.0", text, "info")
        else:
            self.transcription_textbox.insert("end" if append else "1.0", text)
        
        # if append:
        #     self.transcription_textbox.see("end")
        
        self.transcription_textbox.configure(state="disabled")

    def show_spinner(self):
        self.spinner.grid(row=1, column=0, sticky="ew", padx=20, pady=(0,20))
        self.spinner.start()

    def hide_spinner(self):
        self.spinner.stop()
        self.spinner.grid_remove()

    def set_controls_state(self, state="normal"):
        self.select_file_button.configure(state=state)
        self.submit_button.configure(state=state)
            
        if state == "disabled":
            self.download_button.configure(state="disabled")
            self.whisper_dropdown.configure(state="disabled")
            self.llm_dropdown.configure(state="disabled")

        elif state == "normal" and self.transcription_result_data:
            self.download_button.configure(state="normal")
            self.whisper_dropdown.configure(state="readonly")
            self.llm_dropdown.configure(state="readonly")

        else:
            self.download_button.configure(state="disabled")
            self.whisper_dropdown.configure(state="readonly")
            self.llm_dropdown.configure(state="readonly")

    def llm_dropdown_callback(self, choice):
        self.selected_llm = choice

    def lang_dropdown_callback(self, choice): 
        self.selected_trans_lang = choice

    def whisper_dropdown_callback(self, choice):
        self.selected_whisper = choice