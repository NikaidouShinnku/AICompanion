from openai import OpenAI
from typing import List, Dict

def chat(
        prompt:str = None,
        messages: List[Dict] = None,
        stream:bool = False,
        **kwargs
):
    client = OpenAI(
        api_key="Bearer sk-ff0571b1b8054f26a1758a641b5921b9",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
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