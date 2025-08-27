# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_submodules

# 添加项目根目录到系统路径
sys.path.append(os.path.abspath('.'))

block_cipher = None

a = Analysis(
    ['main.py'],  # 入口文件
    pathex=[os.path.abspath('.'),  # 添加项目根目录
            os.path.abspath('./gui'),
            os.path.abspath('./core'),
            os.path.abspath('./services')],
    binaries=[],
    datas=[
        # 外部工具
        ('resources/ffmpeg.exe', '.'),
        ('resources/ffprobe.exe', '.'),

        # 资源文件
        ('resources/icon.ico', '.'),  # 程序图标

        # 递归包含resources目录下的所有文件
        (os.path.join(os.path.abspath('.'), 'resources'), 'resources')
    ],
    hiddenimports=[
        # 显式添加包模块
        'gui',
        'gui.audio_converter_gui',
        'core',
        'core.conversion_engine',
        'core.browser_manager',
        'core.audio_processor',
        'core.utils',
        'services',
        'services.text_processor',
        'services.translation_service',

        # 第三方依赖
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'webdriver_manager',
        'webdriver_manager.chrome',
        'requests',
        'mutagen',
        'mutagen.mp3',
        'numpy',
        'pydub',
        'pydub.effects',
        'librosa',
        'soundfile',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext'
        'resampy'
    ] +
    # 动态收集可能遗漏的子模块
    collect_submodules('selenium') +
    collect_submodules('webdriver_manager') +
    collect_submodules('mutagen') +
    collect_submodules('pydub'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YukkuriAudioConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('resources', 'icon.ico')  # 正确指定图标路径
)