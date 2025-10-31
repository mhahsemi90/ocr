import easyocr
import cv2
import numpy as np
import os
import fitz
from PIL import Image
import io
import magic
import tempfile
import shutil


def detect_file_type(file_path):
    """تشخیص نوع فایل"""
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(file_path)

        if file_type == 'application/pdf':
            return 'pdf'
        elif file_type.startswith('image/'):
            return 'image'
        elif file_type == 'text/plain':
            return 'text'
        else:
            return 'unknown'
    except:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']:
            return 'image'
        elif ext in ['.txt', '.text']:
            return 'text'
        else:
            return 'unknown'


def safe_image_read(image_path):
    """خواندن ایمن تصویر با مدیریت مسیرهای فارسی"""
    try:
        # روش ۱: خواندن مستقیم
        img = cv2.imread(image_path)
        if img is not None:
            return img

        # روش ۲: استفاده از PIL و تبدیل به OpenCV
        try:
            with Image.open(image_path) as pil_img:
                img_array = np.array(pil_img)
                if len(img_array.shape) == 3:
                    return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                else:
                    return cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
        except:
            pass

        # روش ۳: کپی به مسیر موقت
        temp_dir = tempfile.gettempdir()
        temp_filename = f"temp_{os.getpid()}.jpg"
        temp_path = os.path.join(temp_dir, temp_filename)

        shutil.copy2(image_path, temp_path)
        img = cv2.imread(temp_path)

        try:
            os.remove(temp_path)
        except:
            pass

        return img

    except Exception as e:
        print(f"خطا در خواندن تصویر: {e}")
        return None


def extract_text_from_pdf(pdf_path):
    """استخراج متن از PDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()

            if page_text.strip():
                text += f"\n--- صفحه {page_num + 1} ---\n{page_text}"
            else:
                # اگر متن مستقیم وجود نداشت، از OCR استفاده کن
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

                # ذخیره موقت و پردازش با OCR
                temp_path = f"temp_page_{page_num}.png"
                cv2.imwrite(temp_path, img_cv)

                # استفاده از OCR ساده
                reader = easyocr.Reader(['fa', 'en'], gpu=False)
                results = reader.readtext(temp_path, detail=1)
                texts = []
                for (bbox, text_ocr, confidence) in results:
                    if confidence > 0.2 and len(text_ocr.strip()) > 0:
                        texts.append(text_ocr)

                ocr_result = ' '.join(texts) if texts else "متنی یافت نشد"
                text += f"\n--- صفحه {page_num + 1} (OCR) ---\n{ocr_result}"

                # حذف فایل موقت
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        doc.close()
        return text.strip()

    except Exception as e:
        return f"خطا در پردازش PDF: {str(e)}"


def extract_text_from_text_file(file_path):
    """استخراج متن از فایل متنی"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='windows-1256') as f:
                return f.read()
        except:
            return "خطا در خواندن فایل متنی"


def detect_text_type(image_path):
    """تشخیص نوع متن (تایپی یا دستنویس)"""
    try:
        img = safe_image_read(image_path)
        if img is None:
            return "unknown"

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        print(f"واریانس لاپلاسین: {laplacian_var}")

        if laplacian_var < 100:
            return "handwritten"
        else:
            return "printed"
    except Exception as e:
        print(f"خطا در تشخیص نوع متن: {e}")
        return "unknown"


def simple_preprocess(image_path):
    """پیش‌پردازش ساده و مؤثر"""
    try:
        img = safe_image_read(image_path)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # افزایش کنتراست ساده
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # نویزگیری ملایم
        denoised = cv2.medianBlur(enhanced, 3)

        return denoised

    except Exception as e:
        print(f"خطا در پیش‌پردازش: {e}")
        return None


class UniversalOCR:
    def __init__(self):
        try:
            self.reader = easyocr.Reader(['fa', 'en'], gpu=False)
            self.ocr_available = True
            print("✅ EasyOCR با موفقیت راه‌اندازی شد")
        except Exception as e:
            print(f"❌ خطا در راه‌اندازی EasyOCR: {e}")
            self.ocr_available = False

    def extract_text(self, file_path, text_type="auto"):
        """استخراج متن از انواع فایل‌ها"""
        try:
            file_type = detect_file_type(file_path)
            print(f"تشخیص نوع فایل: {file_type}")

            if file_type == 'pdf':
                text = extract_text_from_pdf(file_path)
                return {
                    'text': text if text.strip() else "📝 متنی در PDF یافت نشد",
                    'type': 'pdf',
                    'confidence': 1.0,
                    'file_type': 'pdf'
                }

            elif file_type == 'text':
                text = extract_text_from_text_file(file_path)
                return {
                    'text': text if text.strip() else "📝 فایل متنی خالی است",
                    'type': 'text',
                    'confidence': 1.0,
                    'file_type': 'text'
                }

            elif file_type == 'image':
                if not self.ocr_available:
                    return {
                        'text': "❌ موتور OCR در دسترس نیست",
                        'type': 'error',
                        'confidence': 0.0,
                        'file_type': 'image'
                    }

                # تشخیص نوع متن
                if text_type == "auto":
                    final_text_type = detect_text_type(file_path)
                else:
                    final_text_type = text_type

                print(f"نوع متن: {final_text_type}")

                # تنظیمات براساس نوع متن
                if final_text_type == "handwritten":
                    # برای دستنویس: آستانه پایین‌تر، حساسیت بیشتر
                    text_threshold = 0.2
                    low_text = 0.1
                else:
                    # برای تایپی: آستانه بالاتر، دقت بیشتر
                    text_threshold = 0.4
                    low_text = 0.3

                # پیش‌پردازش ساده
                processed_img = simple_preprocess(file_path)

                if processed_img is not None:
                    # ذخیره موقت تصویر پردازش شده
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, f"processed_{os.getpid()}.png")
                    cv2.imwrite(temp_path, processed_img)

                    # پردازش با تصویر پیش‌پردازش شده
                    results = self.reader.readtext(
                        temp_path,
                        detail=1,
                        text_threshold=text_threshold,
                        low_text=low_text
                    )

                    # حذف فایل موقت
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                else:
                    # پردازش با تصویر اصلی
                    results = self.reader.readtext(
                        file_path,
                        detail=1,
                        text_threshold=text_threshold,
                        low_text=low_text
                    )

                # فیلتر کردن نتایج
                texts = []
                confidences = []
                for (bbox, text, confidence) in results:
                    if confidence > text_threshold and len(text.strip()) > 0:
                        texts.append(text)
                        confidences.append(confidence)

                final_text = ' '.join(texts)
                avg_confidence = float(np.mean(confidences)) if confidences else 0.0

                return {
                    'text': final_text.strip() if final_text.strip() else "📝 متنی در تصویر یافت نشد",
                    'type': final_text_type,
                    'confidence': avg_confidence,
                    'file_type': 'image'
                }

            else:
                return {
                    'text': "❌ فرمت فایل پشتیبانی نمی‌شود",
                    'type': 'error',
                    'confidence': 0.0,
                    'file_type': 'unknown'
                }

        except Exception as e:
            print(f"خطای کلی: {e}")
            return {
                'text': f"❌ خطا: {str(e)}",
                'type': 'error',
                'confidence': 0.0,
                'file_type': 'error'
            }

    def extract_text_simple(self, file_path):
        """ورژن ساده‌تر - فقط متن خروجی بده"""
        result = self.extract_text(file_path)
        return result['text'] if isinstance(result, dict) else result