import os
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image

# --- KONFIGURACJA ---
BASE_DIR = Path(r"C:\Users\rtogt\Downloads\SHS-main\SHS-main")
IMG_DIR = BASE_DIR / "images"
IMG_DIR.mkdir(exist_ok=True) # Tworzy folder images jeśli go nie ma

def download_and_convert(url):
    """Pobiera obraz z URL (np. Wix), konwertuje na WebP i zwraca nową nazwę pliku."""
    try:
        # Generowanie nazwy pliku na podstawie URL (usuwamy dziwne znaki)
        clean_name = re.sub(r'[^\w\s-]', '', Path(url).stem)[:50]
        webp_name = f"{clean_name}.webp"
        webp_path = IMG_DIR / webp_name

        # Jeśli już istnieje, nie pobieraj ponownie
        if webp_path.exists():
            return f"images/{webp_name}"

        # Pobieranie
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            temp_path = IMG_DIR / "temp_img"
            with open(temp_path, "wb") as f:
                f.write(response.content)
            
            # Konwersja
            with Image.open(temp_path) as im:
                im = im.convert("RGB")
                im.save(webp_path, "WEBP", quality=85)
            
            os.remove(temp_path)
            return f"images/{webp_name}"
    except Exception as e:
        print(f"  [!] Błąd Wix/URL {url}: {e}")
    return None

def process_local_image(src, html_file):
    """Konwertuje lokalny plik JPG/PNG na WebP."""
    potential_paths = [BASE_DIR / src, IMG_DIR / Path(src).name, html_file.parent / src]
    img_path = next((p for p in potential_paths if p.exists()), None)

    if img_path and img_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
        try:
            webp_path = img_path.with_suffix('.webp')
            with Image.open(img_path) as im:
                im = im.convert("RGBA") if im.mode in ("RGBA", "P") else im.convert("RGB")
                im.save(webp_path, "WEBP", quality=85)
            return src.replace(img_path.suffix, ".webp")
        except Exception as e:
            print(f"  [!] Błąd lokalny {src}: {e}")
    return None

def run_cleaner():
    print(f"--- START KONWERSJI (BEZ AI) w {BASE_DIR} ---")
    html_files = list(BASE_DIR.glob("*.html"))

    for html_file in html_files:
        print(f"\nPrzetwarzanie: {html_file.name}")
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        modified = False

        # 1. Przetwarzanie tagów <img>
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src: continue

            new_src = None
            if "wixstatic.com" in src:
                print(f"  Pobieram z Wix: {src[:50]}...")
                new_src = download_and_convert(src)
            else:
                new_src = process_local_image(src, html_file)

            if new_src:
                img['src'] = new_src
                modified = True

        # 2. Przetwarzanie teł (background-image)
        for tag in soup.find_all(style=True):
            style = tag['style']
            match = re.search(r'url\([\'"]?(https?://[^\'"\)]+|[^\'"\)]+)[\'"]?\)', style)
            if match:
                src = match.group(1)
                new_src = None
                if "wixstatic.com" in src:
                    new_src = download_and_convert(src)
                else:
                    new_src = process_local_image(src, html_file)
                
                if new_src:
                    tag['style'] = style.replace(src, new_src)
                    modified = True

        if modified:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print(f"  >>> ZAPISANO ZMIANY")

if __name__ == "__main__":
    run_cleaner()
    print("\n--- KONIEC. Wszystkie obrazy (Wix i lokalne) są teraz w WebP. ---")