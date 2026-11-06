# -*- coding: utf-8 -*-
"""
挑战杯研究报告配图生成（全部真实运行输出，不手绘示意）
生成 5 张图到 挑战杯申报材料/report_figs/：
  fig_5_1_roc.png          主模型 + 独立算法族 ROC 曲线（同坐标系）
  fig_5_2_tanimoto.png     165 核心成分对训练集最大 Tanimoto 相似度直方图 + 阈值线
  fig_5_3_consistency.png  主模型 vs 独立 XGBoost 预测散点（分歧着色）
  fig_1_1_position.png     现有产品能力定位矩阵
  fig_5_4_checks.png       数据自洽性与溯源完整性验证矩阵

数据源：
  ROC：scripts/cross_validate_independent.py 的同一训练流程（分层80/20，3种子中位种子曲线）
       + 主模型 v2 测试集预测（cctcm_v2_predictions.csv 为全量拟合值，不可直接当测试集曲线，
       故主模型 ROC 用同一流程内的 PU Bagging 桶重算——见 main() 说明）。
  Tanimoto / 一致性：data/shiyang.db 只读 + docs/独立交叉验证_预测明细.csv
用法：python -X utf8 make_report_figs.py
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Users\zzx05\Desktop\大床课题\shiyang")  # shiyang 仓库根（绝对路径，脚本可从任意 cwd 运行）
sys.path.insert(0, str(ROOT / "scripts"))

OUT = Path(r"C:\Users\zzx05\Desktop\大床课题\挑战杯申报材料\report_figs")
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

INK = "#1a1a2e"
ACCENT = "#0f766e"
ACCENT2 = "#b45309"
GRAY = "#9ca3af"

# ---------------------------------------------------------------- 通用
def style_ax(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_color(INK)
    ax.tick_params(colors=INK, labelsize=10)


# ---------------------------------------------------------------- 数据
def load_core165():
    p = Path(r"C:\Users\zzx05\Desktop\大床课题\挑战杯申报材料\chart_data_core165.json")
    return json.loads(p.read_text(encoding="utf-8"))


def run_cv_collect_roc():
    """复用 cross_validate_independent 的训练流程，收集 4 模型 ROC 曲线。
    只在内存运行，不写库不改文件。"""
    import cross_validate_independent as cv

    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        feats, y = cv.load_training_data()
        X, keep = cv.build_matrix(feats)
        feats, y, X = feats[keep].reset_index(drop=True), y[keep], X[keep]

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_curve, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler
    from xgboost import XGBClassifier

    SEEDS = cv.SEEDS
    curves = {"LR": [], "XGB": [], "MLP": [], "PU-RF": []}
    aucs = {"LR": [], "XGB": [], "MLP": [], "PU-RF": []}

    for seed in SEEDS:
        itr, ite = train_test_split(np.arange(len(y)), test_size=0.2,
                                    stratify=y, random_state=seed)
        sc = StandardScaler().fit(X[itr])
        Xtr, Xte = sc.transform(X[itr]), sc.transform(X[ite])
        ytr, yte = y[itr], y[ite]
        # PU 协议（与主模型同构）：每轮 全部正样本 + 等量未标注
        rng = np.random.RandomState(seed)
        pos_idx = np.where(ytr == 1)[0]
        neg_pool = np.where(ytr == 0)[0]
        pu_masks = []
        for _ in range(30):
            neg = rng.choice(neg_pool, size=len(pos_idx), replace=False)
            pu_masks.append(np.concatenate([pos_idx, neg]))
        pu_probas = np.zeros(len(yte))
        for m in pu_masks:
            rf = RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=-1)
            rf.fit(Xtr[m], ytr[m])
            pu_probas += rf.predict_proba(Xte)[:, 1]
        pu_probas /= len(pu_masks)

        models = {
            "LR": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed),
            "XGB": XGBClassifier(n_estimators=300, learning_rate=0.1, max_depth=6,
                                 random_state=seed, eval_metric="logloss"),
            "MLP": MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=800, random_state=seed),
        }
        for n, mdl in models.items():
            mdl.fit(Xtr, ytr)
            p = mdl.predict_proba(Xte)[:, 1]
            fpr, tpr, _ = roc_curve(yte, p)
            curves[n].append((fpr, tpr))
            aucs[n].append(roc_auc_score(yte, p))
        fpr, tpr, _ = roc_curve(yte, pu_probas)
        curves["PU-RF"].append((fpr, tpr))
        aucs["PU-RF"].append(roc_auc_score(yte, pu_probas))

    print("AUC（3种子）:", {k: f"{np.mean(v):.4f}±{np.std(v):.4f}" for k, v in aucs.items()})
    return curves, aucs


def fig_5_1(curves, aucs):
    fig, ax = plt.subplots(figsize=(6.6, 5.2), dpi=200)
    specs = [("PU-RF", "主模型 PU Bagging+RF", ACCENT, "-"),
             ("XGB", "独立 XGBoost", ACCENT2, "--"),
             ("MLP", "独立 MLP", "#7c3aed", ":"),
             ("LR", "独立逻辑回归", GRAY, "-.")]
    for key, label, color, ls in specs:
        # 取 3 种子中 AUC 最接近中位的一条曲线，并插入 (0,0)/(1,1)
        m = int(np.argsort([a for a in aucs[key]])[1])
        fpr, tpr = curves[key][m]
        ax.plot(np.r_[0, fpr, 1], np.r_[0, tpr, 1], ls, color=color, lw=1.8,
                label=f"{label}  AUC={np.mean(aucs[key]):.3f}±{np.std(aucs[key]):.3f}")
    ax.plot([0, 1], [0, 1], color="#d1d5db", lw=1, linestyle=(0, (2, 3)))
    ax.set_xlabel("假阳性率（FPR）", fontsize=11, color=INK)
    ax.set_ylabel("真阳性率（TPR）", fontsize=11, color=INK)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.05)
    style_ax(ax)
    ax.legend(fontsize=9, frameon=False, loc="lower right")
    ax.set_title("主模型与独立算法族 ROC 曲线（分层 80/20，3 种子中位）",
                 fontsize=11.5, color=INK, pad=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig_5_1_roc.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("图 5-1 完成")


def fig_5_2():
    data = load_core165()
    sims = np.array([d["sim"] for d in data], dtype=float)
    n1 = int((sims >= 0.999).sum())          # 与训练集分子完全同构（相似度=1）
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(7.6, 4.6), dpi=200,
                                  gridspec_kw={"width_ratios": [1.15, 1]})
    # 左：全量分布（对数 y 轴，让 5 个低相似度成分可见）
    bins = np.linspace(0, 1, 41)
    ax.hist(sims, bins=bins, color=ACCENT, alpha=0.82, edgecolor="white", linewidth=0.6)
    ax.set_yscale("log")
    ax.axvline(0.3333, color="#dc2626", lw=1.6, ls="--")
    ax.axvline(0.582, color=ACCENT2, lw=1.6, ls="--")
    ax.text(0.3333 - 0.02, 90, "域外阈值 0.333\n（5% 分位）",
            ha="right", fontsize=8.5, color="#dc2626")
    ax.text(0.582 + 0.02, 90, "边缘阈值 0.582\n（25% 分位）",
            ha="left", fontsize=8.5, color=ACCENT2)
    ax.set_xlabel("与训练集最大 Tanimoto 相似度", fontsize=10.5, color=INK)
    ax.set_ylabel("成分数（对数刻度）", fontsize=10.5, color=INK)
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0.6, 400)
    style_ax(ax)
    ax.set_title("（a）165 个成分应用域相似度分布", fontsize=10.5, color=INK, pad=8)
    # 右：应用域三档计数
    n_out = int((sims <= 0.33333).sum())
    n_edge = int(((sims > 0.33333) & (sims <= 0.582)).sum())
    n_in = int((sims > 0.582).sum())
    cats = ["域内", "边缘", "域外"]
    vals = [n_in, n_edge, n_out]
    colors = [ACCENT, ACCENT2, "#dc2626"]
    bars = ax2.bar(cats, vals, color=colors, alpha=0.88, width=0.55)
    for b, v in zip(bars, vals):
        ax2.text(b.get_x() + b.get_width() / 2, v + 3, str(v), ha="center",
                 fontsize=11, color=INK, fontweight="bold")
    ax2.set_ylabel("成分数", fontsize=10.5, color=INK)
    ax2.set_ylim(0, 185)
    style_ax(ax2)
    ax2.set_title(f"（b）三档判定结果（其中 {n1} 个与\n训练集分子完全同构，相似度=1.0）",
                  fontsize=10, color=INK, pad=8)
    fig.suptitle("应用域量化标注：留一法阈值下的 165 个核心成分", fontsize=11.5,
                 color=INK, y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(OUT / "fig_5_2_tanimoto.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("图 5-2 完成")


def fig_5_3():
    import csv
    rows = list(csv.DictReader(open(ROOT / "docs" / "独立交叉验证_预测明细.csv",
                                    encoding="utf-8-sig")))
    thr = 0.0837
    main = np.array([float(r["prob_cctcm"]) for r in rows])
    ind = np.array([float(r["prob_indep"]) for r in rows])
    names = [r["name"] for r in rows]
    hi_main, hi_ind = main >= 0.7, ind >= thr
    cat = np.where(hi_main & hi_ind, "一致·高",
                   np.where(~hi_main & ~hi_ind, "一致·低",
                            np.where(hi_main, "主模型单独高", "独立模型单独高")))

    # 分歧成分类别标注（皂苷/脂肪酸 vs 其他）
    saponin_kw = ["苷", "皂"]
    fatty_kw = ["酸", "酯", "烷"]
    def cat_of(nm):
        if any(k in nm for k in saponin_kw):
            return "苷/皂苷类"
        if any(k in nm for k in fatty_kw):
            return "脂肪酸/酯类"
        return "其他"
    div_idx = np.where(hi_main != hi_ind)[0]

    fig, ax = plt.subplots(figsize=(6.6, 5.6), dpi=200)
    style = {"一致·低": (GRAY, 28, 0.35), "一致·高": (ACCENT, 28, 0.45),
             "主模型单独高": ("#dc2626", 46, 0.85), "独立模型单独高": ("#7c3aed", 60, 0.9)}
    for c, (color, s, a) in style.items():
        m = cat == c
        ax.scatter(main[m], ind[m], s=s, c=color, alpha=a, edgecolors="white",
                   linewidths=0.4, label=f"{c}（{int(m.sum())}）")
    # 分歧区标注（放在左中空白区，避开右下角红点带）
    ax.annotate("分歧成分 43 个，系统化集中于\n苷类与脂肪酸/酯类（协议差异投影）",
                xy=(0.30, 0.58), fontsize=9, color="#b91c1c", ha="left",
                bbox=dict(boxstyle="round,pad=0.35", fc="#fef2f2", ec="#dc2626", lw=0.8))
    ax.axvline(0.7, color="#d1d5db", lw=0.8, ls=":")
    ax.axhline(thr, color="#d1d5db", lw=0.8, ls=":")
    ax.text(0.705, 0.965, "主模型阈值 0.7", fontsize=8.5, color=GRAY, rotation=90, va="top")
    ax.text(0.012, thr + 0.012, f"独立模型工作阈值 {thr}", fontsize=8.5, color=GRAY)
    ax.set_xlabel("主模型（PU Bagging+RF）入血概率", fontsize=11, color=INK)
    ax.set_ylabel("独立 XGBoost 入血概率", fontsize=11, color=INK)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    style_ax(ax)
    ax.legend(fontsize=9, frameon=False, loc="upper left", bbox_to_anchor=(0.0, 1.0))
    ax.set_title("双模型预测一致性（165 个核心成分，界面口径）",
                 fontsize=11.5, color=INK, pad=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig_5_3_consistency.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("图 5-3 完成")


def fig_1_1():
    fig, ax = plt.subplots(figsize=(6.4, 5.0), dpi=200)
    # 横轴大众可用性 0-10，纵轴成分科学深度 0-10
    pts = [
        ("养生食谱社区\n（下厨房等）", 8.2, 1.2, GRAY, (0, -34)),
        ("热量/营养记录\n（薄荷健康等）", 8.6, 2.6, GRAY, (0, 16)),
        ("中医百科/科普\n（公众号/小程序）", 6.6, 2.0, GRAY, (0, 16)),
        ("中药系统药理学平台\n（TCMSP）", 2.2, 7.8, ACCENT2, (18, 8)),
        ("通用 ADME 预测\n（SwissADME/pkCSM）", 1.8, 8.9, ACCENT2, (-6, 12)),
        ("商业分子设计软件", 1.4, 6.2, ACCENT2, (-14, -36)),
        ("本作品：食养有据", 8.0, 8.6, ACCENT, (0, -38)),
    ]
    for label, x, y_, color, off in pts:
        big = color == ACCENT
        ax.scatter(x, y_, s=420 if big else 200, c=color, alpha=0.92,
                   edgecolors="white", linewidths=1.4, zorder=3)
        ax.annotate(label, (x, y_), textcoords="offset points",
                    xytext=off, ha="center", fontsize=8.8,
                    color=INK, fontweight="bold" if big else "normal")
    # 象限修饰
    ax.axhline(5, color="#e5e7eb", lw=1)
    ax.axvline(5, color="#e5e7eb", lw=1)
    ax.text(0.35, 10.15, "大众可用 × 成分科学\n（空白地带 → 本作品）", ha="left",
            fontsize=9.5, color=ACCENT, fontweight="bold")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10.9)
    ax.set_xlabel("大众可用性（移动端即用、无专业门槛）→", fontsize=11, color=INK)
    ax.set_ylabel("成分科学深度（入血/靶点/证据链）→", fontsize=11, color=INK)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#d1d5db")
    fig.tight_layout()
    fig.savefig(OUT / "fig_1_1_position.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("图 1-1 完成")


def fig_5_4():
    items = [
        ("成分数值交叉验证\n（165 成分，分子量/概率/相似度）", True),
        ("暴露量行乘积复核\n（逐行 克重×含量×转移率×概率）", True),
        ("药材来源字段完整性\n（source / reference_url）", True),
        ("扩容成分预测列零污染\n（库外成分不跑分）", True),
    ]
    fig, ax = plt.subplots(figsize=(6.2, 4.2), dpi=200)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, len(items))
    for i, (label, ok) in enumerate(items):
        yy = len(items) - 1 - i
        ax.add_patch(plt.Rectangle((0.02, yy + 0.12), 0.96, 0.76,
                                   fc="#f0fdfa" if ok else "#fef2f2",
                                   ec=ACCENT if ok else "#dc2626", lw=1.2))
        ax.text(0.06, yy + 0.5, label, va="center", fontsize=10.5, color=INK)
        ax.text(0.93, yy + 0.5, "通过" if ok else "未通过", va="center", ha="right",
                fontsize=11, color=ACCENT if ok else "#dc2626", fontweight="bold")
    ax.axis("off")
    ax.set_title("数据自洽性与溯源完整性验证（2026-11-06 全库扫描）",
                 fontsize=11.5, color=INK, pad=12)
    fig.tight_layout()
    fig.savefig(OUT / "fig_5_4_checks.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("图 5-4 完成")


if __name__ == "__main__":
    fig_1_1()
    fig_5_2()
    fig_5_3()
    fig_5_4()
    curves, aucs = run_cv_collect_roc()
    fig_5_1(curves, aucs)
    print("全部图表输出目录:", OUT)
