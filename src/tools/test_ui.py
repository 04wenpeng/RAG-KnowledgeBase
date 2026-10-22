# -*- coding: utf-8 -*-
"""界面结构自检：确认两个页面渲染出左右分区、关键元素齐全。

用法：先起服务，再 python tools/test_ui.py 8000
"""
from __future__ import annotations

import re
import sys
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
BASE = f"http://127.0.0.1:{PORT}"


def get(path: str) -> str:
    with urllib.request.urlopen(BASE + path, timeout=20) as r:
        return r.read().decode("utf-8", "replace")


def check(name: str, cond: bool, extra: str = "") -> bool:
    print(("  ✅ " if cond else "  ❌ ") + name + (f"  {extra}" if extra else ""))
    return bool(cond)


def main() -> int:
    ok = True
    print("问答页 /")
    ask = get("/")
    lib = get("/library")
    ok &= check("返回 200 且有内容", len(ask) > 3000, f"{len(ask)} 字节")
    ok &= check("有左侧栏 aside.sidebar", 'class="sidebar"' in ask)
    ok &= check("有右侧主区 main.main", 'class="main"' in ask)
    ok &= check("导航当前项正确", 'href="/" class="on"' in ask)
    ok &= check("有输入框与发送按钮", 'id="q"' in ask and 'id="go"' in ask)
    ok &= check("示例问题（欢迎区快捷提问）", "const SAMPLES" in ask and "wchip" in ask)
    ok &= check("有资料区（列表 / 上传按钮）", 'id="fileList"' in ask and 'id="addFileBtn"' in ask)
    ok &= check("有隐藏的文件选择器", 'id="filePicker"' in ask)
    ok &= check("有文件夹选择器（webkitdirectory）",
                'id="folderPicker"' in ask and "webkitdirectory" in ask)
    ok &= check("支持拖文件夹（webkitGetAsEntry）", "webkitGetAsEntry" in ask)
    ok &= check("有填路径导入入口", "askFolderPath" in ask and "import_folder" in ask)
    ok &= check("有全窗口拖拽遮罩", 'id="dropOverlay"' in ask)
    ok &= check("提问靠右、回答靠左（row-reverse）",
                ".msg.me{flex-direction:row-reverse}" in ask
                and ".msg.me .bubble{background:#4d6bfe" in ask)
    ok &= check("有新建对话按钮与会话列表",
                'id="newChatBtn"' in ask and 'id="chatList"' in ask)
    ok &= check("会话相关接口已接上",
                "/api/chats" in ask and "openChat" in ask and "newChat" in ask)
    ok &= check("上传自检脚本已注入", "selftest=upload" in ask)
    ok &= check("占位符已全部替换",
                "__CSS__" not in ask and "__TOAST__" not in ask
                and "__UPLOAD_SELFTEST__" not in ask)

    print("配置页 /config")
    cfg = get("/config")
    ok &= check("返回 200 且有内容", len(cfg) > 5000, f"{len(cfg)} 字节")
    ok &= check("有左侧栏", 'class="sidebar"' in cfg)
    ok &= check("有配置表格容器", 'id="plist"' in cfg)
    ok &= check("有「创建 API 配置」按钮", 'id="addBtn"' in cfg)
    ok &= check("有重建索引按钮", 'id="reindexBtn"' in cfg)
    ok &= check("有配置弹窗", 'id="modal"' in cfg)
    ok &= check("有告警横幅", 'id="banner"' in cfg)
    ok &= check("导航当前项正确", 'href="/config" class="on"' in cfg)
    ok &= check("是浅色主题", "--bg:#f6f7f9" in cfg)
    ok &= check("占位符已全部替换", "__CSS__" not in cfg and "__TOAST__" not in cfg)

    print("默认首页")
    ok &= check("/ 就是问答页（不是配置页）",
                'id="q"' in ask and 'id="go"' in ask and "API 配置" in ask)

    print("样式与脚本")
    ok &= check("左右分区用 flex 布局", "display:flex" in ask and "overflow:hidden" in ask)
    ok &= check("三页侧栏同宽 240px",
                all("flex:0 0 240px" in p for p in (ask, cfg, lib)))
    ok &= check("三页都有白色页头栏",
                all('class="main-head"' in p for p in (ask, cfg, lib)))
    ok &= check("三页页头内边距一致",
                all("padding:14px 26px" in p for p in (ask, cfg, lib)))
    ok &= check("配置页表单字段齐全", all(k in cfg for k in
              ["f_name", "f_provider", "f_base_url", "f_model", "f_api_key", "f_embedding"]))
    ok &= check("弹窗只有一个", len(re.findall(r'id="modal"', cfg)) == 1)
    ok &= check("两页统一浅色主题", "#f6f7f9" in ask and "#f6f7f9" in cfg)
    ok &= check("两页用同一个主色", "--accent:#4d6bfe" in ask and "--accent:#4d6bfe" in cfg)

    print("\n" + ("界面结构检查通过 ✅" if ok else "有失败项 ❌"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
