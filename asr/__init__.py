import os
import pathlib

from groq import Groq

from asr.record import record_with_silence_detection

os.environ['GROQ_API_KEY'] = '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'
def do_asr(file, prompt: str = None, **kwargs):
    file = pathlib.Path(file)
    client = Groq()
    if not os.path.exists(file):
        raise FileNotFoundError(f"File not found: {file}")

    prompt = prompt or "对音频进行中文语音识别,并整理成流畅的文字。"
    transcription = client.audio.transcriptions.create(
        file=(str(file), file.read_bytes()),
        prompt=prompt,
        model="whisper-large-v3",
    )
    return transcription.text


import os
import tempfile
from typing import Literal




def record_and_asr(
    *,
    language: str = "zh",
    duration: int = None,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "output.wav")
        record_with_silence_detection(output_file=output_file, duration=duration or 30)
        if not os.path.exists(output_file):
            return

        return do_asr(output_file, prompt="中文普通话的输入", language=language)

