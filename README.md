# Yukkuri Audio Converter - 多语言音频转换工具

## 概述

Yukkuri Audio Converter 是一个功能强大的音频转换工具，能够将多种语言的文本转换为片假名语音，并生成对应的音频文件。该工具支持中文、英文和日文文本输入，提供丰富的音频参数调整功能，并能够自动生成LRC字幕文件。

## 主要功能

1. **多语言支持**：
   - 中文Yukkuri：将中文文本转换为片假名音频
   - 英文Yukkuri：将英文文本转换为片假名音频
   - 日文Yukkuri：直接使用日文文本生成音频
   - 中文翻译日文Yukkuri：先将中文翻译成日文再生成音频
2. **音频参数调整**：
   - 语速控制（50-300%）
   - 音量调节（0-300%）
   - 音程调整（20-200%）
3. **浏览器支持**：
   - 自动检测或指定使用 Chrome/Edge/Firefox 浏览器
   - 无头模式操作，无需用户交互
4. **多声种选择**：
   - 提供30多种不同的声种选项
   - 支持不同风格的语音输出
5. **字幕生成**：
   - 自动生成LRC字幕文件
   - 根据音频时长自动计算时间轴

## 安装与使用

### 源代码调试

首先从 [https://www.ffmpeg.org/download.html] 下载压缩包，解压后将 bin 文件夹下的 ffprobe.exe 和 ffmpeg.exe 放入 resources 文件夹

安装依赖：

```
pip install selenium webdriver_manager librosa soundfile pydub mutagen requests numpy
```

运行程序：

```
python main.py
```

### 直接使用

直接从仓库下载可执行文件即可

### 使用说明

1. 选择转换模式（中文、英文、日文或中文翻译日文）
2. 选择浏览器类型（自动检测或指定浏览器）
3. 选择声种
4. 调整音频参数（语速、音量、音程）
5. 选择输入文本文件（每行一句）
6. 设置输出目录
7. 勾选是否生成LRC字幕文件
8. 点击"开始转换"按钮

## 文件结构说明

```
│
├── main.py                  # 程序入口
├── yukkuri_converter.spec   # pyinstaller 编译文件
│
├── core/                    # 核心功能模块
│   ├── audio_processor.py   # 音频处理（调整语速、音量等）
│   ├── browser_manager.py   # 浏览器管理（初始化、下载等）
│   ├── conversion_engine.py # 转换流程控制
│   └── utils.py             # 工具函数（资源路径获取）
│
├── gui/                     # 图形用户界面
│   └── audio_converter_gui.py # 主界面实现
│
├── resources/               # 资源文件
│   ├── ffmpeg.exe           # FFmpeg可执行文件
│   ├── ffprobe.exe          # FFprobe可执行文件
│   ├── icon.ico             # 程序图标
│   └── icon.png             # 程序图标（备用）
│
├── services/                # 服务模块
    ├── text_processor.py    # 文本处理（片假名转换等）
    └── translation_service.py # 翻译服务
```

## 技术特点

1. **浏览器自动化**：
   - 使用Selenium进行网页自动化
   - 支持无头模式运行
   - 自动下载和管理浏览器驱动
2. **音频处理**：
   - 使用Librosa进行高质量音程调整
   - 支持Pydub进行基本音频处理
   - 内置FFmpeg处理工具
3. **多线程处理**：
   - 支持后台转换任务
   - 实时进度更新
4. **智能错误处理**：
   - 浏览器初始化失败自动重试
   - 转换失败记录详细日志

   - 用户可随时停止转换过程




