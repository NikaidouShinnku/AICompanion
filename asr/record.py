import signal
import subprocess
import wave
import threading  # Added for Enter key thread
import msvcrt  # Added for capturing Enter key (Windows-specific)
import numpy as np
import pyaudio
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
OUTPUT_WAVE_FILE = "output.wav"

# Signal handler for Ctrl+C (KeyboardInterrupt)
def signal_handler(sig, frame):
    print("Ctrl-C 被按下，停止录制并退出程序...")
    raise KeyboardInterrupt

def record_with_silence_detection(
    output_file: str = "output.wav",
    *,
    duration: int = 60,
    max_silence_seconds: int = 5,
):
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Store recorded audio data
    frames = []

    # Open file for writing audio data
    if output_file:
        wf = wave.open(output_file, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
    else:
        wf = None

    # Real-time update function (unchanged)
    def _update_plot(data):
        data_np = np.frombuffer(data, dtype=np.int16)
        max_amplitude = np.max(np.abs(data_np))
        bar_length = int(max_amplitude / (2**15) * 50)
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

        console_height = console.size.height
        console_width = console.size.width
        vertical_padding = max(1, (console_height - 5) // 2)
        horizontal_padding = max(1, (console_width - 100) // 2)

        padding = Padding(panel, pad=(vertical_padding, horizontal_padding), expand=False)
        return Align.center(padding, vertical="middle"), bar

    # Function to stop recording (unchanged)
    def _stop():
        stream.stop_stream()
        stream.close()
        audio.terminate()

    # Open microphone stream
    stream = audio.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    console = Console()

    # New section: Thread to monitor Enter key press
    # ----------------------- START OF CHANGE -----------------------
    def check_for_enter_key():
        while True:
            if msvcrt.kbhit() and msvcrt.getch() == b'\r':  # Enter key
                print("Enter key pressed, stopping recording...")
                break

    # Start thread to check for Enter key press
    key_listener = threading.Thread(target=check_for_enter_key)
    key_listener.start()
    # ------------------------ END OF CHANGE ------------------------

    bars = []

    try:
        # Using rich's Live object for real-time update
        with Live(console=console, screen=True, refresh_per_second=20) as live:
            while len(frames) < RATE / CHUNK * duration:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                panel, bar = _update_plot(data)

                bars.append(bar)
                if max_silence_seconds:
                    max_silence_len = int(RATE / CHUNK * max_silence_seconds)
                    if len(bars) > max_silence_len and set(bars[-max_silence_len:]) == {""}:
                        break
                live.update(panel)

                # Check if the Enter key thread has finished, then break
                # ----------------------- START OF CHANGE -----------------------
                if not key_listener.is_alive():
                    break
                # ------------------------ END OF CHANGE ------------------------

    except KeyboardInterrupt:
        print("KeyboardInterrupt: 录音中止")
    except Exception as e:
        print(f"Error during recording: {e}")
    finally:
        _stop()

    # Write recorded frames to the file
    if wf:
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