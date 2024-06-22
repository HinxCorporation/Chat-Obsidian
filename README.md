# Chat Obsidian

make obsidian able to chat like GPT.

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

## Notice

- You can set up some `bot define` via text file or markdown note. then attach them to your chat. it will append as prompt.
- You can set up `runs` to powershell alias, it will be a smart choice
- Nerd font is not required. if you want it clear on console, remove them from config
- `requirements` has to be installed

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
