# Chat Obsidian

<p align=center>
Python Obsidian Chat Assistant - 使 Obsidian 能够像 GPT 一样聊天。
</p>

<p align=center>
<a href="https://github.com/HinxCorporation/Chat-Obsidian/blob/master/README.md">English</a> • <b>简体中文</b>
</p>

## 功能

- [x] 自动生成 markdown 文件，类似 chat gpt
- [x] 为 Obsidian 画布节点着色
- [x] 自动为 Obsidian 画布添加边
- [x] 使用系统提示
- [x] 使用文件块
- [x] 聊天重定向新功能
- [x] 通过控制台聊天
- [ ] RAG - 支持 [即将推出]
- [ ] langchain - 支持 [即将推出]
- [ ] 作为 Obsidian 插件 [即将推出]
- [x] 本地工具调用功能 2024/08/15 `需要新的 PyAissistant 包，需要重新安装 requirements`

## 注意

- 您可以通过文本文件或 markdown 笔记设置一些 `bot define`，然后将其附加到您的聊天中。它将作为提示追加。
- 您可以设置 `runs` 到 powershell 别名，这将是一个明智的选择
- Nerd 字体不是必需的。如果您希望在控制台上清晰显示，请从配置中移除它们
- 必须安装 `requirements`
- 至少安装 `PyAissistant 0.1.12` [最新版本](https://pypi.org/project/pyaissistant) [![PyPI Version](https://img.shields.io/pypi/v/pyaissistant.svg)](https://pypi.org/project/pyaissistant/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pyaissistant.svg)](https://pypi.org/project/pyaissistant/)

## 新继续开发

现在您可以将本地暴露功能添加到本地机器人中。

##### 如何操作

1. 在您的 IDE 中打开此项目。
2. 定位到聊天机器人的构造位置，例如 `ChatObsidian/obsolete_obsidian_utils` 文件夹下的 `chat_on_console.py`。
3. 找到构造函数中的 `self.bot: ChatBot = DeepSeekBot(post_words=self.print_console_word)` 这一行，例如第 14 行。
4. 通过 `ai_exposed_function` 装饰器暴露您的自定义暴露方法。例如暴露示例：

```python
# 这是如何将函数暴露给 Ai 助手的示例
@ai_exposed_function
def ai_get_bot_name(self):
    """
    暴露给 Ai 助手的方法，返回当前机器人的名称
    """
    return self.bot_name
```

##### 工作原理

`ai_exposed_function` 装饰器会将函数添加到 `exposed_functions` 列表中。
聊天机器人在构造时会收集所有暴露的函数，并将它们暴露给 Ai 助手。

## 如何使用

##### 第一步：完成配置

将 `config.sample.ini` 复制到 `config.ini`
设置 `note_root` 为您的 Obsidian 笔记根目录。
设置 `deepseek.key` 为您的特殊密钥。

##### 第二步：启动

###### 安装

首先，您需要激活虚拟环境，特别是如果您不熟悉使用 Python，因为 venv 是最直接的方法。
对于 Windows 平台，您可以使用 PowerShell 运行 `install.ps1`。如果您使用的是 Mac 或 Linux，可以使用 `install.sh`。
或者，您可以手动执行以下步骤。

```shell
# 安装 PyAissistant
pip install PyAissistant
```

```shell
python -m venv venv
./venv/Scripts/activate
# 安装 requirements
pip install -rm requirements.txt
```
此时，您的安装任务已完成

###### 启动

打开您的 Python 项目并调用它

```shell
# 作为 Obsidian 笔记运行
python chat_obsidian.py
```

```shell
# 作为控制台聊天运行
python chat_console.py
```

打开您的 Obsidian，将会出现一个名为 `AI-Chat` 的新文件夹。
创建一个新的画布并重命名它。
*Obsidian 画布示例*

![Obsidian](https://raw.githubusercontent.com/HinxCorporation/Chat-Obsidian/master/README.assets/example-Obsidian.png)

一旦您创建了一个新笔记，并以 `\` 结束，它将自动继续。

*控制台示例 (GIF)*
![Console](https://raw.githubusercontent.com/HinxCorporation/Chat-Obsidian/master/README.assets/example-console.gif)

*示例视频*
[![观看视频](http://img.youtube.com/vi/lbK0jWrrjpM/0.jpg)](https://www.youtube.com/watch?v=lbK0jWrrjpM)

##### 第三步：享受
