import subprocess
import os
import json
import tempfile
import time
from PIL import Image
import pytesseract

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(SCRIPT_DIR, "platform-tools", "adb.exe")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

COLOR_DETECTION_ZONE = (250, 182, 481, 654)
COLOR_DETECTION_COLOR = (242, 183, 114)
FIRST_CLICK_POSITION = (481, 654)
SECOND_CHECK_POINT = (338, 614)
SECOND_CLICK_POSITION = (338, 614)
OK_AFTER_DRAGON_STONE_ZONE = (500, 627, 579, 688)
OK_CONFIRMATION_ZONE = (362, 586, 439, 644)
FINAL_CLICK_POSITION = (282, 1014)

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

def find_color_in_zone(img, target_color, zone, tolerance=10):
    x1, y1, x2, y2 = zone
    target_r, target_g, target_b = target_color
    
    for x in range(x1, min(x2, img.width)):
        for y in range(y1, min(y2, img.height)):
            pixel = img.getpixel((x, y))
            if len(pixel) >= 3:
                r, g, b = pixel[:3]
                if (abs(r - target_r) <= tolerance and 
                    abs(g - target_g) <= tolerance and 
                    abs(b - target_b) <= tolerance):
                    return (x, y)
    return None

def check_color_at_point(img, point, target_color, tolerance=10):
    x, y = point
    if x >= img.width or y >= img.height:
        return False
    pixel = img.getpixel((x, y))
    if len(pixel) >= 3:
        r, g, b = pixel[:3]
        target_r, target_g, target_b = target_color
        return (abs(r - target_r) <= tolerance and 
                abs(g - target_g) <= tolerance and 
                abs(b - target_b) <= tolerance)
    return False

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

def use_premium_currency(adb_path, device):
    config = load_config()
    use_dragon_stones = config.get("use_dragon_stones", False)
    
    if not use_dragon_stones:
        print("Dragon stones are disabled in config.json (use_dragon_stones: false).")
        print("Stopping script.")
        return
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        screenshot_file = temp_file.name
    
    try:
        if use_dragon_stones:
            print("Restoring stamina with Dragon Stones")
            ok_found = False
            while not ok_found:
                capture_screenshot(adb_path, device, screenshot_file)
                img = Image.open(screenshot_file)
                ok_pos = find_text_ok_in_zone(img, OK_AFTER_DRAGON_STONE_ZONE)
                if ok_pos:
                    tap_on_device(adb_path, device, ok_pos[0], ok_pos[1])
                    ok_found = True
                    time.sleep(0.4)
                else:
                    time.sleep(0.5)
            
            ok_confirmation_found = False
            while not ok_confirmation_found:
                capture_screenshot(adb_path, device, screenshot_file)
                img = Image.open(screenshot_file)
                ok_confirmation_pos = find_text_ok_in_zone(img, OK_CONFIRMATION_ZONE)
                if ok_confirmation_pos:
                    tap_on_device(adb_path, device, ok_confirmation_pos[0], ok_confirmation_pos[1])
                    ok_confirmation_found = True
                    time.sleep(0.4)
                else:
                    time.sleep(0.5)
                    
            time.sleep(0.4)
            tap_on_device(adb_path, device, FINAL_CLICK_POSITION[0], FINAL_CLICK_POSITION[1])
    
    finally:
        try:
            os.unlink(screenshot_file)
        except:
            pass

use_dragon_stones = use_premium_currency

