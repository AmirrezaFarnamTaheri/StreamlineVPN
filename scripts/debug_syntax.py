import ast
from pathlib import Path

def check_syntax(file_path):
    print(f"Checking syntax of {file_path}...")
    try:
        content = Path(file_path).read_text(encoding='utf-8')
        ast.parse(content)
        print("Syntax is OK!")
    except SyntaxError as e:
        print("Syntax error found:")
        print(e)
        print(f"Line: {e.lineno}, Offset: {e.offset}")
        if e.text:
            print(f"Text: {e.text.strip()}")

if __name__ == "__main__":
    check_syntax("scripts/deployment/content_generators.py")
