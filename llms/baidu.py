import json
import os
from typing import Dict, List

import httpx
import requests
from cachetools import TTLCache, cached
from llms.api_key_config import BAIDU_API_KEY, BAIDU_SECRETE_API_KEY


_BASE_AUTH_URL = "https://aip.baidubce.com/oauth/2.0/token"
_BASE_CHAT_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
TTL = 3600  # Set the TTL to 1 hour (3600 seconds)

# Create a TTL cache for storing the access token
token_cache = TTLCache(maxsize=1, ttl=TTL)

@cached(cache=token_cache)
def _get_access_token(client_id, client_secret):
    params = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    r = requests.post(url=_BASE_AUTH_URL, headers=headers, params=params, timeout=60)
    r.raise_for_status()
    rep = r.json()
    return rep["access_token"]


def refresh_token(client_id, client_secret):
    return _get_access_token(client_id, client_secret)


models_setting = {
    "ernie-bot": {
        "url": f"{_BASE_CHAT_URL}/completions",
        "max_tokens": 4096,
    },
    "ernie-bot-turbo": {
        "url": f"{_BASE_CHAT_URL}/eb-instant",
        "max_tokens": 4096,
    },
    "ernie-bot-pro": {
        "url": f"{_BASE_CHAT_URL}/completions_pro",
        "max_tokens": 4096,
    },
    "ernie-4.0-turbo-8k": {
        "url": f"{_BASE_CHAT_URL}/ernie-4.0-turbo-8k",
        "max_tokens": 8192,
    },
}

client_id = BAIDU_API_KEY
client_secret = BAIDU_SECRETE_API_KEY

def chat(
    *,
    stream: bool = None,
    language: str = None,
    max_tokens: int = None,
    temperature: float = None,
    response_format: bool = None,
    **kwargs,
):
    if temperature is not None:
        if temperature == 0:
            temperature = 0.01
        kwargs["temperature"] = 0.001

    if max_tokens is not None:
        kwargs["max_output_tokens"] = max_tokens

    if response_format is not None:
        kwargs["response_format"] = response_format.get("type")

    if stream:
        return chat_stream(**kwargs)
    else:
        return sync_chat(**kwargs)


def sync_chat(*, prompt: str = None, messages: List[Dict] = None, model: str, **kwargs):
    token = refresh_token(client_id, client_secret)
    url = f"{models_setting[model]['url']}?access_token={token}"
    headers = {"Content-Type": "application/json"}
    if prompt is not None:
        messages = [{"role": "user", "content": prompt}]
    r = requests.post(
        url=url,
        json={"messages": messages, **kwargs},
        headers=headers,
        timeout=60,
    )
    r.raise_for_status()
    rep = r.json()
    error_code = rep.get("error_code")
    if error_code is None:
        return rep['result']
    raise ValueError("Error: " + json.dumps(rep, ensure_ascii=False))

def chat_stream(
    *,
    prompt: str = None,
    messages: List[Dict] = None,
    model: str,
    timeout: float = 60,
    **kwargs,
):
    """
    Send payload to OpenAI's server and return the response using requests streaming.
    """
    headers = {"Content-Type": "application/json"}
    token = refresh_token(client_id, client_secret)
    url = f"{models_setting[model]['url']}?access_token={token}"
    if prompt is not None:
        messages = [{"role": "user", "content": prompt}]
    if model not in models_setting:
        raise ValueError(f"model {model} not found")

    response = requests.post(
        url=url,
        json={
            "messages": messages,
            "stream": True,
            **kwargs,
        },
        headers=headers,
        timeout=timeout,
        stream=True,
    )

    response.raise_for_status()
    for line in response.iter_lines():
        if line:
            try:
                delta = json.loads(line.decode("utf-8").split("data: ")[1])
                error_code = delta.get("error_code")
                if error_code is not None:
                    raise ValueError("Error: " + json.dumps(delta, ensure_ascii=False))
                yield delta['result']

            except (json.JSONDecodeError, IndexError):
                continue
