import tkinter as tk
from gui.audio_converter_gui import AudioConverterGUI
import os
import sys


def resource_path(relative_path):
    """ 获取资源绝对路径（适配开发环境和PyInstaller打包环境） """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    root = tk.Tk()

    # 动态获取图标路径（优先尝试根目录）
    icon_path = resource_path('icon.ico')

    # 如果根目录不存在，尝试resources子目录
    if not os.path.exists(icon_path):
        icon_path = resource_path('resources/icon.ico')

    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
            print(f"成功加载图标: {icon_path}")
        except Exception as e:
            print(f"图标加载失败: {icon_path}, 错误: {str(e)}")
    else:
        print(f"图标文件不存在: {icon_path}")

    app = AudioConverterGUI(root)

    def on_closing():
        if app.is_converting:
            if tk.messagebox.askokcancel("退出", "转换正在进行中，确定要退出吗？"):
                app.is_converting = False
                root.destroy()
        else:
            root.destroy()

    # 添加全局异常处理
    def handle_exception(exc_type, exc_value, exc_traceback):
        error_msg = f"未处理的异常: {exc_value}"
        app.log(error_msg)
        app.reset_conversion_state()  # 重置UI状态
        tk.messagebox.showerror("错误", error_msg)

    sys.excepthook = handle_exception

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
