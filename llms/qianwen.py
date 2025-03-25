from openai import OpenAI
from typing import List, Dict
from llms.api_key_config import QIANWEN_API_KEY

from llms.statistics import update_usage


def chat(
        prompt:str = None,
        messages: List[Dict] = None,
        stream:bool = False,
        **kwargs
):
    client = OpenAI(
        api_key=QIANWEN_API_KEY,
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
        if res.usage:
            price = res.usage.prompt_tokens / 25000 + res.usage.completion_tokens / 8333
            update_usage(res.usage, price=price)
        return res.choices[0].message.content

    return wrap_iter(res)


def wrap_iter(stream):
    for chunk in stream:
        yield chunk.choices[0].delta.content