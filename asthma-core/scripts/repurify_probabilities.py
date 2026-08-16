# -*- coding: utf-8 -*-
"""
数据库入血概率重灌脚本（一次性，保留入库作审计溯源）

作用：
1. 审计旧 prob_cctcm 中的"兜底回填"脏值（cid 匹配不上 ccTCM 干净 CSV
   且 prob_cctcm == blood_entry_probability），导出审计报告
2. 用 V2 union 正式版模型对全库化合物重新预测 prob_cctcm / prob_herb：
   - ccTCM 优先"模式 B"：经 cid→Compound 关联导师特征表（含 7 项真实 ADME），
     关联不上的走 SMILES 模式（ADME 由中位数填补）
   - HERB 优先关联 processed_features.csv（13 描述符 + 指纹全量现成），
     关联不上的走 SMILES 模式
3. blood_entry_probability 重定义为派生字段 = 新 prob_cctcm
   （过渡方案：前端/后端消费方零改动；旧手填假值存档于审计 CSV）

用法（在 asthma-core 目录下）：
    python scripts/repurify_probabilities.py           # dry-run：只出报告不写库
    python scripts/repurify_probabilities.py --apply   # 真正写库
"""
import os
import sys
import glob
import argparse
import sqlite3
import numpy as np
import pandas as pd

_ASTHMA_CORE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_REPO_ROOT = os.path.abspath(os.path.join(_ASTHMA_CORE, '..'))
sys.path.insert(0, _ASTHMA_CORE)

DB_PATH = os.path.join(_ASTHMA_CORE, 'data', 'asthma_v2.db')
CCTCM_CLEAN_CSV = os.path.join(_REPO_ROOT, '数据库溯源', '入血概率cctcm2.0', 'cctcm_v2_predictions.csv')
MENTOR_XLSX = os.path.join(_REPO_ROOT, '入血预测', 'cctcm2.0', '化合物理化性质和生物利用度属性-赵玉男.xlsx')
HERB_FEAT_CSV = os.path.join(_REPO_ROOT, '入血预测', 'herb2.0', 'herb2.0', 'processed_features.csv')
REPORT_DIR = os.path.join(_ASTHMA_CORE, 'scripts', 'reports')

FP_BITS = 1024


def norm_cid(x):
    """pubchem_cid 统一转字符串；空/NaN 返回 None"""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip()
    if not s or s.lower() in ('nan', 'none'):
        return None
    try:
        return str(int(float(s)))
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='真正写入数据库（默认 dry-run）')
    args = parser.parse_args()

    os.makedirs(REPORT_DIR, exist_ok=True)
    stamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')

    from app.services.ml import load_cctcm_model, load_herb_model
    from app.services.feature_engine import (
        parse_smiles, compute_all_19_features, compute_herb_features, morgan_fp
    )

    # ---------- 读取数据库 ----------
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT id, name, smiles, pubchem_cid, '
                     'blood_entry_probability, prob_cctcm, prob_herb FROM compound', con)
    df['cid'] = df['pubchem_cid'].apply(norm_cid)
    print(f"数据库化合物: {len(df)} 行，有 SMILES {df['smiles'].notna().sum()} 行，"
          f"有 cid {df['cid'].notna().sum()} 行")

    # ---------- 步骤1：脏值审计 ----------
    clean = pd.read_csv(CCTCM_CLEAN_CSV)
    clean['cid'] = clean['pubchem_cid'].apply(norm_cid)
    clean_map = dict(zip(clean['cid'], clean['预测入血概率']))

    in_csv = df['cid'].map(lambda c: c in clean_map if c else False)
    eq_blood = (df['prob_cctcm'].notna() & df['blood_entry_probability'].notna() & (
        (df['prob_cctcm'] - df['blood_entry_probability']).abs() < 0.005))
    dirty = (~in_csv) & eq_blood
    print(f"\n[审计] prob_cctcm 与干净 CSV 匹配: {int(in_csv.sum())} 行 | "
          f"判定为回填脏值: {int(dirty.sum())} 行（其中无 cid {int((dirty & df['cid'].isna()).sum())} 行）")

    audit = df.loc[dirty, ['id', 'name', 'pubchem_cid', 'blood_entry_probability', 'prob_cctcm']].copy()
    audit['判定'] = '回填脏值（非 ccTCM 模型输出）'
    audit = audit.rename(columns={'blood_entry_probability': '旧blood(手填)', 'prob_cctcm': '旧prob_cctcm(脏)'})

    # ---------- 步骤2：ccTCM 重灌（模式B优先） ----------
    print('\n[ccTCM] 关联导师特征表...')
    mentor = pd.read_excel(MENTOR_XLSX, header=1)
    mentor = mentor.drop_duplicates(subset='Compound')
    mentor_map = {str(r['Compound']).strip().lower(): r for _, r in mentor.iterrows()}

    cid2compound = dict(zip(clean['cid'], clean['Compound'].astype(str)))
    cctcm_bundle = load_cctcm_model()
    c_cols = cctcm_bundle['feature_cols']
    c_idx = {c: i for i, c in enumerate(c_cols)}

    Xc = np.full((len(df), len(c_cols)), np.nan)
    cctcm_mode = []
    for row, (_, r) in enumerate(df.iterrows()):
        mol = parse_smiles(r['smiles']) if isinstance(r['smiles'], str) else None
        feats = compute_all_19_features(r['smiles']) if mol else {}
        fp = morgan_fp(mol)

        mrow = None
        if r['cid']:
            comp = cid2compound.get(r['cid'])
            if comp:
                mrow = mentor_map.get(comp.strip().lower())

        if mrow is not None:
            # 导师表 LogS 列混有分子式等脏字符串（训练时同样 coerce 为 NaN）
            for col in c_cols[:19]:
                v = mrow.get(col)
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if not np.isnan(v):
                    feats[col] = v
            cctcm_mode.append('B:导师特征')
        else:
            cctcm_mode.append('A:SMILES')

        for k, v in feats.items():
            j = c_idx.get(k)
            if j is not None and v is not None and not (isinstance(v, float) and np.isnan(v)):
                Xc[row, j] = float(v)
        for b in range(FP_BITS):
            j = c_idx.get(f'FP_{b}')
            if j is not None:
                Xc[row, j] = fp[b]

    n_b = sum(1 for m in cctcm_mode if m.startswith('B'))
    print(f"  模式B(导师特征): {n_b} 行 | 模式A(SMILES): {len(df)-n_b} 行")
    Xc = np.where(np.isinf(Xc), np.nan, Xc)
    Xc_p = cctcm_bundle['scaler'].transform(cctcm_bundle['imputer'].transform(Xc))
    prob_cctcm_new = cctcm_bundle['model'].predict_proba(Xc_p)[:, 1]
    print(f"  预测完成，均值 {prob_cctcm_new.mean():.3f}")

    # ---------- 步骤3：HERB 重灌 ----------
    print('\n[HERB] 关联 processed_features.csv...')
    herb_desc = ['MolWt', 'NumHAcceptors', 'NumHDonors', 'MolLogP', 'NumRotatableBonds',
                 'Drug_likeness', 'OB_score', 'TPSA', 'MolMR', 'FractionCSP3',
                 'NumAromaticRings', 'NumAliphaticRings', 'QED']
    fp_cols = [f'FP_{i}' for i in range(FP_BITS)]
    hf = pd.read_csv(HERB_FEAT_CSV, usecols=['PubChem_id'] + herb_desc + fp_cols)
    hf['cid'] = hf['PubChem_id'].apply(norm_cid)
    hf = hf.dropna(subset=['cid']).drop_duplicates(subset='cid').set_index('cid')

    herb_bundle = load_herb_model()
    h_cols = herb_bundle['feature_cols']
    h_idx = {c: i for i, c in enumerate(h_cols)}

    Xh = np.full((len(df), len(h_cols)), np.nan)
    herb_mode = []
    for row, (_, r) in enumerate(df.iterrows()):
        mol = parse_smiles(r['smiles']) if isinstance(r['smiles'], str) else None
        fp = morgan_fp(mol)
        src = hf.loc[r['cid']] if (r['cid'] and r['cid'] in hf.index) else None

        if src is not None:
            feats = {}
            for c in herb_desc:
                try:
                    feats[c] = float(src[c])
                except (TypeError, ValueError):
                    pass  # 个别格子存了分号分隔的双值等脏数据，跳过由 NaN 填补
            fp = np.array([int(src[c]) for c in fp_cols], dtype=np.int8)
            herb_mode.append('B:HERB库特征')
        else:
            feats = compute_herb_features(mol) if mol else {}
            herb_mode.append('A:SMILES')

        for k, v in feats.items():
            j = h_idx.get(k)
            if j is not None and v is not None:
                Xh[row, j] = float(v)
        for b in range(FP_BITS):
            j = h_idx.get(f'FP_{b}')
            if j is not None:
                Xh[row, j] = fp[b]

    n_hb = sum(1 for m in herb_mode if m.startswith('B'))
    print(f"  模式B(HERB库特征): {n_hb} 行 | 模式A(SMILES): {len(df)-n_hb} 行")
    Xh = np.where(np.isinf(Xh), np.nan, Xh)
    Xh_p = herb_bundle['scaler'].transform(herb_bundle['imputer'].transform(Xh))
    prob_herb_new = herb_bundle['model'].predict_proba(Xh_p)[:, 1]
    print(f"  预测完成，均值 {prob_herb_new.mean():.3f}")

    # ---------- 步骤4：报告 ----------
    report = pd.DataFrame({
        'id': df['id'], 'name': df['name'], 'cid': df['cid'],
        '旧prob_cctcm': df['prob_cctcm'], '新prob_cctcm': np.round(prob_cctcm_new, 4),
        '旧prob_herb': df['prob_herb'], '新prob_herb': np.round(prob_herb_new, 4),
        '旧blood(手填)': df['blood_entry_probability'],
        'ccTCM模式': cctcm_mode, 'HERB模式': herb_mode,
        '旧值判定': np.where(dirty, '回填脏值', np.where(in_csv, '干净', '无cctcm值')),
    })
    report['cctcm变化'] = (report['新prob_cctcm'] - report['旧prob_cctcm']).round(4)

    rp = os.path.join(REPORT_DIR, f'repurify_{stamp}')
    report.to_csv(rp + '_delta.csv', index=False, encoding='utf-8-sig')
    audit.to_csv(rp + '_audit_dirty.csv', index=False, encoding='utf-8-sig')

    print('\n[统计] 阈值分布变化:')
    print(f"  prob_cctcm >= 0.5: 旧 {int((df['prob_cctcm'] >= 0.5).sum())} → 新 {int((prob_cctcm_new >= 0.5).sum())}")
    print(f"  prob_cctcm >= 0.85: 旧 {int((df['prob_cctcm'] >= 0.85).sum())} → 新 {int((prob_cctcm_new >= 0.85).sum())}")
    print(f"  prob_herb  >= 0.5: 旧 {int((df['prob_herb'].fillna(0) >= 0.5).sum())} → 新 {int((prob_herb_new >= 0.5).sum())}")
    print(f"  cctcm 变化>0.2 的化合物: {int((report['cctcm变化'].abs() > 0.2).sum())} 个")
    print(f"\n报告: {rp}_delta.csv / _audit_dirty.csv")

    # ---------- 步骤5：写库 ----------
    if not args.apply:
        print('\n[dry-run] 未写库。确认报告无误后加 --apply 执行。')
        con.close()
        return

    cur = con.cursor()
    n_upd = 0
    for (_, r), pc, ph in zip(df.iterrows(), prob_cctcm_new, prob_herb_new):
        cur.execute(
            'UPDATE compound SET prob_cctcm=?, prob_herb=? WHERE id=?',
            (round(float(pc), 4), round(float(ph), 4), str(r['id'])))
        n_upd += cur.rowcount
    con.commit()

    chk = pd.read_sql('SELECT COUNT(*) n FROM compound WHERE prob_cctcm IS NULL', con)
    print(f"\n[apply] 已更新 {n_upd} 行；prob_cctcm 空值 {int(chk['n'][0])} 行")
    print("注：blood_entry_probability 列已于 2026-08-16 最终清理时删除（响应字段保留为 prob_cctcm 别名）")
    con.close()


if __name__ == '__main__':
    main()
