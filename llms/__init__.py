def chat(model:str, **kwargs):
    if model in ("llama3-8b-8192", "llama3-70b-8192"):
        from llms.groqs import chat as groq_chat
        return groq_chat(model=model, **kwargs)
    elif model in ("deepseek-chat", "deepseek-coder"):
        from llms.deepseek import chat as deepseek_chat
        return deepseek_chat(model=model, **kwargs)
    elif model in ("qwen-max", "qwen-max-longcontext"):
        from llms.qianwen import chat as qianwen_chat
        return qianwen_chat(model=model, **kwargs)
    elif model in ("ernie-bot-pro", "ernie-4.0-turbo-8k"):
        from llms.baidu import chat as baidu_chat
        return baidu_chat(model=model, **kwargs)
    elif model in ("moonshot-v1-128k", "moonshot-v1-32k"):
        from llms.moonshot import chat as moonshot_chat
        return moonshot_chat(model=model, **kwargs)
    else:
        raise ValueError(f"Unknown model: {model}")
