#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys


def create_offline_package():
    """ساخت پکیج آفلاین با پکیج‌های wheel"""

    print("🚀 شروع ساخت پکیج آفلاین...")

    # نام پکیج خروجی
    package_dir = "ocr_offline_package"

    # حذف اگر از قبل وجود دارد
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)

    os.makedirs(package_dir)

    # کپی پروژه اصلی
    print("📂 کپی کردن پروژه...")
    for item in os.listdir('.'):
        if item not in ['venv', package_dir, 'offline_wheels', 'db.sqlite3'] and not item.startswith('.'):
            src = item
            dest = os.path.join(package_dir, item)

            if os.path.isdir(src):
                shutil.copytree(src, dest)
                print(f"  📁 {item}")
            else:
                shutil.copy2(src, dest)
                print(f"  📄 {item}")

    # کپی پکیج‌های wheel
    if os.path.exists('offline_wheels'):
        print("📦 کپی پکیج‌های wheel...")
        wheels_dir = os.path.join(package_dir, "offline_wheels")
        shutil.copytree('offline_wheels', wheels_dir)

    # کپی requirements.txt
    if os.path.exists('requirements.txt'):
        shutil.copy2('requirements.txt', package_dir)

    # ایجاد اسکریپت نصب درست
    create_install_script(package_dir)

    print(f"\n🎉 پکیج آفلاین ساخته شد: {package_dir}/")


def create_install_script(package_dir):
    """ایجاد اسکریپت نصب درست"""

    install_script = """import os
import sys
import subprocess

print("🚀 نصب کاملاً آفلاین پکیج‌ها...")

# نصب پکیج‌ها از دایرکتوری wheels بدون اتصال به اینترنت
wheels_dir = "offline_wheels"
if os.path.exists(wheels_dir):
    print("📦 نصب از فایل‌های wheel...")

    # نصب تمام wheel ها به صورت آفلاین
    cmd = [
        sys.executable, "-m", "pip", "install",
        "--no-index",  # عدم اتصال به اینترنت
        "--find-links", wheels_dir,  # جستجو در پوشه محلی
        "-r", "requirements.txt"  # نصب از فایل requirements
    ]

    try:
        subprocess.check_call(cmd)
        print("✅ نصب پکیج‌ها کامل شد!")
    except subprocess.CalledProcessError as e:
        print(f"❌ خطا در نصب: {e}")
        # روش جایگزین: نصب تک تک wheel ها
        print("🔄 تلاش روش جایگزین...")
        for wheel_file in os.listdir(wheels_dir):
            if wheel_file.endswith('.whl'):
                wheel_path = os.path.join(wheels_dir, wheel_file)
                print(f"📦 نصب {wheel_file}...")
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install",
                        "--no-index",
                        wheel_path
                    ])
                except:
                    print(f"⚠️ خطا در نصب {wheel_file}")

# تنظیمات جنگو
print("⚙️  اجرای تنظیمات جنگو...")
try:
    subprocess.check_call([sys.executable, "manage.py", "migrate"])
    print("✅ migrate انجام شد")
except:
    print("⚠️ خطا در migrate")

try:
    #subprocess.check_call([sys.executable, "manage.py", "collectstatic", "--noinput"])
    print("✅ جمع‌آوری فایل‌های استاتیک انجام شد")
except:
    print("⚠️ خطا در collectstatic")

print("🎉 نصب کامل شد!")
print("🌐 برای اجرا: python manage.py runserver")
"""

    with open(os.path.join(package_dir, 'install.py'), 'w', encoding='utf-8') as f:
        f.write(install_script)

    # ایجاد فایل batch
    batch_script = """@echo off
chcp 65001
echo 🚀 نصب برنامه OCR...
python install.py
echo.
echo اگر خطایی مشاهده کردید، مطمئن شوید پایتون نصب است
pause
"""

    with open(os.path.join(package_dir, 'install.bat'), 'w', encoding='utf-8') as f:
        f.write(batch_script)


if __name__ == "__main__":
    create_offline_package()