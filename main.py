# -*- coding: utf-8 -*-
"""
程序入口
- 启动 Flask 后端（后台线程）
- 使用 PyWebView 打开一个本地窗口，加载 http://127.0.0.1:5000/
- 不启动系统浏览器
"""
import os
import threading
import time
import webview
import config
import db
from app import create_app


def start_flask():
    """在后台线程启动 Flask 服务"""
    app = create_app()
    # threaded=True 保证多个请求能并发处理（如图片上传 + 页面保存同时进行）
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=False,
        use_reloader=False,
        threaded=True,
    )


def main():
    # 1. 初始化数据库（如果不存在会自动创建）
    db.init_db()

    # 2. 启动 Flask 后端（守护线程）
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # 3. 等一下，确保 Flask 已经监听端口
    #    如果等太久会拖慢启动，太短可能 webview 打开时后端还没 ready
    #    经验 0.5~1.5 秒都可以
    time.sleep(0.8)

    # 4. 创建 PyWebView 窗口
    #    webview.create_window 的 url 参数加载本地 Flask 服务
    window = webview.create_window(
        title='笔记本 - NoteBook',
        url=f'http://{config.FLASK_HOST}:{config.FLASK_PORT}/',
        width=1280,
        height=800,
        min_size=(960, 600),
        resizable=True,
        text_select=True,
    )

    # 4.5 窗口加载完成后通过 Win32 API 设置图标
    def set_icon():
        try:
            import ctypes
            from ctypes import wintypes
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
            if not os.path.exists(icon_path):
                return
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            IMAGE_ICON = 3
            LR_LOADFROMFILE = 0x00000010
            HWND = wintypes.HWND
            HICON = wintypes.HICON
            window_handle = HWND(user32.FindWindowW(None, '笔记本 - NoteBook'))
            if not window_handle:
                return
            hIcon = user32.LoadImageW(None, icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
            if hIcon:
                user32.SendMessageW(window_handle, 0x0080, 0, hIcon)
                user32.SendMessageW(window_handle, 0x0080, 1, hIcon)
        except Exception as e:
            print('[WARN] set icon failed:', e)

    window.events.shown += lambda: set_icon()

    # 5. 启动 pywebview（阻塞主线程）
    #    gui='edgechromium' 在 Windows 上体验最好（基于系统 Edge/WebView2，性能好）
    #    如果用户机器没装 WebView2 运行时，会自动 fallback 到 mshtml（IE），
    #    但 mshtml 对现代富文本编辑器支持较差，建议提示用户安装 WebView2 Runtime
    try:
        webview.start(gui='edgechromium')
    except Exception as e:
        print('[WARN] edgechromium 启动失败，尝试默认后端:', e)
        webview.start()


if __name__ == '__main__':
    main()