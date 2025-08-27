import os
import sys


def resource_path(relative_path):
    """获取资源的绝对路径（修正路径格式）"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    # 标准化路径：去除相对路径符号，统一分隔符
    normalized_path = os.path.normpath(os.path.join(base_path, relative_path))
    # 显式转换为Windows路径格式（可选）
    return normalized_path.replace('/', '\\')


def get_ffmpeg_path():
    """获取FFmpeg路径（修正相对路径）"""
    # 修改为不带./的相对路径
    return resource_path('resources/ffmpeg.exe')


def get_ffprobe_path():
    """获取FFprobe路径（修正相对路径）"""
    return resource_path('resources/ffprobe.exe')