# -*- coding: utf-8 -*-
"""
多角色结构化试用 —— 统一执行脚本
用法: python -X utf8 run_trial.py <persona_key>

每个 persona 是一串真实操作步骤，脚本逐步执行并记录：
  - 每步耗时
  - 每步截图（存到 trials/<persona>/<step>.png）
  - 步骤成功/失败 + 失败原因
  - 页面是否出现预期关键文本（可读性检查）
最终输出 trials/<persona>/result.json

设计原则：这是「用真人视角操作」而不是「跑通接口」——
必须像用户一样点击、等待、看页面文字，遇到卡住的步骤如实记录，不跳过。
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5174"
OUT_ROOT = Path(__file__).parent / "trials"

VIEWPORTS = {
    # 学生：常见安卓机
    "student": {"width": 390, "height": 844},
    # 长辈：大屏手机 + 适老模式
    "elder": {"width": 430, "height": 932},
    # 慢病用户：iPhone 尺寸
    "patient": {"width": 375, "height": 812},
}


def log(msg):
    print(msg, flush=True)


def run(persona_key, steps):
    out_dir = OUT_ROOT / persona_key
    out_dir.mkdir(parents=True, exist_ok=True)
    vp = VIEWPORTS[persona_key]

    records = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport=vp, device_scale_factor=2,
                                  locale="zh-CN", timezone_id="Asia/Shanghai")
        page = ctx.new_page()
        console_errors = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(f"pageerror: {e}"))

        for idx, (name, action, expect) in enumerate(steps, 1):
            rec = {"step": idx, "name": name, "expect": expect}
            t0 = time.perf_counter()
            try:
                action(page)
                # 等网络静默（AI 类接口慢，最多 25s）
                try:
                    page.wait_for_load_state("networkidle", timeout=25000)
                except Exception:
                    pass
                dt = (time.perf_counter() - t0) * 1000
                body = page.inner_text("body")
                rec["elapsed_ms"] = round(dt, 1)
                rec["ok"] = True
                if expect:
                    rec["expect_found"] = expect in body
                else:
                    rec["expect_found"] = None
                rec["text_len"] = len(body)
                rec["text_sample"] = body[:400].replace("\n", " | ")
                shot = out_dir / f"{idx:02d}_{persona_key}.png"
                page.screenshot(path=str(shot), full_page=False)
                rec["screenshot"] = shot.name
            except Exception as e:
                dt = (time.perf_counter() - t0) * 1000
                rec["elapsed_ms"] = round(dt, 1)
                rec["ok"] = False
                rec["error"] = f"{type(e).__name__}: {str(e)[:250]}"
                rec["expect_found"] = False
                try:
                    shot = out_dir / f"{idx:02d}_{persona_key}_FAIL.png"
                    page.screenshot(path=str(shot), full_page=False)
                    rec["screenshot"] = shot.name
                except Exception:
                    pass
            records.append(rec)
            status = "OK" if rec["ok"] else "FAIL"
            extra = ""
            if rec.get("expect_found") is False:
                extra = f"  [预期文本未出现: {expect}]"
            log(f"[{status}] step {idx} {name}  {rec['elapsed_ms']:.0f}ms{extra}")
            if rec.get("error"):
                log(f"        {rec['error']}")

        result = {
            "persona": persona_key,
            "viewport": vp,
            "url": BASE,
            "steps_total": len(records),
            "steps_ok": sum(1 for r in records if r["ok"]),
            "expect_miss": sum(1 for r in records if r.get("expect_found") is False),
            "total_elapsed_ms": round(sum(r["elapsed_ms"] for r in records), 1),
            "console_errors": console_errors[:20],
            "steps": records,
        }
        (out_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        log("")
        log(f"=== {persona_key} 汇总 ===")
        log(f"步骤 {result['steps_ok']}/{result['steps_total']} 成功")
        log(f"预期文本未命中 {result['expect_miss']} 处")
        log(f"总耗时 {result['total_elapsed_ms']/1000:.1f}s")
        log(f"控制台错误 {len(console_errors)} 条")
        if console_errors:
            for e in console_errors[:5]:
                log(f"  - {e[:150]}")
        log(f"结果文件: {out_dir / 'result.json'}")
        ctx.close()
        browser.close()

    return result
