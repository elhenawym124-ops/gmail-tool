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
        '--add-data', f'{nicegui_path}{os.pathsep}nicegui',
        '--name', 'GmailExtractorPro',
        '--clean',
        '--icon', 'NONE', # You can add an .ico path here if you have one
    ]
    
    print(f"Building with NiceGUI from: {nicegui_path}")
    print(f"Running command: {' '.join(cmd)}")
    
    subprocess.call(cmd)

if __name__ == '__main__':
    build()
