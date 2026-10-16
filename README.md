# 📒 NoteBook

一款 **完全本地离线** 的轻量级笔记本桌面应用，对标 OneNote。  
基于 **Python + Flask + PyWebView** 技术栈，零外部服务依赖，所有数据（笔记、图片）全部存储在你自己的电脑上。

---

## ✨ 功能特性

### 📚 笔记管理
- **笔记本（分类）** 功能：支持新建、重命名、删除，按笔记本分类管理所有页面
- **页面（笔记）** 功能：每个笔记本下可创建任意多的笔记页面
- **自动保存**：编辑 1.5 秒后自动保存，也支持 `Ctrl+S` 手动立即保存
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

### 方式 1：打包后的 EXE（推荐给普通用户）
1. 把 `dist/NoteBook.exe`（及同级的 `notebook.db` / `uploads/`，如果有数据的话）放到任意非 "Program Files" 目录
   - ❌ 不要放到任何名字包含 `Program Files` 的目录（不管 C/D 盘）—— Windows 会拒绝写入权限，导致无法保存
   - ✅ 推荐路径：`D:\NoteBook\`、`E:\MyApps\NoteBook\` 等
2. 双击 `NoteBook.exe` 启动（带自定义图标，无黑框）
3. 可选：右键 exe → 发送到 → 桌面快捷方式；再右键快捷方式 → 属性 → 快捷键（如 `Ctrl+Alt+N`）

### 方式 2：开发模式（需要 Python 环境）
```bash
# 1. 进入项目目录
cd e:\VsCode\NoteBook

# 2. 创建虚拟环境（首次）
python -m venv venv
.\venv\Scripts\activate        # Windows PowerShell

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动（双击 start.bat 或手动运行）
.\venv\Scripts\python.exe main.py
```

启动后 PyWebView 会自动打开一个桌面窗口，**不会启动系统浏览器**。

---

## ⌨️ 快捷键

| 快捷键 | 功能 |
|---|---|
| `Ctrl+S` | 手动立即保存当前页面 |
| `Ctrl+R` | 从数据库刷新当前页面（覆盖未保存修改） |
| `Ctrl+Alt+N` | **全局快捷键**（需自行设置快捷方式），随时呼出 NoteBook |

---

## 📦 打包成 EXE

项目已自带 PyInstaller 打包配置（`build.spec`），一键打包：

```bash
cd e:\VsCode\NoteBook
.\venv\Scripts\python.exe -m PyInstaller build.spec --noconfirm
```

产物位置：`dist/NoteBook.exe`

### 打包配置说明
| 项 | 说明 |
|---|---|
| 单文件 | `onefile` 模式，15MB 左右，双击即用 |
| 无黑框 | `console=False`，完全静默 |
| 自定义图标 | `icon.ico`（渐变蓝色笔记本，多尺寸） |
| 静态资源 | `static/` + `templates/` 内嵌到 exe |
| 数据持久化 | `notebook.db` + `uploads/` 与 exe **同级**，方便用户备份 |

### 重新生成图标（可选）
```bash
.\venv\Scripts\python.exe -c "from make_icon import *; ..."
# 或直接运行项目根目录的 make_icon.py（已自动删除，如需重新生成请再创建）
```

---

## 📁 项目结构

```
NoteBook/
├── main.py                 # 程序入口（启动 Flask + PyWebView）
├── app.py                  # Flask 后端（路由 + API）
├── db.py                   # SQLite 数据库操作
├── config.py               # 配置（端口、路径、上传限制等）
├── build.spec              # PyInstaller 打包配置
├── icon.ico                # 应用图标（渐变蓝色笔记本）
├── requirements.txt        # 依赖列表
├── start.bat               # 双击启动脚本
├── start_silent.vbs        # 完全静默启动（无黑框，用 pythonw）
├── create_shortcut.ps1     # 一键生成桌面快捷方式 + 快捷键
├── README.md               # 本文档
│
├── templates/
│   └── index.html          # 主页面模板
│
├── static/
│   ├── css/style.css       # 样式（含 Modal、表格菜单等）
│   └── js/app.js           # 前端主脚本（状态管理、编辑器、API 调用）
│
├── dist/                   # 打包产物目录
│   └── NoteBook.exe        # 最终可执行文件
│
├── notebook.db             # SQLite 数据库（首次运行自动创建）
└── uploads/                # 图片存储目录（首次运行自动创建）
```

---

## ⚙️ 配置项（config.py）

| 配置 | 默认值 | 说明 |
|---|---|---|
| `FLASK_HOST` | `127.0.0.1` | Flask 监听地址（仅本机） |
| `FLASK_PORT` | `5000` | Flask 监听端口 |
| `IMAGE_STORAGE_MODE` | `filesystem` | 图片存储方式：`filesystem`（本地文件夹）或 `base64`（存入数据库） |
| `MAX_CONTENT_LENGTH` | `8MB` | 单张图片上传限制 |
| `ALLOWED_IMAGE_EXTENSIONS` | `png/jpg/jpeg/gif/bmp/webp` | 允许的图片扩展名 |
| `SECRET_KEY` | `notebook-offline-secret-key-change-me` | Flask Session 密钥 |

---

## ⚠️ 注意事项

### 1. WebView2 Runtime（Windows 10 用户）
- **Windows 11 自带** WebView2 Runtime，无需额外安装
- **Windows 10** 如果没装，PyWebView 会 fallback 到 IE（mshtml），富文本编辑体验会变差
- 建议手动安装：[Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/)

### 2. 杀毒软件误报
PyInstaller `onefile` 模式首次启动时，部分杀软（360、火绒等）可能误报为病毒。  
**原因**：onefile 模式会把自身解压到临时目录执行，这是 PyInstaller 的标准行为。  
**解决**：把 exe 加到杀软白名单即可。

### 3. 数据备份
所有数据都与 exe 同级：
- `notebook.db` — 笔记数据库
- `uploads/` — 图片文件夹

**备份 = 复制这两个文件/目录**，非常简单。

### 4. 不要放到 "Program Files"
Windows 对任何名字含 `Program Files` 的目录都有特殊权限保护，普通用户无法写入。  
即使在 D 盘也一样（`D:\Program Files\XXX` 同样有权限限制）。  
**推荐路径**：`D:\NoteBook\`、`E:\MyApps\NoteBook\`。

---

## 🧩 技术栈

| 层 | 技术 |
|---|---|
| 前端 | 原生 HTML/CSS/JavaScript（零框架） |
| 富文本编辑 | `contenteditable` + `document.execCommand` |
| 后端 | Flask |
| 数据库 | SQLite（单文件，零配置） |
| 桌面容器 | PyWebView（edgechromium 后端，基于系统 WebView2） |
| 打包 | PyInstaller（onefile 单文件模式） |
| 图标生成 | Pillow |

---

## 📝 许可证

本项目采用 [MIT License](LICENSE) 授权，可自由使用、修改、分发，包括商业用途。

详见 [LICENSE](LICENSE) 文件。