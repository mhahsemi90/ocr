#!/usr/bin/env python3
import os
import shutil

def copy_existing_easyocr_models():
    """Copy existing downloaded EasyOCR models"""
    print("Searching for existing Persian OCR models...")

    models_dir = "easyocr_models"
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    # Possible paths for EasyOCR models
    possible_paths = [
        # Alternative path
        os.path.join(os.path.expanduser('~'), '.EasyOCR', 'model')
    ]

    # Add path from environment variable
    torch_home = os.environ.get('TORCH_HOME')
    if torch_home:
        possible_paths.append(os.path.join(torch_home, 'hub', 'EasyOCR'))

    found_models = False

    for model_path in possible_paths:
        if os.path.exists(model_path):
            print(f"Found models in: {model_path}")

            # Copy all .pth files
            for root, dirs, files in os.walk(model_path):
                for file in files:
                    if file.endswith('.pth'):
                        src = os.path.join(root, file)
                        relative_path = os.path.relpath(src, model_path)
                        dest = os.path.join(models_dir, relative_path)

                        # Create destination directory if it doesn't exist
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        print(src, relative_path, dest)
                        shutil.copy2(src, dest)
                        print(f"  Copied model: {file}")
                        found_models = True

            if found_models:
                print(f"Persian models saved in {models_dir} folder")


def download_easyocr_models():
    """Download EasyOCR models for Persian language"""
    try:
        import easyocr
        print("Downloading EasyOCR models for Persian...")

        # Create reader to download Persian models
        easyocr.Reader(['fa', 'en'], gpu=False, download_enabled=True)
        print("EasyOCR models for Persian downloaded successfully")

        # Now models are downloaded, try to copy again
        copy_existing_easyocr_models()

    except Exception as e:
        print(f"Error downloading models: {e}")

def create_offline_package():
    """Create offline package with wheel packages"""

    print("Starting offline package creation...")

    # Copy Persian OCR models
    #download_easyocr_models()

    # Output package name
    package_dir = "ocr_offline_package"

    # Remove if exists
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)

    os.makedirs(package_dir)

    # Copy main project
    print("Copying project...")
    for item in os.listdir('.'):
        if item not in ['venv', package_dir, 'offline_wheels', 'db.sqlite3'] and not item.startswith('.'):
            src = item
            dest = os.path.join(package_dir, item)

            if os.path.isdir(src):
                # Use dirs_exist_ok=True to prevent errors
                shutil.copytree(src, dest, dirs_exist_ok=True)
                print(f"  Directory: {item}")
            else:
                shutil.copy2(src, dest)
                print(f"  File: {item}")

    # Copy wheel packages
    if os.path.exists('offline_wheels'):
        print("Copying wheel packages...")
        wheels_dir = os.path.join(package_dir, "offline_wheels")
        shutil.copytree('offline_wheels', wheels_dir, dirs_exist_ok=True)

    # Copy EasyOCR models
    if os.path.exists('easyocr_models'):
        print("Copying Persian OCR models...")
        models_dir = os.path.join(package_dir, "easyocr_models")
        shutil.copytree('easyocr_models', models_dir, dirs_exist_ok=True)

        # Show models folder content
        print("Models folder content:")
        for root, dirs, files in os.walk(models_dir):
            for file in files:
                if file.endswith('.pth'):
                    print(f"  Model: {file}")
    else:
        print("Warning: easyocr_models folder does not exist")

    # Copy requirements.txt
    if os.path.exists('requirements.txt'):
        shutil.copy2('requirements.txt', package_dir)

    # Create proper installation script
    create_install_script(package_dir)

    print(f"\nOffline package created: {package_dir}/")
    print("Includes Persian OCR models for offline use")


def create_install_script(package_dir):
    """Create proper installation script"""

    install_script = """import os
import sys
import subprocess

print("Installing packages in completely offline mode...")

# Install packages from wheels directory without internet connection
wheels_dir = "offline_wheels"
if os.path.exists(wheels_dir):
    print("Installing from wheel files...")

    # Install all wheels offline
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--no-index",  # No internet connection
        "--find-links", wheels_dir,  # Search in local folder
        "-r", "requirements.txt"  # Install from requirements file
    ]

    try:
        subprocess.check_call(cmd)
        print("Package installation completed!")
    except subprocess.CalledProcessError as e:
        print(f"Installation error: {e}")
        # Alternative method: install wheels one by one
        print("Trying alternative method...")
        for wheel_file in os.listdir(wheels_dir):
            if wheel_file.endswith('.whl'):
                wheel_path = os.path.join(wheels_dir, wheel_file)
                print(f"Installing {wheel_file}...")
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install",
                        "--no-index",
                        wheel_path
                    ])
                except:
                    print(f"Warning: Error installing {wheel_file}")

# Django setup
print("Running Django setup...")
try:
    subprocess.check_call([sys.executable, "manage.py", "makemigrations"])
    print("makemigrations completed")
    subprocess.check_call([sys.executable, "manage.py", "migrate"])
    print("migrate completed")
    subprocess.check_call([sys.executable, "manage.py", "create_default_user"])
    print("create default user completed")
except:
    print("Warning: Error in migrate")

print("Installation completed!")
print("To run: python manage.py runserver")
print("Persian OCR system is ready to use")
"""

    with open(os.path.join(package_dir, 'install.py'), 'w', encoding='utf-8') as f:
        f.write(install_script)

    # Create batch file
    batch_script = """@echo off
chcp 65001
echo Installing OCR application...
python install.py
echo.
echo If you see any errors, make sure Python is installed
pause
"""

    with open(os.path.join(package_dir, 'install.bat'), 'w', encoding='utf-8') as f:
        f.write(batch_script)

    # Create run app file
    batch_script = """@echo off
chcp 65001
echo run application...
python manage.py runserver
"""

    with open(os.path.join(package_dir, 'run_app.bat'), 'w', encoding='utf-8') as f:
        f.write(batch_script)

    # Create run worker file
    batch_script = """@echo off
chcp 65001
echo run worker...
python manage.py ocr_worker
"""

    with open(os.path.join(package_dir, 'run_worker.bat'), 'w', encoding='utf-8') as f:
        f.write(batch_script)


if __name__ == "__main__":
    create_offline_package()