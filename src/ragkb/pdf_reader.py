# -*- coding: utf-8 -*-
"""纯标准库 PDF 文本提取（离线环境下的 PDF 加载器）。

课件 P61/P67 用 PyPDFLoader；本模块在没有第三方库时顶替它，
同样是"一页一个文本块"，产出 (页码, 文本) 列表。

支持：经典 xref PDF、FlateDecode 流、ToUnicode CMap（Type0/Identity-H）、
      无 ToUnicode 时的 GBK 中文回退。
不支持：加密 PDF、对象流（/ObjStm）压缩的 PDF —— 遇到会返回空并提示装 pypdf。
"""
from __future__ import annotations

import re
import zlib

_OBJ_RE = re.compile(rb"(\d+)\s+(\d+)\s+obj\b")


def _parse_objects(buf: bytes) -> dict:
    objs = {}
    for m in _OBJ_RE.finditer(buf):
        num = int(m.group(1))
        start = m.end()
        end = buf.find(b"endobj", start)
        if end < 0:
            end = len(buf)
        objs[num] = buf[start:end]
    return objs


def _stream_bytes(body: bytes):
    i = body.find(b"stream")
    if i < 0:
        return None
    j = i + 6
    if body[j:j + 2] == b"\r\n":
        j += 2
    elif body[j:j + 1] in (b"\n", b"\r"):
        j += 1
    k = body.find(b"endstream", j)
    return body[j:k] if k >= 0 else body[j:]


def _decode_stream(objs: dict, num: int):
    body = objs.get(num)
    if body is None:
        return None
    raw = _stream_bytes(body)
    if raw is None:
        return None
    head = body[: body.find(b"stream")]
    if b"FlateDecode" in head and b"DecodeParms" not in head:
        try:
            return zlib.decompress(raw)
        except Exception:
            try:
                return zlib.decompressobj().decompress(raw)
            except Exception:
                return b""
    return raw


def _deref(objs: dict, tok: bytes):
    tok = tok.strip()
    m = re.match(rb"(\d+)\s+\d+\s+R", tok)
    if m:
        return objs.get(int(m.group(1)))
    return tok


def _entries(body: bytes) -> dict:
    out = {}
    i, n = 0, len(body)
    while i < n:
        m = re.compile(rb"/([A-Za-z0-9#_+.\-]+)").search(body, i)
        if not m:
            break
        key = m.group(1).decode("latin-1")
        i = m.end()
        while i < n and body[i:i + 1].isspace():
            i += 1
        if i >= n:
            break
        c = body[i:i + 1]
        if c == b"/":
            m4 = re.compile(rb"/[A-Za-z0-9#_+.\-]*").match(body, i)
            if m4:
                out[key] = m4.group(0)
                i = m4.end()
                continue
            i += 1
            continue
        if c == b"<":
            if body[i:i + 2] == b"<<":
                depth, s = 0, i
                while i < n:
                    if body[i:i + 2] == b"<<":
                        depth += 1
                        i += 2
                        continue
                    if body[i:i + 2] == b">>":
                        depth -= 1
                        i += 2
                        if depth == 0:
                            break
                        continue
                    i += 1
                out[key] = body[s:i]
                continue
            j = body.find(b">", i)
            if j < 0:
                break
            out[key] = body[i:j + 1]
            i = j + 1
            continue
        if c == b"[":
            depth, s = 0, i
            while i < n:
                ch = body[i:i + 1]
                if ch == b"[":
                    depth += 1
                elif ch == b"]":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            out[key] = body[s:i]
            continue
        m2 = re.compile(rb"(\d+\s+\d+\s+R)").match(body, i)
        if m2:
            out[key] = m2.group(1)
            i = m2.end()
            continue
        m3 = re.compile(rb"[^\s/<>\[\]()]+").match(body, i)
        if m3:
            out[key] = m3.group(0)
            i = m3.end()
            continue
        i += 1
    return out


def _parse_cmap(data: bytes) -> dict:
    cmap = {}
    for block in re.finditer(rb"beginbfchar(.*?)endbfchar", data, re.S):
        for m in re.finditer(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>", block.group(1)):
            src = int(m.group(1), 16)
            hexs = m.group(2).decode()
            dst = "".join(chr(int(hexs[k:k + 4], 16)) for k in range(0, len(hexs) - 3, 4))
            cmap[src] = dst
    for block in re.finditer(rb"beginbfrange(.*?)endbfrange", data, re.S):
        for m in re.finditer(
            rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block.group(1)
        ):
            lo, hi = int(m.group(1), 16), int(m.group(2), 16)
            hexs = m.group(3).decode()
            base = int(hexs[:4], 16) if len(hexs) >= 4 else 0
            for off in range(min(hi - lo + 1, 8192)):
                try:
                    cmap[lo + off] = chr(base + off)
                except ValueError:
                    pass
    return cmap


def _unescape_literal(s: bytes) -> bytes:
    out = bytearray()
    i = 0
    mapping = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f",
               b"(": b"(", b")": b")", b"\\": b"\\"}
    while i < len(s):
        c = s[i:i + 1]
        if c == b"\\":
            nxt = s[i + 1:i + 2]
            if nxt in mapping:
                out += mapping[nxt]
                i += 2
                continue
            m = re.match(rb"[0-7]{1,3}", s[i + 1:i + 4])
            if m:
                out.append(int(m.group(0), 8) & 0xFF)
                i += 1 + len(m.group(0))
                continue
            i += 2
            continue
        out += c
        i += 1
    return bytes(out)


def _decode_string(raw: bytes, font: dict) -> str:
    if raw.startswith(b"<"):
        hexs = re.sub(rb"[^0-9A-Fa-f]", b"", raw[1:-1])
        if len(hexs) % 2:
            hexs += b"0"
        bs = bytes.fromhex(hexs.decode())
    else:
        bs = _unescape_literal(raw[1:-1])

    cmap = font.get("cmap") or {}
    if font.get("two_byte"):
        codes = [int.from_bytes(bs[i:i + 2], "big") for i in range(0, len(bs) - 1, 2)]
    else:
        codes = list(bs)

    if cmap:
        return "".join(cmap.get(c, "") for c in codes)
    try:                       # 中文简单字体常用 GBK 存码
        return bs.decode("gbk")
    except Exception:
        pass
    if font.get("two_byte"):
        return "".join(chr(c) for c in codes if 32 <= c < 0x110000)
    return bs.decode("latin-1", "replace")


def _extract_page(objs: dict, ent: dict) -> str:
    refs = []
    contents = ent.get("Contents")
    if contents:
        for m in re.finditer(rb"(\d+)\s+\d+\s+R", contents):
            refs.append(int(m.group(1)))
    stream = b"\n".join(filter(None, (_decode_stream(objs, r) for r in refs)))
    if not stream:
        return ""

    # 字体表
    font_map = {}
    res = _deref(objs, ent["Resources"]) if "Resources" in ent else None
    if res:
        fdict = _entries(res).get("Font")
        fbody = _deref(objs, fdict) if fdict else None
        if fbody:
            for m in re.finditer(rb"/([A-Za-z0-9#_+.\-]+)\s+(\d+)\s+\d+\s+R", fbody):
                font_map[b"/" + m.group(1)] = int(m.group(2))

    cache = {}

    def font_info(num):
        if num in cache:
            return cache[num]
        info = {"cmap": {}, "two_byte": False}
        body = objs.get(num) or b""
        e = _entries(body)
        if b"/Type0" in e.get("Subtype", b""):
            info["two_byte"] = True
        if "ToUnicode" in e:
            m = re.match(rb"(\d+)\s+\d+\s+R", e["ToUnicode"].strip())
            if m:
                s = _decode_stream(objs, int(m.group(1)))
                if s:
                    info["cmap"] = _parse_cmap(s)
        cache[num] = info
        return info

    out, pending = [], []
    cur_font = None
    i, n = 0, len(stream)
    while i < n:
        c = stream[i:i + 1]
        if c == b"(" or (c == b"<" and stream[i:i + 2] != b"<<"):
            if c == b"<":
                j = stream.find(b">", i)
                if j < 0:
                    break
                tok, i = stream[i:j + 1], j + 1
            else:
                depth, j = 0, i
                while j < n:
                    ch = stream[j:j + 1]
                    if ch == b"\\":
                        j += 2
                        continue
                    if ch == b"(":
                        depth += 1
                    elif ch == b")":
                        depth -= 1
                        if depth == 0:
                            j += 1
                            break
                    j += 1
                tok, i = stream[i:j], j
            pending.append(_decode_string(tok, cur_font or {}))
            continue
        if c == b"/":
            m = re.match(rb"/([A-Za-z0-9#_+.\-]+)\s+[\d.]+\s+Tf", stream[i:i + 80])
            if m:
                name = b"/" + m.group(1)
                if name in font_map:
                    cur_font = font_info(font_map[name])
                i += m.end()
                continue
        two = stream[i:i + 2]
        if two in (b"Td", b"TD"):
            out.append(" ")
            i += 2
            continue
        if two in (b"T*", b"ET"):
            out.append("\n")
            i += 2
            continue
        if two in (b"TJ", b"Tj"):
            out.append("".join(pending))
            pending = []
            i += 2
            continue
        if two[:1] == b"'" or two[:1] == b'"':
            out.append("".join(pending))
            pending = []
            out.append("\n")
            i += 1
            continue
        i += 1
    out.append("".join(pending))
    txt = "".join(out)
    txt = re.sub(r"[ \t]{2,}", " ", txt)
    txt = _join_spaced_latin(txt)
    txt = txt.encode("utf-8", "replace").decode("utf-8", "replace")
    return "".join(ch for ch in txt if not (0xD800 <= ord(ch) <= 0xDFFF))


# 逐字定位的 PDF（PPT 导出常见）会把 "chunk_size" 抽成 "c h u n k _ s i z e"，
# 这里把连续 3 个以上的单字符片段重新粘起来。
_SPACED_RUN = re.compile(
    r"(?:(?<=\s)|(?<=^))([A-Za-z0-9_](?: [A-Za-z0-9_]){2,})(?=\s|$|[，。；：、）】)\]}])"
)


def _join_spaced_latin(text: str) -> str:
    for _ in range(6):                      # 反复几轮，处理长串
        new = _SPACED_RUN.sub(lambda m: m.group(1).replace(" ", ""), text)
        if new == text:
            break
        text = new
    # 中文被逐字排开时（"文 档"）也要粘回去，否则中文 n-gram 全废
    text = re.sub(r"(?<=[\u4e00-\u9fff])[ \t]+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[0-9])[ \t]+(?=[0-9])", "", text)
    return text


def extract_pdf(path) -> list[tuple[int, str]]:
    """返回 [(页码从1开始, 该页文本), ...]；失败返回空列表。"""
    data = open(path, "rb").read()
    if b"/Encrypt" in data[:4096] or b"/ObjStm" in data:
        return []
    objs = _parse_objects(data)

    root = None
    for body in objs.values():
        if re.search(rb"/Type\s*/Catalog", body):
            root = _entries(body)
            break
    if not root or "Pages" not in root:
        return []

    pages: list = []

    def walk(node, depth=0):
        if depth > 64:
            return
        body = _deref(objs, node)
        if not body:
            return
        ent = _entries(body)
        t = ent.get("Type", b"")
        if b"/Pages" in t:
            for m in re.finditer(rb"(\d+)\s+\d+\s+R", ent.get("Kids", b"")):
                walk(m.group(1) + b" 0 R", depth + 1)
        elif b"/Page" in t:
            # 继承父节点的 Resources
            if "Resources" not in ent and pages:
                ent["Resources"] = pages[-1][1].get("Resources", b"")
            pages.append((node, ent))

    walk(root["Pages"])

    result = []
    for idx, (_ref, ent) in enumerate(pages, 1):
        try:
            text = _extract_page(objs, ent)
        except Exception:
            text = ""
        if text.strip():
            result.append((idx, text))
    return result
