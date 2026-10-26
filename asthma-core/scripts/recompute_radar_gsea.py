# -*- coding: utf-8 -*-
"""
用真实 GSEA 富集分析重算 compound 三维机制评分

背景：
  原 radar_anti_inflammatory / radar_immune_regulation / radar_airway_repair
  三列经检验为均匀分布随机数（卡方检验 df=60 全部通过、两两相关系数≈0、
  全为 40-100 整数），且项目内无任何生成代码，无溯源文件。

做法：
  1. 取每个成分的人类蛋白靶点基因符号
  2. 直接调用 Enrichr REST API（绕开本项目内已损坏的 gseapy 0.10.8，
     其 enrichr.py:427 使用了 pandas 2.x 已移除的 DataFrame.append）
  3. 跑 KEGG_2021_Human + GO_Biological_Process_2021
  4. 按药理关键词把命中通路映射到三个疗效维度，累计基因 overlap
  5. 归一化到 0-100

与旧实现的区别（重要）：
  - 旧 _normalize() 在 score==0 时返回 hash 伪随机基线（20-35），本脚本返回真实 0
  - 旧实现 gseapy 崩溃时返回硬编码 {45,52,38}，本脚本不做假兜底
  - 结果写入新列 radar_*_gsea，不覆盖原 radar_* 列，便于对照

用法：
    python -X utf8 scripts/recompute_radar_gsea.py --dry-run   # 跑 10 个样本看效果
    python -X utf8 scripts/recompute_radar_gsea.py --apply     # 全量重算并写库
"""
import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

CORE = Path(__file__).resolve().parent.parent
DB_PATH = CORE / "data" / "asthma_v2.db"
CACHE_PATH = CORE / "scripts" / "gsea_cache.json"

ENRICHR = "https://maayanlab.cloud/Enrichr"
GENE_SETS = ["KEGG_2021_Human", "GO_Biological_Process_2021"]

# 与 app/services/pharmacology.py 的 EFFICACY_DIMENSIONS 保持一致
DIMENSIONS = {
    "anti_inflammatory": ["inflammat", "tnf", "nf-kappa", "cytokine", "il-6", "il-1",
                          "prostaglandin", "cyclooxygenase", "cox"],
    "immune_regulation": ["immun", "t cell", "b cell", "th1", "th2", "treg",
                          "interleukin", "mast cell", "eosinophil", "ige"],
    "airway_repair": ["muscle", "airway", "remodel", "hypoxia", "vascular",
                      "epithelial", "fibrosis", "mucus", "bronch"],
}


def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def enrichr_analyze(genes, session, retries=3):
    """调用 Enrichr REST API，返回 [(term, overlap_count), ...]"""
    for attempt in range(retries):
        try:
            r = session.post(f"{ENRICHR}/addList",
                             files={"list": (None, "\n".join(genes))},
                             data={"description": "asthma-core radar recompute"},
                             timeout=30)
            r.raise_for_status()
            uid = r.json()["userListId"]
            time.sleep(0.6)

            hits = []
            for gs in GENE_SETS:
                r2 = session.get(f"{ENRICHR}/enrich",
                                 params={"userListId": uid, "backgroundType": gs},
                                 timeout=30)
                r2.raise_for_status()
                for item in r2.json().get(gs, []):
                    term = str(item[1])
                    genes_in = item[5] if isinstance(item[5], list) else []
                    hits.append((term, len(genes_in)))
            return hits
        except Exception as e:
            if attempt == retries - 1:
                print(f"    Enrichr 失败: {type(e).__name__}: {e}")
                return None
            time.sleep(2 * (attempt + 1))
    return None


def score_dimensions(hits, gene_count):
    """
    按关键词把命中通路映射到三个疗效维度。

    直接累加 overlap 会让「靶点多、命中通路多」的成分三个维度同时偏高
    （实测各维度 overlap 与命中通路数的相关系数 0.89~0.93），
    导致三个维度退化成同一个信号。因此改用：

        维度得分 = 维度在总 overlap 中的占比 × 富集强度

    占比刻画「该成分的作用偏向哪个维度」，强度用 log(总 overlap) 刻画
    「该成分整体证据量」。两者相乘既保留方向差异，也保留强弱差异。
    """
    raw = {dim: 0 for dim in DIMENSIONS}
    for term, overlap in hits:
        low = term.lower()
        for dim, keywords in DIMENSIONS.items():
            if any(kw in low for kw in keywords):
                raw[dim] += overlap

    total = sum(raw.values())
    if total <= 0:
        return {dim: 0.0 for dim in DIMENSIONS}

    # log 压缩强度，避免少数超大多靶点成分拉爆量纲
    import math
    strength = math.log1p(total)
    return {dim: (raw[dim] / total) * strength for dim in DIMENSIONS}


def rank_normalize(values):
    """
    分位数归一化到 0-100。

    原始 overlap 跨度极大（0 ~ 909，中位数十几），线性缩放会让半数成分撞到上限。
    改用经验分位数映射：0 保持 0（真实无命中），其余按在全体中的排名铺开到 1-100。
    """
    import bisect

    nz = sorted(v for v in values if v and v > 0)
    if not nz:
        return [0 for _ in values]
    out = []
    for v in values:
        if not v or v <= 0:
            out.append(0)
        else:
            # 该值在非零集合中的分位
            pct = bisect.bisect_right(nz, v) / len(nz)
            out.append(max(1, min(100, int(round(pct * 100)))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=10, help="dry-run 时抽样数量")
    ap.add_argument("--sleep", type=float, default=0.8, help="每次请求间隔秒数")
    ap.add_argument("--write-every", type=int, default=25, help="每算 N 个就落库一次")
    args = ap.parse_args()

    con = sqlite3.connect(DB_PATH)

    # 建列（保留原 radar_* 供对照）
    cols = {r[1] for r in con.execute("PRAGMA table_info(compound)")}
    for c in ["radar_anti_inflammatory_gsea", "radar_immune_regulation_gsea",
              "radar_airway_repair_gsea"]:
        if c not in cols:
            con.execute(f"ALTER TABLE compound ADD COLUMN {c} FLOAT")
    con.commit()

    # 取每个成分的人类蛋白靶点
    rows = con.execute("""
        SELECT c.id, c.name, GROUP_CONCAT(DISTINCT t.gene)
        FROM compound c
        JOIN rel_compound_target rt ON rt.compound_id = c.id
        JOIN target t ON t.gene = rt.target_gene
        WHERE t.species = 'Homo sapiens'
          AND t.target_type IN ('Protein', 'Individual Protein')
          AND t.gene NOT LIKE '% %'
        GROUP BY c.id
        ORDER BY c.id
    """).fetchall()
    print(f"有人类蛋白靶点的成分: {len(rows)} / {con.execute('SELECT COUNT(*) FROM compound').fetchone()[0]}")

    if not args.apply:
        rows = rows[:args.limit]
        print(f"[dry-run] 抽样 {len(rows)} 个\n")

    cache = load_cache()
    session = requests.Session()
    session.headers.update({"User-Agent": "asthma-core-radar-recompute/1.0"})

    # 阶段一：收集每个成分的原始 overlap（缓存命中则不发请求）
    raw_rows = []
    no_targets = 0
    failed = 0
    t0 = time.time()

    for i, (cid, name, genes_str) in enumerate(rows, 1):
        genes = [g for g in (genes_str or "").split(",") if g]
        if len(genes) < 2:
            no_targets += 1
            continue

        if cid in cache:
            hits = cache[cid]
        else:
            hits = enrichr_analyze(genes, session)
            if hits is None:
                failed += 1
                continue
            cache[cid] = hits
            if i % 20 == 0:
                save_cache(cache)
            time.sleep(args.sleep)

        raw_rows.append((cid, name, len(genes), score_dimensions(hits, len(genes))))

        if i % 50 == 0:
            save_cache(cache)
            print(f"  进度 {i}/{len(rows)}  已用时 {time.time()-t0:.0f}s")

    save_cache(cache)
    print(f"\n富集完成: {len(raw_rows)} 个 | 靶点不足2个: {no_targets} | Enrichr 失败: {failed}")

    # 阶段二：三个维度分别做分位数归一化
    dims = ["anti_inflammatory", "immune_regulation", "airway_repair"]
    scaled = {}
    for dim in dims:
        scaled[dim] = rank_normalize([r[3][dim] for r in raw_rows])

    results = [
        (raw_rows[i][0], scaled["anti_inflammatory"][i],
         scaled["immune_regulation"][i], scaled["airway_repair"][i])
        for i in range(len(raw_rows))
    ]

    if not args.apply:
        for i, (cid, name, ngene, raw) in enumerate(raw_rows[:args.limit]):
            print(f"  {name:22s} 靶点{ngene:4d} | 抗炎{scaled['anti_inflammatory'][i]:3d} "
                  f"免疫{scaled['immune_regulation'][i]:3d} 气道{scaled['airway_repair'][i]:3d} "
                  f"| overlap {raw}")
        print("[dry-run] 未写库")
        con.close()
        return

    upd = [(a, b, c, cid) for cid, a, b, c in results if a is not None]
    con.executemany("""UPDATE compound SET
        radar_anti_inflammatory_gsea=?, radar_immune_regulation_gsea=?,
        radar_airway_repair_gsea=? WHERE id=?""", upd)
    # 无靶点/失败的显式置 NULL，避免残留
    con.execute("""UPDATE compound SET
        radar_anti_inflammatory_gsea=NULL, radar_immune_regulation_gsea=NULL,
        radar_airway_repair_gsea=NULL
        WHERE id NOT IN (SELECT id FROM compound WHERE radar_anti_inflammatory_gsea IS NOT NULL)""")
    con.commit()

    stat = con.execute("""SELECT
        COUNT(*) FILTER (WHERE radar_anti_inflammatory_gsea IS NOT NULL),
        COUNT(*) FILTER (WHERE radar_anti_inflammatory_gsea = 0),
        ROUND(AVG(radar_anti_inflammatory_gsea),1),
        ROUND(AVG(radar_immune_regulation_gsea),1),
        ROUND(AVG(radar_airway_repair_gsea),1),
        COUNT(*) FILTER (WHERE radar_anti_inflammatory_gsea = 100)
        FROM compound""").fetchone()
    print(f"已写入 {len(upd)} 条")
    print(f"  有值: {stat[0]}  其中抗炎为0(无富集命中): {stat[1]}  抗炎满分100: {stat[5]}")
    print(f"  均值: 抗炎 {stat[2]} 免疫 {stat[3]} 气道 {stat[4]}")
    con.close()


if __name__ == "__main__":
    main()
