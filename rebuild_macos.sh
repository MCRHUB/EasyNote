#!/bin/bash
# ================================================
#   NoteBook - macOS 一键打包
#   产物: dist/macos/NoteBook.app
#   用法:
#     ./rebuild_macos.sh             # 只生成 .app
#     ./rebuild_macos.sh --dmg       # 额外生成 .dmg
# ================================================

cd "$(dirname "$0")"

PYTHON="venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

if ! command -v $PYTHON &>/dev/null; then
    echo "❌ 未找到 python3，请先安装 Python 3.11+"
    exit 1
fi

$PYTHON rebuild_macos.py "$@"