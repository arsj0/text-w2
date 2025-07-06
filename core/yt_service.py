from yt_dlp import YoutubeDL
from pathlib import Path

class YtService:
     

    def obtain_yt(self, video_url, output_path= None, mode="A"):

        if output_path: 
            output_path = str(Path(output_path).with_suffix(''))
            output_path = output_path.replace('[title_of_video]','%(title)s')

        if mode == "V":
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'outtmpl': output_path if output_path + '.%(ext)s' else 'yt-output.%(ext)s',
                'cache_dir': None,
                'cookiefile': None,
                'no_report': True,
            }
        else:
            ydl_opts = {
                'format': 'bestaudio/best',         # Best audio quality
                'extract_audio': True,              # Extract audio (converts video to audio)
                'audio_format': 'mp3',              # Output format (e.g., mp3, wav)
                'outtmpl': output_path if output_path + '.%(ext)s' else 'yt-output.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'cache_dir': None,
                'cookiefile': None,
                'no_report': True,
            }


        with YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
                print("Audio downloaded successfully")
                return True
            except Exception as e:
                print(f"Error: {e}")
                return False
            