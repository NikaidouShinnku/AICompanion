from openai import OpenAI
from typing import List, Dict

from llms.statistics import update_usage

import google.generativeai as genai
import os

os.environ['API_KEY'] = 'AIzaSyA6UrR76tnvDv9L0BDnk33WfrguBpcv-IM'

def chat(
        prompt:str = None,
        messages: List[Dict] = None,
        model:str = 'gemini-1.5-flash',
        **kwargs
):

    genai.configure(api_key=os.environ["API_KEY"])

    model = genai.GenerativeModel(model)

    assert prompt or messages, "Must provide either"

    if messages:
        prompt = [entry['content'] for entry in messages if entry['role'] == 'user'][-1]
    res = model.generate_content(prompt)

    return res.text

def wrap_iter(stream):
    for chunk in stream:
        yield chunk.choices[0].delta.content