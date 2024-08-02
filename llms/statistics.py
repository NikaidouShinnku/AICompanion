USAGE = {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0,
    "price": 0.0
}


def update_usage(usage, price:float = 0.0):
    USAGE["prompt_tokens"] += usage.prompt_tokens
    USAGE["completion_tokens"] += usage.completion_tokens
    USAGE["total_tokens"] += usage.total_tokens
    USAGE["price"] += price
    return USAGE


def get_usage():
    return USAGE