"""
Dokkan Bot - Main Entry Point
Automated farming bot for Dragon Ball Z: Dokkan Battle
"""

import os
import sys
import subprocess

def check_and_install_dependencies():
    """
    Check for required Python packages and install them if missing.
    Returns True if all dependencies are available, False otherwise.
    """
    required_packages = {
        'PIL': 'Pillow',
        'pytesseract': 'pytesseract',
        'cv2': 'opencv-python',
        'numpy': 'numpy'
    }
    
    missing_packages = []
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("=" * 50)
        print("Installing missing dependencies...")
        print("=" * 50)
        
        for package in missing_packages:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
                print(f"✓ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"✗ Failed to install {package}")
                print("Please install it manually with: pip install", package)
                return False
        
        print("=" * 50)
        print("All dependencies installed!")
        print("=" * 50)
        print()
    
    return True

if __name__ == "__main__":
    if not check_and_install_dependencies():
        print("\nError: Failed to install required dependencies.")
        input("Press Enter to exit...")
        sys.exit(1)

from modes.auto_level import run_auto_level
from modes.ztur_finish import run_ztur_finish
from modes.ztur_retry import run_ztur_retry

def display_main_menu():
    """
    Display the main menu with available bot modes.
    """
    print("=" * 50)
    print("Dokkan Bot - Main Menu")
    print("=" * 50)
    print("1. Auto Level")
    print("2. ZTUR Finish")
    print("3. ZTUR Retry")
    print("0. Exit")
    print("=" * 50)

def get_user_choice():
    """
    Prompt user for menu choice and validate input.
    Returns the selected menu option (0-3).
    """
    while True:
        try:
            choice = input("\nSelect a mode (0-3): ").strip()
            if choice in ['0', '1', '2', '3']:
                return int(choice)
            else:
                print("Invalid choice. Please enter 0, 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            sys.exit(0)

def get_number_of_runs():
    """
    Prompt user for number of repetitions and validate input.
    Returns the number of runs, or None if cancelled.
    """
    while True:
        try:
            num_runs = input("How many times to repeat? (Enter a number): ").strip()
            num_runs = int(num_runs)
            if num_runs > 0:
                return num_runs
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            return None

def main():
    """
    Main application loop - displays menu and handles user mode selection.
    """
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        display_main_menu()
        user_choice = get_user_choice()
        
        if user_choice == 0:
            print("\nExiting...")
            break
        elif user_choice == 1:
            num_runs = get_number_of_runs()
            if num_runs:
                print(f"\nStarting Auto Level mode: {num_runs} run(s)\n")
                run_auto_level(num_runs)
                input("\nPress Enter to return to main menu...")
        elif user_choice == 2:
            print(f"\nStarting ZTUR Finish mode\n")
            run_ztur_finish(0)
            input("\nPress Enter to return to main menu...")
        elif user_choice == 3:
            print(f"\nStarting ZTUR Retry mode\n")
            run_ztur_retry(0)
            input("\nPress Enter to return to main menu...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
