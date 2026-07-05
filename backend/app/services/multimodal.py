"""
多模态处理：图片OCR (PaddleOCR) + 语音ASR (云端API)
"""
import os
from pathlib import Path


def extract_text_from_image(image_path: str) -> str:
    """从图片中提取文字（PaddleOCR）"""
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
        result = ocr.ocr(image_path, cls=True)

        text_lines = []
        if result and result[0]:
            for line in result[0]:
                if line[1]:
                    text_lines.append(line[1][0])
        return "\n".join(text_lines)
    except ImportError:
        return "[OCR模块未安装，请运行: pip install paddleocr]"
    except Exception as e:
        return f"[OCR识别失败: {str(e)}]"


def extract_text_from_audio(audio_path: str) -> str:
    """从音频中提取文字（云端ASR API）"""
    return "[语音识别功能需要配置 ASR API 服务（如讯飞、百度等）]"


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
