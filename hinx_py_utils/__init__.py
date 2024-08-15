import os

tree_patterns = ["├── ", "└── ", "│   "]


def parse_text_to_structure(text):
    """
    将结构目录解析成目录列表
    """
    lines = text.split('\n')
    structure = []
    prefix_stack = []
    current_prefix = ""

    for line in lines:
        depth = 0
        for pattern in tree_patterns:
            depth += line.count(pattern)
            line = line.replace(pattern, '')
        if depth == 0:
            # Root level
            current_prefix = line
            prefix_stack = [current_prefix]
        else:
            # Ensure the stack has the correct depth
            prefix_stack = prefix_stack[:depth]
            current_prefix = '/'.join(prefix_stack) + '/' + line
            prefix_stack.append(line)

        structure.append(current_prefix)

    return structure


def create_structure(root_path, structure):
    """
    创建结构目录
    """
    for path in structure:
        full_path = os.path.join(root_path, path)
        print(f'touch:{full_path}')
        if os.path.exists(full_path):
            continue
        if '.' in os.path.basename(full_path):
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            open(full_path, 'w').close()
        else:
            os.makedirs(full_path, exist_ok=True)


def create_files_from_text(root_path, text):
    """
    从指定的文件夹中创建结构目录
    例子:
        ollama_api/
        ├── ollama_api/
        │   ├── __init__.py
        │   ├── client.py
        ├── setup.py
        ├── README.md
    """
    if not root_path:
        root_path = os.getcwd()
    structure = parse_text_to_structure(text)
    print("Generated structure:")
    for item in structure:
        print(item)
    create_structure(root_path, structure)
