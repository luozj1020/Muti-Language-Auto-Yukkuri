from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import glob
import time


class BrowserManager:
    def init_driver(self, download_dir, browser_type, log_callback):
        """初始化浏览器驱动"""
        normalized_dir = os.path.normpath(download_dir)

        # 浏览器映射
        browser_mapping = {
            "自动检测": "auto",
            "Chrome": "chrome",
            "Edge": "edge",
            "Firefox": "firefox"
        }

        selected_browser = browser_mapping.get(browser_type, "auto")

        if selected_browser == "auto":
            return self.init_driver_auto(normalized_dir, log_callback)
        else:
            return self.init_driver_specific(normalized_dir, selected_browser, log_callback)

    def init_driver_auto(self, download_dir, log_callback):
        """自动检测并初始化可用的浏览器驱动"""
        browsers_to_try = [
            ("Chrome", self.init_chrome_driver),
            ("Edge", self.init_edge_driver),
            ("Firefox", self.init_firefox_driver)
        ]

        for browser_name, init_func in browsers_to_try:
            try:
                log_callback(f"尝试初始化{browser_name}浏览器...")
                driver = init_func(download_dir)
                log_callback(f"成功初始化{browser_name}浏览器")
                return driver
            except Exception as e:
                log_callback(f"{browser_name}浏览器初始化失败: {str(e)}")
                continue

        raise Exception("无法初始化任何浏览器，请确保已安装Chrome、Edge或Firefox")

    def init_driver_specific(self, download_dir, browser_type, log_callback):
        """初始化指定类型的浏览器驱动"""
        try:
            if browser_type == "chrome":
                return self.init_chrome_driver(download_dir)
            elif browser_type == "edge":
                return self.init_edge_driver(download_dir)
            elif browser_type == "firefox":
                return self.init_firefox_driver(download_dir)
            else:
                raise Exception(f"不支持的浏览器类型: {browser_type}")
        except Exception as e:
            log_callback(f"{browser_type}浏览器初始化失败: {str(e)}")
            raise e

    def init_chrome_driver(self, download_dir):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True
        })

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    def init_edge_driver(self, download_dir):
        edge_options = webdriver.EdgeOptions()
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--headless")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_experimental_option("prefs", {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True
        })

        service = EdgeService(EdgeChromiumDriverManager().install())
        return webdriver.Edge(service=service, options=edge_options)

    def init_firefox_driver(self, download_dir):
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument("--headless")

        firefox_profile = webdriver.FirefoxProfile()
        firefox_profile.set_preference("browser.download.folderList", 2)
        firefox_profile.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_profile.set_preference("browser.download.dir", download_dir)
        firefox_profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                                       "audio/mpeg,audio/mp3,application/octet-stream")

        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=firefox_options,
                                 firefox_profile=firefox_profile)

    def download_audio(self, driver, text, line_num, clean_name, voice_value, output_dir, log_callback):
        """下载单个音频文件"""
        try:
            # 确保声种已选择
            if not hasattr(driver, 'voice_selected') or not driver.voice_selected:
                self.select_voice_type(driver, voice_value, log_callback)
                driver.voice_selected = True

            # 确保在正确页面
            if driver.current_url != "https://www.yukumo.net/#/":
                driver.get("https://www.yukumo.net/#/")

            # 输入文本
            wait = WebDriverWait(driver, 20)
            input_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#__BVID__21")))
            input_field.clear()
            input_field.send_keys(text)
            time.sleep(0.5)

            # 记录下载前的文件
            existing_files = set(glob.glob(os.path.join(output_dir, '*.mp3')))

            # 点击下载
            download_btn = driver.find_element(By.XPATH, '//*[@id="home-main"]/div[2]/div[2]/div/button[2]')
            download_btn.click()

            # 等待新文件出现
            new_file = None
            end_time = time.time() + 30
            while time.time() < end_time:
                time.sleep(1)
                current_files = set(glob.glob(os.path.join(output_dir, '*.mp3')))
                new_files = current_files - existing_files
                if new_files:
                    new_file = new_files.pop()
                    break

            if not new_file:
                return None

            # 重命名文件
            new_filename = f"{line_num}-{clean_name}.mp3"
            new_path = os.path.join(output_dir, new_filename)

            if os.path.exists(new_path):
                try:
                    os.remove(new_path)
                    log_callback(f"删除已存在的文件: {new_path}")
                except Exception as e:
                    log_callback(f"删除文件时出错: {str(e)}")

            os.rename(new_file, new_path)
            log_callback(f"已重命名文件: {os.path.basename(new_file)} -> {new_filename}")

            return new_path

        except Exception as e:
            log_callback(f"下载音频时出错: {str(e)}")
            if hasattr(driver, 'voice_selected'):
                driver.voice_selected = False
            return None

    def select_voice_type(self, driver, voice_value, log_callback):
        """选择声种"""
        try:
            driver.get("https://www.yukumo.net/#/")
            wait = WebDriverWait(driver, 20)

            # 等待页面加载
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#__BVID__21")))

            # 点击下拉框
            dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#__BVID__22")))
            dropdown.click()

            # 选择选项
            option_selector = f"option[value='{voice_value}']"
            option = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, option_selector)))
            option.click()

            # 关闭下拉框
            dropdown.click()
            time.sleep(1)

            # 验证选择
            selected_value = driver.execute_script("return document.querySelector('#__BVID__22').value;")
            if selected_value == voice_value:
                log_callback(f"声种选择成功: {voice_value}")
                return True

            # 备用方法：直接设置值
            script = f"document.querySelector('#__BVID__22').value = '{voice_value}';"
            driver.execute_script(script)
            log_callback(f"使用JavaScript设置声种: {voice_value}")
            return True

        except Exception as e:
            log_callback(f"选择声种失败: {str(e)}")
            return False