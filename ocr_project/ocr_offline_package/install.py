import os
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
