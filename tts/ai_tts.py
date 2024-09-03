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
    segments = []
    current_segment = ""

    for sentence in sentences:
        if len(current_segment) + len(sentence) <= max_length:
            current_segment += sentence
        else:
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


stop_flag = threading.Event()

def tts_with_ai_segmented(text: str, language: str = "ja"):
    stop_flag.clear()

    segments = split_text_by_custom_rules(text)
    audio_tools = [None] * len(segments)  # 预先分配一个列表来存放生成的音频工具

    def generate_and_store_audio(segment, index):
        output_file = f"output_{index + 1}.wav"
        url = (rf"http://localhost:9880/?refer_wav_path=C:\Users\25899\Desktop\GPT-SoVITS-beta0706\DATA\真红wav\00000110.wav&prompt_text=だから、そんな顔しないでほしいんだ。悲しい夢に負けないでほしい。&prompt_language=ja&text={segment}&text_language={language}")
        audio_tool = AudioPlayerTool(url, output_file)
        audio_tool.fetch_audio()  # 生成音频
        audio_tools[index] = audio_tool  # 按照index将生成的音频工具放入列表
        return index

    def play_audio_in_order():
        current_index = 0
        while current_index < len(segments):
            if stop_flag.is_set():
                break  # 如果终止标志被设置，立即停止播放

            if current_index >= 3 or audio_tools[current_index] is not None:
                audio_tool = audio_tools[current_index]
                if audio_tool is not None:
                    audio_tool.play_audio()  # 播放当前音频
                    current_index += 1  # 继续下一个
                else:
                    continue  # 如果音频还未生成，等待
            else:
                threading.Event().wait(0.1)  # 每100ms检查一次

        # 清理所有音频文件，确保在所有音频播放完后或终止时删除
        for audio_tool in audio_tools:
            if audio_tool is not None:
                audio_tool.clean_up()

    with ThreadPoolExecutor() as executor_generate:
        # 启动播放线程
        threading.Thread(target=play_audio_in_order, daemon=True).start()

        # 提交所有生成音频的任务
        futures = [executor_generate.submit(generate_and_store_audio, segments[i], i) for i in range(len(segments))]

        # 等待所有生成任务完成
        for future in as_completed(futures):
            future.result()  # 获取生成结果以捕获异常

def stop_audio_playback():
    """终止播放并删除音频文件。"""
    stop_flag.set()  # 设置终止标志，播放线程将会终止

# def tts_with_ai(text:str, language:str = "ja"):
#
#     url = rf"http://localhost:9880/?refer_wav_path=C:\Users\25899\Desktop\GPT-SoVITS-beta0706\DATA\真红wav\00000110.wav&prompt_text=だから、そんな顔しないでほしいんだ。悲しい夢に負けないでほしい。&prompt_language=ja&text={text}&text_language={language}"
#
#     audio_tool = AudioPlayerTool(url)
#     audio_tool.run()