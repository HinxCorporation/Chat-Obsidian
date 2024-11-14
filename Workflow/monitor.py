import datetime
import logging
import os

import colorlog


class Monitor:
    def __init__(self, flow_name: str = "non-named-flow",
                 enable_console_log: bool = True,
                 enable_monitor_file_log: bool = False,
                 skip_info: bool = False,
                 skip_warning: bool = False,
                 skip_error: bool = False
                 ):
        """
        Initialize the monitor.
        Parameters:
            flow_name: str, the name of the flow.
            enable_console_log: bool, whether to enable console log.
            enable_monitor_file_log: bool, whether to enable monitor file log.
        """
        self.skip_info = skip_info
        self.skip_warning = skip_warning
        self.skip_error = skip_error
        self._continue = True
        if not enable_monitor_file_log:
            enable_console_log = True
            # at least one log method should be enabled
        logger = logging.getLogger(flow_name)
        logger.setLevel(20)
        if not logger.handlers:  # 作用,防止重新生成处理器
            if enable_console_log:
                sh = logging.StreamHandler()  # 创建控制台日志处理器
                log_colors_config = {
                    'DEBUG': 'white',
                    'INFO': 'white',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                }
                sh_fmt = colorlog.ColoredFormatter(
                    fmt="%(log_color)s[%(asctime)s.%(msecs)03d]  %(filename)s:%(lineno)d  [%(levelname)s]: %(message)s",
                    datefmt='%Y-%m-%d  %H:%M:%S',
                    log_colors=log_colors_config)
                # 给处理器添加格式
                sh.setFormatter(fmt=sh_fmt)
                # 给日志器添加处理器，过滤器一般在工作中用的比较少，如果需要精确过滤，可以使用过滤器
                logger.addHandler(sh)
                # print out green color to indicate logger is set up successfully
                # print('\033[32m' + f"Logger set up successfully: {log_file}" + '\033[0m')
            if enable_monitor_file_log:
                # setup logger
                now = datetime.datetime.now()
                file_name = now.strftime('%Y%m%d_%H%M%S') + ".log"
                pure_flow_name_for_log_file = flow_name.replace(" ", "_")
                # ensure pure_flow_name_for_log_file exclude ':/\?*^#'
                pure_flow_name_for_log_file = "".join(
                    [c for c in pure_flow_name_for_log_file if c not in ':/\?*^#'])
                log_file = f"wf_logs/{pure_flow_name_for_log_file}/{file_name}"
                log_file = os.path.join(os.getcwd(), log_file)
                log_file = os.path.abspath(log_file)
                log_folder = os.path.dirname(log_file)
                if not os.path.exists(log_folder):
                    os.makedirs(log_folder)
                fh = logging.FileHandler(filename=log_file, mode='a', encoding="utf-8")  # 创建日志文件处理器
                fmt = logging.Formatter(
                    fmt="[%(asctime)s.%(msecs)03d]-[%(levelname)s]: %(message)s",
                    datefmt='%Y-%m-%d  %H:%M:%S')
                fh.setFormatter(fmt=fmt)
                logger.addHandler(fh)
        else:
            pass
        self.logger = logger

    def on_except(self, exception: Exception) -> None:
        self.logger.error(f"Exception occurred: {exception}")
        self._continue = False
        raise exception

    def warning(self, message: str) -> None:
        if self.skip_warning:
            return
        self.logger.warning(f"{message}")

    def error(self, message: str) -> None:
        if self.skip_error:
            return
        self.logger.error(f"{message}")

    def info(self, message: str) -> None:
        if self.skip_info:
            return
        self.logger.info(f"{message}")

    def log(self, message: str) -> None:
        if self.skip_info:
            return
        self.logger.info(f"{message}")

    def stop_workflow(self) -> None:
        self._continue = False

    def can_continue(self) -> bool:
        return self._continue
