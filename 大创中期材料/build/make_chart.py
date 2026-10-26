# 图1：双模型入血预测性能对比（ROC-AUC）
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 中文字体（Windows 自带黑体）
font_manager.fontManager.addfont(r"C:\Windows\Fonts\simhei.ttf")
plt.rcParams["font.family"] = "SimHei"
plt.rcParams["axes.unicode_minus"] = False

models = ["ccTCM 2.0\n（主力模型）", "HERB 2.0\n（兜底模型）"]
grid_auc = [0.8229, 0.8463]
grid_err = [0.0081, 0.0105]
test_auc = [0.8073, 0.8243]

x = [0, 1]
w = 0.32
fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=150)
b1 = ax.bar([i - w / 2 for i in x], grid_auc, width=w, yerr=grid_err, capsize=5,
            color="#2E86C1", edgecolor="none", label="网格搜索交叉验证 AUC（均值±标准差）")
b2 = ax.bar([i + w / 2 for i in x], test_auc, width=w,
            color="#1A5276", edgecolor="none", label="独立测试集 AUC")

for rect, v in zip(b1, grid_auc):
    ax.text(rect.get_x() + rect.get_width() / 2, v + 0.028, f"{v:.4f}", ha="center", fontsize=10)
for rect, v in zip(b2, test_auc):
    ax.text(rect.get_x() + rect.get_width() / 2, v + 0.006, f"{v:.4f}", ha="center", fontsize=10)

ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=11)
ax.set_ylim(0.70, 0.92)
ax.set_ylabel("ROC-AUC", fontsize=11)
ax.set_title("PU Learning 双模型入血预测性能对比", fontsize=13, pad=12)
ax.legend(fontsize=9.5, loc="lower right", frameon=False)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.35)
fig.tight_layout()
fig.savefig("chart_auc.png", dpi=150)
print("chart saved")
