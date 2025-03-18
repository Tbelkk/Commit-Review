import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--name=CommitReview',
    '--onefile', 
    '--windowed', 
    '--hidden-import=customtkinter',
    '--hidden-import=git',
    '--hidden-import=ollama',
    '--hidden-import=tkinter',
    '--hidden-import=PIL', 
    '--clean' 
])