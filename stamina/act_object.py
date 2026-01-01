import subprocess
import os
import json
import tempfile
import time
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(SCRIPT_DIR, "platform-tools", "adb.exe")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")

COLOR_DETECTION_POINT = (570, 427)
COLOR_DETECTION_COLOR = (244, 176, 93)
FOOD_CLICK_POSITION = (572, 649)
DRAGON_STONE_CLICK_POSITION = (577, 427)
OK_AFTER_FOOD_ZONE = (497, 721, 567, 775)
OK_AFTER_DRAGON_STONE_ZONE = (494, 627, 572, 689)
RESTORE_ACT_COLOR_POINT = (619, 661)
RESTORE_ACT_COLOR = (238, 102, 23)
OK_RESTORE_CONFIRMATION_ZONE = (366, 586, 436, 640)
FINAL_CLICK_POSITION = (266, 1014)
POST_RESTORE_CLICK_2 = (537, 658)

def load_config():
    default_config = {
        "use_meat_first": False,
        "use_dragon_stones": False
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if "use_meat_first" in config and "use_dragon_stones" in config:
                    return config
        return default_config
    except Exception:
        return default_config

def capture_screenshot(adb_path, device, temp_file):
    subprocess.run([adb_path, '-s', device, 'shell', 'screencap', '-p', '/sdcard/t.png'], capture_output=True)
    subprocess.run([adb_path, '-s', device, 'pull', '/sdcard/t.png', temp_file], capture_output=True)
    subprocess.run([adb_path, '-s', device, 'shell', 'rm', '/sdcard/t.png'], capture_output=True)

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

def use_items(adb_path, device):
    config = load_config()
    food_first = config.get("use_meat_first", False)
    use_dragon_stones = config.get("use_dragon_stones", False)
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        screenshot_file = temp_file.name
    
    try:
        capture_screenshot(adb_path, device, screenshot_file)
        img = Image.open(screenshot_file)
        
        if check_color_at_point(img, COLOR_DETECTION_POINT, COLOR_DETECTION_COLOR):
            print("Refill act with food/ds")
            
            if food_first:
                print("Using food (meat)...")
                tap_on_device(adb_path, device, FOOD_CLICK_POSITION[0], FOOD_CLICK_POSITION[1])
                time.sleep(0.4)
                
                ok_found = False
                while not ok_found:
                    capture_screenshot(adb_path, device, screenshot_file)
                    img = Image.open(screenshot_file)
                    ok_pos = find_text_ok_in_zone(img, OK_AFTER_FOOD_ZONE)
                    if ok_pos:
                        tap_on_device(adb_path, device, ok_pos[0], ok_pos[1])
                        ok_found = True
                        time.sleep(0.4)
                    else:
                        time.sleep(0.5)
                
                restore_act_color_found = False
                while not restore_act_color_found:
                    capture_screenshot(adb_path, device, screenshot_file)
                    img = Image.open(screenshot_file)
                    if check_color_at_point(img, RESTORE_ACT_COLOR_POINT, RESTORE_ACT_COLOR):
                        time.sleep(0.4)
                        tap_on_device(adb_path, device, RESTORE_ACT_COLOR_POINT[0], RESTORE_ACT_COLOR_POINT[1])
                        restore_act_color_found = True
                        time.sleep(0.4)
                    else:
                        time.sleep(0.5)
                
                ok_confirmation_found = False
                while not ok_confirmation_found:
                    capture_screenshot(adb_path, device, screenshot_file)
                    img = Image.open(screenshot_file)
                    ok_confirmation_pos = find_text_ok_in_zone(img, OK_RESTORE_CONFIRMATION_ZONE)
                    if ok_confirmation_pos:
                        tap_on_device(adb_path, device, ok_confirmation_pos[0], ok_confirmation_pos[1])
                        ok_confirmation_found = True
                        time.sleep(0.4)
                        tap_on_device(adb_path, device, FINAL_CLICK_POSITION[0], FINAL_CLICK_POSITION[1])
                        time.sleep(0.4)
                    else:
                        time.sleep(0.5)
                
                time.sleep(0.4)
                tap_on_device(adb_path, device, POST_RESTORE_CLICK_2[0], POST_RESTORE_CLICK_2[1])
            
            elif not food_first and use_dragon_stones:
                print("Using dragon stones...")
                tap_on_device(adb_path, device, DRAGON_STONE_CLICK_POSITION[0], DRAGON_STONE_CLICK_POSITION[1])
                time.sleep(0.4)
                
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
                    ok_confirmation_pos = find_text_ok_in_zone(img, OK_RESTORE_CONFIRMATION_ZONE)
                    if ok_confirmation_pos:
                        tap_on_device(adb_path, device, ok_confirmation_pos[0], ok_confirmation_pos[1])
                        ok_confirmation_found = True
                        time.sleep(0.4)
                        tap_on_device(adb_path, device, FINAL_CLICK_POSITION[0], FINAL_CLICK_POSITION[1])
                        time.sleep(0.4)
                    else:
                        time.sleep(0.5)
                
                time.sleep(0.4)
                tap_on_device(adb_path, device, POST_RESTORE_CLICK_2[0], POST_RESTORE_CLICK_2[1])
            
            else:
                print("Both food and dragon stones are disabled. Stopping script.")
        else:
            print("Stamina recovery condition not met.")
    
    finally:
        try:
            os.unlink(screenshot_file)
        except:
            pass

