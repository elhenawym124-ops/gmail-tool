import os
import subprocess
from pathlib import Path
import nicegui

def build():
    # Get NiceGUI path
    nicegui_path = Path(nicegui.__file__).parent
    
    # Define the command
    cmd = [
        'python',
        '-m', 'PyInstaller',
        'main_app.py',
        '--onefile',
        '--windowed',
        '--icon=app_icon.ico',
        '--add-data', f'{nicegui_path}{os.pathsep}nicegui',
        '--collect-all', 'nicegui',
        '--collect-all', 'uvicorn',
        '--collect-all', 'fastapi',
        '--collect-all', 'starlette',
        '--name', 'GmailExtractorPro',
        '--clean',
    ]
    
    print(f"Building with NiceGUI from: {nicegui_path}")
    print(f"Running command: {' '.join(cmd)}")
    
    subprocess.call(cmd)

if __name__ == '__main__':
    build()
