# 1.检查venv是否存在
if (!(Test-Path venv)) {
    Write-Output "Creating a virtual environment..."
    python -m venv venv
} else {
    Write-Output "Virtual environment already exists."
}

# 2.激活venv
Write-Output "Activating the virtual environment..."
. .\venv\Scripts\activate

# 3.pip安装requirements
Write-Output "Installing requirements..."
pip install -r requirements.txt

clear

python chat_obsidian.py
# # 4.启动 python chat_obsidian.py
# Write-Output "Starting the Python script..."
# $job = Start-Job -ScriptBlock { python chat_obsidian.py }
# Write-Output "Running chat obsidian."
#
# # 5.程序等待循环
# # 这个不是非常明确, 但是这里有一个简单的方式，循环检查python脚本是否在运行，如果不在运行就退出循环
# while ((Get-Job | Where-Object State -EQ 'Running')) {
#     # Write-Output "Python script is still running..."
#     Start-Sleep -Seconds 5 # 延迟5秒再次检查
# }
#
# # 结束
# Write-Output "Program exit."
