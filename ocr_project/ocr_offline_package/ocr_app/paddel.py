from paddleocr import PaddleOCR
import cv2
import numpy as np
from PIL import Image

# راه‌اندازی با مدل فارسی
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='fa'
)


def paddle_ocr_offline(image_path):
    try:
        result = ocr.ocr(image_path)
        text = ''

        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    text += line[1][0] + '\n'

        return text.strip() if text.strip() else "متنی یافت نشد"

    except Exception as e:
        return f"خطا: {str(e)}"