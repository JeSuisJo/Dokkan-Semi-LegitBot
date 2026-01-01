import subprocess
import os
import sys
import time
import tempfile
from PIL import Image
import cv2
import numpy as np
import pytesseract

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stamina.ztur_act_no_object import use_dragon_stones, DragonStonesDisabledException
from stamina.ztur_act_object import use_items, NoStaminaException

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(SCRIPT_DIR, "platform-tools", "adb.exe")
EMULATOR_PORTS = ['127.0.0.1:7555', '127.0.0.1:5555', '127.0.0.1:62001', '127.0.0.1:21503']

ZTUR_ZONE = (86, 639, 260, 721)
ZTUR_TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "img", "ztur.png")

ZTUR_CLICK_POSITION = (399, 770)
START_COLOR_POINT = (665, 1030)
START_COLOR = (255, 0, 0)
OK_LEVEL_COMPLETE_ZONE = (360, 986, 443, 1045)
BACK_CLICK_POSITION = (413, 18)
OK_FRIEND_REQUEST_ZONE = (490, 657, 577, 714)
CANCEL_FRIEND_REQUEST_CLICK = (273, 686)
OK_TOO_MANY_FRIENDS_ZONE = (357, 656, 437, 715)

OK_CONFIRMATION_ZONE = (493, 937, 580, 995)
MEDAL_COLOR_POINT = (447, 949)
MEDAL_COLOR = (155, 159, 159)
STAMINA_RECOVERY_COLOR_POINT = (570, 427)
STAMINA_RECOVERY_COLOR = (244, 176, 93)
OK_STAMINA_ZONE = (499, 629, 575, 686)
FOOD_COLOR_POINT = (563, 670)
FOOD_COLOR = (238, 141, 22)

def connect_to_emulators(adb_path):
    for port in EMULATOR_PORTS:
        try:
            subprocess.run([adb_path, 'connect', port], capture_output=True, timeout=1)
        except:
            pass

def get_connected_device(adb_path):
    result = subprocess.run([adb_path, 'devices'], capture_output=True, text=True)
    for line in result.stdout.split('\n')[1:]:
        if '\tdevice' in line:
            return line.split('\t')[0]
    return None

def capture_screenshot(adb_path, device, temp_file):
    subprocess.run([adb_path, '-s', device, 'shell', 'screencap', '-p', '/sdcard/t.png'], capture_output=True)
    subprocess.run([adb_path, '-s', device, 'pull', '/sdcard/t.png', temp_file], capture_output=True)
    subprocess.run([adb_path, '-s', device, 'shell', 'rm', '/sdcard/t.png'], capture_output=True)

def tap_on_device(adb_path, device, x, y):
    subprocess.run([adb_path, '-s', device, 'shell', 'input', 'tap', str(x), str(y)])

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

def find_image_in_zone(img, template_path, zone, threshold=0.8):
    x1, y1, x2, y2 = zone
    region = img.crop((x1, y1, x2, y2))
    
    template = cv2.imread(template_path)
    if template is None:
        return None
    
    region_cv = cv2.cvtColor(np.array(region), cv2.COLOR_RGB2BGR)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    region_gray = cv2.cvtColor(region_cv, cv2.COLOR_BGR2GRAY)
    
    result = cv2.matchTemplate(region_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        match_x = max_loc[0] + template_gray.shape[1] // 2
        match_y = max_loc[1] + template_gray.shape[0] // 2
        absolute_x = x1 + match_x
        absolute_y = y1 + match_y
        return (absolute_x, absolute_y)
    
    return None

def get_num_characters():
    while True:
        try:
            num = input("How many characters have sub ZTUR? (Enter a number): ").strip()
            num = int(num)
            if num > 0:
                return num
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            return None

def run_ztur_function(device, screenshot_file):
    capture_screenshot(ADB_PATH, device, screenshot_file)
    img = Image.open(screenshot_file)
    
    ztur_pos = find_image_in_zone(img, ZTUR_TEMPLATE_PATH, ZTUR_ZONE)
    if ztur_pos:
        print(f"Lancement du niveau ZTUR")
        tap_on_device(ADB_PATH, device, ZTUR_CLICK_POSITION[0], ZTUR_CLICK_POSITION[1])
        time.sleep(0.4)
        
        while True:
            capture_screenshot(ADB_PATH, device, screenshot_file)
            img = Image.open(screenshot_file)
            
            if check_color_at_point(img, START_COLOR_POINT, START_COLOR):
                print(f"Lancement du niveau")
                tap_on_device(ADB_PATH, device, START_COLOR_POINT[0], START_COLOR_POINT[1])
                time.sleep(0.4)
                break
            
            if check_color_at_point(img, FOOD_COLOR_POINT, FOOD_COLOR):
                print(f"Plus d'act")
                use_items(ADB_PATH, device)
                time.sleep(0.4)
                continue
            
            ok_stamina = find_text_ok_in_zone(img, OK_STAMINA_ZONE)
            if ok_stamina:
                print(f"Plus d'act")
                use_dragon_stones(ADB_PATH, device)
                time.sleep(0.4)
                continue
            
            ztur_pos_alt = find_image_in_zone(img, ZTUR_TEMPLATE_PATH, ZTUR_ZONE)
            if ztur_pos_alt:
                tap_on_device(ADB_PATH, device, ZTUR_CLICK_POSITION[0], ZTUR_CLICK_POSITION[1])
                time.sleep(0.4)
                continue
            
            time.sleep(0.4)
    
    while True:
        capture_screenshot(ADB_PATH, device, screenshot_file)
        img = Image.open(screenshot_file)
        
        ok_pos = find_text_ok_in_zone(img, OK_LEVEL_COMPLETE_ZONE)
        if ok_pos:
            print(f"Level complete")
            tap_on_device(ADB_PATH, device, ok_pos[0], ok_pos[1])
            time.sleep(0.4)
            break
        
        ztur_death_check = find_image_in_zone(img, ZTUR_TEMPLATE_PATH, ZTUR_ZONE)
        if ztur_death_check:
            print(f"ZTUR image detected, checking for death...")
            time.sleep(2.0)
            capture_screenshot(ADB_PATH, device, screenshot_file)
            img = Image.open(screenshot_file)
            ztur_death_check_2 = find_image_in_zone(img, ZTUR_TEMPLATE_PATH, ZTUR_ZONE)
            if ztur_death_check_2:
                print(f"Death confirmed, restarting ZTUR")
                return True
        
        tap_on_device(ADB_PATH, device, BACK_CLICK_POSITION[0], BACK_CLICK_POSITION[1])
        time.sleep(0.4)
    
    while True:
        capture_screenshot(ADB_PATH, device, screenshot_file)
        img = Image.open(screenshot_file)
        
        ztur_pos_check = find_image_in_zone(img, ZTUR_TEMPLATE_PATH, ZTUR_ZONE)
        if ztur_pos_check:
            break
        
        tap_on_device(ADB_PATH, device, BACK_CLICK_POSITION[0], BACK_CLICK_POSITION[1])
        time.sleep(0.4)
        
        capture_screenshot(ADB_PATH, device, screenshot_file)
        img = Image.open(screenshot_file)
        
        ok_friend_request = find_text_ok_in_zone(img, OK_FRIEND_REQUEST_ZONE)
        if ok_friend_request:
            print(f"Cancelling friend request")
            tap_on_device(ADB_PATH, device, CANCEL_FRIEND_REQUEST_CLICK[0], CANCEL_FRIEND_REQUEST_CLICK[1])
            time.sleep(0.4)
            continue
        
        ok_too_many = find_text_ok_in_zone(img, OK_TOO_MANY_FRIENDS_ZONE)
        if ok_too_many:
            print(f"Too many friends")
            tap_on_device(ADB_PATH, device, ok_too_many[0], ok_too_many[1])
            time.sleep(0.4)
            continue
    
    return False

def run_medal_loop(device, screenshot_file, num_characters, medal_name, wait_before_click, medal_click_position, color_click_if_found, color_click_if_not_found, loop_multiplier):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{'='*50}")
    print(f"{medal_name} Medal Selection")
    print(f"{'='*50}\n")
    
    while True:
        capture_screenshot(ADB_PATH, device, screenshot_file)
        img = Image.open(screenshot_file)
        
        ztur_pos = find_image_in_zone(img, ZTUR_TEMPLATE_PATH, ZTUR_ZONE)
        if ztur_pos:
            print(f"Lancement du niveau ZTUR")
            if wait_before_click > 0:
                time.sleep(wait_before_click)
            tap_on_device(ADB_PATH, device, medal_click_position[0], medal_click_position[1])
            time.sleep(0.4)
            
            while True:
                capture_screenshot(ADB_PATH, device, screenshot_file)
                img = Image.open(screenshot_file)
                
                if check_color_at_point(img, MEDAL_COLOR_POINT, MEDAL_COLOR):
                    print(f"Medal color found")
                    tap_on_device(ADB_PATH, device, color_click_if_found[0], color_click_if_found[1])
                    time.sleep(0.4)
                else:
                    tap_on_device(ADB_PATH, device, color_click_if_not_found[0], color_click_if_not_found[1])
                    time.sleep(0.4)
                
                while True:
                    capture_screenshot(ADB_PATH, device, screenshot_file)
                    img = Image.open(screenshot_file)
                    
                    ok_pos = find_text_ok_in_zone(img, OK_CONFIRMATION_ZONE)
                    if ok_pos:
                        print(f"Confirmation OK found")
                        tap_on_device(ADB_PATH, device, ok_pos[0], ok_pos[1])
                        time.sleep(1.0)
                        
                        num_iterations = loop_multiplier * num_characters
                        i = 0
                        while i < num_iterations:
                            os.system('cls' if os.name == 'nt' else 'clear')
                            print(f"{'='*50}")
                            print(f"{medal_name} Medal Run {i+1}/{num_iterations}")
                            print(f"{'='*50}\n")
                            
                            death_detected = run_ztur_function(device, screenshot_file)
                            if not death_detected:
                                i += 1
                            time.sleep(0.4)
                        
                        return
                    
                    time.sleep(0.4)
            
            break
        
        time.sleep(0.4)

def run_bronze_medal(device, screenshot_file, num_characters):
    run_medal_loop(
        device, screenshot_file, num_characters,
        "Bronze",
        0,
        (588, 848),
        (399, 798),
        (588, 848),
        6
    )

def run_silver_medal(device, screenshot_file, num_characters):
    run_medal_loop(
        device, screenshot_file, num_characters,
        "Silver",
        5.0,
        (588, 848),
        (390, 593),
        (588, 848),
        5
    )

def run_gold_medal(device, screenshot_file, num_characters):
    run_medal_loop(
        device, screenshot_file, num_characters,
        "Gold",
        5.0,
        (588, 848),
        (390, 485),
        (588, 848),
        3
    )

def run_rainbow_medal(device, screenshot_file, num_characters):
    run_medal_loop(
        device, screenshot_file, num_characters,
        "Rainbow",
        5.0,
        (588, 848),
        (397, 380),
        (588, 848),
        3
    )

def run_ztur_retry(num_runs):
    num_characters = get_num_characters()
    if not num_characters:
        return
    
    print(f"\nZTUR Retry mode - All Medals - {num_characters} character(s)")
    
    connect_to_emulators(ADB_PATH)
    device = get_connected_device(ADB_PATH)
    if not device:
        print("No device connected")
        return
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        screenshot_file = temp_file.name
    
    try:
        run_bronze_medal(device, screenshot_file, num_characters)
        run_silver_medal(device, screenshot_file, num_characters)
        run_gold_medal(device, screenshot_file, num_characters)
        run_rainbow_medal(device, screenshot_file, num_characters)
    except (DragonStonesDisabledException, NoStaminaException):
        print("Stopping ZTUR Retry mode")
        return
    finally:
        if os.path.exists(screenshot_file):
            os.remove(screenshot_file)
