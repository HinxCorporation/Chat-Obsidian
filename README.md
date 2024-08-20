# Chat Obsidian

<p align=center>
Python Obsidian Chat Assistant - make obsidian able to chat like GPT.
</p>

<br>

<p align=center>
<b>English</b> • <a href="https://github.com/HinxCorporation/Chat-Obsidian/blob/master/README.cn.md">简体中文</a>
</p>

<br>

## Features

- [x] Auto generate markdown file , like chat gpt
- [x] Color Obsidian canvas nodes
- [x] Auto edges Obsidian canvas
- [x] Using system prompt
- [x] Using file block
- [x] Chat RE-Direct new
- [x] Chat via Console
- [ ] RAG - support [ In coming ]
- [ ] langchain - support [ In coming ]
- [ ] plugin as Obsidian [ In coming ]
- [x] Local tool call features 2024/08/15 `require new PyAissistant package , needs to reinstall requirements`

## Notice

- You can set up some `bot define` via text file or markdown note. then attach them to your chat. it will append as prompt.
- You can set up `runs` to powershell alias, it will be a smart choice
- Nerd font is not required. if you want it clear on console, remove them from config
- `requirements` has to be installed
- At lease `PyAissistant 0.1.12` has installed  [![PyPI Version](https://img.shields.io/pypi/v/pyaissistant.svg)](https://pypi.org/project/pyaissistant/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/pyaissistant.svg)](https://pypi.org/project/pyaissistant/)

## New Continue DEV

Now you call add you local expose features to local bot.

##### HOW TO

1. open this project on your ide.
2. locate to the construction of chat bot , for example 'chat_on_console.py' under the `ChatObsidian/obsolete_obsidian_utils` folder.
3. find the line `self.bot: ChatBot = DeepSeekBot(post_words=self.print_console_word)` on the constructor , eg: line 14
4. Expose you custom expose method via `ai_exposed_function` decorator. like the expose demo

```python
# this is the example of how to expose a function to Ai assistant
@ai_exposed_function
def ai_get_bot_name(self):
    """
    method exposed to Ai assistant , returns current bot name
    """
    return self.bot_name
```

##### HOW IT WORKS

The `ai_exposed_function` decorator will add the function to the `exposed_functions` list.
The Chat bot collect all exposed function and expose them to Ai assistant while it was constructing.


## How to use

##### step.1 finished config with se

copy `config.sample.ini` to `config.ini`
set `note_root` to you obsidian note root.
set `deepseek.key` to your special key.

##### step.2 fire up

###### install

First, you need to activate the venv, especially if you are not familiar with using Python, as venv is the most straightforward method.
For Windows platforms, you can use PowerShell to run `install.ps1`. If you are on a Mac or Linux, you can use `install.sh`.
Alternatively, you can manually execute the following steps.

```shell
# install PyAissistant
pip install PyAissistant
```

```shell
python -m venv venv
./venv/Scripts/activate
# install requirements
pip install -rm requirements.txt
```
At this point, your installation task is complete
###### fire up
open you python project and call it

```shell
# run as obsidian note
python chat_obsidian.py
```

```shell
# run as console chat
python chat_console.py
```

Open you obsidian , and there will be a new folder. called `AI-Chat`
create a new Canvas and make a rename it.
*Obsidian canvas example*

![Obsidian](https://raw.githubusercontent.com/HinxCorporation/Chat-Obsidian/master/README.assets/example-Obsidian.png)

Once you are create a new note , finished with `\` , It will auto go-on.

*console example (GIF)*
![Console](https://raw.githubusercontent.com/HinxCorporation/Chat-Obsidian/master/README.assets/example-console.gif)

*example video*
[![watch video](http://img.youtube.com/vi/lbK0jWrrjpM/0.jpg)](https://www.youtube.com/watch?v=lbK0jWrrjpM)


##### step.3 enjoy
