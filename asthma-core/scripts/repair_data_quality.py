# -*- coding: utf-8 -*-
"""
大创数据库数据质量修复脚本

修复项（按执行顺序）：
  P0-1  rel_herb_compound：用原始溯源 Excel 重建（原表 99.2% 关联错误）
  P0-2  compound.mw / logp：用 RDKit 从 SMILES 重算（原值全为随机数）
        compound.smile_short：改为真实 SMILES 的截断摘要（原值多为乱码 SMILES）
        compound.target_count：与实际关联数对齐
  P0-4  rel_compound_target.source_db / network_centrality：置 NULL（原值为随机填充）
  P1-1  rel_prescription_herb：按 prescription.description 重建 + 合并重复方剂

用法：
    python -X utf8 scripts/repair_data_quality.py --dry-run    # 只打印计划
    python -X utf8 scripts/repair_data_quality.py --apply      # 实际写库
"""
import argparse
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

CORE = Path(__file__).resolve().parent.parent
REPO = CORE.parent.parent
DB_PATH = CORE / "data" / "asthma_v2.db"
SRC_DIR = REPO / "数据库溯源" / "主要展示数据均为cctcm2.0"
XLSX_HERB_COMPOUND = SRC_DIR / "药材-化合物-含量-赵玉男.xlsx"
XLSX_PHYSCHEM = SRC_DIR / "化合物理化性质和生物利用度属性-赵玉男.xlsx"
XLSX_COMPOUND = SRC_DIR / "化合物数据_cctcm2.0.xlsx"


def norm(s):
    """名称归一：全角转半角、去所有空白、小写。"""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    return re.sub(r"\s+", "", s).lower()


def strip_paren(s):
    """去掉中英文括号及内容，用于「红车轴草苷（三叶豆紫檀苷）」这类别名匹配。"""
    return re.sub(r"[（(].*?[)）]", "", str(s)).strip()


# ==================== P0-1 药材-成分归属 ====================

def repair_herb_compound(con, apply):
    print("\n" + "=" * 70)
    print("P0-1  重建 rel_herb_compound")
    print("=" * 70)

    wb = openpyxl.load_workbook(XLSX_HERB_COMPOUND, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    excel_map = defaultdict(set)
    for r in ws.iter_rows(min_row=2, values_only=True):
        herb, comp = r[1], r[5]
        if herb and comp:
            excel_map[str(herb).strip()].add(str(comp).strip())
    wb.close()
    print(f"源表读入：{len(excel_map)} 味药材")

    db_herbs = {r[1]: r[0] for r in con.execute("SELECT id, name FROM herb")}
    db_comps = {r[1]: r[0] for r in con.execute("SELECT id, name FROM compound")}

    # 成分名归一索引（含去括号别名）
    comp_index = {}
    for name, cid in db_comps.items():
        comp_index[norm(name)] = cid
        stripped = strip_paren(name)
        if stripped:
            comp_index.setdefault(norm(stripped), cid)

    links = []
    herb_missing = []
    comp_missing = defaultdict(set)
    for herb_name, herb_id in db_herbs.items():
        comps = excel_map.get(herb_name)
        if not comps:
            herb_missing.append(herb_name)
            continue
        for cname in comps:
            cid = comp_index.get(norm(cname)) or comp_index.get(norm(strip_paren(cname)))
            if not cid:
                comp_missing[herb_name].add(cname)
                continue
            links.append((herb_id, cid))

    # 去重
    seen = set()
    unique_links = []
    for h, c in links:
        if (h, c) not in seen:
            seen.add((h, c))
            unique_links.append((h, c))

    old_total = con.execute("SELECT COUNT(*) FROM rel_herb_compound").fetchone()[0]
    print(f"旧表：{old_total} 条")
    print(f"新表：{len(unique_links)} 条（覆盖 {len(db_herbs) - len(herb_missing)} 味药材）")
    print(f"源表无成分记录的药材（{len(herb_missing)} 味）：{herb_missing}")
    print(f"源表成分名在库中不存在：{sum(len(v) for v in comp_missing.values())} 个"
          f"（库只收 569 个成分，源表有 {len(set().union(*excel_map.values()))} 个）")

    if not apply:
        return

    con.execute("DROP TABLE IF EXISTS rel_herb_compound_old")
    con.execute("ALTER TABLE rel_herb_compound RENAME TO rel_herb_compound_old")
    con.execute("""CREATE TABLE rel_herb_compound (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        herb_id VARCHAR(50) NOT NULL,
        compound_id VARCHAR(50) NOT NULL,
        UNIQUE(herb_id, compound_id))""")
    con.executemany(
        "INSERT INTO rel_herb_compound(herb_id, compound_id) VALUES (?, ?)",
        unique_links)
    # 同步 herb.compound_count
    con.execute("UPDATE herb SET compound_count = "
                "(SELECT COUNT(*) FROM rel_herb_compound r WHERE r.herb_id = herb.id)")
    con.commit()
    print(f"✓ 已重建，旧表保留为 rel_herb_compound_old")


# ==================== P0-2 成分理化属性 ====================

def repair_compound_props(con, apply):
    print("\n" + "=" * 70)
    print("P0-2  重算 compound.mw / logp / smile_short / target_count")
    print("=" * 70)

    from rdkit import Chem, RDLogger
    from rdkit.Chem import Crippen, Descriptors
    RDLogger.DisableLog("rdApp.*")

    # 导师理化表：按 SMILES 反查真实 logP
    # 注意：该表有 957 行整体右移一列（LogS 列填了分子式、LogD 列填了分子量、
    #       LogP 列填了重原子数），这些行的 LogP 不可用，必须排除
    wb = openpyxl.load_workbook(XLSX_PHYSCHEM, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    phys_by_smiles = {}
    shifted = 0
    for r in ws.iter_rows(min_row=3, values_only=True):
        if not r[1]:
            continue
        # 错位判定：LogS 列存的是分子式字符串而非数值
        if isinstance(r[2], str):
            shifted += 1
            continue
        phys_by_smiles.setdefault(str(r[1]).strip(), r)
    wb.close()
    print(f"  理化表跳过 {shifted} 行错位数据（LogS 列为分子式字符串）")

    # 化合物主表：按化合物代码反查权威 SMILES（用于修复库内损坏的 SMILES）
    wb = openpyxl.load_workbook(XLSX_COMPOUND, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    src_smiles = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] and r[7]:
            src_smiles[str(r[0]).strip()] = str(r[7]).strip()
    wb.close()

    rows = con.execute("SELECT id, name, smiles, mw, logp, smile_short FROM compound").fetchall()
    updates = []
    stat = {"mw_rdkit": 0, "logp_rdkit": 0, "logp_phys": 0, "smiles_fixed": [], "fail": []}

    for cid, name, smiles, old_mw, old_logp, old_short in rows:
        mol = Chem.MolFromSmiles(smiles) if smiles else None

        # SMILES 解析失败 → 从源表回填权威值
        if mol is None:
            fixed = src_smiles.get(cid)
            fixed_mol = Chem.MolFromSmiles(fixed) if fixed else None
            if fixed_mol is not None:
                stat["smiles_fixed"].append(name)
                smiles = fixed
                mol = fixed_mol
            else:
                stat["fail"].append(name)
                continue

        new_mw = round(Descriptors.MolWt(mol), 2)
        stat["mw_rdkit"] += 1

        # logP：优先导师理化表实测值，否则 RDKit Crippen 计算
        phys = phys_by_smiles.get(str(smiles).strip())
        if phys and phys[4] is not None:
            try:
                new_logp = round(float(phys[4]), 2)
                stat["logp_phys"] += 1
            except (TypeError, ValueError):
                new_logp = round(Crippen.MolLogP(mol), 2)
                stat["logp_rdkit"] += 1
        else:
            new_logp = round(Crippen.MolLogP(mol), 2)
            stat["logp_rdkit"] += 1

        # smile_short：真实 SMILES 截断摘要（前端列表页展示用）
        canonical = Chem.MolToSmiles(mol)
        new_short = canonical if len(canonical) <= 60 else canonical[:57] + "..."

        updates.append((smiles, new_mw, new_logp, new_short, cid))

    print(f"RDKit 可解析：{stat['mw_rdkit']}/{len(rows)}")
    if stat["smiles_fixed"]:
        print(f"  SMILES 损坏已从源表回填：{stat['smiles_fixed']}")
    print(f"  mw   全部由 RDKit 重算")
    print(f"  logp 取导师理化表实测值：{stat['logp_phys']} 条，RDKit Crippen 计算：{stat['logp_rdkit']} 条")
    if stat["fail"]:
        print(f"  SMILES 无法修复（保留原值）：{stat['fail']}")

    # target_count 对齐
    bad_tc = con.execute("""SELECT COUNT(*) FROM compound c
        WHERE c.target_count != (SELECT COUNT(*) FROM rel_compound_target r WHERE r.compound_id = c.id)
    """).fetchone()[0]
    print(f"target_count 与实际关联数不符：{bad_tc} 条 → 将对齐")

    if not apply:
        return

    con.executemany(
        "UPDATE compound SET smiles=?, mw=?, logp=?, smile_short=? WHERE id=?", updates)
    con.execute("""UPDATE compound SET target_count =
        (SELECT COUNT(*) FROM rel_compound_target r WHERE r.compound_id = compound.id)""")
    con.commit()
    print(f"✓ 已更新 {len(updates)} 条成分属性，target_count 已对齐")


# ==================== P0-4 靶点关联脏字段 ====================

def repair_target_rel_fields(con, apply):
    print("\n" + "=" * 70)
    print("P0-4  清空 rel_compound_target.source_db / network_centrality")
    print("=" * 70)

    total = con.execute("SELECT COUNT(*) FROM rel_compound_target").fetchone()[0]
    print(f"总关联 {total} 条")
    print("  source_db：同一 PMID 被平均分到 5 个库，判定为随机填充 → 置 NULL")
    print("  network_centrality：0.0-1.0 均匀分布，random.uniform 特征 → 置 NULL")

    if not apply:
        return
    con.execute("UPDATE rel_compound_target SET source_db = NULL, network_centrality = NULL")
    con.commit()
    print("✓ 已置 NULL（前端已有 '—' 兜底，不会报错）")


# ==================== P1-1 方剂组成 ====================

# 重复方剂合并映射：被合并方剂 id → 保留的方剂 id
MERGE_MAP = {
    4: 3,    # 麻黄桂枝汤 → 麻黄汤（组成完全相同）
    13: 12,  # 生脉饮 → 生脉散（组成完全相同）
    14: 12,  # 生脉方 → 生脉散（组成完全相同）
}

# 合并后为保留方剂补充的别名
MERGE_ALIASES = {
    3: ["麻黄桂枝汤"],
    12: ["生脉饮", "生脉方"],
}


def parse_description(desc):
    """从 description 解析药材名与剂量。支持 、；,， 分隔和括号剂量。"""
    if not desc:
        return []
    d = desc.replace("（", "(").replace("）", ")")
    parts = re.split(r"[、;；,，]", d)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        dose = None
        m = re.search(r"\(([^)]*)\)", p)
        if m:
            dose = m.group(1).strip()
            p = re.sub(r"\([^)]*\)", "", p).strip()
        if p:
            out.append((p, dose))
    return out


# 药材别名 → 库中标准名（仅收录库内确为同一药材、只是写法不同的情况）
HERB_ALIAS = {
    "芍药": "白芍",
    "杏仁": "苦杏仁",
    "炙甘草": "甘草",
    "山萸肉": "山茱萸",
}


def repair_prescription_herbs(con, apply):
    print("\n" + "=" * 70)
    print("P1-1  按 description 重建 rel_prescription_herb + 合并重复方剂")
    print("=" * 70)

    herbs = {r[1]: r[0] for r in con.execute("SELECT id, name FROM herb")}
    presc = con.execute("SELECT id, name, description FROM prescription").fetchall()

    # 旧表剂量回退索引：(prescription_id, herb_name) -> dosage
    old_dose = {}
    for pid, hname, dose in con.execute(
            "SELECT prescription_id, herb_name, dosage FROM rel_prescription_herb"):
        if hname and dose:
            old_dose[(pid, hname.strip())] = dose

    plan = []
    unresolved = defaultdict(list)
    stats = {"parsed": 0, "herb_missing": 0, "dose_desc": 0, "dose_old": 0, "dose_none": 0}

    for pid, pname, desc in presc:
        if pid in MERGE_MAP:
            continue
        items = parse_description(desc)
        stats["parsed"] += 1
        seen = set()
        for hname, dose in items:
            std = HERB_ALIAS.get(hname, hname)
            if std in seen:
                continue
            seen.add(std)
            herb_id = herbs.get(std)
            if not herb_id:
                unresolved[pname].append(hname)
                stats["herb_missing"] += 1
                continue
            if dose:
                final_dose = dose
                stats["dose_desc"] += 1
            elif (pid, std) in old_dose:
                final_dose = old_dose[(pid, std)]
                stats["dose_old"] += 1
            else:
                final_dose = None
                stats["dose_none"] += 1
            plan.append((pid, herb_id, std, final_dose))

    print(f"解析方剂：{stats['parsed']} 首（已排除 {len(MERGE_MAP)} 首待合并）")
    print(f"生成关联：{len(plan)} 条")
    print(f"  剂量来源 — description: {stats['dose_desc']}, 旧表回退: {stats['dose_old']}, 无: {stats['dose_none']}")
    if unresolved:
        print(f"药材名无法匹配（{stats['herb_missing']} 处）：")
        for p, hs in unresolved.items():
            print(f"  {p}: {hs}")

    if not apply:
        return

    # 备份旧表
    con.execute("DROP TABLE IF EXISTS rel_prescription_herb_old")
    con.execute("ALTER TABLE rel_prescription_herb RENAME TO rel_prescription_herb_old")
    con.execute("""CREATE TABLE rel_prescription_herb (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prescription_id INTEGER NOT NULL,
        herb_id VARCHAR(50) NOT NULL,
        herb_name VARCHAR(100),
        dosage VARCHAR(200),
        UNIQUE(prescription_id, herb_id))""")
    con.executemany(
        "INSERT INTO rel_prescription_herb(prescription_id, herb_id, herb_name, dosage) "
        "VALUES (?,?,?,?)", plan)

    # 删除被合并的方剂，并给保留方剂写别名
    for drop_id, keep_id in MERGE_MAP.items():
        con.execute("DELETE FROM prescription WHERE id=?", (drop_id,))
    for keep_id, aliases in MERGE_ALIASES.items():
        note = "（含别名：" + "、".join(aliases) + "）"
        cur = con.execute("SELECT core_effect FROM prescription WHERE id=?", (keep_id,)).fetchone()
        if cur:
            con.execute("UPDATE prescription SET core_effect = ? WHERE id=?",
                        ((cur[0] or "") + note, keep_id))

    con.commit()
    remain = con.execute("SELECT COUNT(*) FROM prescription").fetchone()[0]
    print(f"✓ 已重建；方剂数 46 → {remain}，旧表保留为 rel_prescription_herb_old")


# ==================== 主流程 ====================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="实际写库（默认 dry-run）")
    ap.add_argument("--skip", nargs="*", default=[], help="跳过指定步骤")
    args = ap.parse_args()
    apply = args.apply

    print(f"数据库：{DB_PATH}")
    print(f"模式：{'APPLY 写库' if apply else 'DRY-RUN 只打印'}")

    con = sqlite3.connect(DB_PATH)
    try:
        if "p0-1" not in args.skip:
            repair_herb_compound(con, apply)
        if "p0-2" not in args.skip:
            repair_compound_props(con, apply)
        if "p0-4" not in args.skip:
            repair_target_rel_fields(con, apply)
        if "p1-1" not in args.skip:
            repair_prescription_herbs(con, apply)
    finally:
        con.close()

    if not apply:
        print("\n[DRY-RUN] 未写库。确认无误后加 --apply 执行。")
    else:
        print("\n✓ 全部修复完成")


if __name__ == "__main__":
    main()
