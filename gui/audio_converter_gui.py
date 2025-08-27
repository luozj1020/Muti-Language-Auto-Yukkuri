import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import time
import os
import threading

from core.conversion_engine import ConversionEngine
from core.utils import resource_path
from services.text_processor import TextProcessor


class AudioConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("多语言Yukkuri音频转换器")
        self.root.geometry("850x650")
        self.root.resizable(True, True)

        # 初始化核心组件
        self.conversion_engine = ConversionEngine()
        self.text_processor = TextProcessor()

        # 变量初始化
        self.input_file_path = tk.StringVar()
        self.download_path = tk.StringVar()
        self.conversion_mode = tk.StringVar(value="中文Yukkuri")
        self.generate_lrc = tk.BooleanVar(value=True)
        self.is_converting = False
        self.browser_type = tk.StringVar(value="自动检测")

        # 声种选项
        self.voice_options = self.text_processor.get_voice_options()
        self.voice_type = tk.StringVar(value=self.voice_options[0]["text"])

        # 音频参数
        self.speed_var = tk.IntVar(value=100)
        self.volume_var = tk.IntVar(value=100)
        self.pitch_var = tk.IntVar(value=100)

        # 设置UI
        self.setup_ui()

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(8, weight=1)  # 增加行数以容纳新控件

        # 标题
        title_label = ttk.Label(main_frame, text="多语言Yukkuri音频转换器",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))

        # 创建选项框架（用于并排显示三个选择控件）
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # 转换模式选择
        ttk.Label(options_frame, text="转换模式:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        mode_combo = ttk.Combobox(options_frame, textvariable=self.conversion_mode,
                                  values=["中文Yukkuri", "英文Yukkuri", "日文Yukkuri", "中文翻译日文Yukkuri"],
                                  state="readonly", width=15)
        mode_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_changed)

        # 浏览器选择
        ttk.Label(options_frame, text="浏览器选择:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        browser_combo = ttk.Combobox(options_frame, textvariable=self.browser_type,
                                     values=["自动检测", "Chrome", "Edge", "Firefox"],
                                     state="readonly", width=10)
        browser_combo.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))

        # 声种选择
        ttk.Label(options_frame, text="声种选择:").grid(row=0, column=4, sticky=tk.W, padx=(0, 5))
        voice_values = [option["text"] for option in self.voice_options]
        voice_combo = ttk.Combobox(options_frame, textvariable=self.voice_type,
                                   values=voice_values, state="readonly", width=20)
        voice_combo.grid(row=0, column=5, sticky=tk.W)
        voice_combo.set(self.voice_options[0]["text"])  # 设置默认选项

        # 新增音频参数控制
        audio_params_frame = ttk.LabelFrame(main_frame, text="音频参数调整")
        audio_params_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10, padx=5)
        audio_params_frame.columnconfigure(1, weight=1)
        audio_params_frame.columnconfigure(4, weight=1)
        audio_params_frame.columnconfigure(7, weight=1)

        # 语速控制
        ttk.Label(audio_params_frame, text="语速 (50-300):").grid(row=0, column=0, padx=(10, 5), sticky=tk.W)
        speed_scale = ttk.Scale(audio_params_frame, from_=50, to=300, variable=self.speed_var,
                                command=lambda v: self.speed_var.set(int(float(v))))
        speed_scale.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))

        # 修改后的语速输入框
        speed_entry = ttk.Entry(audio_params_frame, textvariable=self.speed_var, width=5,
                                validate="key",
                                validatecommand=(self.root.register(self.validate_int), '%P', 50, 300))
        speed_entry.grid(row=0, column=2, padx=(5, 0))
        speed_entry.bind("<FocusOut>", lambda e: self.focus_out_handler(self.speed_var, 50, 300))
        # 添加回车键处理
        speed_entry.bind("<Return>", lambda e: self.focus_out_handler(self.speed_var, 50, 300))

        # 音量控制
        ttk.Label(audio_params_frame, text="音量 (0-300):").grid(row=0, column=3, padx=(10, 5), sticky=tk.W)
        volume_scale = ttk.Scale(audio_params_frame, from_=0, to=300, variable=self.volume_var,
                                 command=lambda v: self.volume_var.set(int(float(v))))
        volume_scale.grid(row=0, column=4, padx=5, sticky=(tk.W, tk.E))

        # 修改后的音量输入框
        volume_entry = ttk.Entry(audio_params_frame, textvariable=self.volume_var, width=5,
                                 validate="key",
                                 validatecommand=(self.root.register(self.validate_int), '%P', 0, 300))
        volume_entry.grid(row=0, column=5, padx=(5, 0))
        volume_entry.bind("<FocusOut>", lambda e: self.focus_out_handler(self.volume_var, 0, 300))
        volume_entry.bind("<Return>", lambda e: self.focus_out_handler(self.volume_var, 0, 300))

        # 音程控制
        ttk.Label(audio_params_frame, text="音程 (20-200):").grid(row=0, column=6, padx=(10, 5), sticky=tk.W)
        pitch_scale = ttk.Scale(audio_params_frame, from_=20, to=200, variable=self.pitch_var,
                                command=lambda v: self.pitch_var.set(int(float(v))))
        pitch_scale.grid(row=0, column=7, padx=5, sticky=(tk.W, tk.E))

        # 修改后的音程输入框
        pitch_entry = ttk.Entry(audio_params_frame, textvariable=self.pitch_var, width=5,
                                validate="key",
                                validatecommand=(self.root.register(self.validate_int), '%P', 20, 200))
        pitch_entry.grid(row=0, column=8, padx=(5, 0))
        pitch_entry.bind("<FocusOut>", lambda e: self.focus_out_handler(self.pitch_var, 20, 200))
        pitch_entry.bind("<Return>", lambda e: self.focus_out_handler(self.pitch_var, 20, 200))

        # 输入文件选择 - 使用框架包装，使元素更紧凑
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(input_frame, text="输入文件:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        input_entry = ttk.Entry(input_frame, textvariable=self.input_file_path,
                                state="readonly", width=45)
        input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(input_frame, text="选择文件", width=10,
                   command=self.select_input_file).grid(row=0, column=2, padx=(0, 0))

        input_frame.columnconfigure(1, weight=1)  # 让输入框可扩展

        # 下载路径选择 - 同样使用框架包装
        download_frame = ttk.Frame(main_frame)
        download_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(download_frame, text="下载路径:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        download_entry = ttk.Entry(download_frame, textvariable=self.download_path,
                                   state="readonly", width=45)
        download_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(download_frame, text="选择路径", width=10,
                   command=self.select_download_path).grid(row=0, column=2, padx=(0, 0))

        download_frame.columnconfigure(1, weight=1)  # 让输入框可扩展

        # LRC字幕选项
        lrc_frame = ttk.Frame(main_frame)
        lrc_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W), pady=5)
        ttk.Checkbutton(lrc_frame, text="生成LRC字幕文件", variable=self.generate_lrc).pack(side=tk.LEFT)

        # 添加LRC说明标签
        lrc_info = ttk.Label(lrc_frame, text="（自动根据音频时长生成字幕时间轴）",
                             font=("Arial", 8), foreground="gray")
        lrc_info.pack(side=tk.LEFT, padx=(10, 0))

        # 转换按钮和进度条
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=4, pady=20)

        self.convert_btn = ttk.Button(button_frame, text="开始转换",
                                      command=self.start_conversion, state="disabled")
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = ttk.Button(button_frame, text="停止转换",
                                   command=self.stop_conversion, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(button_frame, variable=self.progress_var,
                                            maximum=100, length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=(10, 0))

        # 进度标签
        self.progress_label = ttk.Label(button_frame, text="准备就绪")
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))

        # 日志显示区域
        ttk.Label(main_frame, text="转换日志:").grid(row=7, column=0, sticky=(tk.W, tk.N), pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.log_text.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))

        # 状态栏
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))

    def validate_int(self, value, min_val, max_val):
        """验证输入是否为有效数字，允许输入过程中的临时状态"""
        if value == "":
            return True
        try:
            # 只验证是否为数字，不限制范围，让用户可以正常输入
            int(value)
            return True
        except ValueError:
            return False  # 只阻止非数字输入

    def focus_out_handler(self, var, min_val, max_val):
        """失去焦点时验证并修正数值范围"""
        try:
            current_value = var.get()
            # 处理空字符串或空白字符串
            if not str(current_value).strip():
                var.set(100)
                return

            current_val = int(current_value)
            min_val_int = int(min_val)
            max_val_int = int(max_val)

            # 如果超出范围，设置为默认值100
            if current_val < min_val_int or current_val > max_val_int:
                var.set(100)
                # 可选：显示提示信息
                param_name = ""
                if var == self.speed_var:
                    param_name = f"语速范围应为 {min_val}-{max_val}"
                elif var == self.volume_var:
                    param_name = f"音量范围应为 {min_val}-{max_val}"
                elif var == self.pitch_var:
                    param_name = f"音程范围应为 {min_val}-{max_val}"

                if param_name:
                    self.log(f"输入值超出范围，已重置为默认值100。{param_name}")

        except (ValueError, tk.TclError):
            var.set(100)  # 无效输入设为默认值100
            self.log("输入值无效，已重置为默认值100")

    def select_input_file(self):
        """选择输入文件"""
        file_path = filedialog.askopenfilename(
            title="选择输入文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            self.input_file_path.set(file_path)
            self.log(f"已选择输入文件: {file_path}")
            self.check_ready_state()

    def select_download_path(self):
        """选择下载路径"""
        folder_path = filedialog.askdirectory(title="选择下载路径")
        if folder_path:
            self.download_path.set(folder_path)
            self.log(f"已选择下载路径: {folder_path}")
            self.check_ready_state()

    def check_ready_state(self):
        """检查是否可以开始转换"""
        if self.input_file_path.get() and self.download_path.get() and not self.is_converting:
            self.convert_btn.config(state="normal")
            self.status_var.set("准备就绪 - 点击开始转换")
        else:
            self.convert_btn.config(state="disabled")

    def log(self, message):
        """在日志区域显示消息"""
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def reset_ui(self):
        """重置UI状态"""
        self.is_converting = False
        self.convert_btn.config(
            state="normal" if self.input_file_path.get() and self.download_path.get() else "disabled")
        self.stop_btn.config(state="disabled")
        self.progress_var.set(0)
        self.progress_label.config(text="准备就绪")
        self.status_var.set("准备就绪")

    def start_conversion(self):
        """开始转换过程"""
        if not self.input_file_path.get() or not self.download_path.get():
            messagebox.showerror("错误", "请选择输入文件和下载路径")
            return

        # 获取声种值
        voice_display = self.voice_type.get()
        voice_value = self.get_voice_value(voice_display)

        # 确认开始转换
        mode = self.conversion_mode.get()
        lrc_status = "生成LRC字幕" if self.generate_lrc.get() else "不生成LRC字幕"
        audio_params = f"语速: {self.speed_var.get()} | 音量: {self.volume_var.get()} | 音程: {self.pitch_var.get()}"
        voice_info = f"声种: {voice_display} ({voice_value})"

        if messagebox.askyesno("确认",
                               f"确定要开始{mode}转换吗？\n{lrc_status}\n{voice_info}\n音频参数: {audio_params}\n这个过程可能需要一些时间。"):
            self.is_converting = True
            self.convert_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.progress_var.set(0)
            self.status_var.set("转换中...")

            # 在新线程中运行转换
            self.conversion_thread = threading.Thread(target=self.run_conversion, args=(voice_value,))
            self.conversion_thread.daemon = True
            self.conversion_thread.start()

    def stop_conversion(self):
        """停止转换"""
        self.is_converting = False
        self.stop_btn.config(state="disabled")
        self.status_var.set("正在停止...")
        self.log("用户请求停止转换...")

    def get_voice_value(self, display_text):
        return self.text_processor.get_voice_value(display_text)

    def on_mode_changed(self, event=None):
        """转换模式改变时的处理"""
        mode = self.conversion_mode.get()
        self.log(f"切换转换模式: {mode}")
        self.check_ready_state()

    def run_conversion(self, voice_value):
        # 获取转换参数
        params = {
            "input_file": self.input_file_path.get(),
            "output_dir": self.download_path.get(),
            "mode": self.conversion_mode.get(),
            "voice_type": voice_value,
            "speed": self.speed_var.get(),
            "volume": self.volume_var.get(),
            "pitch": self.pitch_var.get(),
            "generate_lrc": self.generate_lrc.get(),
            "browser_type": self.browser_type.get(),
            "log_callback": self.log,
            "progress_callback": self.update_progress,
            "status_callback": self.update_status,
            "stop_flag": lambda: not self.is_converting
        }

        try:
            # 启动转换线程
            self.conversion_thread = threading.Thread(
                target=self.conversion_engine.run_conversion,
                args=(params,)
            )
            self.conversion_thread.daemon = True
            self.conversion_thread.start()
            self.conversion_thread.join()  # 等待转换线程完成
        except Exception as e:
            self.log(f"转换过程中发生错误: {str(e)}")
        finally:
            # 无论成功或失败，转换完成后重置UI状态
            self.root.after(0, self.reset_conversion_state)

    def reset_conversion_state(self):
        """重置转换状态，启用开始按钮"""
        self.is_converting = False
        self.convert_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set("转换已完成")
        self.log("转换过程结束")

    def update_progress(self, value, text):
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.root.update_idletasks()

    def update_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()
