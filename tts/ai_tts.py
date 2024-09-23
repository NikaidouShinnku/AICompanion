import requests
from pydub import AudioSegment
from pydub.playback import play
import os, re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading


class AudioPlayerTool:
    def __init__(self, url, output_file):
        self.url = url
        self.audio_file = output_file

    def fetch_audio(self):
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                with open(self.audio_file, "wb") as f:
                    f.write(response.content)
            else:
                print(f"Failed to fetch audio. Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while fetching the audio: {e}")

    def play_audio(self):
        try:
            song = AudioSegment.from_wav(self.audio_file)
            play(song)
        except Exception as e:
            print(f"An error occurred while playing the audio: {e}")
        finally:
            self.clean_up()

    def clean_up(self):
        try:
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)
        except Exception as e:
            print(f"An error occurred during cleanup: {e}")


def split_text_by_custom_rules(text, max_length=20):
    sentences = re.split(r'(?<=[。！？\n])', text)
    segments = [sentence.strip() for sentence in sentences if sentence.strip()]
    return segments


stop_flag = threading.Event()

def tts_with_ai_segmented(text: str, language: str = "ja"):
    stop_flag.clear()

    segments = split_text_by_custom_rules(text)
    audio_tools = [None] * len(segments)  # 预先分配一个列表来存放生成的音频工具

    def generate_and_store_audio(segment, index):
        output_file = rf"temp_tts_output\output_{index + 1}.wav"
        url = (rf"http://localhost:9880/?refer_wav_path=C:\Users\25899\Desktop\GPT-SoVITS-beta0706\DATA\真红wav\00000110.wav&prompt_text=だから、そんな顔しないでほしいんだ。悲しい夢に負けないでほしい。&prompt_language=ja&text={segment}&text_language={language}")
        audio_tool = AudioPlayerTool(url, output_file)
        audio_tool.fetch_audio()
        audio_tools[index] = audio_tool
        return index

    def play_audio_in_order():
        current_index = 0
        while current_index < len(segments):
            if stop_flag.is_set():
                break
            if current_index >= 3 or audio_tools[current_index] is not None:
                audio_tool = audio_tools[current_index]
                if audio_tool is not None:
                    audio_tool.play_audio()
                    current_index += 1
                else:
                    continue
            else:
                threading.Event().wait(0.1)

        for audio_tool in audio_tools:
            if audio_tool is not None:
                audio_tool.clean_up()

    with ThreadPoolExecutor() as executor_generate:

        threading.Thread(target=play_audio_in_order, daemon=True).start()

        futures = [executor_generate.submit(generate_and_store_audio, segments[i], i) for i in range(len(segments))]
        for future in as_completed(futures):
            future.result()

def stop_audio_playback():
    """终止播放并删除音频文件。"""
    stop_flag.set()  # 设置终止标志，播放线程将会终止

# def tts_with_ai(text:str, language:str = "ja"):
#
#     url = rf"http://localhost:9880/?refer_wav_path=C:\Users\25899\Desktop\GPT-SoVITS-beta0706\DATA\真红wav\00000110.wav&prompt_text=だから、そんな顔しないでほしいんだ。悲しい夢に負けないでほしい。&prompt_language=ja&text={text}&text_language={language}"
#
#     audio_tool = AudioPlayerTool(url)
#     audio_tool.run()