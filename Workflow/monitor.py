import datetime
import logging
import os

import colorlog


class Monitor:
    def __init__(self, flow_name: str = "non-named-flow"):
        self._continue = True
        # setup logger

        now = datetime.datetime.now()
        file_name = now.strftime('%Y%m%d_%H%M%S') + ".log"
        log_file = f"wf_logs/{flow_name}/{file_name}"
        log_file = os.path.join(os.getcwd(), log_file)
        log_folder = os.path.dirname(log_file)
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)
        logger = logging.getLogger(flow_name)
        logger.setLevel(20)

        if not logger.handlers:  # 作用,防止重新生成处理器
            sh = logging.StreamHandler()  # 创建控制台日志处理器
            fh = logging.FileHandler(filename=log_file, mode='a', encoding="utf-8")  # 创建日志文件处理器
            log_colors_config = {
                'DEBUG': 'white',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
            fmt = logging.Formatter(
                fmt="[%(asctime)s.%(msecs)03d]-[%(levelname)s]: %(message)s",
                datefmt='%Y-%m-%d  %H:%M:%S')
            sh_fmt = colorlog.ColoredFormatter(
                fmt="%(log_color)s[%(asctime)s.%(msecs)03d]-[%(levelname)s]: %(message)s",
                datefmt='%Y-%m-%d  %H:%M:%S',
                log_colors=log_colors_config)
            # 给处理器添加格式
            sh.setFormatter(fmt=sh_fmt)
            fh.setFormatter(fmt=fmt)
            # 给日志器添加处理器，过滤器一般在工作中用的比较少，如果需要精确过滤，可以使用过滤器
            logger.addHandler(sh)
            logger.addHandler(fh)
            # print out green color to indicate logger is set up successfully
            print('\033[32m' + "Logger set up successfully" + '\033[0m')
        else:
            # print out orange color to indicate logger is already set up
            print('\033[33m' + "Logger already set up, skipping" + '\033[0m')
        self.logger = logger
        self.logger.info(f"Flow {flow_name} started at {now}")

    def on_except(self, exception: Exception) -> None:
        self.logger.error(f"Exception occurred: {exception}")
        self._continue = False

    def warning(self, message: str) -> None:
        self.logger.warning(f"Warning: {message}")

    def error(self, message: str) -> None:
        self.logger.error(f"Error: {message}")

    def info(self, message: str) -> None:
        self.logger.info(f"Log: {message}")

    def log(self, message: str) -> None:
        self.logger.info(f"Log: {message}")

    def stop_workflow(self) -> None:
        self._continue = False

    def can_continue(self) -> bool:
        return self._continue