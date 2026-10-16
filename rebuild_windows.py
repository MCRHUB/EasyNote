# -*- coding: utf-8 -*-
"""
Windows 平台打包脚本
- 重新生成 icon.ico（确保多尺寸完整）
- 清理旧的 build/windows/ 产物
- PyInstaller onefile 打包
- 重建桌面快捷方式
- 刷新 Windows 图标缓存
- 产物统一放到 dist/windows/ 目录（与 macos 隔离）

用法: python rebuild_windows.py
入口: 双击 rebuild_windows.bat
"""
import os, sys, subprocess, ctypes, shutil, struct

BASE = os.path.dirname(os.path.abspath(__file__))


def step(msg):
    print(f"\n{msg}")
    print("-" * len(msg))


def gen_icons():
    step("🎨  [1/6] 重新生成 Windows 图标")
    from build_icons import generate_windows_icon
    p = generate_windows_icon()
    print(f"   ✅ {p} ({os.path.getsize(p):,} bytes)")


def clean():
    step("🧹  [2/6] 清理旧产物")
    for d in ['build', 'dist_windows']:
        p = os.path.join(BASE, d)
        if os.path.exists(p):
            shutil.rmtree(p)
            print(f"   删除 {d}/")
    target = os.path.join(BASE, 'dist', 'windows')
    if os.path.exists(target):
        shutil.rmtree(target)
        print(f"   删除 dist/windows/")


def build():
    step("📦  [3/6] PyInstaller 打包（约 30 秒）")
    sys.stdout.flush()

    venv_python = os.path.join(BASE, 'venv', 'Scripts', 'python.exe')
    icon = os.path.join(BASE, 'icon.ico')
    main_py = os.path.join(BASE, 'main.py')
    dist_dir = os.path.join(BASE, 'dist_windows')
    work_dir = os.path.join(BASE, 'build_windows')
    spec = os.path.join(BASE, 'NoteBook-Windows.spec')

    # 动态生成 spec 文件 —— 用 SPECPATH 动态算 BASE，避免硬编码路径的转义问题
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import os
BASE = SPECPATH

a = Analysis(
    ['main.py'],
    pathex=[BASE],
    binaries=[],
    datas=[
        (os.path.join(BASE, 'static'), 'static'),
        (os.path.join(BASE, 'templates'), 'templates'),
    ],
    hiddenimports=['flask', 'flask.templating', 'jinja2', 'jinja2.ext', 'webview', 'webview.platforms', 'webview.platforms.winforms'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='NoteBook',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(BASE, 'icon.ico'),
)
'''
    with open(spec, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print(f"   ✅ 已生成 {os.path.basename(spec)}")

    proc = subprocess.run(
        [venv_python, '-m', 'PyInstaller', spec,
         '--noconfirm', '--clean',
         '--distpath', dist_dir,
         '--workpath', work_dir],
        cwd=BASE, capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    if proc.returncode != 0:
        print("   ❌ 打包失败！")
        print(proc.stderr[-2000:])
        sys.exit(1)

    exe = os.path.join(dist_dir, 'NoteBook.exe')
    if not os.path.exists(exe):
        print("   ❌ 没找到 exe，打包可能部分失败")
        sys.exit(1)
    size_mb = os.path.getsize(exe) // 1024 // 1024
    print(f"   ✅ {exe} ({size_mb} MB)")
    return exe, dist_dir


def move_to_standard_dist(exe, dist_dir):
    step("📂  [4/6] 整理产物到 dist/windows/")
    final = os.path.join(BASE, 'dist', 'windows')
    os.makedirs(final, exist_ok=True)

    # 把 dist_windows/NoteBook.exe 移过去
    target_exe = os.path.join(final, 'NoteBook.exe')
    if os.path.exists(target_exe):
        os.remove(target_exe)
    shutil.move(exe, target_exe)

    # 可选：把 icon.ico 也复制一份到产物目录（方便用户查看）
    src_icon = os.path.join(BASE, 'icon.ico')
    dst_icon = os.path.join(final, 'icon.ico')
    if os.path.exists(src_icon):
        shutil.copy2(src_icon, dst_icon)

    print(f"   ✅ 产物目录: {final}")
    for f in os.listdir(final):
        fp = os.path.join(final, f)
        print(f"      {f}  ({os.path.getsize(fp):,} bytes)")

    # 清理中间目录
    for d in ['dist_windows', 'build_windows']:
        p = os.path.join(BASE, d)
        if os.path.exists(p):
            shutil.rmtree(p)
    spec = os.path.join(BASE, 'NoteBook-Windows.spec')
    if os.path.exists(spec):
        os.remove(spec)

    return final


def make_shortcut(final_dir):
    step("🔗  [5/6] 重建桌面快捷方式")
    try:
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        lnk_path = os.path.join(desktop, 'NoteBook.lnk')
        if os.path.exists(lnk_path):
            os.remove(lnk_path)

        exe_path = os.path.join(final_dir, 'NoteBook.exe')
        ps_code = f'''
$WshShell = New-Object -ComObject WScript.Shell
$sc = $WshShell.CreateShortcut("{lnk_path}")
$sc.TargetPath = "{exe_path}"
$sc.WorkingDirectory = "{final_dir}"
$sc.IconLocation = "{exe_path},0"
$sc.Description = "NoteBook - 本地离线笔记本"
$sc.Hotkey = "Ctrl+Alt+N"
$sc.Save()
'''
        ps = os.path.join(os.environ['SystemRoot'], 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
        subprocess.run([ps, '-NoProfile', '-Command', ps_code], capture_output=True)
        print(f"   ✅ 桌面快捷方式 -> {lnk_path}")
        print(f"      快捷键: Ctrl+Alt+N")
    except Exception as e:
        print(f"   (跳过快捷方式: {e})")


def refresh_icon_cache():
    step("🔄  [6/6] 刷新 Windows 图标缓存")
    try:
        # 广播 WM_SETTINGCHANGE
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, 0, 2, 1000, None)
        print("   ✅ 已通知资源管理器")
    except Exception as e:
        print(f"   (SendMessageTimeout: {e})")


def main():
    if sys.platform != 'win32':
        print("❌ rebuild_windows.py 只能在 Windows 上运行")
        sys.exit(1)

    gen_icons()
    clean()
    exe, dist_dir = build()
    final_dir = move_to_standard_dist(exe, dist_dir)
    make_shortcut(final_dir)
    refresh_icon_cache()

    print("\n" + "=" * 50)
    print("🎉  Windows 打包完成！")
    print(f"   产物: {os.path.join(final_dir, 'NoteBook.exe')}")
    print()
    print("   如果桌面/任务栏还是旧图标：")
    print("   Ctrl+Shift+Esc → 资源管理器 → 右键 → 重启")
    print("=" * 50)


if __name__ == '__main__':
    main()