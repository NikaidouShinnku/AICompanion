import signal
import subprocess
import wave

import numpy as np
import pyaudio
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# 音频设置
CHUNK = 1024  # 每个块的样本数量
FORMAT = pyaudio.paInt16  # 16-bit音频
CHANNELS = 1  # 单声道
RATE = 44100  # 采样率
OUTPUT_WAVE_FILE = "output.wav"  # 输出文件名


def signal_handler(sig, frame):
    print("Ctrl-C 被按下，停止录制并继续处理...")
    raise KeyboardInterrupt


def record_with_silence_detection(
    output_file: str = "output.wav",
    *,
    duration: int = 60,
    max_silence_seconds: int = 5,
):
    signal.signal(signal.SIGINT, signal_handler)
    # 初始化pyaudio
    audio = pyaudio.PyAudio()

    # 存储录制的音频数据
    frames = []

    # 打开文件以写入音频数据
    if output_file:
        wf = wave.open(output_file, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
    else:
        wf = None

    # 实时更新函数
    def _update_plot(data):
        data_np = np.frombuffer(data, dtype=np.int16)
        max_amplitude = np.max(np.abs(data_np))
        bar_length = int(max_amplitude / (2**15) * 50)  # 调整条形图长度
        bar = "█" * bar_length
        text = Text(bar, style="green")
        panel = Panel(
            text,
            title="               [yellow]录音中[/yellow]               ",
            expand=False,
            width=60,
        )

        from rich.align import Align
        from rich.padding import Padding
        # from rich.layout import Layout

        # layout = Layout()
        # layout.split_column(
        #     Layout(visible=True, size=10), Layout(name="center")
        # )
        # layout["center"].update(Align.center(panel))

        # return layout, bar

        # padding = Padding(panel, pad=(20, 1), expand=False)

        # 计算动态padding值
        console_height = console.size.height
        console_width = console.size.width
        vertical_padding = max(1, (console_height - 5) // 2)  # 5是面板的估计高度
        horizontal_padding = max(1, (console_width - 100) // 2)  # 60是面板的估计宽度

        # 使用计算得出的padding值
        padding = Padding(
            panel, pad=(vertical_padding, horizontal_padding), expand=False
        )
        # # 计算动态padding值
        # console_height = console.size.height
        # vertical_padding = max(1, (console_height - 5) // 2)  # 5是面板的估计高度

        # # 使用计算得出的padding值
        # padding = Padding(panel, pad=(vertical_padding, 1), expand=False)
        return Align.center(padding, vertical="middle"), bar

    def _stop():
        # 关闭流
        stream.stop_stream()
        stream.close()
        audio.terminate()

    bars = []

    # 打开麦克风流
    stream = audio.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    # 初始化 rich 控制台
    console = Console()

    try:
        # 使用 rich 的 Live 对象进行实时更新
        with Live(console=console, screen=True, refresh_per_second=20) as live:
            while len(frames) < RATE / CHUNK * duration:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                panel, bar = _update_plot(data)

                bars.append(bar)
                if max_silence_seconds:
                    max_silence_len = int(RATE / CHUNK * max_silence_seconds)
                    if len(bars) > max_silence_len and set(bars[-max_silence_len:]) == {
                        ""
                    }:
                        break
                live.update(panel)
    except KeyboardInterrupt:
        pass

    _stop()
    # 写入音频数据到文件
    wf.writeframes(b"".join(frames))
    wf.close()

    return frames


def _ffmpeg_record_and_convert_to_wav(
    *, device_id: int = 0, duration: int = None, output_file: str
):
    if not is_ffmpeg_available():
        raise EnvironmentError(
            "ffmpeg is not installed or not available in the system path"
        )

    if output_file is None:
        raise ValueError("output_file must be specified")
    cmd = f'ffmpeg -f avfoundation -i ":{device_id}" -ar 16000 -ac 1 -c:a pcm_s16le'
    if duration is not None:
        cmd += f" -t {duration}"
    cmd += f" {output_file}"
    subprocess.run(cmd, shell=True)


def convert_audio_to_format(input_file: str, output_file: str):
    if not is_ffmpeg_available():
        raise EnvironmentError(
            "ffmpeg is not installed or not available in the system path"
        )

    cmd = f'ffmpeg -i "{input_file}" -ar 16000 -ac 1 -c:a pcm_s16le "{output_file}"'
    subprocess.run(cmd, shell=True)


def is_ffmpeg_available():
    """Check if `ffmpeg` is available on the system."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def ffmpeg_record(*, output_file: str, duration: int = None):
    signal.signal(signal.SIGINT, signal_handler)
    try:
        _ffmpeg_record_and_convert_to_wav(
            device_id=1,
            output_file=output_file,
            duration=duration,
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    record_with_silence_detection(output_file=OUTPUT_WAVE_FILE)