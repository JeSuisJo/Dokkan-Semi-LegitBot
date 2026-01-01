import subprocess
import os
import json
import tempfile
import time
from PIL import Image
import pytesseract

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

DRAGON_STONE_CLICK_POSITION = (532, 658)
OK_CONFIRMATION_ZONE = (364, 585, 439, 646)

class DragonStonesDisabledException(Exception):
    pass

def load_config():
    default_config = {
        "use_meat_first": False,
        "use_dragon_stones": False
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "use_dragon_stones" in config:
                    return config
        return default_config
    except Exception:
        return default_config

def capture_screenshot(adb_path, device, temp_file):
    subprocess.run([adb_path, '-s', device, 'shell', 'screencap', '-p', '/sdcard/t.png'], capture_output=True)
    subprocess.run([adb_path, '-s', device, 'pull', '/sdcard/t.png', temp_file], capture_output=True)
    subprocess.run([adb_path, '-s', device, 'shell', 'rm', '/sdcard/t.png'], capture_output=True)

def tap_on_device(adb_path, device, x, y):
    subprocess.run([adb_path, '-s', device, 'shell', 'input', 'tap', str(x), str(y)])

def find_text_ok_in_zone(img, zone):
    x1, y1, x2, y2 = zone
    region = img.crop((x1, y1, x2, y2))
    
    try:
        region_gray = region.convert('L')
        region_resized = region_gray.resize((region_gray.width * 2, region_gray.height * 2), Image.LANCZOS)
        
        data = pytesseract.image_to_data(region_resized, lang='eng', config='--psm 7', output_type=pytesseract.Output.DICT)
        for i, text in enumerate(data['text']):
            if text.strip().upper() == 'OK':
                left = data['left'][i]
                top = data['top'][i]
                width_text = data['width'][i]
                height_text = data['height'][i]
                center_x_relative = (left + width_text // 2) // 2
                center_y_relative = (top + height_text // 2) // 2
                center_x = x1 + center_x_relative
                center_y = y1 + center_y_relative
                return (center_x, center_y)
        
        text = pytesseract.image_to_string(region_resized, lang='eng', config='--psm 7').strip().upper()
        if 'OK' in text:
            return ((x1 + x2) // 2, (y1 + y2) // 2)
    except Exception:
        pass
    
    methods = [
        lambda r: r.convert('L').resize((r.width * 3, r.height * 3), Image.LANCZOS),
        lambda r: r.convert('L').resize((r.width * 2, r.height * 2), Image.LANCZOS).point(lambda p: 255 if p > 128 else 0, mode='1'),
        lambda r: r.resize((r.width * 2, r.height * 2), Image.LANCZOS),
    ]
    
    psm_configs = ['--psm 8', '--psm 6', '--psm 13']
    
    for method in methods:
        try:
            processed_region = method(region)
            
            for psm in psm_configs:
                try:
                    data = pytesseract.image_to_data(processed_region, lang='eng', config=psm, output_type=pytesseract.Output.DICT)
                    for i, text in enumerate(data['text']):
                        if text.strip().upper() == 'OK':
                            left = data['left'][i]
                            top = data['top'][i]
                            width_text = data['width'][i]
                            height_text = data['height'][i]
                            resize_factor = processed_region.width // region.width
                            center_x_relative = (left + width_text // 2) // resize_factor
                            center_y_relative = (top + height_text // 2) // resize_factor
                            center_x = x1 + center_x_relative
                            center_y = y1 + center_y_relative
                            return (center_x, center_y)
                    
                    text = pytesseract.image_to_string(processed_region, lang='eng', config=psm).strip().upper()
                    if 'OK' in text:
                        return ((x1 + x2) // 2, (y1 + y2) // 2)
                except Exception:
                    continue
        except Exception:
            continue
    
    return None

def use_dragon_stones(adb_path, device):
    config = load_config()
    
    if not config.get("use_dragon_stones", False):
        print("use_dragon_stones is false, stopping script")
        raise DragonStonesDisabledException("use_dragon_stones is disabled in config")
    
    tap_on_device(adb_path, device, DRAGON_STONE_CLICK_POSITION[0], DRAGON_STONE_CLICK_POSITION[1])
    time.sleep(0.4)
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        screenshot_file = temp_file.name
    
    try:
        while True:
            capture_screenshot(adb_path, device, screenshot_file)
            img = Image.open(screenshot_file)
            
            ok_pos = find_text_ok_in_zone(img, OK_CONFIRMATION_ZONE)
            if ok_pos:
                tap_on_device(adb_path, device, ok_pos[0], ok_pos[1])
                time.sleep(0.4)
                break
            
            time.sleep(0.4)
    finally:
        if os.path.exists(screenshot_file):
            os.remove(screenshot_file)
