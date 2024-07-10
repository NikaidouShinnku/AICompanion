import openai
from typing import List, Dict

def chat(
        prompt:str = None,
        messages: List[Dict] = None,
        stream:bool = False,
        **kwargs
):

    client = openai.OpenAI(
        api_key="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",
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
