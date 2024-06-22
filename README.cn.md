# Chat Obsidian

使Chat Obsidian能够像GPT一样进行对话。

## 特性

- [x] 自动生成 markdown 文件，类似于 chat gpt
- [x] 给 Obsidian 画布节点上色
- [x] 自动连接 Obsidian 画布
- [x] 使用系统提示
- [x] 使用文件块
- [x] 通过新的重定向进行对话
- [x] 通过控制台进行对话
- [ ] RAG - 支持 [即将推出]
- [ ] langchain - 支持 [即将推出]
- [ ] 作为 Obsidian 插件 [即将推出]

## 注意事项

- 您可以通过文本文件或 Markdown 笔记设置一些 `bot define`，然后将它们附加到您的对话中。它将作为提示附加。
- 您可以设置 `runs` 来作为 PowerShell 的别名，这将是一个聪明的选择。
- 控制台上不需要 Nerd 字体。如果您希望在控制台上清晰显示，请从配置中删除它们。
- 必须安装 `requirements`。

## 如何使用

##### 步骤1：完成配置

将 `config.sample.ini` 复制到 `config.ini`
将 `note_root` 设置为您的 Obsidian 笔记根目录。
将 `deepseek.key` 设置为您的特殊密钥。

##### 步骤2：启动

###### 安装

首先，您需要激活 venv 环境，特别是如果您不熟悉使用 Python 的话，venv 是最直接的方法。
对于 Windows 平台，您可以使用 PowerShell 运行 `install.ps1`。如果您使用的是 Mac 或 Linux，则可以使用 `install.sh`。
或者，您可以手动执行以下步骤。

```shell
python -m venv venv
./venv/Scripts/activate
# 安装依赖
pip install -rm requirements.txt
```

在此时，您的安装任务已经完成。

###### 启动

打开您的 Python 项目并调用它。

```shell
# 作为 Obsidian 笔记运行
python chat_obsidian.py
```

```shell
# 作为控制台对话运行
python chat_console.py
```

打开您的 Obsidian，将会有一个名为 `AI-Chat` 的新文件夹。
创建一个新的 Canvas 并重命名它。

*Obsidian画布示例*

![example - obsidian](https://raw.githubusercontent.com/HinxCorporation/Chat-Obsidian/master/README.assets/example-Obsidian.png)

创建一个新的笔记，完成后使用 `\`，它将自动进行下一步。

*控制台示例*

![example - console](https://raw.githubusercontent.com/HinxCorporation/Chat-Obsidian/master/README.assets/example-console.gif)

##### 步骤3：享受使用
