import re


def parse_to_filename(input_string: str, length=12):
    """
    Parse the input string and convert it to a valid filename.

    Args:
        input_string (str): The input string to be parsed.
        length (int): The maximum length of the output filename. Default is 12.

    Returns:
        str: The parsed and valid filename.
    """
    INVALID_CHARS_FOR_FILENAMES = re.compile(r'[<>:"/\\|?*]')
    REPLACED_CHARS = ['\n', '\r', '\t', '#', '%', '&', '^', '@', '~', '!', '$']
    if len(input_string) > length:
        input_string = input_string[:length]
    for char in REPLACED_CHARS:
        input_string = input_string.replace(char, '')
    valid_filename = INVALID_CHARS_FOR_FILENAMES.sub('', input_string).strip()
    return valid_filename[:length] + '...' if len(valid_filename) > length else valid_filename
