"""
多模态处理：图片OCR + 语音ASR
"""
import os
import base64
from pathlib import Path


def extract_text_from_image(image_path: str) -> str:
    """从图片中提取文字（OCR）"""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="chi_sim+eng")
        return text.strip()
    except ImportError:
        return "[OCR模块未安装，请安装 pytesseract 和 Pillow]"
    except Exception as e:
        return f"[OCR识别失败: {str(e)}]"


def extract_text_from_audio(audio_path: str) -> str:
    """从音频中提取文字（ASR）"""
    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(audio_path, language="zh")
        return result["text"].strip()
    except ImportError:
        return "[ASR模块未安装，请安装 openai-whisper]"
    except Exception as e:
        return f"[语音识别失败: {str(e)}]"


def extract_text_from_file(file_path: str) -> str:
    """根据文件类型提取文字"""
    ext = Path(file_path).suffix.lower()

    if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"):
        return extract_text_from_image(file_path)
    elif ext in (".mp3", ".wav", ".m4a", ".ogg", ".flac"):
        return extract_text_from_audio(file_path)
    else:
        from .rag_engine import parse_document
        return parse_document(file_path)
