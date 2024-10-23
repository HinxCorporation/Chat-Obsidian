import fnmatch
import os

# 预定义的连接符号
CONNECTORS = {
    "default": ("├── ", "└── ", "│   "),
    "simple": ("+-- ", "`-- ", "|   "),
    "compact": ("+ ", "` ", "| "),
    "custom": ("", "", "")  # 用户可以自定义
}


def create_folder_view(folder_path,
                       prefix="",
                       top_only=True,
                       recurse=False,
                       connector_style="default",
                       ignores=None):
    """
    生成文件夹的树状视图
    :param folder_path: 文件夹路径
    :param prefix: 前缀，用于递归生成树状视图
    :param top_only: 是否只显示顶层文件夹
    :param recurse: 是否递归显示子文件夹
    :param connector_style: 连接符号样式，可选值为 "default", "simple", "compact", "custom"
    :param ignores: 需要忽略的文件或文件夹的通配符列表
    :return: 树状视图的字符串
    """
    is_travel = not top_only or recurse
    if ignores is None:
        ignores = []
    tree_view = ""
    files_and_dirs = os.listdir(folder_path)
    connectors = CONNECTORS.get(connector_style, CONNECTORS["default"])

    for index, item in enumerate(files_and_dirs):
        item_path = os.path.join(folder_path, item)

        # 检查是否需要忽略该文件或文件夹
        if any(fnmatch.fnmatch(item, ignore) for ignore in ignores):
            continue

        if index == len(files_and_dirs) - 1:
            connector = connectors[1]  # "└── "
            new_prefix = prefix + connectors[2]  # "    "
        else:
            connector = connectors[0]  # "├── "
            new_prefix = prefix + connectors[2]  # "│   "

        tree_view += f"{prefix}{connector}{item}\n"

        if os.path.isdir(item_path) and is_travel:
            tree_view += create_folder_view(item_path, new_prefix, top_only, recurse, connector_style, ignores)

    return tree_view


def list_folder(folder_path, ignores=None, recursive=False):
    """
    列出文件夹中的文件和文件夹
    :param folder_path: 文件夹路径
    :param ignores: 需要忽略的文件或文件夹的通配符列表
    :param recursive: 是否递归列出子文件夹
    :return: 文件和文件夹列表
    """
    if not folder_path:
        folder_path = os.getcwd()
    if ignores is None:
        ignores = []
    return create_folder_view(folder_path, "", True, recursive, "default", ignores)

