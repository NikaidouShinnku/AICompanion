import openai
from typing import List, Dict
from llms.api_key_config import GROQ_API_KEY

def chat(
        prompt:str = None,
        messages: List[Dict] = None,
        stream:bool = False,
        **kwargs
):

    client = openai.OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"

    )

    assert prompt or messages, "Must provide either"

    if prompt:
        messages = [
            {"role": "user", "content": prompt}
        ]
    res = client.chat.completions.create(
        messages=messages,
        stream=stream,
        **kwargs
    )
    if not stream:
        return res.choices[0].message.content

    return wrap_iter(res)


def wrap_iter(stream):
    for chunk in stream:
        yield chunk.choices[0].delta.content
