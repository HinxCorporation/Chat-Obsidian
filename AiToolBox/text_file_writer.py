import os
import threading
import time


class TextFileWriter:
    def __init__(self, file_path, hold_file=False, flush_interval=0.1, encoding='utf-8', mode='w', max_cache_size=20,
                 debug_console=False):
        if mode not in ['w', 'a']:
            raise ValueError("Invalid mode. Use 'w' for write or 'a' for append.")
        self.file_path = file_path
        self.hold_file = hold_file
        self.flush_interval = flush_interval
        self.encoding = encoding
        self.mode = mode
        self.max_cache_size = max_cache_size
        self.is_alive = True
        self.debug_console = debug_console
        self.friendly_grace = False
        self.lock = threading.Lock()  # For thread safety
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, self.mode, encoding=self.encoding) as f:
            f.write('')  # Create file if not exist , overwrite if mode is 'w'
        if hold_file:
            self.fs = open(self.file_path, 'a', encoding=self.encoding)
        self.text_stack = ''
        self.thread = threading.Thread(target=self.life_cycle)
        self.thread.start()

    def write(self, text):
        with self.lock:
            self.text_stack += text
        if len(self.text_stack) >= self.max_cache_size:
            self.flush()

    def close(self):
        self.kill()

    def kill(self):
        with self.lock:
            self.friendly_grace = True

    def flush_with_open(self):
        with open(self.file_path, 'a', encoding=self.encoding) as f:
            f.write(self.text_stack)
        pass

    def flush_with_fs(self):
        self.fs.write(self.text_stack)
        pass

    def flush(self):
        if len(self.text_stack) == 0:
            return
        with self.lock:
            try:
                if self.hold_file:
                    self.flush_with_fs()
                else:
                    self.flush_with_open()
                if self.debug_console:
                    print(f'\033[32m{self.text_stack}\033[0m', end='')
                self.text_stack = ''
            except:
                print('\033[31m[Flush Error]\033[0m')
                pass

    # Destructor
    def __del__(self):
        self.close()

    def goodbye(self):
        self.flush()  # Flush remaining text
        self.is_alive = False
        if self.hold_file:
            self.fs.close()

    def life_cycle(self):
        while self.is_alive:
            self.flush()
            time.sleep(self.flush_interval)
            if self.friendly_grace:
                self.goodbye()
                break
        print('\033[36m[TextWriter Closed]\033[0m')
