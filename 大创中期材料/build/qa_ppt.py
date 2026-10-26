# PPT 程序化 QA：文本溢出 / 形状越界 / 文本框重叠
import sys
from pptx import Presentation
from pptx.util import Emu

PATH = sys.argv[1]
prs = Presentation(PATH)
SW, SH = prs.slide_width, prs.slide_height
EMU_IN = 914400
issues = []

def walk(shapes):
    for sh in shapes:
        if sh.shape_type == 6:
            yield from walk(sh.shapes)
        else:
            yield sh

for si, slide in enumerate(prs.slides, 1):
    boxes = []
    for sh in walk(slide.shapes):
        if sh.left is None:
            continue
        l, t, w, h = sh.left, sh.top, sh.width, sh.height
        # 越界检查：仅查有文字的形状（无文字的自动形状是刻意出血的装饰）
        has_txt = sh.has_text_frame and sh.text_frame.text.strip()
        if has_txt and (l < -10000 or t < -10000 or l + w > SW + 10000 or t + h > SH + 10000):
            issues.append(f"S{si} 越界: {sh.shape_type} '{(sh.name or '')[:12]}' at ({l/EMU_IN:.2f},{t/EMU_IN:.2f}) {w/EMU_IN:.2f}x{h/EMU_IN:.2f}")
        if sh.has_text_frame and sh.text_frame.text.strip():
            txt = sh.text_frame.text
            # 估算每段宽度需求（CJK≈fontsize, latin≈0.55*fontsize）
            max_pt = 0
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.size:
                        max_pt = max(max_pt, r.font.size.pt)
            if max_pt == 0:
                max_pt = 18
            box_w_in = w / EMU_IN
            box_h_in = h / EMU_IN
            # 每行需求高度
            n_lines = 0
            for p in sh.text_frame.paragraphs:
                ptxt = "".join(r.text for r in p.runs)
                if not ptxt:
                    n_lines += 1
                    continue
                p_pt = max((r.font.size.pt for r in p.runs if r.font.size), default=max_pt)
                need_w = sum((1.0 if ord(c) > 0x2E80 else 0.55) * p_pt / 72 for c in ptxt)
                n_lines += max(1, -(-need_w // max(box_w_in, 0.1)))
            need_h = n_lines * max_pt * 1.35 / 72
            if need_h > box_h_in * 1.25 and box_h_in > 0.05:
                issues.append(f"S{si} 可能竖向溢出: '{txt[:14]}…' 需~{need_h:.2f}in 框{box_h_in:.2f}in")
            boxes.append((l, t, w, h, txt[:10]))
    # 文本框重叠
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
            oy = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
            if ox > 0.06 * EMU_IN and oy > 0.06 * EMU_IN:
                area = (ox / EMU_IN) * (oy / EMU_IN)
                if area > 0.04:
                    issues.append(f"S{si} 文本重叠({area:.2f}in²): '{a[4]}…' × '{b[4]}…'")

print(f"slides={len(prs.slides)}, issues={len(issues)}")
for i in issues:
    print(" -", i)
