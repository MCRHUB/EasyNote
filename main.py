# -*- coding: utf-8 -*-
"""
程序入口
- 启动 Flask 后端（后台线程）
- 使用 PyWebView 打开一个本地窗口，加载 http://127.0.0.1:5000/
- 不启动系统浏览器
- 跨平台：Windows / macOS / Linux 通用
"""
import os
import sys
import threading
import time
import webview
import config
import db
from app import create_app


def start_flask():
    app = create_app()
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


def set_window_icon_cross_platform(window):
    """
    窗口图标设置（跨平台）
    - Windows: 通过 Win32 API 加载 icon.ico
    - macOS  : PyWebView 自动读取 .app bundle 内的 Resources/icon.icns，
               或用 window.set_icon(png_path)（pywebview >= 5.0 支持）
    - Linux  : 基本不支持窗口图标，跳过即可
    """
    icon_path = None

    if sys.platform == 'win32':
        # Windows: 优先用 exe 内嵌资源（0 号），其次用同级 icon.ico
        if getattr(sys, 'frozen', False):
            icon_path = os.path.dirname(sys.executable)
        else:
            icon_path = os.path.dirname(os.path.abspath(__file__))
        ico = os.path.join(icon_path, 'icon.ico')
        if not os.path.exists(ico):
            return
        _set_icon_windows(ico)

    elif sys.platform == 'darwin':
        # macOS: 尝试用 set_icon（pywebview 5.x 支持 PNG）
        icon_path = os.path.dirname(os.path.abspath(__file__))
        png = os.path.join(icon_path, 'icon_256.png')
        if os.path.exists(png):
            try:
                window.set_icon(png)
            except Exception:
                pass


def _set_icon_windows(ico_path):
    """Windows 专用：通过 Win32 API 设置窗口图标"""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        HWND = wintypes.HWND
        title = '笔记本 - NoteBook'
        hwnd = HWND(user32.FindWindowW(None, title))
        if not hwnd:
            return

        IMAGE_ICON = 3
        LR_LOADFROMFILE = 0x00000010
        hIcon = user32.LoadImageW(None, ico_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
        if hIcon:
            user32.SendMessageW(hwnd, 0x0080, 0, hIcon)  # WM_SETICON large
            user32.SendMessageW(hwnd, 0x0080, 1, hIcon)  # WM_SETICON small
    except Exception as e:
        print('[WARN] set icon failed:', e)


def main():
    db.init_db()

    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    time.sleep(0.8)

    window = webview.create_window(
        title='笔记本 - NoteBook',
        url=f'http://{config.FLASK_HOST}:{config.FLASK_PORT}/',
        width=1280,
        height=800,
        min_size=(960, 600),
        resizable=True,
        text_select=True,
    )

    window.events.shown += lambda: set_window_icon_cross_platform(window)

    # GUI 后端选择：
    #   Windows -> edgechromium（WebView2 体验最佳，缺 runtime 会自动 fallback）
    #   macOS   -> 默认 cocoa+webkit（系统自带 WKWebView）
    #   Linux   -> 默认（GTK2 / Qt）
    gui_backend = None
    if sys.platform == 'win32':
        gui_backend = 'edgechromium'

    try:
        if gui_backend:
            webview.start(gui=gui_backend)
        else:
            webview.start()
    except Exception as e:
        print(f'[WARN] {gui_backend or "default"} 启动失败，回退:', e)
        webview.start()


if __name__ == '__main__':
    main()