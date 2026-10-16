# -*- coding: utf-8 -*-
"""
macOS 平台打包脚本
- 重新生成 icon.icns + icon_256.png
- PyInstaller --windowed 打包（产出 .app bundle）
- 可选：自动用 create-dmg 打包成 .dmg
- 产物统一放到 dist/macos/ 目录（与 windows 隔离）

注意：PyInstaller 不支持交叉编译，本脚本必须在 Mac 上运行

用法:
    python rebuild_macos.py                # 生成 .app
    python rebuild_macos.py --dmg          # 额外生成 .dmg（需安装 create-dmg）
"""
import os, sys, subprocess, shutil

BASE = os.path.dirname(os.path.abspath(__file__))


def step(msg):
    print(f"\n{msg}")
    print("-" * len(msg))


def gen_icons():
    step("🎨  [1/6] 重新生成 macOS 图标")
    from build_icons import generate_macos_icon
    icns, png = generate_macos_icon()
    print(f"   ✅ {icns}  ({os.path.getsize(icns):,} bytes)")
    print(f"   ✅ {png}   ({os.path.getsize(png):,} bytes)")


def clean():
    step("🧹  [2/6] 清理旧产物")
    for d in ['build_macos', 'dist_macos']:
        p = os.path.join(BASE, d)
        if os.path.exists(p):
            shutil.rmtree(p)
            print(f"   删除 {d}/")
    target = os.path.join(BASE, 'dist', 'macos')
    if os.path.exists(target):
        shutil.rmtree(target)
        print(f"   删除 dist/macos/")


def build():
    step("📦  [3/6] PyInstaller 打包（--windowed，约 60 秒）")
    sys.stdout.flush()

    # Mac 上 python3 + venv
    venv_python = os.path.join(BASE, 'venv', 'bin', 'python3')
    if not os.path.exists(venv_python):
        venv_python = 'python3'
        print("   (未找到 venv/bin/python3，使用系统 python3)")

    icon = os.path.join(BASE, 'icon.icns')
    main_py = os.path.join(BASE, 'main.py')
    dist_dir = os.path.join(BASE, 'dist_macos')
    work_dir = os.path.join(BASE, 'build_macos')
    spec = os.path.join(BASE, 'NoteBook-Mac.spec')

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
    hiddenimports=['flask', 'flask.templating', 'jinja2', 'jinja2.ext', 'webview', 'webview.platforms'],
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
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    name='NoteBook',
)
app = BUNDLE(
    coll,
    name='NoteBook.app',
    icon=os.path.join(BASE, 'icon.icns'),
    bundle_identifier='com.notebook.app',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
    },
)
'''
    with open(spec, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print(f"   ✅ 已生成 {os.path.basename(spec)}")

    cmd = [venv_python, '-m', 'PyInstaller', spec,
           '--noconfirm', '--clean',
           '--distpath', dist_dir,
           '--workpath', work_dir]

    proc = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if proc.returncode != 0:
        print("   ❌ 打包失败！")
        print(proc.stderr[-2000:])
        print("\nSTDOUT tail:")
        print(proc.stdout[-1500:])
        sys.exit(1)

    app_path = os.path.join(dist_dir, 'NoteBook.app')
    if not os.path.exists(app_path):
        print("   ❌ 没找到 .app bundle")
        sys.exit(1)

    # 估算 bundle 总大小
    total = 0
    for root, dirs, files in os.walk(app_path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    print(f"   ✅ NoteBook.app ({total // 1024 // 1024} MB)")
    return app_path, dist_dir


def move_to_standard_dist(app_path, dist_dir):
    step("📂  [4/6] 整理产物到 dist/macos/")
    final = os.path.join(BASE, 'dist', 'macos')
    os.makedirs(os.path.dirname(final), exist_ok=True)

    target = os.path.join(final, 'NoteBook.app')
    if os.path.exists(target):
        shutil.rmtree(target)
    shutil.move(app_path, target)

    # 复制一份 icon.icns 方便用户查看
    src_icon = os.path.join(BASE, 'icon.icns')
    dst_icon = os.path.join(final, 'icon.icns')
    if os.path.exists(src_icon):
        shutil.copy2(src_icon, dst_icon)

    print(f"   ✅ 产物目录: {final}")
    print(f"      NoteBook.app")

    # 清理中间目录
    for d in ['dist_macos', 'build_macos']:
        p = os.path.join(BASE, d)
        if os.path.exists(p):
            shutil.rmtree(p)
    spec = os.path.join(BASE, 'NoteBook-Mac.spec')
    if os.path.exists(spec):
        os.remove(spec)

    return final


def maybe_dmg(final_dir):
    step("💾  [5/6] 创建 DMG（--dmg 参数触发）")
    if '--dmg' not in sys.argv:
        print("   (未指定 --dmg，跳过。需要 dmg 再跑一次加 --dmg)")
        return
    try:
        subprocess.run(['create-dmg', '--version'], capture_output=True, check=True)
    except FileNotFoundError:
        print("   ❌ 未找到 create-dmg，请先 `brew install create-dmg`")
        return

    app = os.path.join(final_dir, 'NoteBook.app')
    dmg_path = os.path.join(final_dir, 'NoteBook.dmg')
    if os.path.exists(dmg_path):
        os.remove(dmg_path)

    cmd = [
        'create-dmg',
        '--volname', 'NoteBook',
        '--window-size', '480', '320',
        '--icon-size', '100',
        '--icon', 'NoteBook.app', '120', '160',
        '--hide-extension', 'NoteBook.app',
        '--app-drop-link', '360', '160',
        dmg_path,
        app,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        print(f"   ✅ {dmg_path}")
    else:
        print(f"   ❌ create-dmg 失败: {r.stderr}")


def xattr_cleanup(final_dir):
    step("🧽  [6/6] 清理 macOS 扩展属性")
    app = os.path.join(final_dir, 'NoteBook.app')
    try:
        subprocess.run(['xattr', '-cr', app], capture_output=True)
        print("   ✅ 已清理 com.apple.quarantine 等属性")
    except FileNotFoundError:
        print("   (xattr 不可用，跳过)")


def main():
    if sys.platform != 'darwin':
        print("❌ rebuild_macos.py 只能在 macOS 上运行")
        sys.exit(1)

    gen_icons()
    clean()
    app_path, dist_dir = build()
    final_dir = move_to_standard_dist(app_path, dist_dir)
    maybe_dmg(final_dir)
    xattr_cleanup(final_dir)

    print("\n" + "=" * 50)
    print("🎉  macOS 打包完成！")
    print(f"   产物: {os.path.join(final_dir, 'NoteBook.app')}")
    print()
    print("   首次运行: 右键 NoteBook.app → 打开")
    print("   （macOS 未签名 App 需要手动放行一次）")
    print("=" * 50)


if __name__ == '__main__':
    main()