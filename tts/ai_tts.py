import requests
from pydub import AudioSegment
from pydub.playback import play
import os, re


class AudioPlayerTool:
    def __init__(self, url):
        self.url = url
        self.audio_file = "output.wav"

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

    def play_audio_pydub(self):
        try:
            song = AudioSegment.from_wav(self.audio_file)
            play(song)
        except Exception as e:
            print(f"An error occurred while playing the audio with pydub: {e}")

    def clean_up(self):
        try:
            if os.path.exists(self.audio_file):
                os.remove(self.audio_file)
        except Exception as e:
            print(f"An error occurred during cleanup: {e}")

    def run(self):
        self.fetch_audio()
        self.play_audio_pydub()
        self.clean_up()


def split_text_by_custom_rules(text, max_length=20):
    # 按照标点符号分割，句号、换行、感叹号、问号直接算作一句话
    sentences = re.split(r'(?<=[。！？\n])', text)
    segments = []
    current_segment = ""

    for sentence in sentences:
        if len(current_segment) + len(sentence) <= max_length:
            current_segment += sentence
        else:
            # 如果一句话超过max_length，寻找下一个标点符号分割
            sub_sentences = re.split(r'(?<=[，,；;])', sentence)
            for sub_sentence in sub_sentences:
                if len(current_segment) + len(sub_sentence) <= max_length:
                    current_segment += sub_sentence
                else:
                    segments.append(current_segment.strip())
                    current_segment = sub_sentence
            if current_segment:
                segments.append(current_segment.strip())
                current_segment = ""

    if current_segment:
        segments.append(current_segment.strip())

    return segments

def tts_with_ai(text:str, language:str = "ja"):

    url = rf"http://localhost:9880/?refer_wav_path=C:\Users\25899\Desktop\GPT-SoVITS-beta0706\DATA\真红wav\00000110.wav&prompt_text=だから、そんな顔しないでほしいんだ。悲しい夢に負けないでほしい。&prompt_language=ja&text={text}&text_language={language}"

    audio_tool = AudioPlayerTool(url)
    audio_tool.run()

from concurrent.futures import ThreadPoolExecutor, as_completed

def tts_with_ai_segmented(text: str, language: str = "ja"):
    segments = split_text_by_custom_rules(text)
    futures = []
    audio_files = []

    with ThreadPoolExecutor() as executor:
        for i, segment in enumerate(segments, 1):
            output_file = f"output_{i}.wav"
            url = (rf"http://localhost:9880/?refer_wav_path=C:\\Users\\25899\\Desktop\\GPT-SoVITS-beta0706\\DATA\\"
                   f"真红wav\\00000110.wav&prompt_text=だから、そんな顔しないでほしいんだ。悲しい夢に負けないでほしい。"
                   f"&prompt_language=ja&text={segment}&text_language={language}")

            audio_tool = AudioPlayerTool(url)
            audio_tool.audio_file = output_file
            future = executor.submit(audio_tool.fetch_audio)
            futures.append(future)
            audio_files.append(output_file)

        for future in as_completed(futures):
            future.result()

    # 按顺序播放生成的音频
    for audio_file in audio_files:
        song = AudioSegment.from_wav(audio_file)
        play(song)
        os.remove(audio_file)