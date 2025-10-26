pyinstaller --onefile --windowed -i hanview.ico --add-data "hanview.ico;." --hidden-import "pystray._win32" hanview.py
pause