import re
import time
import os
from mutagen.mp3 import MP3
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TextProcessor:
    def __init__(self):
        pass

    def get_voice_options(self):
        return [
            {"text": "声種: AT1-F1(ゆっくり)", "value": "aqtk1-f1"},
            {"text": "声種: AT1-F2", "value": "aqtk1-f2"},
            {"text": "声種: AT1-M1", "value": "aqtk1-m1"},
            {"text": "声種: AT1-M2", "value": "aqtk1-m2"},
            {"text": "声種: AT1-DVD", "value": "aqtk1-dvd"},
            {"text": "声種: AT1-IMD1", "value": "aqtk1-imd1"},
            {"text": "声種: AT1-JGR", "value": "aqtk1-jgr"},
            {"text": "声種: AT1-R1", "value": "aqtk1-r1"},
            {"text": "声種: AT2-RM", "value": "aqtk2-rm"},
            {"text": "声種: AT2-F1C", "value": "aqtk2-f1c"},
            {"text": "声種: AT2-RM", "value": "aqtk2-f3a"},
            {"text": "声種: AT2-HUSKEY", "value": "aqtk2-huskey"},
            {"text": "声種: AT2-M4B", "value": "aqtk2-m4b"},
            {"text": "声種: AT2-MF1", "value": "aqtk2-mf1"},
            {"text": "声種: AT2-RB2", "value": "aqtk2-rb2"},
            {"text": "声種: AT2-RB3", "value": "aqtk2-rb3"},
            {"text": "声種: AT2-ROBO", "value": "aqtk2-robo"},
            {"text": "声種: AT2-YUKKURI", "value": "aqtk2-yukkuri"},
            {"text": "声種: AT2-F4", "value": "aqtk2-f4"},
            {"text": "声種: AT2-M5", "value": "aqtk2-m5"},
            {"text": "声種: AT2-MF2", "value": "aqtk2-mf2"},
            {"text": "声種: AT2-RM3", "value": "aqtk2-rm3"},
            {"text": "声種: AT10-F1", "value": "aqtk10-f1"},
            {"text": "声種: AT10-F2", "value": "aqtk10-f2"},
            {"text": "声種: AT10-F3", "value": "aqtk10-f3"},
            {"text": "声種: AT10-M1", "value": "aqtk10-m1"},
            {"text": "声種: AT10-M2", "value": "aqtk10-m2"},
            {"text": "声種: AT10-R1", "value": "aqtk10-r1"},
            {"text": "声種: AT10-R2", "value": "aqtk10-r2"}
        ]

    def get_voice_value(self, display_text):
        for option in self.get_voice_options():
            if option["text"] == display_text:
                return option["value"]
        return "aqtk1-f1"

    def validate_input_language(self, lines, mode):
        """验证输入语言"""
        combined_text = "\n".join(lines)

        if mode == "英文Yukkuri":
            if not self.is_pure_english(combined_text):
                return False, "输入内容不是纯英文，请检查文本内容。"
        elif mode == "日文Yukkuri":
            if not self.is_pure_japanese(combined_text):
                return False, "输入内容不是纯日文，请检查文本内容。"
        elif mode in ["中文Yukkuri", "中文翻译日文Yukkuri"]:
            if not self.contains_chinese(combined_text):
                return False, "输入内容不包含中文字符，请检查文本内容。"

        return True, ""

    def is_pure_english(self, text):
        pattern = r'^[a-zA-Z0-9\s\.,!?;:\'\"-]*$'
        return bool(re.match(pattern, text))

    def is_pure_japanese(self, text):
        japanese_pattern = r'^[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\s\.,!?;:\'\"-]*$'
        return bool(re.match(japanese_pattern, text))

    def contains_chinese(self, text):
        pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
        return bool(pattern.search(text))

    def convert_chinese_to_katakana(self, driver, chinese_lines, log_callback):
        """将中文转换为片假名"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                log_callback(f"访问中文转片假名网站（尝试 #{attempt + 1}）")
                driver.get(
                    "https://www.ltool.net/chinese_simplified_and_traditional_characters_pinyin_to_katakana_converter_in_simplified_chinese.php"
                )

                # 输入文本并转换
                input_area = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#contents"))
                )
                input_area.clear()
                input_area.send_keys("\n".join(chinese_lines))

                submit_btn = driver.find_element(By.XPATH, '//*[@id="ltool"]/div[2]/div[1]/form/div[3]/center/input')
                submit_btn.click()

                # 获取结果
                result_div = WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "#result"))
                )
                raw_katakana = result_div.text

                if not raw_katakana.strip():
                    raise ValueError("转换结果为空")

                katakana_lines = [self.clean_katakana(line) for line in raw_katakana.splitlines() if line.strip()]

                if katakana_lines:
                    log_callback(f"中文转片假名成功（第{attempt + 1}次尝试）")
                    return katakana_lines

            except Exception as e:
                log_callback(f"尝试 #{attempt + 1} 失败: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)

        log_callback(f"中文转片假名失败，尝试{max_retries}次后仍无有效结果")
        raise Exception(f"中文转片假名失败，尝试{max_retries}次后仍无有效结果")

    def convert_english_to_katakana(self, driver, english_lines, log_callback):
        """将英文转换为片假名"""
        katakana_lines = []
        try:
            log_callback("正在访问英文转片假名网站...")
            wait = WebDriverWait(driver, 20)  # 修复：定义 wait 对象

            for i, line in enumerate(english_lines):

                log_callback(f"转换第{i + 1}行英文: {line}")

                driver.get("https://www.sljfaq.org/cgi/e2k_ja.cgi")

                # 输入英文
                input_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#word-input")))
                input_field.clear()
                input_field.send_keys(line)

                # 点击转换按钮
                submit_btn = driver.find_element(By.CSS_SELECTOR,
                                                 "#converter > form > table > tbody > tr:nth-child(4) > td.buttons > input[type=submit]:nth-child(1)")
                submit_btn.click()

                # 添加重试机制解决空文本问题
                max_retries = 5
                retry_delay = 1
                katakana_text = ""

                for attempt in range(max_retries):
                    try:
                        # 获取片假名结果
                        katakana_element = wait.until(
                            EC.presence_of_element_located((By.XPATH, '//*[@id="katakana-string"]'))
                        )
                        katakana_text = katakana_element.text.strip()

                        if katakana_text:
                            break

                        if attempt == max_retries - 1:
                            log_callback(f"第{i + 1}行转换失败（尝试{max_retries}次后仍为空）")
                            katakana_text = ""
                    except Exception as e:
                        log_callback(f"第{i + 1}行转换尝试时出错: {str(e)}")

                    if not katakana_text and attempt < max_retries - 1:
                        log_callback(f"第{i + 1}行转换结果为空，等待{retry_delay}秒后重试...")
                        time.sleep(retry_delay)

                        submit_btn = driver.find_element(By.CSS_SELECTOR,
                                                         "#converter > form > table > tbody > tr:nth-child(4) > td.buttons > input[type=submit]:nth-child(1)")
                        submit_btn.click()
                        time.sleep(1)

                if katakana_text:
                    # 清理片假名文本（但保留"・"）
                    cleaned_katakana = self.clean_katakana_preserve_dots(katakana_text)
                    # 修正标点符号
                    corrected_katakana = self.correct_katakana_punctuation(line, cleaned_katakana)
                    katakana_lines.append(corrected_katakana)
                    log_callback(f"第{i + 1}行转换成功: {corrected_katakana}")
                else:
                    katakana_lines.append("")
                    log_callback(f"第{i + 1}行转换失败，使用空文本")

                time.sleep(1)

        except Exception as e:
            log_callback(f"英文转片假名失败: {str(e)}")

        return katakana_lines

    def correct_katakana_punctuation(self, original_english, katakana_text):
        """修正片假名标点符号"""
        if not original_english or not katakana_text:
            return katakana_text

        punctuation_map = {
            ',': '，', '.': '。', '!': '！', '?': '？', ':': '：',
            ';': '；', '"': '"', "'": "'", '(': '（', ')': '）',
            '[': '［', ']': '］', '{': '｛', '}': '｝', '-': 'ー', '_': 'ー'
        }

        try:
            # 获取原文中的标点符号
            punctuation_info = []
            words = []
            current_word = ""

            for char in original_english:
                if char in punctuation_map:
                    if current_word.strip():
                        words.append(current_word.strip())
                        current_word = ""
                    punctuation_info.append((len(words) - 1, punctuation_map[char]))
                elif char.isspace():
                    if current_word.strip():
                        words.append(current_word.strip())
                        current_word = ""
                else:
                    current_word += char

            if current_word.strip():
                words.append(current_word.strip())

            # 分割片假名
            katakana_parts = katakana_text.split('・')
            katakana_parts = [part for part in katakana_parts if part.strip()]

            # 如果数量不匹配，直接返回
            if len(katakana_parts) != len(words):
                return katakana_text

            # 重建文本
            result_parts = []
            for i, part in enumerate(katakana_parts):
                result_parts.append(part)

                has_punct = False
                for word_pos, punct in punctuation_info:
                    if word_pos == i:
                        result_parts.append(punct)
                        has_punct = True

                if i < len(katakana_parts) - 1 and not has_punct:
                    result_parts.append('・')

            return ''.join(result_parts)

        except Exception:
            return katakana_text

    def clean_katakana(self, text):
        """清理片假名文本"""
        cleaned = re.sub(r'\s+', '', text)
        cleaned = re.sub(r'[\(（].*?[\)）]', '', cleaned)
        return cleaned

    def clean_katakana_preserve_dots(self, text):
        """清理片假名但保留'·'分隔符"""
        cleaned = re.sub(r'\s+', '', text)
        cleaned = re.sub(r'[\(（].*?[\)）]', '', text)
        return cleaned

    def sanitize_filename(self, filename):
        """清理文件名中的非法字符"""
        return re.sub(r'[\\/*?:"<>|]', '', filename)

    def get_audio_duration(self, audio_file_path):
        """获取音频时长"""
        try:
            audio = MP3(audio_file_path)
            return audio.info.length
        except Exception:
            return 5.0

    def generate_combined_lrc_file(self, text_lines, audio_files, output_prefix, output_dir, language_suffix,
                                   log_callback):
        """生成整合的LRC字幕文件"""
        try:
            # 计算总时长
            total_duration = 0
            durations = []

            for audio_file in audio_files:
                duration = self.get_audio_duration(audio_file)
                durations.append(duration)
                total_duration += duration

            # 生成文件路径
            lrc_filename = f"{output_prefix}{language_suffix}.lrc"
            lrc_path = os.path.join(output_dir, lrc_filename)

            # 生成内容
            lrc_content = []
            lrc_content.append("[ar:Yukkuri Audio Converter]")
            lrc_content.append("[ti:Generated Audio]")
            lrc_content.append("[al:Yukkuri Conversion]")
            lrc_content.append(f"[length:{int(total_duration // 60):02d}:{int(total_duration % 60):02d}]")
            lrc_content.append("")

            # 添加时间轴
            current_time = 0.0
            for i, line in enumerate(text_lines):
                if i < len(audio_files):
                    if line.strip():
                        minutes = int(current_time // 60)
                        seconds = current_time % 60
                        time_tag = f"[{minutes:02d}:{seconds:05.2f}]"
                        lrc_content.append(f"{time_tag}{line.strip()}")

                    if i < len(durations):
                        current_time += durations[i]

            # 添加结束标记
            end_minutes = int(total_duration // 60)
            end_seconds = total_duration % 60
            end_time_tag = f"[{end_minutes:02d}:{end_seconds:05.2f}]"
            lrc_content.append(f"{end_time_tag}")

            # 写入文件
            with open(lrc_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lrc_content))

            log_callback(f"已生成LRC字幕文件: {lrc_filename}")
            return True

        except Exception as e:
            log_callback(f"生成LRC字幕文件失败: {str(e)}")
            return False