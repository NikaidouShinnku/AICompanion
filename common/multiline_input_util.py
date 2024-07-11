import json

def multi_input(hint: str = '> '):
    lines = []
    while True:
        try:
            user_input = input(hint)
            if user_input.strip().upper() == 'END':
                break
            # 处理特殊字符和非法Unicode字符
            user_input = user_input.encode('utf-8', 'replace').decode('utf-8')
            lines.append(user_input)
        except EOFError:
            break

    combined_input = "\n".join(lines)

    # 确保返回的字符串是有效的JSON格式
    try:
        json.dumps(combined_input)
    except (TypeError, ValueError) as e:
        print(f"Error converting to JSON: {e}")
        return None

    return combined_input