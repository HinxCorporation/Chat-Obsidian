import json
import logging

import chatutil


def console_out(content: str):
    try:
        json_obj = json.loads(content)
        content = json_obj['choices'][0]['delta']['content']
        print(content, end='', flush=True)
    except Exception as ee:
        logging.error(f"Error processing content: {ee}")
        logging.error(content)
        print('-', end='', flush=True)


if __name__ == '__main__':
    util = chatutil.ChatUtil(console_out)
    print(' (Q to quit.)  free any time.')
    while True:
        msg = input("You: ")
        if not msg:
            continue
        if msg in ["Q", 'q', "quit"]:
            break
        print('assistant:', end='')
        util.chat(msg)
        # new empty line to continue.
        print('                                                           ')
    print('exit. tks for use.')
