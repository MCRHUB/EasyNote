# -*- coding: utf-8 -*-
"""
Flask Web 服务主应用
仅监听 127.0.0.1，作为 PyWebView 的本地后端
"""
import os
import sys
import uuid
import base64
import mimetypes
from flask import Flask, jsonify, request, send_from_directory, abort
import config
import db


def detect_image_format(data: bytes) -> str | None:
    """
    通过文件头字节判断图片格式（替代 Python 3.11 移除的 imghdr）
    返回 'png' / 'jpeg' / 'gif' / 'bmp' / 'webp' / None
    """
    if not data:
        return None
    h = data[:12]
    if h[:4] == b'\x89PNG':
        return 'png'
    if h[:2] == b'\xff\xd8':
        return 'jpeg'
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if h[:2] == b'BM':
        return 'bmp'
    if h[:4] == b'RIFF' and h[8:12] == b'WEBP':
        return 'webp'
    return None


def create_app():
    """创建 Flask 应用"""
    app = Flask(
        __name__,
        static_folder=get_resource_path('static'),
        template_folder=get_resource_path('templates'),
    )
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        traceback.print_exc()
        return jsonify({'code': -1, 'msg': str(e)}), 500

    # ========== 前端页面路由 ==========

    @app.route('/')
    def index():
        """主页面"""
        from flask import render_template
        return render_template('index.html')

    # ========== 笔记本 API ==========

    @app.route('/api/notebooks', methods=['GET'])
    def api_list_notebooks():
        """获取所有笔记本列表"""
        return jsonify({'code': 0, 'data': db.list_notebooks()})

    @app.route('/api/notebooks', methods=['POST'])
    def api_create_notebook():
        """新建笔记本"""
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get('name') or '').strip() or '新笔记本'
        nid = db.create_notebook(name)
        return jsonify({'code': 0, 'data': {'id': nid, 'name': name}})

    @app.route('/api/notebooks/<int:notebook_id>', methods=['PUT'])
    def api_rename_notebook(notebook_id):
        """重命名笔记本"""
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'code': 1, 'msg': '名称不能为空'}), 400
        db.rename_notebook(notebook_id, name)
        return jsonify({'code': 0})

    @app.route('/api/notebooks/<int:notebook_id>', methods=['DELETE'])
    def api_delete_notebook(notebook_id):
        """
        删除笔记本
        filesystem 模式下需要先删除关联图片文件
        """
        # 收集所有要删除的图片文件路径
        pages = db.list_pages(notebook_id)
        paths_to_delete = []
        for p in pages:
            for img in db.get_images_by_page(p['id']):
                if img['storage_mode'] == 'filesystem' and img['file_path']:
                    full = os.path.join(config.UPLOAD_FOLDER, img['file_path'])
                    paths_to_delete.append(full)

        db.delete_notebook(notebook_id)

        # 删除物理文件
        for f in paths_to_delete:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                print('[WARN] 删除图片文件失败:', f, e)

        return jsonify({'code': 0})

    # ========== 页面 API ==========

    @app.route('/api/notebooks/<int:notebook_id>/pages', methods=['GET'])
    def api_list_pages(notebook_id):
        """获取某个笔记本下的所有页面"""
        return jsonify({'code': 0, 'data': db.list_pages(notebook_id)})

    @app.route('/api/notebooks/<int:notebook_id>/pages', methods=['POST'])
    def api_create_page(notebook_id):
        """新建笔记页面"""
        data = request.get_json(force=True, silent=True) or {}
        title = (data.get('title') or '').strip() or '未命名笔记'
        pid = db.create_page(notebook_id, title)
        return jsonify({'code': 0, 'data': {'id': pid, 'title': title}})

    @app.route('/api/pages/<int:page_id>', methods=['GET'])
    def api_get_page(page_id):
        """获取页面详情"""
        page = db.get_page(page_id)
        if not page:
            return jsonify({'code': 1, 'msg': '页面不存在'}), 404
        return jsonify({'code': 0, 'data': page})

    @app.route('/api/pages/<int:page_id>', methods=['PUT'])
    def api_update_page(page_id):
        """保存页面（标题 + 富文本内容）"""
        data = request.get_json(force=True, silent=True) or {}
        title = data.get('title')
        content = data.get('content')
        db.update_page(page_id, title=title, content=content)
        return jsonify({'code': 0})

    @app.route('/api/pages/<int:page_id>', methods=['DELETE'])
    def api_delete_page(page_id):
        """
        删除页面（级联删除图片记录 + 物理文件）
        """
        paths_to_delete = []
        for img in db.get_images_by_page(page_id):
            if img['storage_mode'] == 'filesystem' and img['file_path']:
                full = os.path.join(config.UPLOAD_FOLDER, img['file_path'])
                paths_to_delete.append(full)

        db.delete_page(page_id)

        for f in paths_to_delete:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                print('[WARN] 删除图片文件失败:', f, e)

        return jsonify({'code': 0})

    # ========== 图片上传 API ==========

    @app.route('/api/upload/image', methods=['POST'])
    def api_upload_image():
        """
        上传图片
        前端通过 multipart/form-data 上传，字段名 'file'
        可选字段 'page_id' 用于关联到某个页面
        返回 image_id 和可直接插入富文本的 URL（或 data URI）
        """
        if 'file' not in request.files:
            return jsonify({'code': 1, 'msg': '未找到上传文件'}), 400

        f = request.files['file']
        if not f or f.filename == '':
            return jsonify({'code': 1, 'msg': '文件名为空'}), 400

        # 校验扩展名
        ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
        if ext not in config.ALLOWED_IMAGE_EXTENSIONS:
            return jsonify({'code': 1, 'msg': '不支持的图片格式'}), 400

        # 读取字节
        raw = f.read()

        # 用文件头字节进一步校验图片格式（宽松处理，判断失败也允许继续）
        detect_image_format(raw)
        mime = mimetypes.types_map.get('.' + ext, 'image/' + ext)

        # 生成唯一文件名，避免冲突
        safe_name = f"{uuid.uuid4().hex}.{ext}"

        storage_mode = config.IMAGE_STORAGE_MODE
        url_for_editor = ''

        if storage_mode == 'base64':
            # 方案1：base64 存入数据库
            b64 = base64.b64encode(raw).decode('ascii')
            data_uri = f'data:{mime};base64,{b64}'
            img_id = db.save_image_record(
                filename=safe_name,
                storage_mode='base64',
                base64_data=data_uri,
                page_id=request.form.get('page_id', type=int),
            )
            url_for_editor = data_uri  # 直接把 data URI 塞进编辑器 <img src>

        else:
            # 方案2：保存到本地文件夹
            os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
            dest_path = os.path.join(config.UPLOAD_FOLDER, safe_name)
            with open(dest_path, 'wb') as out:
                out.write(raw)
            img_id = db.save_image_record(
                filename=safe_name,
                storage_mode='filesystem',
                file_path=safe_name,
                page_id=request.form.get('page_id', type=int),
            )
            # 通过后端路由访问图片（避免跨域 / file:// 等问题）
            url_for_editor = f'/api/image/{img_id}'

        return jsonify({
            'code': 0,
            'data': {
                'image_id': img_id,
                'url': url_for_editor,
                'storage_mode': storage_mode,
            }
        })

    @app.route('/api/image/<int:image_id>')
    def api_get_image(image_id):
        """读取图片（仅 filesystem 模式需要）"""
        record = db.get_image_by_id(image_id)
        if not record:
            abort(404)

        if record['storage_mode'] == 'base64':
            # base64 模式：直接重定向到 data URI（浏览器支持）
            if record['base64_data']:
                from flask import redirect
                return redirect(record['base64_data'])
            abort(404)

        # filesystem 模式：从 uploads 目录发送
        if record['file_path']:
            return send_from_directory(
                os.path.abspath(config.UPLOAD_FOLDER),
                record['file_path']
            )
        abort(404)

    return app


# ============ 资源路径辅助函数 ============

def get_resource_path(rel):
    """
    获取 Flask 模板/静态资源的真实路径
    - 开发环境：当前目录下对应子目录
    - PyInstaller 打包后：sys._MEIPASS 解压目录（包含打包进去的静态文件）
      注意：数据库和 uploads 用的是 exe 所在目录（get_base_dir）
      静态资源（html/js/css）是只读的，应该用 sys._MEIPASS
    """
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel)


# ============ 启动入口 ============

if __name__ == '__main__':
    db.init_db()
    app = create_app()
    # debug=False，避免 PyWebView 下 reloader 导致进程冲突
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False, use_reloader=False)