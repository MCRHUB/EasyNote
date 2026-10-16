# -*- coding: utf-8 -*-
"""
跨平台图标生成模块
- 所有平台共用同一张"设计图"（Pillow 绘制）
- Windows -> icon.ico（手动拼 ICO，多尺寸 BMP 内嵌）
- macOS   -> icon.icns（Pillow 原生支持，多尺寸 PNG 内嵌）
- 额外产出 icon_256.png（Mac 开发模式窗口图标用）

调用方式:
    python build_icons.py           # 生成 ico + icns + png
    python build_icons.py --win     # 只生成 icon.ico
    python build_icons.py --mac     # 只生成 icon.icns + icon_256.png
"""
import os
import sys
import struct
from PIL import Image, ImageDraw


BASE = os.path.dirname(os.path.abspath(__file__))


def make_source_image(size):
    """
    绘制一张笔记本风格的图标（设计源头）
    返回 PIL.Image(RGBA)，尺寸 size x size
    """
    s = size
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # 渐变背景（深蓝 → 亮蓝）
    for y in range(s):
        t = y / s
        r = int(43 + (74 - 43) * t)
        g = int(87 + (144 - 87) * t)
        b = int(154 + (226 - 154) * t)
        d.line([(0, y), (s, y)], fill=(r, g, b, 255))

    # 圆角蒙层
    radius = int(s * 0.18)
    mask = Image.new('L', (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (s - 1, s - 1)], radius, fill=255)
    img.putalpha(mask)

    # 白色笔记本主体
    pad = int(s * 0.12)
    nb_left = pad + int(s * 0.06)
    nb_top = pad
    nb_right = s - pad
    nb_bottom = s - pad
    d.rounded_rectangle([nb_left, nb_top, nb_right, nb_bottom],
                        radius=int(s * 0.12), fill=(255, 255, 255, 245))

    # 折角（右上）
    fold_size = int(s * 0.18)
    d.polygon([(nb_right - fold_size, nb_top),
               (nb_right, nb_top),
               (nb_right, nb_top + fold_size)],
              fill=(220, 230, 245, 255))
    d.line([(nb_right - fold_size, nb_top), (nb_right - 1, nb_top + fold_size - 1)],
           fill=(180, 200, 230, 255), width=max(1, s // 128))

    # 蓝色装订竖线（左侧）
    bind_x = nb_left + int(s * 0.02)
    bind_w = max(2, int(s * 0.035))
    d.rectangle([bind_x, nb_top + int(s * 0.02),
                 bind_x + bind_w, nb_bottom - int(s * 0.02)],
                fill=(43, 87, 154, 255))

    # 浅灰色横线（模拟笔记本纸）
    line_color = (200, 215, 235, 120)
    gap = max(4, int(s * 0.12))
    sx = nb_left + int(s * 0.1)
    ex = nb_right - int(s * 0.04)
    first_y = nb_top + int(s * 0.18)
    for y in range(first_y, nb_bottom - int(s * 0.08), gap):
        d.line([(sx, y), (ex, y)], fill=line_color, width=max(1, s // 128))

    return img


def build_ico(images):
    """
    手动拼接标准 ICO 文件（BMP 内嵌），绕开 Pillow append_images 对 ICO 不生效的 bug。
    每个 image 为 PIL.Image(RGBA)。
    """
    num = len(images)
    header = struct.pack('<HHH', 0, 1, num)

    entry_bufs = []
    img_datas = []
    data_offset = 6 + 16 * num

    for img in images:
        s = img.size[0]
        rgba = img.convert('RGBA').transpose(Image.FLIP_TOP_BOTTOM)
        raw = rgba.tobytes('raw', 'BGRA')

        biSize = 40
        biWidth = s
        biHeight = s * 2
        biPlanes = 1
        biBitCount = 32
        biCompression = 0
        biSizeImage = len(raw) + (s * s // 8) * 2
        biXPelsPerMeter = 0
        biYPelsPerMeter = 0
        biClrUsed = 0
        biClrImportant = 0
        bmi = struct.pack('<IiiHHIIiiII',
                          biSize, biWidth, biHeight, biPlanes, biBitCount,
                          biCompression, biSizeImage,
                          biXPelsPerMeter, biYPelsPerMeter,
                          biClrUsed, biClrImportant)

        # AND 掩码（透明像素位为 1）
        alpha = img.split()[3].transpose(Image.FLIP_TOP_BOTTOM)
        mask_row_size = ((s + 31) // 32) * 4
        mask_bytes = bytearray()
        for y in range(s):
            row = alpha.crop((0, y, s, y + 1)).tobytes()
            byte_row = bytearray([0] * mask_row_size)
            for x in range(s):
                if row[x] < 128:
                    byte_row[x // 8] |= (0x80 >> (x % 8))
            mask_bytes.extend(byte_row)

        img_data = bmi + raw + bytes(mask_bytes)
        img_datas.append(img_data)

        w = 0 if s >= 256 else s
        h = 0 if s >= 256 else s
        entry = struct.pack('<BBBBHHII', w, h, 0, 0, 1, 32, len(img_data), data_offset)
        entry_bufs.append(entry)
        data_offset += len(img_data)

    return header + b''.join(entry_bufs) + b''.join(img_datas)


def generate_windows_icon():
    """生成 icon.ico（16/32/48/64/128/256 六尺寸）"""
    sizes = [16, 32, 48, 64, 128, 256]
    images = [make_source_image(s) for s in sizes]
    ico_bytes = build_ico(images)
    path = os.path.join(BASE, 'icon.ico')
    with open(path, 'wb') as f:
        f.write(ico_bytes)
    return path


def generate_macos_icon():
    """生成 icon.icns（Pillow 原生支持）+ icon_256.png"""
    # icns 需要的尺寸
    icns_sizes = [16, 32, 64, 128, 256, 512]  # Pillow ICNS 常见尺寸
    icns_images = [make_source_image(s) for s in icns_sizes]
    path = os.path.join(BASE, 'icon.icns')
    # Pillow IcnsImagePlugin.save 支持 sizes 参数
    icns_images[0].save(
        path, format='ICNS',
        sizes=[(s, s) for s in icns_sizes],
        append_images=icns_images[1:]
    )

    # 额外一张 256 PNG（Mac 开发模式 pywebview window.set_icon 需要）
    png_path = os.path.join(BASE, 'icon_256.png')
    make_source_image(256).save(png_path, format='PNG')

    return path, png_path


def generate_all():
    ico = generate_windows_icon()
    icns, png = generate_macos_icon()
    return ico, icns, png


def print_summary():
    for name in os.listdir(BASE):
        if name.startswith('icon.'):
            p = os.path.join(BASE, name)
            print(f'  {name:20s} {os.path.getsize(p):>8d} bytes')


if __name__ == '__main__':
    targets = sys.argv[1:]
    if '--win' in targets:
        p = generate_windows_icon()
        print(f'✅ Windows 图标: {p} ({os.path.getsize(p)} bytes)')
    elif '--mac' in targets:
        icns, png = generate_macos_icon()
        print(f'✅ macOS 图标:    {icns} ({os.path.getsize(icns)} bytes)')
        print(f'✅ 256x256 PNG:   {png} ({os.path.getsize(png)} bytes)')
    else:
        ico, icns, png = generate_all()
        print('✅ 全部图标生成完成:')
        print_summary()