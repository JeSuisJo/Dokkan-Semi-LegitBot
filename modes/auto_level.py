import subprocess
import os
import sys
import time
import tempfile
from PIL import Image
import pytesseract

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stamina.act_object import use_items
from stamina.act_no_object import use_dragon_stones

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(SCRIPT_DIR, "platform-tools", "adb.exe")
EMULATOR_PORTS = ['127.0.0.1:7555', '127.0.0.1:5555', '127.0.0.1:62001', '127.0.0.1:21503']

COLOR_SEARCH_ZONE = (613, 982, 713, 1082)
OK_LEVEL_END_ZONE = (504, 993, 567, 1030)
OK_LEVEL_END_CLICK = (273, 1014)
OK_FRIEND_ADD_ZONE = (485, 658, 579, 712)
OK_FRIEND_ADD_CLICK = (268, 677)
OK_ENOUGH_ACT_ZONE = (488, 616, 574, 675)
RELANCER_NIVEAU_ZONE = (252, 352, 536, 533)

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

def find_color_in_zone(img, target_color, zone):
    x1, y1, x2, y2 = zone
    for x in range(x1, min(x2, img.width)):
        for y in range(y1, min(y2, img.height)):
            pixel = img.getpixel((x, y))
            if len(pixel) >= 3 and pixel[:3] == target_color:
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

def find_text_relancer_niveau(img, zone):
    x1, y1, x2, y2 = zone
    region = img.crop((x1, y1, x2, y2))
    
    try:
        region_gray = region.convert('L')
        region_resized = region_gray.resize((region_gray.width * 3, region_gray.height * 3), Image.LANCZOS)
        text = pytesseract.image_to_string(region_resized, lang='eng', config='--psm 6').strip()
        if "relancer ce niveau" in text.lower():
            return True
    except Exception:
        pass
    
    return False

def tap_on_device(adb_path, device, x, y):
    subprocess.run([adb_path, '-s', device, 'shell', 'input', 'tap', str(x), str(y)])

def run_auto_level(num_runs):
    try:
        if not os.path.exists(ADB_PATH):
            print(f"ADB not found: {ADB_PATH}")
            print("Please ensure 'platform-tools' folder with adb.exe is in the script directory")
            return
        
        connect_to_emulators(ADB_PATH)
        device = get_connected_device(ADB_PATH)
        if not device:
            print("No device connected. Please:")
            print("1. Start your Android emulator")
            print("2. Enable USB debugging if using a physical device")
            return
        
        print(f"Device connected: {device}\n")
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot_file = temp_file.name
        
        try:
            for run_number in range(1, num_runs + 1):
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"{'='*50}")
                print(f"Run {run_number}/{num_runs}")
                print(f"{'='*50}\n")
                
                target_color = (255, 0, 0)
                color_found = False
                
                while not color_found:
                    capture_screenshot(ADB_PATH, device, screenshot_file)
                    img = Image.open(screenshot_file)
                    position = find_color_in_zone(img, target_color, COLOR_SEARCH_ZONE)
                    if position:
                        x, y = position
                        tap_on_device(ADB_PATH, device, x, y)
                        print("Starting level")
                        color_found = True
                        time.sleep(0.4)
                    else:
                        time.sleep(0.4)
                
                ok_level_end_found = False
                
                while not ok_level_end_found:
                    capture_screenshot(ADB_PATH, device, screenshot_file)
                    img = Image.open(screenshot_file)
                    
                    ok_friend_pos = find_text_ok_in_zone(img, OK_FRIEND_ADD_ZONE)
                    if ok_friend_pos:
                        tap_on_device(ADB_PATH, device, OK_FRIEND_ADD_CLICK[0], OK_FRIEND_ADD_CLICK[1])
                        print("Friend request cancelled")
                        time.sleep(0.4)
                        continue
                    
                    tap_on_device(ADB_PATH, device, 399, 13)
                    
                    ok_level_pos = find_text_ok_in_zone(img, OK_LEVEL_END_ZONE)
                    if ok_level_pos:
                        if run_number < num_runs:
                            tap_on_device(ADB_PATH, device, OK_LEVEL_END_CLICK[0], OK_LEVEL_END_CLICK[1])
                            print("Restarting level")
                        else:
                            print("Level completed")
                        ok_level_end_found = True
                        time.sleep(0.4)
                    else:
                        time.sleep(0.5)
                
                ok_enough_act_found = False
                
                while not ok_enough_act_found:
                    capture_screenshot(ADB_PATH, device, screenshot_file)
                    img = Image.open(screenshot_file)
                    
                    ok_act_pos = find_text_ok_in_zone(img, OK_ENOUGH_ACT_ZONE)
                    if ok_act_pos:
                        if find_text_relancer_niveau(img, RELANCER_NIVEAU_ZONE):
                            tap_on_device(ADB_PATH, device, ok_act_pos[0], ok_act_pos[1])
                            print("Returning to team selection")
                            ok_enough_act_found = True
                            time.sleep(0.4)
                        else:
                            print("Out of stamina")
                            use_dragon_stones(ADB_PATH, device)
                            time.sleep(0.4)
                    else:
                        time.sleep(0.4)
                        capture_screenshot(ADB_PATH, device, screenshot_file)
                        img = Image.open(screenshot_file)
                        
                        stamina_recovery_color = (244, 176, 93)
                        stamina_recovery_point = (570, 427)
                        
                        if check_color_at_point(img, stamina_recovery_point, stamina_recovery_color):
                            use_items(ADB_PATH, device)
                            time.sleep(0.4)
                        else:
                            ok_enough_act_found = True
                
                print(f"\nRun {run_number}/{num_runs} completed!\n")
                
                if run_number < num_runs:
                    time.sleep(2)
            
            print(f"{'='*50}")
            print(f"All {num_runs} level(s) completed successfully!")
            print(f"{'='*50}")
        
        finally:
            try:
                os.unlink(screenshot_file)
            except:
                pass
    
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

def main():
    while True:
        try:
            num_runs = input("How many times do you want to repeat the level? (Enter a number): ")
            num_runs = int(num_runs)
            if num_runs > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
    
    print(f"\nStarting automation: {num_runs} level(s) to complete\n")
    run_auto_level(num_runs)
    input("\nPress Enter to close...")

if __name__ == "__main__":
    main()

