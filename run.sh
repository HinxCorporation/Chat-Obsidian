#!/bin/sh

# 1. Check if venv exists
if [ ! -d "venv" ]
then
  echo "Creating a virtual environment..."
  python -m venv venv
else
  echo "Virtual environment already exists."
fi

# 2. Activate venv
echo "Activating the virtual environment..."
source venv/bin/activate

# 3. Install requirements with pip
echo "Installing requirements..."
pip install -r requirements.txt

clear

# 4. Start python chat_obsidian.py
echo "Starting the Python script..."
echo "Running chat obsidian."
python chat_obsidian.py

# End
echo "Program exit."
