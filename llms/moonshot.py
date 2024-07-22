from openai import OpenAI
from typing import List, Dict

def chat(
        prompt:str = None,
        messages: List[Dict] = None,
        stream:bool = False,
        **kwargs
):

    client = OpenAI(
        api_key="sk-bnh8Ogoj2KdQSq9i8bnkcNmUZK5KaHs8rMr4lAdSVjfSJm07",
        base_url="https://api.moonshot.cn/v1"

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