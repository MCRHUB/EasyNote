# -*- coding: utf-8 -*-
"""
SQLite 数据库操作模块
数据库文件：notebook.db（单文件，位于项目根目录/exe 同级目录）
"""
import sqlite3
import os
import time
import config


def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(config.DB_PATH)
    # 让 sqlite3 返回字典而不是元组，方便操作
    conn.row_factory = sqlite3.Row
    # 启用外键约束
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def init_db():
    """初始化数据库，创建所有表"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.executescript("""
            -- 笔记本表
            CREATE TABLE IF NOT EXISTS notebooks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                created_at  INTEGER NOT NULL,
                updated_at  INTEGER NOT NULL
            );

            -- 笔记页面表
            CREATE TABLE IF NOT EXISTS pages (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                notebook_id INTEGER NOT NULL,
                title       TEXT    NOT NULL DEFAULT '未命名笔记',
                content     TEXT    NOT NULL DEFAULT '',
                created_at  INTEGER NOT NULL,
                updated_at  INTEGER NOT NULL,
                FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
            );

            -- 图片资源表（两种存储方案都存一条记录，方便统一管理）
            CREATE TABLE IF NOT EXISTS images (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                page_id     INTEGER,
                filename    TEXT    NOT NULL,
                storage_mode TEXT   NOT NULL,   -- 'base64' 或 'filesystem'
                file_path   TEXT,               -- filesystem 模式：相对路径；base64 模式：NULL
                base64_data TEXT,               -- base64 模式：完整 data URI；filesystem 模式：NULL
                created_at  INTEGER NOT NULL,
                FOREIGN KEY (page_id) REFERENCES pages(id) ON DELETE SET NULL
            );

            -- 创建索引，加速查询
            CREATE INDEX IF NOT EXISTS idx_pages_notebook ON pages(notebook_id);
            CREATE INDEX IF NOT EXISTS idx_images_page    ON images(page_id);
        """)
        conn.commit()
        print('[DB] 数据库初始化完成:', config.DB_PATH)
    finally:
        conn.close()


# ==================== 笔记本相关 ====================

def create_notebook(name):
    """新建笔记本"""
    now = int(time.time())
    conn = get_connection()
    try:
        cur = conn.execute(
            'INSERT INTO notebooks (name, created_at, updated_at) VALUES (?, ?, ?)',
            (name, now, now)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_notebooks():
    """列出所有笔记本（按 id 升序）"""
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT * FROM notebooks ORDER BY id ASC'
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def rename_notebook(notebook_id, name):
    """重命名笔记本"""
    now = int(time.time())
    conn = get_connection()
    try:
        conn.execute(
            'UPDATE notebooks SET name = ?, updated_at = ? WHERE id = ?',
            (name, now, notebook_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_notebook(notebook_id):
    """
    删除笔记本（同时级联删除该笔记本下所有页面及其图片）
    PyWebView 侧需要先删除关联图片文件（filesystem 模式）
    这里只处理数据库级别的删除
    """
    conn = get_connection()
    try:
        conn.execute('DELETE FROM notebooks WHERE id = ?', (notebook_id,))
        conn.commit()
    finally:
        conn.close()


# ==================== 页面相关 ====================

def create_page(notebook_id, title='未命名笔记'):
    """新建笔记页面"""
    now = int(time.time())
    conn = get_connection()
    try:
        cur = conn.execute(
            'INSERT INTO pages (notebook_id, title, content, created_at, updated_at) '
            'VALUES (?, ?, ?, ?, ?)',
            (notebook_id, title, '', now, now)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_page(page_id):
    """获取单个页面详情"""
    conn = get_connection()
    try:
        row = conn.execute('SELECT * FROM pages WHERE id = ?', (page_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_pages(notebook_id):
    """列出某个笔记本下的所有页面"""
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT * FROM pages WHERE notebook_id = ? ORDER BY updated_at DESC',
            (notebook_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_page(page_id, title=None, content=None):
    """更新页面标题和/或内容"""
    now = int(time.time())
    conn = get_connection()
    try:
        # 动态构建 SET 子句，只更新传入了的字段
        fields = ['updated_at = ?']
        values = [now]
        if title is not None:
            fields.append('title = ?')
            values.append(title)
        if content is not None:
            fields.append('content = ?')
            values.append(content)
        values.append(page_id)
        sql = f'UPDATE pages SET {", ".join(fields)} WHERE id = ?'
        conn.execute(sql, values)
        conn.commit()
    finally:
        conn.close()


def delete_page(page_id):
    """
    删除页面（数据库级）
    关联图片的物理文件删除由外层 app.py 负责
    """
    conn = get_connection()
    try:
        conn.execute('DELETE FROM pages WHERE id = ?', (page_id,))
        conn.commit()
    finally:
        conn.close()


# ==================== 图片相关 ====================

def save_image_record(filename, storage_mode, file_path=None, base64_data=None, page_id=None):
    """保存一条图片记录"""
    now = int(time.time())
    conn = get_connection()
    try:
        cur = conn.execute(
            'INSERT INTO images (page_id, filename, storage_mode, file_path, base64_data, created_at) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (page_id, filename, storage_mode, file_path, base64_data, now)
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_image_by_id(image_id):
    """根据 id 获取图片记录"""
    conn = get_connection()
    try:
        row = conn.execute('SELECT * FROM images WHERE id = ?', (image_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_images_by_page(page_id):
    """获取某个页面关联的所有图片记录"""
    conn = get_connection()
    try:
        rows = conn.execute(
            'SELECT * FROM images WHERE page_id = ?', (page_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_image_record(image_id):
    """删除图片数据库记录"""
    conn = get_connection()
    try:
        conn.execute('DELETE FROM images WHERE id = ?', (image_id,))
        conn.commit()
    finally:
        conn.close()