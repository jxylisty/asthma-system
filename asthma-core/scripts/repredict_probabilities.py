# -*- coding: utf-8 -*-
"""
用重训后的模型重新预测库内 569 个成分的入血概率

背景：
  理化性质表有 957 行整体右移一列（LogS=分子式、LogD=分子量、LogP=重原子数…），
  原 ccTCM 模型训练时直接读入这些错误值（pd.to_numeric 把分子式转成 NaN，
  但 LogD/LogP/Pgp/F20%/Caco-2/MDCK 等 11 个特征是错误数值，未被填补逻辑纠正）。
  现已用 RDKit 重算 12 个结构描述符、7 个 ADME 列置空，并重训模型：
    完整版 test ROC-AUC 0.8073 → 0.8129，PR-AUC 0.7003 → 0.7025，F1 0.6414 → 0.6546

本脚本用新模型重算 compound.prob_cctcm / prob_herb。

用法：
    python -X utf8 scripts/repredict_probabilities.py           # dry-run
    python -X utf8 scripts/repredict_probabilities.py --apply   # 写库
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

CORE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPO = os.path.abspath(os.path.join(CORE, "..", ".."))
sys.path.insert(0, CORE)

DB_PATH = os.path.join(CORE, "data", "asthma_v2.db")
CCTCM_CLEAN_CSV = os.path.join(REPO, "数据库溯源", "入血概率cctcm2.0", "cctcm_v2_predictions.csv")
MENTOR_XLSX = os.path.join(REPO, "数据库溯源", "主要展示数据均为cctcm2.0",
                           "化合物理化性质和生物利用度属性-赵玉男.xlsx")
HERB_FEAT_CSV = os.path.join(REPO, "入血预测", "herb2.0", "herb2.0", "processed_features.csv")

FP_BITS = 1024


def norm_cid(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    try:
        return str(int(float(s)))
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    import sqlite3
    from app.services.ml import load_cctcm_model, load_herb_model
    from app.services.feature_engine import (
        compute_all_19_features, compute_herb_features, morgan_fp, parse_smiles,
    )

    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT id, name, smiles, pubchem_cid, prob_cctcm, prob_herb FROM compound", con)
    df["cid"] = df["pubchem_cid"].apply(norm_cid)
    print(f"数据库化合物: {len(df)} 行，有 SMILES {df['smiles'].notna().sum()}，有 cid {df['cid'].notna().sum()}")

    # ---------- ccTCM ----------
    print("\n[ccTCM] 读取预测 CSV 与导师特征表...")
    clean = pd.read_csv(CCTCM_CLEAN_CSV)
    clean["cid"] = clean["pubchem_cid"].apply(norm_cid)
    cid2compound = dict(zip(clean["cid"], clean["Compound"].astype(str)))

    # 导师理化表：跳过 957 行错位数据（LogS 列是分子式字符串）
    mentor = pd.read_excel(MENTOR_XLSX, header=1)
    mentor = mentor.drop_duplicates(subset="Compound")
    mentor_map = {}
    skipped_shifted = 0
    for _, r in mentor.iterrows():
        logs = r.get("LogS")
        if isinstance(logs, str):
            try:
                float(logs)
            except ValueError:
                skipped_shifted += 1
                continue
        mentor_map[str(r["Compound"]).strip().lower()] = r
    print(f"  导师表可用 {len(mentor_map)} 行（跳过 {skipped_shifted} 行错位数据）")

    cctcm_bundle = load_cctcm_model()
    c_cols = cctcm_bundle["feature_cols"]
    c_idx = {c: i for i, c in enumerate(c_cols)}

    Xc = np.full((len(df), len(c_cols)), np.nan)
    modes = []
    for row, (_, r) in enumerate(df.iterrows()):
        mol = parse_smiles(r["smiles"]) if isinstance(r["smiles"], str) else None
        feats = compute_all_19_features(r["smiles"]) if mol else {}
        fp = morgan_fp(mol)

        mrow = None
        if r["cid"]:
            comp = cid2compound.get(r["cid"])
            if comp:
                mrow = mentor_map.get(comp.strip().lower())

        if mrow is not None:
            for col in c_cols[:19]:
                v = mrow.get(col)
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if not np.isnan(v):
                    feats[col] = v
            modes.append("B:导师特征")
        else:
            modes.append("A:SMILES")

        for k, v in feats.items():
            j = c_idx.get(k)
            if j is not None and v is not None and not (isinstance(v, float) and np.isnan(v)):
                Xc[row, j] = float(v)
        for b in range(FP_BITS):
            j = c_idx.get(f"FP_{b}")
            if j is not None:
                Xc[row, j] = fp[b]

    n_b = sum(1 for m in modes if m.startswith("B"))
    print(f"  模式B(导师特征): {n_b} | 模式A(SMILES): {len(df) - n_b}")
    Xc = np.where(np.isinf(Xc), np.nan, Xc)
    Xc_p = cctcm_bundle["scaler"].transform(cctcm_bundle["imputer"].transform(Xc))
    prob_cctcm = cctcm_bundle["model"].predict_proba(Xc_p)[:, 1]
    print(f"  预测均值 {prob_cctcm.mean():.3f}")

    # ---------- HERB ----------
    print("\n[HERB] 关联 processed_features.csv...")
    herb_desc = ["MolWt", "NumHAcceptors", "NumHDonors", "MolLogP", "NumRotatableBonds",
                 "Drug_likeness", "OB_score", "TPSA", "MolMR", "FractionCSP3",
                 "NumAromaticRings", "NumAliphaticRings", "QED"]
    fp_cols = [f"FP_{i}" for i in range(FP_BITS)]
    hf = pd.read_csv(HERB_FEAT_CSV, usecols=["PubChem_id"] + herb_desc + fp_cols)
    hf["cid"] = hf["PubChem_id"].apply(norm_cid)
    hf = hf.dropna(subset=["cid"]).drop_duplicates(subset="cid").set_index("cid")

    herb_bundle = load_herb_model()
    h_cols = herb_bundle["feature_cols"]
    h_idx = {c: i for i, c in enumerate(h_cols)}

    Xh = np.full((len(df), len(h_cols)), np.nan)
    herb_modes = []
    for row, (_, r) in enumerate(df.iterrows()):
        mol = parse_smiles(r["smiles"]) if isinstance(r["smiles"], str) else None
        fp = morgan_fp(mol)
        src = hf.loc[r["cid"]] if (r["cid"] and r["cid"] in hf.index) else None

        if src is not None:
            feats = {}
            for c in herb_desc:
                try:
                    feats[c] = float(src[c])
                except (TypeError, ValueError):
                    pass
            fp = np.array([int(src[c]) for c in fp_cols], dtype=np.int8)
            herb_modes.append("B:HERB库特征")
        else:
            feats = compute_herb_features(mol) if mol else {}
            herb_modes.append("A:SMILES")

        for k, v in feats.items():
            j = h_idx.get(k)
            if j is not None and v is not None:
                Xh[row, j] = float(v)
        for b in range(FP_BITS):
            j = h_idx.get(f"FP_{b}")
            if j is not None:
                Xh[row, j] = fp[b]

    n_hb = sum(1 for m in herb_modes if m.startswith("B"))
    print(f"  模式B(HERB库特征): {n_hb} | 模式A(SMILES): {len(df) - n_hb}")
    Xh = np.where(np.isinf(Xh), np.nan, Xh)
    Xh_p = herb_bundle["scaler"].transform(herb_bundle["imputer"].transform(Xh))
    prob_herb = herb_bundle["model"].predict_proba(Xh_p)[:, 1]
    print(f"  预测均值 {prob_herb.mean():.3f}")

    # ---------- 变化统计 ----------
    d_c = np.abs(prob_cctcm - df["prob_cctcm"].fillna(0).values)
    d_h = np.abs(prob_herb - df["prob_herb"].fillna(0).values)
    print(f"\n[变化] prob_cctcm 平均绝对变化 {d_c.mean():.4f}，最大 {d_c.max():.4f}，"
          f">0.2 的 {int((d_c > 0.2).sum())} 个")
    print(f"       prob_herb  平均绝对变化 {d_h.mean():.4f}，最大 {d_h.max():.4f}")
    print(f"[阈值] prob_cctcm>=0.5: 旧 {int((df['prob_cctcm'] >= 0.5).sum())} → "
          f"新 {int((prob_cctcm >= 0.5).sum())}")

    if not args.apply:
        print("\n[dry-run] 未写库")
        con.close()
        return

    cur = con.cursor()
    for (_, r), pc, ph in zip(df.iterrows(), prob_cctcm, prob_herb):
        cur.execute("UPDATE compound SET prob_cctcm=?, prob_herb=? WHERE id=?",
                    (round(float(pc), 4), round(float(ph), 4), str(r["id"])))
    con.commit()
    print(f"\n✓ 已更新 {len(df)} 条概率")
    con.close()


if __name__ == "__main__":
    main()
