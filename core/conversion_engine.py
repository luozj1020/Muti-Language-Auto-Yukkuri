import time
import os
import threading
import re

from core.browser_manager import BrowserManager
from core.audio_processor import AudioProcessor
from services.text_processor import TextProcessor
from services.translation_service import TranslationService


class ConversionEngine:
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.audio_processor = AudioProcessor()
        self.text_processor = TextProcessor()
        self.translation_service = TranslationService()

    def run_conversion(self, params):
        try:
            params["log_callback"]("开始转换过程...")
            mode = params["mode"]

            # 读取输入文件
            with open(params["input_file"], "r", encoding="utf-8") as f:
                original_lines = [line.strip() for line in f.readlines() if line.strip()]

            if not original_lines:
                params["log_callback"]("错误: 输入文件为空")
                return

            # 验证输入语言
            validation_result, error_msg = self.text_processor.validate_input_language(
                original_lines, mode
            )
            if not validation_result:
                params["log_callback"](f"语言验证失败: {error_msg}")
                return

            # 初始化浏览器
            driver = self.browser_manager.init_driver(
                params["output_dir"],
                params["browser_type"],
                params["log_callback"]
            )

            # 处理文本
            katakana_lines = []
            japanese_lines = []

            if mode == "中文Yukkuri":
                katakana_lines = self.text_processor.convert_chinese_to_katakana(
                    driver, original_lines, params["log_callback"]
                )
            elif mode == "英文Yukkuri":
                katakana_lines = self.text_processor.convert_english_to_katakana(
                    driver,
                    original_lines,
                    params["log_callback"]  # Add log_callback argument
                )
            elif mode == "日文Yukkuri":
                katakana_lines = original_lines
                params["log_callback"]("日文模式：直接使用原文本")
            elif mode == "中文翻译日文Yukkuri":
                japanese_lines = self.translation_service.translate_chinese_to_japanese(
                    original_lines, params["log_callback"]
                )
                katakana_lines = japanese_lines

            if not katakana_lines:
                params["log_callback"]("错误: 无法获取有效的片假名文本")
                return

            # 下载音频
            downloaded_audio_files = self.download_audio_files(
                driver, katakana_lines, original_lines, params
            )

            # 生成LRC文件
            if params["generate_lrc"] and downloaded_audio_files:
                self.generate_lrc_files(
                    original_lines, downloaded_audio_files,
                    japanese_lines, mode, params
                )

            # 完成
            params["progress_callback"](100, f"完成 {len(downloaded_audio_files)}/{len(original_lines)}")
            params["log_callback"](f"转换完成！成功下载 {len(downloaded_audio_files)}/{len(original_lines)} 个音频文件")

        except Exception as e:
            params["log_callback"](f"转换过程出错: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            params["status_callback"]("转换完成")

    def download_audio_files(self, driver, katakana_lines, original_lines, params):
        downloaded_audio_files = []
        total_lines = min(len(original_lines), len(katakana_lines))

        for idx in range(total_lines):
            if params["stop_flag"]():
                params["log_callback"]("转换已被用户停止")
                break

            # 更新进度
            progress = (idx / total_lines) * 100
            params["progress_callback"](progress, f"{idx + 1}/{total_lines}")

            original_line = original_lines[idx]
            katakana_line = katakana_lines[idx]

            if not katakana_line:
                params["log_callback"](f"跳过第{idx + 1}行（空文本）")
                continue

            # 下载音频
            audio_file_path = self.browser_manager.download_audio(
                driver, katakana_line, idx + 1,
                self.text_processor.sanitize_filename(original_line)[:50],
                params["voice_type"],
                params["output_dir"],
                params["log_callback"]
            )

            if audio_file_path:
                # 处理音频
                processed_audio = self.audio_processor.process_audio(
                    audio_file_path,
                    params["speed"],
                    params["volume"],
                    params["pitch"],
                    params["log_callback"]
                )

                if processed_audio:
                    downloaded_audio_files.append(processed_audio)
                    params["log_callback"](f"第{idx + 1}行处理成功")
                else:
                    downloaded_audio_files.append(audio_file_path)
                    params["log_callback"](f"第{idx + 1}行下载成功（未处理）")

            time.sleep(1)

        return downloaded_audio_files

    def generate_lrc_files(self, original_lines, audio_files, japanese_lines, mode, params):
        base_name = os.path.splitext(os.path.basename(params["input_file"]))[0]

        if mode == "中文翻译日文Yukkuri":
            # 中文LRC
            self.text_processor.generate_combined_lrc_file(
                original_lines[:len(audio_files)],
                audio_files,
                base_name,
                params["output_dir"],
                "_chinese",
                params["log_callback"]
            )
            # 日文LRC
            self.text_processor.generate_combined_lrc_file(
                japanese_lines[:len(audio_files)],
                audio_files,
                base_name,
                params["output_dir"],
                "_japanese",
                params["log_callback"]
            )
        else:
            # 单个LRC
            self.text_processor.generate_combined_lrc_file(
                original_lines[:len(audio_files)],
                audio_files,
                base_name,
                params["output_dir"],
                "",
                params["log_callback"]
            )