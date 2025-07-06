import customtkinter as ctk
from ui.app_frame import AppFrame
from utils import app_config
from core.transcription_service import TranscriptionService
import multiprocessing as mp

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(app_config.APP_NAME)
        self.geometry("880x770")
        self.minsize(700,580)

        theme_file_path = TranscriptionService.get_resource_path(self, app_config.DEFAULT_COLOR_THEME)

        ctk.set_appearance_mode(app_config.DEFAULT_APPEARANCE_MODE)
        ctk.set_default_color_theme(theme_file_path)

        self.app_frame = AppFrame(master=self)
        self.app_frame.pack(fill="both", expand=True, padx=10, pady=10)

if __name__ == "__main__":
    mp.freeze_support()
    app = App()
    app.mainloop()