# HanView: Effortless Learning Chinese on Wallpapers
Transform your desktop into a daily learning adventure. HanView fetches the stunning daily Bing wallpaper, uses AI to seamlessly overlay a frequently used Chinese word, and sets the enriched image as your Windows wallpaper. It’s a perfect way to "encounter" a Chinese word, effortlessly—blending the beauty of the world with the richness of language, right on your desktop.

This is a sister project of [Github Project Binglish](https://github.com/klemperer/binglish), which empowers users to learn English words on Bing wallpapers.

- Image URL: https://ss.blueforge.org/han
- Wallpaper Source: https://github.com/TimothyYe/bing-wallpaper
- Words Difficulty: Top 10,000 frequently used Chinese words
- Update Frequency: Every 3 hours
- Generative AI cannot guarantee complete accuracy of the content
- Suitable for Windows 10 and above, 1920x1080 resolution (other resolutions not fully tested)
<img width="1920" height="1080" alt="HanView Screenshot" src="https://github.com/user-attachments/assets/4e649925-7205-4802-a3a8-53d31eb8fee0" />


## Download Compiled Program
[Github releases](https://github.com/klemperer/HanView/releases/latest/download/hanview.exe) Or [Alternative Download Link](https://ss.blueforge.org/hanview/hanview.exe)

## Or Compile by Yourself
```Bash
git clone https://github.com/klemperer/HanView/
cd HanView
pip install -r requirements.txt
pip install pyinstaller
bundle.bat
```

## Run
Double-click hanview.exe (if packaged yourself, you can find this file in the dist directory under the project) to run; no installation is required. After running, the program will minimize to the system tray. You can select "Run automatically at startup" from the right-click menu.

You can also run it by executing the following command in the command line (not recommended, the "Check for Updates" feature is unavailable):

```Bash
python hanview.py
```

## Right-Click Menu Description
- Look Up Word: Jump to a dictionary to learn more about the word's usage.
- Read Word: Play the AI-generated explanation of the word's usage.
- Random Review: Randomly display a past wallpaper (does not affect the current wallpaper update cycle).
- Copy & Save: If you like the current wallpaper, click this option to copy and save a copy (saved to the program's directory).
- Image Info: Content, copyright, and other related information about the current wallpaper.

## Occasional Issues
#### ModuleNotFoundError: No module named 'tkinter'
You might encounter this issue when directly running hanview.py. This is usually because tkinter is not installed correctly. When you install a full Python interpreter, tkinter should be included. However, if you are using a custom Python version or selected a minimal installation option, tkinter might be missing. To solve this, you need to install tkinter separately. You can use the following command to install it:

```Bash
pip install tk
```

#### Wallpaper Display is Abnormal (Overly Stretched or Squashed)
Try the following solution: Right-click on the desktop, select "Personalize", select "Background", and then choose "Fill" or "Fit".
