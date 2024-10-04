import signal
import subprocess
import wave
import threading  # Added for Enter key thread
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
    max_silence_seconds: int = 3,
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

    # New section: Listening for Enter key (using input() instead of msvcrt)
    # ----------------------- START OF CHANGE -----------------------
    def check_for_enter_key():
        input("Press Enter to stop recording...\n")
        print("Enter key pressed, stopping recording...")

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
                if not key_listener.is_alive():
                    break

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

if __name__ == "__main__":
    record_with_silence_detection(output_file=OUTPUT_WAVE_FILE)
