# -*- coding: utf-8 -*-
"""把「质量回归」写进 FAQ，让知识库知道自己的自检方式。"""
from pathlib import Path

p = Path(r"E:\RAG-KnowledgeBase\data\使用说明-FAQ.md")
s = p.read_text(encoding="utf-8")

anchor = "## 十四、检索不准怎么办"
if "## 十三、怎么自检答案质量" not in s:
    add = """## 十三、怎么自检答案质量

运行 `python src\\tools\\test_quality.py` 会跑 12 个典型问题，覆盖三类：课件类（如 chunk_size 默认值）、操作类（如怎么给别人用、怎么备份）、库外问题（如今天股价多少、帮我写一首诗）。

期望结果：课件类和操作类给出内容并带出处，库外问题明确说无法回答。目前 12 个全部通过。

如果某题变红，通常是两种原因：一是资料没同步（重建索引会自动同步说明文档），二是检索阈值被改动了。

"""
    i = s.index(anchor)
    s = s[:i] + add + s[i:]
    # 重新编号
    import re
    nums = "一二三四五六七八九十"
    def cn(n):
        return nums[n-1] if n <= 10 else "十" + nums[n-11]
    parts = re.split(r"(?m)^## ", s)
    head, sections = parts[0], parts[1:]
    out = [head.rstrip(), ""]
    for idx, chunk in enumerate(sections, 1):
        title, _, body = chunk.partition("\n")
        clean = re.sub(r"^[一二三四五六七八九十]+、", "", title.strip())
        out.append(f"## {cn(idx)}、{clean}")
        out.append("")
        out.append(body.strip())
        out.append("")
    p.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print("FAQ 已加「怎么自检答案质量」，共", len(sections), "节")
else:
    print("已存在")
