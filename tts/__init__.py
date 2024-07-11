import os.path
import subprocess


def edge_tts(
    text,
    *,
    voice: str = "zh-CN-YunyangNeural",
    rate: str = "+50%",
    output: str,
    **kwargs,
):
    if not voice:
        voice = "zh-CN-YunyangNeural"
    command = [
        "C:\\Users\\25899\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\edge-tts.exe",
        "--voice",
        voice,
        f"--rate={rate}",
        "--text",
        text,
        "--write-media",
        output,
        "--write-subtitles",
        output.replace(".mp3", ".vtt"),
    ]
    print(' '.join(command), end='')

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating audio: {e}")
        raise


import tempfile


def play_sound(file: str):
    """
    Play a media file using ffplay.

    Parameters:
    file_path (str): The path to the media file to be played.
    """
    try:
        # Construct the ffplay command
        command = ['C:\\Users\\25899\\scoop\\shims\\ffplay.exe', '-vn', '-nodisp', '-autoexit', file]

        # Call the command using subprocess
        subprocess.run(command)
    except Exception as e:
        print(f"An error occurred: {e}")

def tts(text: str, *, vendor="edge", output: str = None, play: bool = False, **kwargs):
    if output:
        if os.path.exists(output):
            os.remove(output)
        do_tts(text, vendor=vendor, output=output, **kwargs)
        if play:
            play_sound(output)
        return output

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as f:
        output = f.name
        do_tts(text, vendor=vendor, output=output, **kwargs)
        if play:
            play_sound(output)
        return None



def do_tts(text: str, *, vendor="edge", output: str, **kwargs):
    assert output, "Please provide an output file path"
    edge_tts(text, output=output, **kwargs)

