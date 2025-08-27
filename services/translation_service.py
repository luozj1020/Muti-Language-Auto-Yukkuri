import time
import requests


class TranslationService:
    def __init__(self):
        pass

    def translate_chinese_to_japanese(self, chinese_lines, log_callback):
        """将中文翻译为日文"""
        japanese_lines = []

        try:
            log_callback("开始中文到日文翻译...")

            for i, line in enumerate(chinese_lines):
                if not line.strip():
                    japanese_lines.append("")
                    continue

                log_callback(f"翻译第{i + 1}行: {line}")
                translated_text = self.translate_with_api(line)

                if translated_text:
                    japanese_lines.append(translated_text)
                    log_callback(f"第{i + 1}行翻译成功: {translated_text}")
                else:
                    japanese_lines.append(line)
                    log_callback(f"第{i + 1}行翻译失败，使用原文")

                time.sleep(0.5)

            return japanese_lines

        except Exception as e:
            log_callback(f"翻译过程出错: {str(e)}")
            return chinese_lines

    def translate_with_api(self, text):
        """使用API进行翻译"""
        try:
            # 使用免费的翻译API
            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text,
                'langpair': 'zh|ja'
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'responseData' in data and 'translatedText' in data['responseData']:
                    return data['responseData']['translatedText']

            return ""
        except Exception:
            return ""