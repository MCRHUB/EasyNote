/* ================================================================
 * NoteBook 前端主脚本 - 修复版
 * ================================================================ */

const state = {
    notebooks: [],
    activeNotebookId: null,
    activePageId: null,
    expandedIds: new Set(),
    isEditMode: true,
    saveTimer: null,
    _modeToken: 0,
};

const $ = (id) => document.getElementById(id);
const notebookListEl = $('notebook-list');
const pageTitleEl = $('page-title');
const editorEl = $('editor');
const previewEl = $('preview');
const saveStatusEl = $('save-status');
const fileImageEl = $('file-image');
const toastEl = $('toast');
const toolbarEl = $('toolbar');

function toast(msg, type = 'info', duration = 1800) {
    toastEl.textContent = msg;
    toastEl.className = 'toast show' + (type === 'error' ? ' error' : '');
    clearTimeout(toast._t);
    toast._t = setTimeout(() => { toastEl.className = 'toast'; }, duration);
}

async function api(url, options = {}) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    return await res.json();
}

async function apiFetch(url, options = {}) {
    const res = await fetch(url, options);
    return await res.json();
}

function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = String(s ?? '');
    return div.innerHTML;
}

let _savedRange = null;
function saveEditorSelection() {
    editorEl.focus();
    const sel = window.getSelection();
    if (sel.rangeCount > 0) {
        const range = sel.getRangeAt(0);
        if (editorEl.contains(range.commonAncestorContainer)) {
            _savedRange = range.cloneRange();
            return true;
        }
    }
    _savedRange = null;
    return false;
}
function restoreEditorSelection() {
    if (!_savedRange) return false;
    editorEl.focus();
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(_savedRange);
    return true;
}

const modal = {
    confirm(options) {
        const opts = typeof options === 'string'
            ? { title: '提示', message: options, danger: false }
            : { title: '提示', danger: false, confirmText: '确定', cancelText: '取消', ...options };
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.innerHTML = `
                <div class="modal-box" role="dialog">
                    <div class="modal-header">
                        <div class="modal-title">
                            <span>${opts.danger ? '⚠️' : '📌'}</span>
                            <span>${escapeHtml(opts.title)}</span>
                        </div>
                        <button class="modal-close" title="关闭">✕</button>
                    </div>
                    <div class="modal-body">
                        <p>${escapeHtml(opts.message).replace(/\n/g, '<br>')}</p>
                    </div>
                    <div class="modal-footer">
                        <button class="modal-btn modal-btn-default" data-act="cancel">${escapeHtml(opts.cancelText || '取消')}</button>
                        <button class="modal-btn ${opts.danger ? 'modal-btn-danger' : 'modal-btn-primary'}" data-act="ok">${escapeHtml(opts.confirmText || '确定')}</button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
            const close = (result) => { overlay.remove(); resolve(result); };
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) close(false);
                else if (e.target.matches('[data-act="ok"]')) close(true);
                else if (e.target.matches('[data-act="cancel"], .modal-close')) close(false);
            });
        });
    },

    prompt(options) {
        const opts = typeof options === 'string'
            ? { title: '输入', message: options, value: '' }
            : { title: '输入', value: '', ...options };
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.innerHTML = `
                <div class="modal-box" role="dialog">
                    <div class="modal-header">
                        <div class="modal-title">
                            <span>✏️</span>
                            <span>${escapeHtml(opts.title)}</span>
                        </div>
                        <button class="modal-close" title="关闭">✕</button>
                    </div>
                    <div class="modal-body">
                        ${opts.message ? `<p>${escapeHtml(opts.message)}</p>` : ''}
                        <input type="text" value="${escapeHtml(opts.value ?? '')}" placeholder="${escapeHtml(opts.placeholder || '')}" />
                    </div>
                    <div class="modal-footer">
                        <button class="modal-btn modal-btn-default" data-act="cancel">取消</button>
                        <button class="modal-btn modal-btn-primary" data-act="ok">确定</button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
            const input = overlay.querySelector('input');
            setTimeout(() => input.focus(), 50);
            const close = (result) => { overlay.remove(); resolve(result); };
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) close(null);
                else if (e.target.matches('[data-act="ok"]')) close(input.value.trim());
                else if (e.target.matches('[data-act="cancel"], .modal-close')) close(null);
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') close(input.value.trim());
                else if (e.key === 'Escape') close(null);
            });
        });
    },

    tablePicker() {
        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.innerHTML = `
                <div class="modal-box" role="dialog">
                    <div class="modal-header">
                        <div class="modal-title">
                            <span>▦</span>
                            <span>插入表格</span>
                        </div>
                        <button class="modal-close" title="关闭">✕</button>
                    </div>
                    <div class="modal-body">
                        <p style="text-align:center;color:#666;">先悬停预览，然后<strong>点击任意格</strong>锁定行列数，最后点"插入"</p>
                        <div class="table-grid-info">请选择行列</div>
                        <div class="table-grid-picker" id="grid-picker"></div>
                    </div>
                    <div class="modal-footer">
                        <button class="modal-btn modal-btn-default" data-act="cancel">取消</button>
                        <button class="modal-btn modal-btn-primary" data-act="ok">插入</button>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);

            const GRID_COLS = 10;
            const GRID_ROWS = 8;
            const grid = overlay.querySelector('#grid-picker');
            const info = overlay.querySelector('.table-grid-info');
            let hoverCols = 0, hoverRows = 0;
            let finalCols = 0, finalRows = 0;
            let locked = false;

            function renderPreview(cols, rows) {
                hoverCols = cols;
                hoverRows = rows;
                [...grid.children].forEach((el) => {
                    const rr = parseInt(el.dataset.row, 10);
                    const cc = parseInt(el.dataset.col, 10);
                    const cond = rr <= rows && cc <= cols;
                    el.classList.toggle('hovered', cond && !locked);
                    el.classList.toggle('selected', cond && locked);
                });
                if (locked) info.textContent = cols + ' 列 × ' + rows + ' 行 ✓ 已锁定';
                else info.textContent = cols + ' 列 × ' + rows + ' 行';
            }

            for (let r = 0; r < GRID_ROWS; r++) {
                for (let c = 0; c < GRID_COLS; c++) {
                    const cell = document.createElement('div');
                    cell.className = 'cell';
                    cell.dataset.row = r + 1;
                    cell.dataset.col = c + 1;
                    cell.addEventListener('mouseenter', () => {
                        if (locked) return;
                        const rr = parseInt(cell.dataset.row, 10);
                        const cc = parseInt(cell.dataset.col, 10);
                        renderPreview(cc, rr);
                    });
                    cell.addEventListener('click', () => {
                        const rr = parseInt(cell.dataset.row, 10);
                        const cc = parseInt(cell.dataset.col, 10);
                        finalCols = cc;
                        finalRows = rr;
                        locked = true;
                        renderPreview(cc, rr);
                    });
                    grid.appendChild(cell);
                }
            }

            const close = (result) => { overlay.remove(); resolve(result); };
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) close(null);
                else if (e.target.matches('.modal-close, [data-act="cancel"]')) close(null);
                else if (e.target.matches('[data-act="ok"]')) {
                    const c = locked ? finalCols : hoverCols;
                    const r = locked ? finalRows : hoverRows;
                    if (c === 0 || r === 0) {
                        toast('请先在网格上点击选择行列', 'error');
                        return;
                    }
                    close({ cols: c, rows: r });
                }
            });
        });
    },
};

window.addEventListener('DOMContentLoaded', async () => {
    bindToolbarEvents();
    bindSidebarEvents();
    bindGlobalEvents();

    await loadAll();

    if (state.notebooks.length === 0) {
        toast('首次使用，已为你创建默认笔记本');
        await createDefaultData();
        return;
    }

    const firstNb = state.notebooks[0];
    state.expandedIds.add(firstNb.id);
    state.activeNotebookId = firstNb.id;

    if (firstNb.pages.length > 0) {
        await selectPage(firstNb.pages[0].id);
    } else {
        await handleNewPage(firstNb.id);
    }
    renderSidebar();
});

async function createDefaultData() {
    const nbRes = await api('/api/notebooks', {
        method: 'POST',
        body: JSON.stringify({ name: '我的笔记本' }),
    });
    if (nbRes.code !== 0) { toast('初始化失败', 'error'); return; }

    const nbId = nbRes.data.id;
    await loadAll();
    state.expandedIds.add(nbId);
    state.activeNotebookId = nbId;

    const pageRes = await api('/api/notebooks/' + nbId + '/pages', {
        method: 'POST',
        body: JSON.stringify({ title: '欢迎使用 NoteBook' }),
    });
    await loadAll();
    await selectPage(pageRes.data.id);
}

async function loadAll() {
    const nbRes = await api('/api/notebooks');
    if (nbRes.code !== 0) {
        toast('加载笔记本失败', 'error');
        return;
    }

    state.notebooks = await Promise.all(
        nbRes.data.map(async (nb) => {
            const pRes = await api('/api/notebooks/' + nb.id + '/pages');
            return { ...nb, pages: pRes.data || [] };
        })
    );

    renderSidebar();
}

function findPage(pageId) {
    for (const nb of state.notebooks) {
        for (const p of nb.pages) {
            if (p.id === pageId) return p;
        }
    }
    return null;
}

function findNotebook(nbId) {
    return state.notebooks.find(n => n.id === nbId);
}

function renderSidebar() {
    notebookListEl.innerHTML = '';

    if (state.notebooks.length === 0) {
        notebookListEl.innerHTML =
            '<li style="padding:20px;text-align:center;color:#aaa;">还没有笔记本，点击上方 + 新建</li>';
        return;
    }

    for (const nb of state.notebooks) {
        const isActiveNb = state.activeNotebookId === nb.id;
        const isExpanded = state.expandedIds.has(nb.id);

        const nbLi = document.createElement('li');
        nbLi.className = 'notebook-item' + (isActiveNb ? ' active' : '') + (isExpanded ? '' : ' collapsed');

        const header = document.createElement('div');
        header.className = 'notebook-header';
        header.innerHTML = `
            <span class="notebook-arrow">▼</span>
            <span class="notebook-name">📁 ${escapeHtml(nb.name)}</span>
            <span class="nb-actions">
                <button title="重命名"   data-act="rename-nb">✎</button>
                <button title="新建页面" data-act="new-page">+页</button>
                <button title="删除笔记本" data-act="del-nb">🗑</button>
            </span>
        `;
        header.addEventListener('click', (e) => {
            const actBtn = e.target.closest('[data-act]');
            if (actBtn) {
                handleNotebookAction(nb.id, actBtn.dataset.act);
                e.stopPropagation();
                return;
            }
            toggleExpand(nb.id);
            state.activeNotebookId = nb.id;
            renderSidebar();
        });
        nbLi.appendChild(header);

        const pageUl = document.createElement('ul');
        pageUl.className = 'page-list';

        for (const pg of nb.pages) {
            const pgLi = document.createElement('li');
            pgLi.className = 'page-item' + (state.activePageId === pg.id ? ' active' : '');
            pgLi.innerHTML = `
                <span class="page-title">📄 ${escapeHtml(pg.title || '未命名笔记')}</span>
                <span class="page-actions">
                    <button title="编辑模式" data-pg-mode="edit" data-pg-id="${pg.id}"
                        ${state.activePageId === pg.id && state.isEditMode ? 'class="active-mode"' : ''}>✏️</button>
                    <button title="查看模式" data-pg-mode="view"  data-pg-id="${pg.id}"
                        ${state.activePageId === pg.id && !state.isEditMode ? 'class="active-mode"' : ''}>👁</button>
                    <button title="删除此页面" class="danger" data-pg-del="${pg.id}">🗑</button>
                </span>
            `;
            pgLi.addEventListener('click', (e) => {
                const modeBtn = e.target.closest('[data-pg-mode]');
                if (modeBtn) {
                    const mode = modeBtn.dataset.pgMode;
                    selectPage(parseInt(modeBtn.dataset.pgId, 10), mode === 'edit');
                    e.stopPropagation();
                    return;
                }
                if (e.target.hasAttribute('data-pg-del')) {
                    handleDeletePage(parseInt(e.target.dataset.pgDel, 10));
                    e.stopPropagation();
                    return;
                }
                selectPage(pg.id, true);
            });
            pageUl.appendChild(pgLi);
        }

        const newPgLi = document.createElement('li');
        newPgLi.className = 'page-item new-page-quick';
        newPgLi.style.color = '#2b579a';
        newPgLi.innerHTML = '<span class="page-title">＋ 新建页面</span>';
        newPgLi.addEventListener('click', () => handleNewPage(nb.id));
        pageUl.appendChild(newPgLi);

        nbLi.appendChild(pageUl);
        notebookListEl.appendChild(nbLi);
    }
}

function toggleExpand(nbId) {
    if (state.expandedIds.has(nbId)) {
        state.expandedIds.delete(nbId);
    } else {
        state.expandedIds.add(nbId);
    }
}

function bindSidebarEvents() {
    $('btn-new-notebook').addEventListener('click', handleNewNotebook);
    $('btn-toggle-side').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('collapsed');
    });
}

function bindGlobalEvents() {
    $('btn-save').addEventListener('click', () => savePage(true));
    $('btn-refresh').addEventListener('click', refreshCurrentPage);

    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            savePage(true);
        }
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'r') {
            e.preventDefault();
            refreshCurrentPage();
        }
    });

    $('btn-mode-edit').addEventListener('click', () => switchMode(true));
    $('btn-mode-preview').addEventListener('click', () => switchMode(false));

    editorEl.addEventListener('input', () => {
        scheduleAutoSave();
        updateSaveStatus('正在编辑…');
    });
    pageTitleEl.addEventListener('input', () => {
        scheduleAutoSave();
        updateSaveStatus('正在编辑…');
    });

    window.addEventListener('beforeunload', () => { savePageSync(); });

    fileImageEl.addEventListener('change', onImageFileChange);

    editorEl.addEventListener('contextmenu', (e) => {
        const cell = e.target.closest('td, th');
        if (cell) {
            e.preventDefault();
            showTableCellMenu(e.clientX, e.clientY, cell);
        }
    });
    document.addEventListener('click', hideTableCellMenu);
    document.addEventListener('scroll', hideTableCellMenu, true);
}

async function handleNewNotebook() {
    const name = await modal.prompt({
        title: '新建笔记本',
        message: '请输入笔记本名称（用于分类）：',
        value: '新笔记本',
    });
    if (!name) return;

    const r = await api('/api/notebooks', {
        method: 'POST',
        body: JSON.stringify({ name }),
    });
    if (r.code !== 0) return toast('创建失败：' + r.msg, 'error');

    toast('笔记本已创建');
    state.activeNotebookId = r.data.id;
    state.expandedIds.add(r.data.id);

    await loadAll();
    await handleNewPage(r.data.id);
}

async function handleNotebookAction(nbId, act) {
    if (act === 'rename-nb') {
        const nb = findNotebook(nbId);
        if (!nb) return;
        const name = await modal.prompt({
            title: '重命名笔记本',
            value: nb.name,
        });
        if (!name) return;
        const r = await api('/api/notebooks/' + nbId, {
            method: 'PUT',
            body: JSON.stringify({ name }),
        });
        if (r.code !== 0) return toast('重命名失败', 'error');
        toast('已重命名');
        await loadAll();
    } else if (act === 'new-page') {
        handleNewPage(nbId);
    } else if (act === 'del-nb') {
        handleDeleteNotebook(nbId);
    }
}

async function handleDeleteNotebook(nbId) {
    const nb = findNotebook(nbId);
    if (!nb) return;
    const ok = await modal.confirm({
        title: '删除笔记本',
        message: '确定删除笔记本「' + nb.name + '」？\n其中所有页面和图片都将被永久删除，无法恢复。',
        danger: true,
    });
    if (!ok) return;

    const r = await api('/api/notebooks/' + nbId, { method: 'DELETE' });
    if (r.code !== 0) return toast('删除失败', 'error');
    toast('已删除');

    if (state.activeNotebookId === nbId) {
        state.activeNotebookId = null;
        state.activePageId = null;
        state.expandedIds.delete(nbId);
        clearEditor();
    }
    await loadAll();

    if (state.notebooks.length > 0 && !state.activePageId) {
        const firstNb = state.notebooks[0];
        state.activeNotebookId = firstNb.id;
        state.expandedIds.add(firstNb.id);
        if (firstNb.pages.length > 0) {
            await selectPage(firstNb.pages[0].id);
        }
        renderSidebar();
    }
}

async function handleNewPage(nbId) {
    const r = await api('/api/notebooks/' + nbId + '/pages', {
        method: 'POST',
        body: JSON.stringify({ title: '未命名笔记' }),
    });
    if (r.code !== 0) return toast('创建失败', 'error');

    state.activeNotebookId = nbId;
    state.expandedIds.add(nbId);

    await loadAll();
    await selectPage(r.data.id);
    toast('已新建页面，可以开始写了');
}

async function handleDeletePage(pageId) {
    const page = findPage(pageId);
    if (!page) return;
    const ok = await modal.confirm({
        title: '删除页面',
        message: '确定删除页面「' + (page.title || '未命名笔记') + '」吗？',
        danger: true,
    });
    if (!ok) return;

    const r = await api('/api/pages/' + pageId, { method: 'DELETE' });
    if (r.code !== 0) return toast('删除失败', 'error');
    toast('已删除');

    const wasActive = state.activePageId === pageId;
    const nbIdOfDeleted = page.notebook_id;

    await loadAll();

    if (wasActive) {
        state.activePageId = null;
        const nb = findNotebook(nbIdOfDeleted);
        if (nb && nb.pages.length > 0) {
            await selectPage(nb.pages[0].id);
        } else {
            clearEditor();
        }
    }
}

async function selectPage(pageId, forceEdit) {
    if (state.activePageId && state.activePageId !== pageId) {
        await savePage(false, true);
    }

    state.activePageId = pageId;

    const r = await api('/api/pages/' + pageId);
    if (r.code !== 0) { toast('页面加载失败', 'error'); return; }
    const page = r.data;

    state.activeNotebookId = page.notebook_id;
    state.expandedIds.add(page.notebook_id);

    pageTitleEl.value = page.title || '';
    const content = page.content || '<p><br></p>';
    editorEl.innerHTML = content;
    previewEl.innerHTML = content;

    if (forceEdit === true) switchMode(true);
    else if (forceEdit === false) switchMode(false);

    updateSaveStatus('已保存');
    renderSidebar();
}

function clearEditor() {
    pageTitleEl.value = '';
    editorEl.innerHTML = '<p><br></p>';
    previewEl.innerHTML = '';
    updateSaveStatus('');
}

async function refreshCurrentPage() {
    if (!state.activePageId) {
        toast('请先选择一个页面', 'error');
        return;
    }
    clearTimeout(state.saveTimer);
    await savePage(true, true);
    await loadAll();
    const page = findPage(state.activePageId);
    if (page) {
        pageTitleEl.value = page.title || '';
        const content = page.content || '<p><br></p>';
        editorEl.innerHTML = content;
        previewEl.innerHTML = content;
        updateSaveStatus('已从数据库刷新');
        toast('已刷新 ✓');
    }
}

function scheduleAutoSave() {
    clearTimeout(state.saveTimer);
    state.saveTimer = setTimeout(() => savePage(), 1500);
}

async function savePage(isManual = false, silent = false) {
    if (!state.activePageId) return;

    const content = state.isEditMode ? editorEl.innerHTML : previewEl.innerHTML;
    const title = pageTitleEl.value.trim() || '未命名笔记';

    updateSaveStatus('保存中…');
    try {
        const r = await api('/api/pages/' + state.activePageId, {
            method: 'PUT',
            body: JSON.stringify({ title, content }),
        });
        if (r.code !== 0) {
            updateSaveStatus('保存失败');
            if (!silent) toast('保存失败：' + r.msg, 'error');
            return;
        }
        updateSaveStatus('已保存');
        if (isManual && !silent) toast('已保存 ✓');

        const page = findPage(state.activePageId);
        if (page) { page.title = title; renderSidebar(); }
    } catch (e) {
        updateSaveStatus('保存失败');
        if (!silent) toast('保存失败', 'error');
    }
}

function savePageSync() {
    if (!state.activePageId) return;
    const content = state.isEditMode ? editorEl.innerHTML : previewEl.innerHTML;
    const title = pageTitleEl.value.trim() || '未命名笔记';
    navigator.sendBeacon && navigator.sendBeacon(
        '/api/pages/' + state.activePageId,
        JSON.stringify({ title, content })
    );
}

function updateSaveStatus(text) {
    saveStatusEl.textContent = text;
    saveStatusEl.className = 'save-status';
    if (text === '已保存') saveStatusEl.classList.add('saved');
    else if (text.includes('保存中')) saveStatusEl.classList.add('saving');
}

function switchMode(toEdit) {
    const myToken = ++state._modeToken;
    state.isEditMode = toEdit;
    $('btn-mode-edit').classList.toggle('active', toEdit);
    $('btn-mode-preview').classList.toggle('active', !toEdit);
    toolbarEl.style.display = toEdit ? 'flex' : 'none';

    if (toEdit) {
        editorEl.innerHTML = previewEl.innerHTML || '<p><br></p>';
        editorEl.style.display = 'block';
        previewEl.style.display = 'none';
        editorEl.focus();
    } else {
        savePage(false, true).then(() => {
            if (state._modeToken !== myToken) return;
            previewEl.innerHTML = editorEl.innerHTML;
            editorEl.style.display = 'none';
            previewEl.style.display = 'block';
        });
    }
}

function bindToolbarEvents() {
    document.querySelectorAll('.tool-btn[data-cmd]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            execCmd(btn.dataset.cmd, null, btn.dataset.arg || null);
        });
    });

    $('color-fore').addEventListener('input', (e) => {
        execCmd('foreColor', null, e.target.value);
    });
    $('color-back').addEventListener('input', (e) => {
        execCmd('hiliteColor', null, e.target.value);
    });

    $('select-heading').addEventListener('change', (e) => {
        execCmd('formatBlock', null, '<' + e.target.value + '>');
        e.target.selectedIndex = 0;
    });
    $('select-fontsize').addEventListener('change', (e) => {
        execCmd('fontSize', null, e.target.value);
    });

    $('btn-insert-table').addEventListener('click', insertTableDialog);
    $('btn-insert-image').addEventListener('click', () => fileImageEl.click());
    $('btn-insert-link').addEventListener('click', async () => {
        saveEditorSelection();
        const url = await modal.prompt({
            title: '插入链接',
            message: '请输入链接地址：',
            value: 'https://',
        });
        if (!url) return;
        restoreEditorSelection();
        ensureEditorSelection();

        const sel = window.getSelection();
        const range = sel.getRangeAt(0);
        const selectedText = range.toString().trim();

        if (selectedText) {
            range.deleteContents();
        }
        const a = document.createElement('a');
        a.href = url;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.textContent = selectedText || url;
        range.insertNode(a);

        range.setStartAfter(a);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
        editorEl.focus();
        scrollToCaret();
        scheduleAutoSave();
    });
}

function ensureEditorSelection() {
    editorEl.focus();
    const sel = window.getSelection();
    if (sel.rangeCount > 0) {
        const r = sel.getRangeAt(0);
        if (editorEl.contains(r.commonAncestorContainer)) return;
    }
    const range = document.createRange();
    range.selectNodeContents(editorEl);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
}

function scrollToCaret() {
    const sel = window.getSelection();
    if (!sel.rangeCount) return;
    try {
        const range = sel.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return;
        const editorRect = editorEl.getBoundingClientRect();
        const offset = rect.top - editorRect.top;
        if (offset > editorEl.clientHeight * 0.8 || offset < 0) {
            editorEl.scrollTop += offset - editorEl.clientHeight * 0.3;
        }
    } catch (e) {}
}

function execCmd(cmd, ui = null, value = null) {
    try {
        ensureEditorSelection();

        if (cmd === 'insertHorizontalRule' || cmd === 'horizontalRule') {
            insertHtmlAtCursor('<hr><p><br></p>');
            return;
        }

        document.execCommand(cmd, !!ui, value);
    } catch (e) {
        console.warn('execCommand error:', cmd, e);
    }
    scheduleAutoSave();
}

function insertHtmlAtCursor(html) {
    ensureEditorSelection();
    const sel = window.getSelection();
    if (sel.rangeCount === 0) return;
    const range = sel.getRangeAt(0);
    range.deleteContents();
    const temp = document.createElement('div');
    temp.innerHTML = html;
    const frag = document.createDocumentFragment();
    let node;
    while ((node = temp.firstChild)) frag.appendChild(node);
    range.insertNode(frag);
    range.collapse(false);
    sel.removeAllRanges();
    sel.addRange(range);
    editorEl.focus();
    scrollToCaret();
    scheduleAutoSave();
}

async function insertTableDialog() {
    saveEditorSelection();
    const result = await modal.tablePicker();
    if (!result) return;
    restoreEditorSelection();
    const cols = result.cols;
    const rows = result.rows;

    let html = '<table><tbody>';
    for (let r = 0; r < rows; r++) {
        html += '<tr>';
        for (let c = 0; c < cols; c++) {
            html += (r === 0) ? '<th>&nbsp;</th>' : '<td>&nbsp;</td>';
        }
        html += '</tr>';
    }
    html += '</tbody></table><p><br></p>';

    insertHtmlAtCursor(html);
    toast('已插入 ' + cols + '×' + rows + ' 表格');
}

let _tableMenuEl = null;
function hideTableCellMenu() {
    if (_tableMenuEl) { _tableMenuEl.remove(); _tableMenuEl = null; }
}
function showTableCellMenu(x, y, cell) {
    hideTableCellMenu();
    const menu = document.createElement('div');
    menu.className = 'table-cell-menu';
    menu.innerHTML = `
        <div data-act="insert-row-above">⬆ 在上方插入行</div>
        <div data-act="insert-row-below">⬇ 在下方插入行</div>
        <div data-act="insert-col-left">⬅ 在左侧插入列</div>
        <div data-act="insert-col-right">➡ 在右侧插入列</div>
        <div class="sep"></div>
        <div data-act="delete-row" class="danger">🗑 删除此行</div>
        <div data-act="delete-col" class="danger">🗑 删除此列</div>
        <div data-act="delete-table" class="danger">❌ 删除整个表格</div>
    `;
    document.body.appendChild(menu);
    const maxX = window.innerWidth - menu.offsetWidth - 10;
    const maxY = window.innerHeight - menu.offsetHeight - 10;
    menu.style.left = Math.min(x, maxX) + 'px';
    menu.style.top = Math.min(y, maxY) + 'px';
    _tableMenuEl = menu;

    menu.addEventListener('click', (e) => {
        const act = e.target.dataset.act;
        if (!act) return;
        handleTableCellAction(act, cell);
        hideTableCellMenu();
    });
}
function handleTableCellAction(act, cell) {
    const table = cell.closest('table');
    if (!table) return;
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody ? tbody.children : table.querySelectorAll('tr'));
    const rowIdx = rows.indexOf(cell.parentElement);
    const cellsInRow = Array.from(cell.parentElement.children);
    const colIdx = cellsInRow.indexOf(cell);

    switch (act) {
        case 'insert-row-above':
        case 'insert-row-below': {
            const count = rows[0].children.length;
            const newTr = document.createElement('tr');
            for (let i = 0; i < count; i++) {
                const newTd = document.createElement(rowIdx === 0 ? 'th' : 'td');
                newTd.innerHTML = '&nbsp;';
                newTr.appendChild(newTd);
            }
            const refNode = (act === 'insert-row-above') ? rows[rowIdx] : rows[rowIdx].nextSibling;
            (tbody || table).insertBefore(newTr, refNode);
            break;
        }
        case 'insert-col-left':
        case 'insert-col-right': {
            rows.forEach((tr, ri) => {
                const newCell = document.createElement(ri === 0 ? 'th' : 'td');
                newCell.innerHTML = '&nbsp;';
                const cells = Array.from(tr.children);
                const ref = (act === 'insert-col-left') ? cells[colIdx] : cells[colIdx].nextSibling;
                tr.insertBefore(newCell, ref);
            });
            break;
        }
        case 'delete-row': {
            if (rows.length <= 1) { toast('不能删除最后一行', 'error'); return; }
            rows[rowIdx].remove();
            break;
        }
        case 'delete-col': {
            if (rows[0].children.length <= 1) { toast('不能删除最后一列', 'error'); return; }
            rows.forEach(tr => { tr.children[colIdx].remove(); });
            break;
        }
        case 'delete-table': {
            table.remove();
            break;
        }
    }
    scheduleAutoSave();
}

async function onImageFileChange(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    if (file.size > 8 * 1024 * 1024) {
        toast('图片不能超过 8MB', 'error');
        fileImageEl.value = '';
        return;
    }

    updateSaveStatus('图片上传中…');
    try {
        const formData = new FormData();
        formData.append('file', file);
        if (state.activePageId) formData.append('page_id', state.activePageId);

        const r = await apiFetch('/api/upload/image', {
            method: 'POST',
            body: formData,
        });
        if (r.code !== 0) {
            toast('上传失败：' + r.msg, 'error');
            updateSaveStatus('上传失败');
            return;
        }

        const imgUrl = r.data.url;
        insertHtmlAtCursor('<img src="' + imgUrl + '" alt="image">');
        toast('图片已插入');
    } catch (err) {
        toast('上传失败：网络错误', 'error');
        updateSaveStatus('上传失败');
    } finally {
        fileImageEl.value = '';
    }
}