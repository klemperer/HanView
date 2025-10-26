import requests
import ctypes
import os
import sys
import time
import threading
import winreg
import webbrowser
from PIL import Image
import exifread
from pystray import MenuItem as item, Icon, Menu
import tkinter as tk
from tkinter import messagebox
import subprocess
import json
from playsound3 import playsound 
import shutil 
from datetime import datetime 

VERSION = "1.0.0"
RELEASE_JSON_URL = "https://ss.blueforge.org/hanview/release.json" # JSON file URL containing version number and update notes
DOWNLOAD_URL = "https://ss.blueforge.org/hanview/hanview.exe" # Latest version executable file
IMAGE_URL = f"https://ss.blueforge.org/han?v={VERSION}"  # Image URL

UPDATE_INTERVAL_SECONDS = 3 * 60 * 60 # Update image every 3 hours
APP_NAME = "HanView"
REG_KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
ICON_FILENAME = "hanview.ico"
DOWNLOAD_RETRY_INTERVAL_SECONDS = 30
INTERNET_CHECK_INTERVAL_SECONDS = 60
PROJECT_URL = "https://github.com/klemperer/HanView" # Project website

han_word = None # The word itself
han_url = None  # Word details page URL
han_mp3 = None  # Word pronunciation MP3 file URL
han_copyright = None # Image copyright text
han_copyright_url = None # Image copyright link

# Used to hold a reference to the pystray icon object
root = None
icon = None


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_executable_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(__file__)

def is_startup_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False

# Toggle startup option        
def toggle_startup():
    executable_path = get_executable_path()
    if is_startup_enabled():
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, APP_NAME)
            print(f"[{time.ctime()}] Successfully removed from startup items.")
        except Exception as e:
            print(f"[{time.ctime()}] Failed to remove startup item: {e}")
    else:
        try:
            if executable_path.endswith('.exe'):
                command = f'"{executable_path}"'
            else:
                pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
                command = f'"{pythonw_path}" "{executable_path}"'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
            print(f"[{time.ctime()}] Successfully added to startup items.")
        except Exception as e:
            print(f"[{time.ctime()}] Failed to add startup item: {e}")

# Download image
def download_image(image_url, save_path):
    try:
        print(f"[{time.ctime()}] Downloading image from {image_url}...")
        response = requests.get(image_url, stream=True, timeout=20)
        if response.status_code == 200:
            with open(save_path, 'wb') as f: f.write(response.content)
            print(f"[{time.ctime()}] Image successfully saved to: {save_path}")
            return True
        else:
            print(f"[{time.ctime()}] Download failed, status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[{time.ctime()}] Error occurred during download: {e}")
        return False

# Set wallpaper
def set_as_wallpaper(image_path):
    if os.name != 'nt': return False
    try:
        print(f"[{time.ctime()}] Setting desktop wallpaper...")
        SPI_SETDESKWALLPAPER = 20
        abs_image_path = os.path.abspath(image_path)
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, abs_image_path, 3)
        print(f"[{time.ctime()}] Desktop wallpaper set successfully!")
        return True
    except Exception as e:
        print(f"[{time.ctime()}] Error occurred while setting wallpaper: {e}")
        return False

# Check internet connection
def check_internet_connection():
    try:
        requests.get("https://www.bing.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False

# Show copyright info popup in the main thread
def show_copyright_info():
    root.after(0, _show_copyright_dialog_thread_safe)

# Function to actually show the popup
def _show_copyright_dialog_thread_safe():
    if han_copyright and han_copyright_url:
        if messagebox.askyesno("Image Info", f"{han_copyright}\n\nView related information?"):
            webbrowser.open(han_copyright_url)
    elif han_copyright:
        messagebox.showinfo("Image Info", han_copyright)

# Show "About" popup
def show_about_dialog():
    root.after(0, _show_about_dialog_thread_safe)

def _show_about_dialog_thread_safe():
    title = "About HanView"
    message = (
        f"HanView {VERSION}\n"
        f"{PROJECT_URL}\n"
    )
    messagebox.showinfo(title, message)

# Dynamically build menu items
def build_menu_items():
    menu_items = []

    if han_url:
        menu_items.append(item(f'Look up {han_word}', lambda: webbrowser.open(han_url)))
    
    if han_mp3:
        menu_items.append(item(f'Read {han_word}', lambda: threading.Thread(target=play_word_sound, daemon=True).start()))
    
    if han_url or han_mp3:
        menu_items.append(Menu.SEPARATOR)

    menu_items.append(item('Random Review', lambda: threading.Thread(target=update_wallpaper_job, args=(True,), daemon=True).start()))
    
    wallpaper_path = os.path.join(os.path.dirname(get_executable_path()), "wallpaper.jpg")
    if os.path.exists(wallpaper_path):
        menu_items.append(item('Copy&Save', copy_and_save_wallpaper))

    if han_copyright:
        menu_items.append(item('Image Info', show_copyright_info))

    menu_items.append(Menu.SEPARATOR)

    menu_items.append(item('Run on Startup', toggle_startup, checked=lambda item: is_startup_enabled()))

    if getattr(sys, 'frozen', False):
        menu_items.append(item('Check for Updates', lambda: check_for_updates(icon)))
    
    menu_items.append(item('About', show_about_dialog)) 
    menu_items.append(item('Exit', lambda: quit_app(icon)))
    
    return tuple(menu_items)

# Update wallpaper task
def update_wallpaper_job(is_random=False): # is_random parameter is used to determine if it's a random review
    global icon, han_word, han_url, han_mp3, han_copyright, han_copyright_url
    han_word, han_url, han_mp3, han_copyright, han_copyright_url = None, None, None, None, None
    if icon:
        print(f"[{time.ctime()}] Updating context menu (clearing state).")
        icon.menu = Menu(*build_menu_items())

    base_directory = os.path.dirname(get_executable_path())
    save_filename = "wallpaper.jpg"
    full_save_path = os.path.join(base_directory, save_filename)
    
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        dc = user32.GetDC(None)
        width = gdi32.GetDeviceCaps(dc, 8) 
        height = gdi32.GetDeviceCaps(dc, 10)
        user32.ReleaseDC(None, dc)
        dynamic_image_url = f"{IMAGE_URL}&w={width}&h={height}"
    except Exception as e:
        print(f"[{time.ctime()}] Failed to get screen resolution: {e}, will use default URL: {IMAGE_URL}")
        dynamic_image_url = IMAGE_URL
    
    # If it's random review, add random parameter to the URL
    if is_random:
        dynamic_image_url += "&random"
        print(f"[{time.ctime()}] Random review mode, will use URL: {dynamic_image_url}")
    else:
        print(f"[{time.ctime()}] Normal loop mode, will use URL: {dynamic_image_url}")

    image_downloaded = download_image(dynamic_image_url, full_save_path)
    if image_downloaded:
        try:
            print(f"[{time.ctime()}] Extracting EXIF info from {full_save_path} (using exifread)...")
            
            with open(full_save_path, 'rb') as f:
                tags = exifread.process_file(f) 

            if tags:
                han_word = str(tags.get('Image Artist', '')).strip()
                
                han_url = str(tags.get('Image ImageDescription', '')).strip()
                
                han_mp3 = str(tags.get('Image DocumentName', '')).strip()
                
                copyright_info = str(tags.get('Image Copyright', '')).strip()

                if copyright_info:
                    if "||" in copyright_info:
                        parts = copyright_info.split("||", 1)
                        han_copyright = parts[0].strip()
                        han_copyright_url = parts[1].strip()
                    else:
                        han_copyright = copyright_info
                        han_copyright_url = None
                else:
                    han_copyright = None
                    han_copyright_url = None
                
                print(f"[{time.ctime()}] EXIF info extracted successfully:")
                print(f"    - Artist (han_word): {han_word}")
                print(f"    - ImageDescription (han_url): {han_url}")
                print(f"    - DocumentName (han_mp3): {han_mp3}")
                print(f"    - Copyright (han_copyright): {han_copyright}")
                print(f"    - Copyright URL (han_copyright_url): {han_copyright_url}")

            else:
                print(f"[{time.ctime()}] No EXIF info found in image, clearing old data.")
                han_word, han_url, han_mp3, han_copyright, han_copyright_url = None, None, None, None, None

        except Exception as e:
            print(f"[{time.ctime()}] Error occurred while extracting EXIF info: {e}")
            han_word, han_url, han_mp3, han_copyright, han_copyright_url = None, None, None, None, None
        
        if icon:
            print(f"[{time.ctime()}] Updating context menu...")
            icon.menu = Menu(*build_menu_items())

        if set_as_wallpaper(full_save_path):
            return True 
    
    return False

# Scheduler function
def run_scheduler(icon):
    print(f"[{time.ctime()}] Program started, checking network connection...")
    while not check_internet_connection():
        print(f"[{time.ctime()}] No network connection, retrying in {INTERNET_CHECK_INTERVAL_SECONDS} seconds...")
        time.sleep(INTERNET_CHECK_INTERVAL_SECONDS)

    print(f"[{time.ctime()}] Connected to the internet, attempting first wallpaper update...")
    
    while not update_wallpaper_job():
        if not icon.visible:
            print(f"[{time.ctime()}] User exited before first update completed.")
            return
            
        print(f"[{time.ctime()}] Update failed, retrying in {DOWNLOAD_RETRY_INTERVAL_SECONDS} seconds...")
        time.sleep(DOWNLOAD_RETRY_INTERVAL_SECONDS)

    print(f"[{time.ctime()}] First wallpaper update successful.")
    print(f"[{time.ctime()}] Switched to scheduled update mode, updating every {UPDATE_INTERVAL_SECONDS / 3600:.1f} hours.")

    while icon.visible:
        time.sleep(UPDATE_INTERVAL_SECONDS)
        
        if not icon.visible:
            break
            
        print(f"\n[{time.ctime()}] Time's up, starting scheduled update.")
        if check_internet_connection():
            update_wallpaper_job()
        else:
            print(f"[{time.ctime()}] No network connection detected, skipping this update.")
    print(f"[{time.ctime()}] Scheduled update thread has exited.")

# Copy and save the current wallpaper
def copy_and_save_wallpaper():
    try:
        base_directory = os.path.dirname(get_executable_path())
        source_path = os.path.join(base_directory, "wallpaper.jpg")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        destination_filename = f"{timestamp}.jpg"
        destination_path = os.path.join(base_directory, destination_filename)
        
        shutil.copy(source_path, destination_path)
        print(f"[{time.ctime()}] Wallpaper copied from {source_path} to {destination_path}")
        
        root.after(0, lambda: messagebox.showinfo("Operation Successful", "Wallpaper successfully copied to the program directory"))
    except FileNotFoundError:
        print(f"[{time.ctime()}] Copy operation failed: wallpaper.jpg does not exist.")
        root.after(0, lambda: messagebox.showerror("Operation Failed", "wallpaper.jpg file not found."))
    except Exception as e:
        print(f"[{time.ctime()}] Error occurred while copying wallpaper: {e}")
        root.after(0, lambda: messagebox.showerror("Operation Failed", f"Error copying file: {e}"))

# Update to new program version
def download_and_update(icon):
    new_exe_path = os.path.join(os.path.dirname(get_executable_path()), "han_new.exe")
    try:
        print(f"[{time.ctime()}] Downloading new version from {DOWNLOAD_URL}...")
        response = requests.get(DOWNLOAD_URL, stream=True, timeout=60)
        if response.status_code == 200:
            with open(new_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[{time.ctime()}] New version downloaded to: {new_exe_path}")
            
            updater_bat_path = os.path.join(os.path.dirname(get_executable_path()), "updater.bat")
            current_exe_path = get_executable_path()
            
            with open(updater_bat_path, 'w') as f:
                f.write(f'''
@echo off
echo Waiting for {APP_NAME} to close...
taskkill /F /IM "{os.path.basename(current_exe_path)}" > nul
timeout /t 2 /nobreak > nul
echo Replacing old version...
del "{current_exe_path}"
rename "{new_exe_path}" "{os.path.basename(current_exe_path)}"
echo Starting new version...
start "" "{current_exe_path}"
echo Cleaning up...
del "%~f0"
''')
            subprocess.Popen(f'"{updater_bat_path}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            print(f"[{time.ctime()}] Program is exiting for update...")
            root.after(100, quit_app, icon)
            
        else:
            root.after(0, lambda: messagebox.showerror("Download Failed", f"Failed to download new version. Status code: {response.status_code}"))
            print(f"[{time.ctime()}] Failed to download new version. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        root.after(0, lambda: messagebox.showerror("Download Failed", f"Error occurred while downloading new version: {e}"))
        print(f"[{time.ctime()}] Error occurred during download: {e}")

# Check for updates dialog box
def show_update_dialog(result, icon):
    status, version_or_error, releasenotes = result
    if status == 'update_available':
        message = f"A new version ({version_or_error}) is available.\n\nUpdate notes:\n{releasenotes}\n\nWould you like to update now?\nClicking OK will update the program in the background."
        if messagebox.askyesno("New Version Found", message):
            threading.Thread(target=download_and_update, args=(icon,)).start()
    elif status == 'no_update':
        messagebox.showinfo("No Update", "You are using the latest version.")
    elif status == 'error':
        messagebox.showerror("Update Check Failed", f"Error occurred while checking for updates: {version_or_error}")

# Check for updates function
def perform_network_check(icon):
    print(f"[{time.ctime()}] Checking for updates...")
    try:
        response = requests.get(RELEASE_JSON_URL, timeout=20)
        response.raise_for_status()
        release_info = response.json()
        latest_version = release_info.get("version")
        releasenotes = release_info.get("releasenotes")
        
        print(f"[{time.ctime()}] Current version: {VERSION}, Latest version: {latest_version}")
        
        if latest_version and latest_version != VERSION:
            result = ('update_available', latest_version, releasenotes)
        else:
            result = ('no_update', None, None)
            
    except requests.exceptions.RequestException as e:
        print(f"[{time.ctime()}] Error occurred while checking for updates: {e}")
        result = ('error', e, None)
    except json.JSONDecodeError as e:
        print(f"[{time.ctime()}] Error parsing update info: {e}")
        result = ('error', f"Could not parse update file: {e}", None)
    
    root.after(0, show_update_dialog, result, icon)

# Check for updates thread
def check_for_updates(icon):
    threading.Thread(target=perform_network_check, args=(icon,)).start()

# Play word-related audio
def play_word_sound():
    if han_mp3:
        try:
            print(f"[{time.ctime()}] Playing online audio: {han_mp3}")
            playsound(han_mp3)
            print(f"[{time.ctime()}] Audio playback finished.")
        except Exception as e:
            print(f"[{time.ctime()}] Error occurred while playing audio: {e}")
            root.after(0, lambda: messagebox.showerror("Playback Failed", f"Could not play online audio: {e}"))

# Exit program
def quit_app(icon):
    print("Exiting program...")
    if icon:
        icon.stop()
    if root:
        root.destroy()

def main():
    global root, icon
    root = tk.Tk()
    root.withdraw()

    try:
        icon_path = resource_path(ICON_FILENAME)
        image = Image.open(icon_path)
    except FileNotFoundError:
        print(f"Error: Could not find icon file '{ICON_FILENAME}'.")
        sys.exit(1)
    
    initial_menu = Menu(*build_menu_items())
    icon = Icon(APP_NAME, image, "HanView", menu=initial_menu)
    
    threading.Thread(target=icon.run, daemon=True).start()

    update_thread = threading.Thread(target=run_scheduler, args=(icon,), daemon=True)
    update_thread.start()
    
    print("Program has started and is running in the background. Please find the icon in the system tray.")
    root.mainloop()

if __name__ == "__main__":
    main()