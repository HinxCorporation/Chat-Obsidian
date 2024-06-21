import os
import json
import uuid

BOT_ROLE = "assistant"
SYS_ROLE = "system"
USER_ROLE = "user"

PREFIX_LENGTH = 9


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def generate_uuid():
    # def length = 32
    return str(uuid.uuid4()).replace('-', '')[:16]


# def get_words(content):
#     try:
#         json_obj = json.loads(content)
#         content = json_obj['choices'][0]['delta']['content']
#         return content
#     # except Exception as ee:
#     except:
#         return '-'


def get_words(content):
    try:
        json_obj = json.loads(content)
        return json_obj['choices'][0]['delta']['content']
    except:
        return '-'


def is_text_file(file) -> bool:
    _, extension = os.path.splitext(file)
    return extension and extension.lower() in ['.md', '.markdown', '.html', '.csv', '.json', '.txt']


def find_file_under(working_dir, file):
    # file may be relative/to/file
    first = os.path.join(working_dir, file)
    if os.path.exists(first) and os.path.isfile(first):
        return first

    folder_to_scan, shortName = os.path.split(first)

    def entry_match(ent):
        # ensure name or name without extension equals shortName
        if ent.is_file():
            _, _nn = os.path.split(ent.path)
            if _nn == shortName:
                return True
            _pn, _ = os.path.splitext(_nn)
            if _pn == shortName:
                return True
        return False

    for top_entry in os.scandir(folder_to_scan):
        if entry_match(top_entry):
            return top_entry.path

    def walk(folder):
        # travel to end
        for entry in os.scandir(folder):
            if entry.is_dir():
                _res = walk(entry.path)
                if _res is not None:
                    return _res
            else:
                if entry_match(entry):
                    return entry.path
                return None

    result = walk(folder_to_scan)
    return result if result is not None else first


def read_attachment(file, working_dir):
    if file.startswith('[[') and file.endswith(']]'):
        file = file.replace('[[', '').replace(']]', '').strip()
        path = find_file_under(working_dir, file)
    else:
        if not os.path.exists(file):
            file = os.path.join(working_dir, file)
        path = file

    if not os.path.exists(path):
        return 'missing file'
    if is_text_file(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return 'cant read file format'


def get_message(message_content, role) -> dict:
    return {'content': message_content, 'role': role}


def create_system_message(text_content, working_dir=''):
    prefix, remainder = text_content.split(':', 1)
    remainder = remainder.strip()

    if prefix.lower().startswith('file'):
        file_detail = read_attachment(remainder, working_dir)
        return get_message(f'Here is a attachment ({remainder}) : {file_detail}', SYS_ROLE)

    elif prefix.lower() == 'system':
        return get_message(remainder, SYS_ROLE)

    else:
        return get_message(f'Here is a chat, {prefix}:{remainder}', SYS_ROLE)


def process_text_node(text_content, working_dir=''):
    if not working_dir:
        working_dir = os.getcwd()

    prefix = text_content[:PREFIX_LENGTH] if len(text_content) > PREFIX_LENGTH else text_content
    if ':' in prefix:
        return create_system_message(text_content, working_dir)
    else:
        return get_message(text_content, USER_ROLE)
