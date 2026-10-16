# -*- coding: utf-8 -*-
"""一键重新生成图标 + 重新打包 + 重建快捷方式 + 刷新 Windows 图标缓存"""
import os, sys, subprocess, ctypes, shutil, struct, io

BASE = os.path.dirname(os.path.abspath(__file__))

# ========== 1. 生成好看的新 icon.ico ==========
print("🎨  正在生成新图标...")
from PIL import Image, ImageDraw

def make_icon(size):
    s = size
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    for y in range(s):
        t = y / s
        r = int(43 + (74 - 43) * t)
        g = int(87 + (144 - 87) * t)
        b = int(154 + (226 - 154) * t)
        d.line([(0, y), (s, y)], fill=(r, g, b, 255))

    radius = int(s * 0.18)
    mask = Image.new('L', (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (s - 1, s - 1)], radius, fill=255)
    img.putalpha(mask)

    pad = int(s * 0.12)
    nb_left = pad + int(s * 0.06)
    nb_top = pad
    nb_right = s - pad
    nb_bottom = s - pad
    d.rounded_rectangle([nb_left, nb_top, nb_right, nb_bottom],
                        radius=int(s * 0.12), fill=(255, 255, 255, 245))

    fold_size = int(s * 0.18)
    d.polygon([(nb_right - fold_size, nb_top),
               (nb_right, nb_top),
               (nb_right, nb_top + fold_size)],
              fill=(220, 230, 245, 255))

    d.line([(nb_right - fold_size, nb_top), (nb_right - 1, nb_top + fold_size - 1)],
           fill=(180, 200, 230, 255), width=max(1, s // 128))

    bind_x = nb_left + int(s * 0.02)
    bind_w = max(2, int(s * 0.035))
    d.rectangle([bind_x, nb_top + int(s * 0.02),
                 bind_x + bind_w, nb_bottom - int(s * 0.02)],
                fill=(43, 87, 154, 255))

    line_color = (200, 215, 235, 120)
    gap = max(4, int(s * 0.12))
    sx = nb_left + int(s * 0.1)
    ex = nb_right - int(s * 0.04)
    first_y = nb_top + int(s * 0.18)
    for y in range(first_y, nb_bottom - int(s * 0.08), gap):
        d.line([(sx, y), (ex, y)], fill=line_color, width=max(1, s // 128))

    return img

def build_ico(images):
    """手动拼接标准 ICO 文件（BMP 内嵌），绕开 Pillow append_images 的 bug"""
    num = len(images)
    header = struct.pack('<HHH', 0, 1, num)

    # 先把每张图转成 BMP（从 BITMAPINFOHEADER 开始，无文件头）
    entry_bufs = []
    img_datas = []
    data_offset = 6 + 16 * num  # ICO header + N directory entries

    for img in images:
        s = img.size[0]
        # 把 RGBA 转成 BGRA（BMP 位图数组的行序是 BGR）
        rgba = img.convert('RGBA')
        # 翻转 Y 轴（BMP 自底向上存）
        rgba = rgba.transpose(Image.FLIP_TOP_BOTTOM)
        raw = rgba.tobytes('raw', 'BGRA')

        biSize = 40          # BITMAPINFOHEADER
        biWidth = s
        biHeight = s * 2     # ICO 里高度要 *2（包含掩码）
        biPlanes = 1
        biBitCount = 32
        biCompression = 0
        biSizeImage = len(raw) + (s * s // 8) * 2   # 像素 + 2 层掩码（每像素 1bit）
        biXPelsPerMeter = 0
        biYPelsPerMeter = 0
        biClrUsed = 0
        biClrImportant = 0

        bmi = struct.pack('<IiiHHIIiiII',
                          biSize, biWidth, biHeight, biPlanes, biBitCount,
                          biCompression, biSizeImage,
                          biXPelsPerMeter, biYPelsPerMeter,
                          biClrUsed, biClrImportant)

        # AND 掩码（全 0 = 不透明；这里 RGBA 的 alpha 已经处理了透明度，
        # 但 ICO 格式要求掩码必须有，所以也用 alpha 通道生成）
        alpha = img.split()[3]
        # 翻转 Y
        alpha = alpha.transpose(Image.FLIP_TOP_BOTTOM)
        # 每行填充到 4 字节对齐
        mask_row_size = ((s + 31) // 32) * 4
        mask_bytes = bytearray()
        for y in range(s):
            row = alpha.crop((0, y, s, y + 1)).tobytes()
            byte_row = bytearray([0] * mask_row_size)
            for x in range(s):
                if row[x] < 128:  # 透明
                    byte_row[x // 8] |= (0x80 >> (x % 8))
            mask_bytes.extend(byte_row)

        img_data = bmi + raw + bytes(mask_bytes)
        img_datas.append(img_data)

        # directory entry
        w = 0 if s >= 256 else s
        h = 0 if s >= 256 else s
        entry = struct.pack('<BBBBHHII',
                            w, h, 0, 0, 1, 32, len(img_data), data_offset)
        entry_bufs.append(entry)
        data_offset += len(img_data)

    return header + b''.join(entry_bufs) + b''.join(img_datas)

SIZES = [16, 32, 48, 64, 128, 256]
icons = [make_icon(s) for s in SIZES]
icon_path = os.path.join(BASE, 'icon.ico')
ico_bytes = build_ico(icons)
with open(icon_path, 'wb') as f:
    f.write(ico_bytes)
print(f"   ✅ icon.ico ({os.path.getsize(icon_path)} bytes, {len(SIZES)} 个尺寸)")

# ========== 2. 清理旧产物 ==========
print("\n🧹  清理旧产物...")
for d in ['build', 'dist']:
    p = os.path.join(BASE, d)
    if os.path.exists(p):
        shutil.rmtree(p)
        print(f"   删除 {d}/")

# ========== 3. 重新打包 ==========
print("\n📦  PyInstaller 打包中（约 30 秒）...")
sys.stdout.flush()
venv_python = os.path.join(BASE, 'venv', 'Scripts', 'python.exe')
proc = subprocess.run(
    [venv_python, '-m', 'PyInstaller', 'build.spec', '--noconfirm'],
    cwd=BASE, capture_output=True, text=True, encoding='utf-8', errors='replace'
)
if proc.returncode != 0:
    print("   ❌ 打包失败！")
    print(proc.stderr[-1500:])
    print("\n完整日志：")
    print(proc.stdout[-1000:])
    sys.exit(1)

exe_path = os.path.join(BASE, 'dist', 'NoteBook.exe')
size_mb = os.path.getsize(exe_path) // 1024 // 1024
print(f"   ✅ {exe_path} ({size_mb} MB)")

# ========== 4. 重建桌面快捷方式 ==========
print("\n🔗  重建桌面快捷方式...")
desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
lnk_path = os.path.join(desktop, 'NoteBook.lnk')
if os.path.exists(lnk_path):
    os.remove(lnk_path)

# 用 PowerShell 重建
ps_code = f'''
$WshShell = New-Object -ComObject WScript.Shell
$sc = $WshShell.CreateShortcut("{lnk_path}")
$sc.TargetPath = "{exe_path}"
$sc.WorkingDirectory = "{os.path.dirname(exe_path)}"
$sc.IconLocation = "{exe_path},0"
$sc.Description = "NoteBook - 本地离线笔记本"
$sc.Hotkey = "Ctrl+Alt+N"
$sc.Save()
'''
ps_path = os.path.join(os.environ['SystemRoot'], 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
subprocess.run([ps_path, '-NoProfile', '-Command', ps_code], capture_output=True)
print(f"   ✅ {lnk_path}")

# ========== 5. 刷新 Windows 图标缓存 ==========
print("\n🔄  刷新 Windows 图标缓存...")
try:
    # 广播 WM_SETTINGCHANGE 通知资源管理器
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, 0, 2, 1000, None)
    print("   ✅ 已通知资源管理器")
except Exception as e:
    print(f"   (SendMessageTimeout 失败: {e})")

print("\n" + "=" * 50)
print("🎉  全部完成！")
print()
print("   请双击 dist\\NoteBook.exe 查看新图标")
print("   如果桌面/任务栏还是旧图标：")
print("   按 Ctrl+Shift+Esc 打开任务管理器")
print("   → 找到 Windows 资源管理器 → 右键 → 重启")
print("=" * 50)