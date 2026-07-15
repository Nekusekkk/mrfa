cat > install_mrfa.py << 'EOF'
#!/usr/bin/env python3
# Jednoplikowy instalator MRFA - pobiera i instaluje wszystkie pliki z raw.github

import os
import sys
import subprocess
import urllib.request
import json
import shutil
import tempfile

# ===== KONFIGURACJA =====
REPO_OWNER = "Nekusekkk"
REPO_NAME = "mrfa"
BRANCH = "main"
PATH_IN_REPO = "mrfa"  # ścieżka do folderu z plikami w repo

# Lista plików do pobrania (nazwa_pliku: raw_url)
FILES = {
    "mrfa.py": f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{PATH_IN_REPO}/mrfa.py",
    "agent.py": f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{PATH_IN_REPO}/agent.py",
    "requirements.txt": f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{PATH_IN_REPO}/requirements.txt",
    "config.json": f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{PATH_IN_REPO}/config.json",
    "inject.bat": f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{PATH_IN_REPO}/inject.bat",
    "unload.bat": f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{PATH_IN_REPO}/unload.bat",
    "README.md": f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{PATH_IN_REPO}/README.md"
}

# ===== FUNKCJE =====
def print_status(msg, status="INFO"):
    print(f"[{status}] {msg}")

def download_file(url, dest_path):
    """Pobiera plik z URL i zapisuje pod ścieżką dest_path"""
    try:
        print_status(f"Pobieranie: {url}", "DOWNLOAD")
        urllib.request.urlretrieve(url, dest_path)
        return True
    except Exception as e:
        print_status(f"Błąd pobierania {url}: {e}", "ERROR")
        return False

def install_requirements():
    """Instaluje zależności z requirements.txt"""
    try:
        print_status("Instalacja zależności Python...", "INSTALL")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"Błąd instalacji zależności: {e}", "ERROR")
        return False

def create_symlink():
    """Tworzy dowiązanie symboliczne w $PREFIX/bin"""
    try:
        prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
        bin_dir = os.path.join(prefix, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        link_path = os.path.join(bin_dir, "mrfa")
        target_path = os.path.join(os.getcwd(), "mrfa.py")
        
        if os.path.exists(link_path):
            os.remove(link_path)
        os.symlink(target_path, link_path)
        print_status(f"Dowiązanie utworzone: {link_path} -> {target_path}", "OK")
        return True
    except Exception as e:
        print_status(f"Błąd tworzenia dowiązania: {e}", "ERROR")
        return False

def main():
    print_status("=== INSTALATOR MRFA ===", "START")
    print_status(f"Repozytorium: {REPO_OWNER}/{REPO_NAME}", "INFO")
    
    # Krok 1: Pobranie plików
    print_status("Pobieranie plików...", "INFO")
    for filename, url in FILES.items():
        if download_file(url, filename):
            print_status(f"Zapisano: {filename}", "OK")
        else:
            print_status(f"Nie udało się pobrać: {filename}", "ERROR")
            # Kontynuuj mimo błędów - niektóre pliki mogą być opcjonalne
    
    # Krok 2: Instalacja zależności
    if os.path.exists("requirements.txt"):
        if not install_requirements():
            print_status("Instalacja zależności nieudana, spróbuj ręcznie: pip install -r requirements.txt", "WARN")
    else:
        # Ręczna instalacja podstawowych bibliotek
        print_status("Brak requirements.txt - instaluję podstawowe biblioteki...", "WARN")
        basic_packages = ["requests", "pillow", "pyautogui", "pynput", "psutil", "pygetwindow"]
        for pkg in basic_packages:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=True)
            except:
                print_status(f"Nie udało się zainstalować {pkg}", "ERROR")
    
    # Krok 3: Nadanie uprawnień
    if os.path.exists("mrfa.py"):
        os.chmod("mrfa.py", 0o755)
        print_status("Nadano uprawnienia do mrfa.py", "OK")
    
    # Krok 4: Tworzenie dowiązania
    if not create_symlink():
        print_status("Spróbuj ręcznie: ln -s ~/mrfa/mrfa.py $PREFIX/bin/mrfa", "WARN")
    
    # Krok 5: Test
    print_status("Test: uruchom 'mrfa --help'", "INFO")
    try:
        result = subprocess.run(["mrfa", "--help"], capture_output=True, text=True)
        print_status("Instalacja zakończona pomyślnie!", "SUCCESS")
        print(result.stdout)
    except FileNotFoundError:
        print_status("mrfa nie znaleziony - spróbuj zrestartować terminal", "WARN")
        print_status("Lub uruchom ręcznie: python mrfa.py --help", "INFO")

if __name__ == "__main__":
    main()
EOF
