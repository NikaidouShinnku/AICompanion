import PyPDF2
import re
import os


def read_pdf_content(file_path):
    try:
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except IOError as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def extract_reply(res: str, token: str) -> str:
    pattern = fr"<{token}>(.*?)</{token}>"
    match = re.search(pattern, res, re.DOTALL)
    if match:
        return match.group(1).strip()
    return res

def fetch_url_content(url):
    import requests
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch URL: {url}. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def read_file_content(file_path):
    # 确保文件路径规范化
    file_path = os.path.abspath(file_path.strip('\"').replace("\\", "\\\\"))

    # 根据文件类型处理
    if file_path.endswith('.pdf'):
        return read_pdf_content(file_path)
    elif file_path.endswith('.txt'):
        return read_txt_content(file_path)
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return None
        except PermissionError:
            print(f"Permission denied for file: {file_path}")
            return None
        except IOError as e:
            print(f"Error reading file {file_path}: {e}")
            return None


def check_file_exists(file_path):
    # 使用os.path.abspath规范化路径后再检查文件是否存在
    file_path = os.path.abspath(file_path.strip('\"').replace("\\", "\\\\"))
    return os.path.exists(file_path)

def check_url_valid(url):
    import requests
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False