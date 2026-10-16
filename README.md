# 📒 NoteBook

一款 **完全本地离线** 的轻量级笔记本桌面应用，对标 OneNote。  
基于 **Python + Flask + PyWebView** 技术栈，零外部服务依赖，所有数据（笔记、图片）全部存储在你自己的电脑上。

支持 **Windows** 和 **macOS**，两端代码一份，分别在各自平台上打包。

---

## ✨ 功能特性

### 📚 笔记管理
- **笔记本（分类）** 功能：支持新建、重命名、删除，按笔记本分类管理所有页面
- **页面（笔记）** 功能：每个笔记本下可创建任意多的笔记页面
- **自动保存**：编辑 1.5 秒后自动保存，也支持 `Ctrl+S` / `Cmd+S` 手动立即保存
- **实时状态**：右上角显示"保存中… / 已保存 / 保存失败"

### ✍️ 富文本编辑
- **格式化**：加粗 / 斜体 / 下划线 / 删除线
- **颜色**：文字颜色 + 高亮颜色（背景色）
- **标题**：正文 / H1 / H2 / H3 / H4 快速切换
- **字体大小**：4 / 5 / 6 / 7（Small → XX-Large）
- **对齐**：左对齐 / 居中 / 右对齐 / 两端对齐
- **列表**：有序列表 / 无序列表 / 缩进 / 反缩进
- **撤销 / 重做 / 清除格式**

### 📐 插入元素
| 元素 | 说明 |
|---|---|
| 🖼 **图片** | 点击工具栏按钮上传本地图片（支持 PNG/JPG/GIF/BMP/WEBP，单张最大 8MB） |
| 🔗 **链接** | 输入 URL 插入超链接；有选中文字则用选中文字作为链接文本，无选中则用 URL 本身 |
| ▦ **表格** | 可视化网格选择器，鼠标悬停预览，点击锁定行列数，自动生成带表头的表格 |
| ― **分割线** | 插入水平分割线 |
| ↶ / ↷ | 撤销 / 重做 |

### 🔲 表格高级操作
右键点击任意表格单元格，弹出菜单：
- ⬆ 在上方插入行 / ⬇ 在下方插入行
- ⬅ 在左侧插入列 / ➡ 在右侧插入列
- 🗑 删除此行 / 🗑 删除此列
- ❌ 删除整个表格

### 👁 预览 / 编辑模式
- 顶部工具栏"✏️ 编辑 / 👁 预览"按钮切换
- 侧边栏每个页面也有 ✏️ / 👁 图标直接进入对应模式
- **预览模式**：纯阅读，工具栏隐藏
- **编辑模式**：可输入内容，工具栏显示

---

## 🚀 快速启动

### 方式 1：打包后的可执行文件（推荐给普通用户）

#### Windows
1. 拿到 `dist/windows/NoteBook.exe`（及同级的 `notebook.db` / `uploads/`，如果有数据的话）
2. ❌ 不要放到任何名字包含 `Program Files` 的目录——Windows 会拒绝写入权限
3. ✅ 推荐路径：`D:\NoteBook\`、`E:\MyApps\NoteBook\`
4. 双击 `NoteBook.exe` 启动

#### macOS
1. 拿到 `dist/macos/NoteBook.app`（或 `.dmg`）
2. 拖到"应用程序"文件夹（或 `~/Applications/`）
3. 首次运行**右键 NoteBook.app → 打开**（macOS Gatekeeper 未签名 App 需要手动放行一次）
4. 之后双击即可

### 方式 2：开发模式（需要 Python 环境）

```bash
# 1. 进入项目目录
cd NoteBook

# 2. 创建虚拟环境
python3 -m venv venv          # macOS / Linux
python -m venv venv           # Windows

# 3. 激活虚拟环境
source venv/bin/activate      # macOS / Linux
.\venv\Scripts\activate       # Windows PowerShell

# 4. 安装依赖
pip install -r requirements.txt

# 5. 启动
python main.py
```

启动后 PyWebView 会自动打开一个桌面窗口，**不会启动系统浏览器**。

---

## ⌨️ 快捷键

| 快捷键 | Windows | macOS | 功能 |
|---|---|---|---|
| 立即保存 | `Ctrl+S` | `Cmd+S` | 手动立即保存当前页面 |
| 刷新页面 | `Ctrl+R` | `Cmd+R` | 从数据库刷新当前页面（覆盖未保存修改） |
| 全局呼出 | `Ctrl+Alt+N` | ⌘+N（需自行设置） | 随时呼出 NoteBook |

---

## 📦 平台打包（分开管理，互不覆盖）

PyInstaller **不支持跨平台交叉编译**——Windows 上只能产出 `.exe`，macOS 上只能产出 `.app`。  
打包产物统一放到 `dist/<platform>/` 目录下，两个平台完全隔离。

### 🪟 Windows 打包

```bash
# 方式 A：双击 rebuild_windows.bat
# 方式 B：命令行
cd NoteBook
.\venv\Scripts\python.exe rebuild_windows.py
```

**产物**：`dist/windows/NoteBook.exe`（约 16 MB，单文件，无黑框）

脚本自动完成：
1. 生成多尺寸 `icon.ico`（16/32/48/64/128/256）
2. PyInstaller `--onefile --console=False` 打包
3. 在桌面重建快捷方式（目标 exe 同级图标，快捷键 `Ctrl+Alt+N`）
4. 广播 `WM_SETTINGCHANGE` 通知资源管理器刷新图标缓存

### 🍎 macOS 打包

```bash
# 方式 A：命令行
cd NoteBook
python3 rebuild_macos.py          # 只生成 .app
python3 rebuild_macos.py --dmg    # 额外生成 .dmg

# 方式 B：双击 rebuild_macos.sh（需 chmod +x rebuild_macos.sh 首次）
./rebuild_macos.sh
./rebuild_macos.sh --dmg
```

**产物**：`dist/macos/NoteBook.app`（可选 `NoteBook.dmg`）

脚本自动完成：
1. 生成多尺寸 `icon.icns`（16/32/64/128/256/512）+ `icon_256.png`
2. PyInstaller `--windowed` 打包为 `.app bundle`
3. 清理 macOS 扩展属性（`com.apple.quarantine` 等）
4. `--dmg` 时调用 `create-dmg`（需 `brew install create-dmg`）生成 DMG

### 产物目录结构

```
dist/
├── windows/
│   ├── NoteBook.exe      # Windows 最终可执行文件（单文件）
│   └── icon.ico          # 打包时用的图标（备份）
│
└── macos/
    ├── NoteBook.app      # macOS 应用 bundle
    ├── NoteBook.dmg      # 可选：DMG 分发包
    └── icon.icns         # 打包时用的图标（备份）
```

两端**完全隔离**，不会互相覆盖。把 `dist/` 目录整体复制到另一台同平台机器上即可使用。

---

## 📁 项目结构

```
NoteBook/
├── main.py                     # 程序入口（启动 Flask + PyWebView，跨平台）
├── app.py                      # Flask 后端（路由 + API）
├── db.py                       # SQLite 数据库操作
├── config.py                   # 配置（端口、路径、上传限制等）
├── build_icons.py              # 共用图标生成（一源两形：.ico + .icns）
├── rebuild_windows.py          # Windows 打包脚本（一键）
├── rebuild_windows.bat         # Windows 打包入口（双击）
├── rebuild_macos.py            # macOS 打包脚本（一键）
├── rebuild_macos.sh            # macOS 打包入口
├── icon.ico                    # Windows 图标（Pillow 生成，多尺寸）
├── icon.icns                   # macOS 图标（Pillow 生成，多尺寸）
├── icon_256.png                # 256×256 PNG（Mac 开发模式用）
├── requirements.txt            # 依赖列表
│
├── templates/
│   └── index.html              # 主页面模板
│
├── static/
│   ├── css/style.css           # 样式
│   └── js/app.js               # 前端主脚本
│
├── dist/                       # 打包产物（跨平台分开）
│   ├── windows/                # Windows 产物
│   └── macos/                  # macOS 产物
│
├── notebook.db                 # SQLite 数据库（首次运行自动创建）
└── uploads/                    # 图片存储目录（首次运行自动创建）
```

---

## ⚙️ 配置项（config.py）

| 配置 | 默认值 | 说明 |
|---|---|---|
| `FLASK_HOST` | `127.0.0.1` | Flask 监听地址（仅本机） |
| `FLASK_PORT` | `5000` | Flask 监听端口 |
| `IMAGE_STORAGE_MODE` | `filesystem` | 图片存储：`filesystem`（本地文件夹）或 `base64`（存数据库） |
| `MAX_CONTENT_LENGTH` | `8MB` | 单张图片上传限制 |
| `ALLOWED_IMAGE_EXTENSIONS` | `png/jpg/jpeg/gif/bmp/webp` | 允许的图片扩展名 |
| `SECRET_KEY` | `notebook-offline-secret-key-change-me` | Flask Session 密钥 |

---

## ⚠️ 各平台注意事项

### 🪟 Windows

| 项目 | 说明 |
|---|---|
| **WebView2 Runtime** | Windows 11 自带；Windows 10 需手动装（缺 runtime 时 PyWebView 会 fallback 到 IE，富文本体验变差）→ [下载链接](https://developer.microsoft.com/microsoft-edge/webview2/) |
| **杀毒误报** | PyInstaller onefile 首次解压可能被 360 / 火绒等误报。加白名单即可 |
| **不要放到 "Program Files"** | 任何含该字样的目录都有权限限制（D 盘也一样）。推荐 `D:\NoteBook\` |
| **图标缓存顽固** | 打包后桌面/任务栏如果还是旧图标：按 `Ctrl+Shift+Esc` → 重启"Windows 资源管理器" |
| **数据备份** | 复制 `notebook.db` + `uploads/` 两个文件/目录即可 |

### 🍎 macOS

| 项目 | 说明 |
|---|---|
| **Gatekeeper 拦截** | 未签名 App 首次打开会被拦截。**右键 NoteBook.app → 打开** → 再点"打开"即可；或终端执行 `xattr -cr NoteBook.app` |
| **签名 & 公证** | 如果分发给他人/上架 App Store，需要 Apple Developer ID（$99/年）+ 苹果公证流程。未签名 App 个人自用完全没问题 |
| **PyWebView 后端** | 默认使用系统 WKWebView（Mac 8000+ 全系统支持，无需额外安装） |
| **数据位置** | 默认与 `.app` bundle **同级**（例如把 NoteBook.app 放在 `~/MyApps/`，数据就在那里）。想遵循 macOS 规范可以改 `config.py` 让它存到 `~/Library/Application Support/NoteBook/` |
| **DMG 制作** | 需先装 `brew install create-dmg`，打包时加 `--dmg` 参数 |

---

## 🧩 技术栈

| 层 | 技术 |
|---|---|
| 前端 | 原生 HTML/CSS/JavaScript（零框架） |
| 富文本编辑 | `contenteditable` + `document.execCommand` |
| 后端 | Flask |
| 数据库 | SQLite（单文件，零配置） |
| 桌面容器 | PyWebView（Windows: edgechromium；macOS: cocoa + WKWebView） |
| 打包 | PyInstaller（Windows: onefile；macOS: --windowed .app） |
| 图标生成 | Pillow（自定义 ICO 结构拼接，绕开 Pillow ICO 的 append_images bug） |

---

## 📝 许可证

本项目采用 [MIT License](LICENSE) 授权，可自由使用、修改、分发，包括商业用途。

详见 [LICENSE](LICENSE) 文件。