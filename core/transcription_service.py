from faster_whisper import WhisperModel
from utils import app_config 
import os
import sys


class TranscriptionService:
    def __init__(self, model_name=None):
        self.model_name = model_name if model_name else app_config.WHISPER_MODEL_NAME
        self.model = None

    def get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)



    def faster_transcribe_audio(self, audio_file_path):
        model_path = self.get_resource_path(self.model_name)

        print("model_path = " + model_path)
        
        model = WhisperModel(model_path, # 'tiny', 
                             device="auto", 
                             compute_type="default", 
                             #download_root='models/base'
                             )

        if not model:
            print("Transcription service: Model not loaded.")
            return {"error": app_config.MESSAGE_MODEL_LOAD_ERROR, "text": "", "segments": []}
        

        segments, info = model.transcribe(audio_file_path, beam_size=5, condition_on_previous_text=False)

        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

        # for segment in segments:
        #     print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

        print("return segments.")

        return segments



    def generate_srt_from_segments(self, segments, output_filepath):
        """
        Generates an SRT file from faster-whisper segments.
        """

        try:
            with open(output_filepath, "w", encoding="utf-8") as f:
                i = 0
                for segment in segments:
                    start_time = self._format_timestamp(segment.start)
                    end_time = self._format_timestamp(segment.end)
                    f.write(f"{i + 1}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment.text.strip()}\n\n")
                    i+=1
            print(f"SRT file generated successfully: {output_filepath}")
            return True
        except Exception as e:
            print(f"Error generating SRT for '{output_filepath}': {e}")
            return False

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

        return f"{hours:02d}:{minutes:02d}:{seconds_val:02d},{milliseconds:03d}"