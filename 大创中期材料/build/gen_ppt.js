// 大创中期答辩 PPT — 12页，医疗蓝主题（与中期报告同色系），深-浅-深三明治
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 × 7.5"
pres.author = "张震翔 周俊峰";
pres.title = "基于入血预测的中医治疗儿童哮喘作用机制分析 — 中期检查汇报";

// ---------- 画布与调色板（BG→PRIMARY→ACCENT，与 Word 材料一致） ----------
const W = 13.33, H = 7.5, M = 0.6;
const DARK = "0F2740";      // 封面/结尾深底
const PRIMARY = "1A5276";   // 主色（标题/图形）
const ACCENT = "2E86C1";    // 强调色
const TINT = "EDF3F8";      // 浅蓝底
const TEXT = "1E2A32";
const MUTED = "5A6B7A";
const LIGHT = "9FC3DC";     // 深底上的浅文字
const F = "微软雅黑";

const shadow = () => ({ type: "outer", color: "1A5276", blur: 7, offset: 2, angle: 45, opacity: 0.14 });
const bu = () => ({ code: "2013", indent: 12 });

// ---------- 公共构件 ----------
function header(slide, kicker, title) {
  slide.addText(kicker, { x: M, y: 0.42, w: 8.4, h: 0.32, fontSize: 13, color: ACCENT, fontFace: F, bold: true, margin: 0 });
  slide.addText(title, { x: M, y: 0.74, w: W - 2 * M, h: 0.62, fontSize: 28, color: TEXT, fontFace: F, bold: true, margin: 0 });
  slide.addText("东方智喘 · 中期检查汇报", { x: W - 3.1 - M, y: 0.46, w: 3.1, h: 0.3, fontSize: 11, color: MUTED, fontFace: F, align: "right", margin: 0 });
}
function pageNum(slide, n) {
  slide.addText(String(n), { x: W - 0.9, y: H - 0.52, w: 0.5, h: 0.3, fontSize: 11, color: MUTED, fontFace: F, align: "right", margin: 0 });
}
function hairline(slide, x, y, w) {
  slide.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: "D5DFE8", width: 0.75 } });
}
function arrow(slide, x1, y1, x2, y2) {
  slide.addShape(pres.shapes.LINE, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color: ACCENT, width: 2, endArrowType: "triangle" } });
}
function box(slide, x, y, w, h, fill, lineColor) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: fill }, line: lineColor ? { color: lineColor, width: 1 } : { color: fill, width: 0 },
    shadow: shadow(),
  });
}

// ============ S1 封面 ============
{
  const s = pres.addSlide();
  s.background = { color: DARK };
  s.addShape(pres.shapes.OVAL, { x: 9.2, y: 3.4, w: 6.2, h: 6.2, fill: { color: ACCENT, transparency: 88 }, line: { color: ACCENT, width: 0 } });
  s.addShape(pres.shapes.OVAL, { x: 10.9, y: 1.1, w: 3.4, h: 3.4, fill: { color: LIGHT, transparency: 90 }, line: { color: LIGHT, width: 0 } });
  s.addText("大学生创新创业训练计划 · 重点项目 · 中期检查汇报", { x: M, y: 1.15, w: 11, h: 0.4, fontSize: 15, color: LIGHT, fontFace: F, bold: true, margin: 0 });
  s.addText([
    { text: "基于入血预测的中医治疗儿童哮喘", options: { breakLine: true } },
    { text: "作用机制分析", options: {} },
  ], { x: M, y: 1.85, w: 11.8, h: 1.9, fontSize: 40, color: "FFFFFF", fontFace: F, bold: true, lineSpacingMultiple: 1.15, margin: 0 });
  s.addText("中药入血成分智能预测与方剂机制可视化分析平台（东方智喘）", { x: M, y: 3.95, w: 11.5, h: 0.5, fontSize: 17, color: LIGHT, fontFace: F, margin: 0 });
  hairline(s, M, 5.9, 6.8);
  s.addText([
    { text: "汇报人：张震翔　周俊峰", options: { breakLine: true } },
    { text: "指导教师：丁有伟　赵玉男　　南京中医药大学 人工智能与信息技术学院", options: {} },
  ], { x: M, y: 6.1, w: 8.9, h: 0.85, fontSize: 14, color: LIGHT, fontFace: F, lineSpacingMultiple: 1.4, margin: 0 });
  s.addText("2026年10月", { x: W - 3.0 - M, y: 6.55, w: 3.0, h: 0.4, fontSize: 14, color: LIGHT, fontFace: F, align: "right", margin: 0 });
  s.addNotes("开场30秒：一句话讲清定位——用AI预测中药成分能否入血，再从入血成分出发解释方剂治疗儿童哮喘的机制。强调是省级重点大创。");
}

// ============ S2 项目回顾 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "PROJECT REVIEW", "项目回顾：以入血预测为切口的机制分析平台");
  s.addText("研究背景", { x: M, y: 1.62, w: 4.4, h: 0.4, fontSize: 17, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  s.addText("中药复方\u201c哪些成分能真正入血起效\u201d长期依赖动物实验测定，成本高、通量低；传统网络药理学不筛入血成分，靶点假阳性高。", {
    x: M, y: 2.06, w: 4.4, h: 1.7, fontSize: 14.5, color: TEXT, fontFace: F, lineSpacingMultiple: 1.35, margin: 0,
  });
  s.addText("项目思路", { x: M, y: 3.9, w: 4.4, h: 0.4, fontSize: 17, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  s.addText("自研入血预测模型先筛\u201c真正起效的成分\u201d，再结合网络药理学与富集分析解释机制，形成数据—模型—机制—系统全链条工具。", {
    x: M, y: 4.34, w: 4.4, h: 1.7, fontSize: 14.5, color: TEXT, fontFace: F, lineSpacingMultiple: 1.35, margin: 0,
  });
  const rows = [
    ["01", "数据库建设", "儿童哮喘方剂、药材、化合物、靶点多源数据整合与治理"],
    ["02", "入血预测模型", "PU Learning 双模型，面向无可靠负样本场景建模"],
    ["03", "作用机制评价", "四层网络药理学拓扑 + GSEA 富集 + 三维疗效评分"],
    ["04", "可视化系统", "前后端分离平台，预测、分析、AI 报告一体化"],
  ];
  let y = 1.66;
  for (const [no, t, d] of rows) {
    s.addText(no, { x: 5.6, y: y + 0.06, w: 0.9, h: 0.6, fontSize: 30, color: ACCENT, fontFace: F, bold: true, margin: 0 });
    s.addText(t, { x: 6.6, y, w: 5.9, h: 0.42, fontSize: 17.5, color: TEXT, fontFace: F, bold: true, margin: 0 });
    s.addText(d, { x: 6.6, y: y + 0.44, w: 5.9, h: 0.4, fontSize: 13.5, color: MUTED, fontFace: F, margin: 0 });
    if (no !== "04") hairline(s, 5.6, y + 1.06, 6.9);
    y += 1.28;
  }
  pageNum(s, 2);
  s.addNotes("对照申报书四项研究内容逐条点名，告诉专家中期就是围绕这四条线推进的。");
}

// ============ S3 总体进展 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "OVERALL PROGRESS", "总体进展：前两阶段全部完成，进入模型深化期");
  const stages = [
    ["2026.6–8", "数据整理与特征构建", "已完成", TINT, PRIMARY],
    ["2026.8–10", "模型训练调参与系统集成", "已完成", TINT, PRIMARY],
    ["2026.10–12", "暴露量特征与弱负样本校正", "进行中", "D9EAF5", ACCENT],
    ["2027.1–5", "论文、案例研究与结题", "按计划推进", "FFFFFF", MUTED],
  ];
  const bw = 2.86, gap = 0.22;
  let x = M;
  for (let i = 0; i < stages.length; i++) {
    const [time, work, st, fill, stColor] = stages[i];
    box(s, x, 1.75, bw, 1.72, fill, fill === "FFFFFF" ? "C9D6E0" : null);
    s.addText(time, { x: x + 0.18, y: 1.92, w: bw - 0.36, h: 0.34, fontSize: 13, color: ACCENT, fontFace: F, bold: true, margin: 0 });
    s.addText(work, { x: x + 0.18, y: 2.28, w: bw - 0.36, h: 0.72, fontSize: 14.5, color: TEXT, fontFace: F, bold: true, lineSpacingMultiple: 1.15, margin: 0 });
    s.addText(st, { x: x + 0.18, y: 3.05, w: bw - 0.36, h: 0.32, fontSize: 12.5, color: stColor, fontFace: F, bold: true, margin: 0 });
    if (i < stages.length - 1) arrow(s, x + bw + 0.02, 2.6, x + bw + gap - 0.02, 2.6);
    x += bw + gap;
  }
  s.addText("中期关键结果一览", { x: M, y: 4.05, w: 6, h: 0.42, fontSize: 17, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  const stats = [
    ["0.82 – 0.85", "双模型交叉验证 ROC-AUC 区间，符合申报书预期"],
    ["15+ 项", "系统核心功能已上线，13 个页面组件"],
    ["双云端", "前端 Vercel / 后端 Render，代码托管 GitHub"],
  ];
  x = M;
  for (const [num, label] of stats) {
    s.addText(num, { x, y: 4.6, w: 3.9, h: 0.75, fontSize: 34, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
    s.addText(label, { x, y: 5.42, w: 3.75, h: 0.95, fontSize: 13, color: MUTED, fontFace: F, lineSpacingMultiple: 1.25, margin: 0 });
    x += 4.11;
  }
  pageNum(s, 3);
  s.addNotes("时间轴讲30秒：前四个月完成了从数据到系统的全部主体研发，当前处在第三阶段（特征深化+知识产权）。");
}

// ============ S4 数据库成果 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "DATA FOUNDATION", "数据库建设：四类实体的标准化数据底座");
  const nums = [
    ["46", "首", "经典哮喘方剂", "含每味药材精确剂量"],
    ["278", "味", "中药药材", "性味归经、功效主治"],
    ["569", "个", "入血候选化合物", "双模型概率零空值"],
    ["7398", "个", "哮喘相关靶点", "基因名与相关性标注"],
  ];
  const bw = 2.92, gap = 0.17;
  let x = M;
  for (const [n, u, t, d] of nums) {
    box(s, x, 1.7, bw, 2.35, TINT);
    s.addText([
      { text: n, options: { fontSize: 46, color: PRIMARY, bold: true } },
      { text: " " + u, options: { fontSize: 18, color: MUTED, bold: true } },
    ], { x: x + 0.2, y: 1.95, w: bw - 0.4, h: 0.85, fontFace: F, margin: 0 });
    s.addText(t, { x: x + 0.2, y: 2.92, w: bw - 0.4, h: 0.4, fontSize: 15.5, color: TEXT, fontFace: F, bold: true, margin: 0 });
    s.addText(d, { x: x + 0.2, y: 3.34, w: bw - 0.4, h: 0.5, fontSize: 12, color: MUTED, fontFace: F, margin: 0 });
    x += bw + gap;
  }
  s.addText("数据治理三步", { x: M, y: 4.45, w: 6, h: 0.4, fontSize: 17, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  const gov = [
    ["结构化提取", "原始 Excel 源表（1591 行 × 21 列）重构为关系库，方剂数量由 15 首扩充至 46 首"],
    ["剂量精确校准", "方剂级剂量优先、标准用量回退，为后续处方暴露量特征打基础"],
    ["数据质量把控", "清除无文献依据的 AI 生成字段；SQLite 单文件存储，GitHub Release 版本化分发"],
  ];
  y = 4.95;
  for (const [t, d] of gov) {
    s.addShape(pres.shapes.RECTANGLE, { x: M + 0.02, y: y + 0.12, w: 0.09, h: 0.09, fill: { color: ACCENT }, line: { color: ACCENT, width: 0 } });
    s.addText([
      { text: t + "　", options: { bold: true, color: TEXT } },
      { text: d, options: { color: MUTED } },
    ], { x: M + 0.28, y, w: W - 2 * M - 0.28, h: 0.55, fontSize: 13.5, fontFace: F, lineSpacingMultiple: 1.2, margin: 0 });
    y += 0.68;
  }
  pageNum(s, 4);
  s.addNotes("数字卡片逐个报一遍；重点讲数据治理——专家常问数据从哪来、质量怎么保证，\u201c清除AI生成字段\u201d是加分点。");
}

// ============ S5 PU 方法 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "METHOD", "核心方法：无可靠负样本下的 PU Learning 建模");
  s.addText("为什么不用普通二分类？", { x: M, y: 1.68, w: 4.5, h: 0.4, fontSize: 16.5, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  s.addText([
    { text: "中药\u201c确定入血\u201d的样本只有实验验证过的少数正样本", options: { bullet: bu(), breakLine: true } },
    { text: "文献中\u201c未检出\u201d的成分不等于\u201c不入血\u201d，直接当负样本会引入系统性偏差", options: { bullet: bu(), breakLine: true } },
    { text: "PU Learning 仅用正样本 + 未标注样本：每轮从未标注集中采样作伪负集，训练后集成，避免错杀潜在正样本", options: { bullet: bu() } },
  ], { x: M, y: 2.14, w: 4.6, h: 3.4, fontSize: 14, color: TEXT, fontFace: F, paraSpaceAfter: 12, lineSpacingMultiple: 1.3, margin: 0 });
  s.addText("特征体系：19 维 ADME + RDKit 拓扑特征，拼接 1024 维 Morgan 分子指纹（合计 1043 维）", {
    x: M, y: 5.75, w: 4.6, h: 1.0, fontSize: 13.5, color: MUTED, fontFace: F, lineSpacingMultiple: 1.3, margin: 0,
  });
  // 右侧流程图
  const fx = 6.0, fw = 6.7;
  const steps = [
    ["已知入血成分（正样本）+ 大规模未标注化合物库", TINT, TEXT],
    ["每轮按 1:1（ccTCM）/ 1:5（HERB）从未标注集采样伪负集", TINT, TEXT],
    ["基分类器训练 × 30 轮非对称 Bagging 集成", "D9EAF5", TEXT],
    ["输出入血概率 → 按工作阈值分级（高潜化合物专区）", PRIMARY, "FFFFFF"],
  ];
  let fy = 1.75;
  for (let i = 0; i < steps.length; i++) {
    const [t, fill, tc] = steps[i];
    box(s, fx, fy, fw, 0.92, fill);
    s.addText(t, { x: fx + 0.25, y: fy + 0.08, w: fw - 0.5, h: 0.76, fontSize: 14, color: tc, fontFace: F, bold: i === steps.length - 1, valign: "middle", lineSpacingMultiple: 1.15, margin: 0 });
    if (i < steps.length - 1) arrow(s, fx + fw / 2, fy + 0.94, fx + fw / 2, fy + 1.32);
    fy += 1.34;
  }
  pageNum(s, 5);
  s.addNotes("这是方法核心页：先讲清\u201c未检出不等于不入血\u201d，再讲 PU 的采样-集成思路，最后落到双模型互为补充。");
}

// ============ S6 模型性能 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "MODEL PERFORMANCE", "双模型性能：判别准确度达到申报书预期区间");
  s.addChart(pres.charts.BAR, [
    { name: "网格搜索交叉验证 AUC", labels: ["ccTCM 2.0（主力）", "HERB 2.0（兜底）"], values: [0.8229, 0.8463] },
    { name: "独立测试集 AUC", labels: ["ccTCM 2.0（主力）", "HERB 2.0（兜底）"], values: [0.8073, 0.8243] },
  ], {
    x: M, y: 1.75, w: 7.1, h: 4.7, barDir: "col", barGapWidthPct: 90,
    chartColors: [ACCENT, PRIMARY],
    chartArea: { fill: { color: "FFFFFF" } },
    valAxisMinVal: 0.7, valAxisMaxVal: 0.9, valAxisMajorUnit: 0.05,
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontFace: F, valAxisLabelFontFace: F,
    catAxisLabelFontSize: 12, valAxisLabelFontSize: 11,
    valGridLine: { color: "E2E8F0", size: 0.5 }, catGridLine: { style: "none" },
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: TEXT, dataLabelFontSize: 11, dataLabelFontFace: F, dataLabelFormatCode: "0.0000",
    showLegend: true, legendPos: "b", legendFontSize: 12, legendFontFace: F, legendColor: MUTED,
  });
  const calls = [
    ["1043 / 1037 维", "ccTCM / HERB 特征维度（理化 + 拓扑 + Morgan 指纹）"],
    ["0.56 / 0.62", "双模型工作阈值，支撑概率分级与高潜化合物筛选"],
    ["0.9956", "云端 31MB 精简版与完整版预测概率相关系数"],
  ];
  let cy = 1.85;
  for (const [n, d] of calls) {
    s.addText(n, { x: 8.1, y: cy, w: 4.6, h: 0.55, fontSize: 26, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
    s.addText(d, { x: 8.1, y: cy + 0.58, w: 4.5, h: 0.75, fontSize: 12.5, color: MUTED, fontFace: F, lineSpacingMultiple: 1.25, margin: 0 });
    cy += 1.55;
  }
  s.addText("数据来源：模型训练调参日志与结果报告（项目组 asthma-core 仓库，2026-08）", { x: M, y: 6.85, w: 9, h: 0.3, fontSize: 11, color: MUTED, fontFace: F, margin: 0 });
  pageNum(s, 6);
  s.addNotes("只报关键数：交叉验证 0.82–0.85、测试集 0.81–0.82，与申报书承诺一致；右侧三个数字按需展开。");
}

// ============ S7 系统架构与功能 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "SYSTEM", "系统实现：前后端分离，已完成云端部署");
  // 顶部架构图
  box(s, M, 1.7, 3.55, 1.5, TINT);
  s.addText([
    { text: "前端", options: { bold: true, fontSize: 15, color: TEXT, breakLine: true } },
    { text: "Vue3 + Element Plus\nECharts + Cytoscape.js", options: { fontSize: 12.5, color: MUTED } },
  ], { x: M + 0.2, y: 1.82, w: 3.15, h: 1.26, fontFace: F, lineSpacingMultiple: 1.25, margin: 0 });
  arrow(s, M + 3.6, 2.45, M + 4.35, 2.45);
  s.addText("REST API\n30+ 接口", { x: M + 3.52, y: 1.95, w: 0.95, h: 0.8, fontSize: 10.5, color: MUTED, fontFace: F, align: "center", margin: 0 });
  box(s, M + 4.4, 1.7, 4.6, 1.5, "D9EAF5");
  s.addText([
    { text: "后端 FastAPI", options: { bold: true, fontSize: 15, color: TEXT, breakLine: true } },
    { text: "PU 双模型推理 · RDKit 特征引擎\nGSEA 富集 · SQLite 数据库", options: { fontSize: 12.5, color: MUTED } },
  ], { x: M + 4.6, y: 1.82, w: 4.2, h: 1.26, fontFace: F, lineSpacingMultiple: 1.25, margin: 0 });
  arrow(s, M + 9.05, 2.45, M + 9.8, 2.45);
  box(s, M + 9.85, 1.7, 1.95, 1.5, PRIMARY);
  s.addText([
    { text: "云端部署", options: { bold: true, fontSize: 14, color: "FFFFFF", breakLine: true } },
    { text: "Vercel + Render", options: { fontSize: 11.5, color: LIGHT } },
  ], { x: M + 9.98, y: 1.98, w: 1.7, h: 1.0, fontFace: F, lineSpacingMultiple: 1.25, margin: 0 });
  // 功能清单
  s.addText("已上线核心功能", { x: M, y: 3.55, w: 6, h: 0.4, fontSize: 17, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  const fns = [
    ["入血预测控制台", "单化合物 SMILES 秒级预测；ADME 实验值校准重算；单次 500 条批量文件预测与结果下载"],
    ["方剂智能分析", "四层网络拓扑（阈值可调）、GSEA 通路富集柱状图、三维疗效雷达图、语音播报"],
    ["自定义方剂 + AI 报告", "自由组方一键分析；兼容 OpenAI/DeepSeek，SSE 流式生成机制解读，支持 PDF 导出"],
    ["数据浏览与检索", "方剂/药材/化合物三库联动；拼音首字母联想（输入 xh 匹配\u201c小青龙汤\u201d）、药材反查方剂"],
    ["专家模式", "模型特征贡献度、数据集统计等分析视图"],
  ];
  let y = 4.02;
  for (const [t, d] of fns) {
    s.addText([
      { text: t + "　", options: { bold: true, color: TEXT } },
      { text: d, options: { color: MUTED } },
    ], { x: M, y, w: W - 2 * M, h: 0.52, fontSize: 13, fontFace: F, lineSpacingMultiple: 1.15, margin: 0 });
    y += 0.56;
  }
  pageNum(s, 7);
  s.addNotes("架构图10秒带过，重点讲功能闭环：预测→网络→富集→报告。可现场演示系统（云端地址备用）。");
}

// ============ S8 机制分析成果 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "MECHANISM ANALYSIS", "机制分析：从方剂到靶点的完整解析链条");
  const chain = [
    ["方剂", "46 首", "含精确剂量"],
    ["药材", "278 味", "性味归经"],
    ["入血化合物", "569 个", "概率加权"],
    ["作用靶点", "7398 个", "哮喘相关"],
  ];
  const bw = 2.62, gap = 0.5;
  let x = M + 0.1;
  for (let i = 0; i < chain.length; i++) {
    const [t, n, d] = chain[i];
    box(s, x, 1.72, bw, 1.55, i === 3 ? PRIMARY : TINT);
    s.addText(t, { x, y: 1.9, w: bw, h: 0.4, fontSize: 15, color: i === 3 ? "FFFFFF" : TEXT, fontFace: F, bold: true, align: "center", margin: 0 });
    s.addText(n, { x, y: 2.32, w: bw, h: 0.55, fontSize: 25, color: i === 3 ? "FFFFFF" : ACCENT, fontFace: F, bold: true, align: "center", margin: 0 });
    s.addText(d, { x, y: 2.88, w: bw, h: 0.32, fontSize: 11.5, color: i === 3 ? LIGHT : MUTED, fontFace: F, align: "center", margin: 0 });
    if (i < chain.length - 1) arrow(s, x + bw + 0.06, 2.5, x + bw + gap - 0.06, 2.5);
    x += bw + gap;
  }
  s.addText("关键机制评价手段", { x: M, y: 3.62, w: 6, h: 0.4, fontSize: 17, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  s.addText([
    { text: "GSEA 实时富集：KEGG / GO 通路（Enrichr API），LRU 缓存 30 分钟，柱状图呈现关键通路", options: { bullet: bu(), breakLine: true } },
    { text: "靶点双重过滤：入血概率阈值 × 哮喘相关性，压缩低可信靶点、降低假阳性", options: { bullet: bu() } },
  ], { x: M, y: 4.1, w: 6.4, h: 1.6, fontSize: 13.5, color: TEXT, fontFace: F, paraSpaceAfter: 10, lineSpacingMultiple: 1.25, margin: 0 });
  s.addText("三维疗效评分", { x: 7.35, y: 3.62, w: 5, h: 0.4, fontSize: 17, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  const dims = [["抗炎效能", "炎症通路富集加权"], ["免疫调节", "免疫相关通路加权"], ["气道修复", "重塑修复通路加权"]];
  x = 7.35;
  for (const [t, d] of dims) {
    box(s, x, 4.12, 1.72, 1.25, TINT);
    s.addText(t, { x, y: 4.32, w: 1.72, h: 0.38, fontSize: 14, color: PRIMARY, fontFace: F, bold: true, align: "center", margin: 0 });
    s.addText(d, { x: x + 0.08, y: 4.72, w: 1.56, h: 0.55, fontSize: 10.5, color: MUTED, fontFace: F, align: "center", lineSpacingMultiple: 1.15, margin: 0 });
    x += 1.86;
  }
  s.addText("三项评分按入血概率加权归一，构成方剂疗效雷达图，支撑方剂间横向比较", { x: 7.35, y: 5.6, w: 5.3, h: 0.7, fontSize: 12.5, color: MUTED, fontFace: F, lineSpacingMultiple: 1.25, margin: 0 });
  pageNum(s, 8);
  s.addNotes("链条图讲\u201c从方剂到靶点\u201d的漏斗；三维疗效评分是用户可感知的输出，答辩时可举小青龙汤的例子。");
}

// ============ S9 成果对照 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "DELIVERABLES", "阶段性成果：对照申报书考核指标");
  const rows = [
    [{ text: "申报书预期成果", options: { bold: true, color: "FFFFFF", fill: { color: PRIMARY }, fontFace: F } },
     { text: "中期完成情况", options: { bold: true, color: "FFFFFF", fill: { color: PRIMARY }, fontFace: F } },
     { text: "状态", options: { bold: true, color: "FFFFFF", fill: { color: PRIMARY }, fontFace: F } }],
    ["儿童哮喘中药入血成分预测与可视化分析系统 1 套", "前后端分离系统已上线，云端可访问，具备完整分析能力", "已完成"],
    ["儿童哮喘中药化合物数据集及候选入血成分清单 1 套", "46 首方剂 / 278 味药材 / 569 个化合物 / 7398 个靶点，随系统发布", "已完成"],
    ["知识产权（软件著作权、学术论文等）1–2 项", "软著申报材料整理中，拟 2026 年 12 月前提交；论文撰写中", "推进中"],
    ["儿童哮喘中药用药机制分析研究报告 1 篇", "中期进展报告即阶段性研究报告；结题研究报告 2027 年一季度完成", "推进中"],
  ];
  s.addTable(rows, {
    x: M, y: 1.75, w: W - 2 * M, colW: [4.6, 5.9, 1.6],
    border: { type: "solid", pt: 0.75, color: "D5DFE8" },
    fontFace: F, fontSize: 13, color: TEXT, valign: "middle",
    rowH: [0.5, 0.85, 0.85, 0.85, 0.85], margin: 0.09,
    fill: { color: "FFFFFF" },
  });
  s.addText("状态列：已完成 2 项，推进中 2 项，整体进度符合申报书计划安排。", { x: M, y: 6.6, w: 10, h: 0.35, fontSize: 13, color: MUTED, fontFace: F, margin: 0 });
  pageNum(s, 9);
  s.addNotes("逐行对照考核指标，结论一句话：两项交付物已完成，两项按计划推进，无延期风险。");
}

// ============ S10 经费使用 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "BUDGET", "经费使用：中期列支 1760 元，全部在预算范围内");
  s.addChart(pres.charts.DOUGHNUT, [{
    name: "已使用经费构成",
    labels: ["计算/分析/测试费", "文献检索费", "会议/差旅费", "材料费", "能源动力费", "论文出版费"],
    values: [620, 380, 260, 240, 140, 120],
  }], {
    x: M, y: 1.8, w: 6.3, h: 4.6, holeSize: 60,
    chartColors: ["1A5276", "2E86C1", "5FA8D3", "8FC1DC", "B9D7E8", "D9EAF5"],
    showPercent: true, dataLabelColor: "FFFFFF", dataLabelFontSize: 10.5, dataLabelFontFace: F,
    showLegend: true, legendPos: "r", legendFontSize: 12, legendFontFace: F, legendColor: TEXT,
    chartArea: { fill: { color: "FFFFFF" } },
  });
  s.addText("1760 元", { x: 7.6, y: 1.9, w: 5.0, h: 0.9, fontSize: 48, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  s.addText("中期已列支（占已拨付 2800 元的 62.9%）", { x: 7.6, y: 2.85, w: 5.0, h: 0.4, fontSize: 14, color: MUTED, fontFace: F, margin: 0 });
  const funds = [
    ["预算总额", "5000 元"],
    ["前半阶段已拨付", "2800 元"],
    ["剩余及后半阶段", "3240 元（含未拨付 2200 元）"],
  ];
  let y = 3.6;
  for (const [t, v] of funds) {
    hairline(s, 7.6, y - 0.12, 5.0);
    s.addText(t, { x: 7.6, y, w: 2.0, h: 0.4, fontSize: 14, color: TEXT, fontFace: F, bold: true, margin: 0 });
    s.addText(v, { x: 9.7, y, w: 2.9, h: 0.4, fontSize: 14, color: MUTED, fontFace: F, align: "right", margin: 0 });
    y += 0.58;
  }
  s.addText("支出主要投向模型训练算力与文献检索；后续经费重点保障论文出版、软著申报与结题材料。\n注：以上为阶段性统计，以实际报销凭证为准。", {
    x: 7.6, y: 5.5, w: 5.0, h: 1.2, fontSize: 12.5, color: MUTED, fontFace: F, lineSpacingMultiple: 1.3, margin: 0,
  });
  pageNum(s, 10);
  s.addNotes("强调两句话：列支进度（63%）与拨付进度匹配；大头花在算力和文献上，符合研究型项目支出结构。");
}

// ============ S11 问题与计划 ============
{
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  header(s, "ISSUES & NEXT STEPS", "存在问题与下一阶段计划");
  s.addText("存在的主要问题", { x: M, y: 1.66, w: 5.5, h: 0.4, fontSize: 17, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  const issues = [
    ["儿童特异性特征未融入", "处方暴露量、成分含量尚未进入特征矩阵，与申报书目标尚有差距"],
    ["弱负样本校正待深化", "文献\u201c未检出\u201d数据仅作参考，尚未参与概率校正与模型融合"],
    ["工程细节待完善", "部分界面风格未统一，自动化测试覆盖不足"],
  ];
  let y = 2.14;
  for (const [t, d] of issues) {
    box(s, M, y, 5.6, 1.28, TINT);
    s.addText(t, { x: M + 0.22, y: y + 0.14, w: 5.2, h: 0.4, fontSize: 14.5, color: TEXT, fontFace: F, bold: true, margin: 0 });
    s.addText(d, { x: M + 0.22, y: y + 0.56, w: 5.2, h: 0.6, fontSize: 12.5, color: MUTED, fontFace: F, lineSpacingMultiple: 1.2, margin: 0 });
    y += 1.46;
  }
  s.addText("下一阶段计划", { x: 6.9, y: 1.66, w: 5.5, h: 0.4, fontSize: 17, color: PRIMARY, fontFace: F, bold: true, margin: 0 });
  const plans = [
    ["2026.11–12", "暴露量特征消融实验；弱负样本校正与多模型融合；提交软著申请 1 项"],
    ["2027.1–2", "论文撰写与投稿；小青龙汤等典型方剂机制案例研究；系统测试优化"],
    ["2027.3–4", "成果汇总，撰写研究报告与结题材料"],
    ["2027.5", "结题答辩，提交全部结题材料"],
  ];
  y = 2.2;
  for (const [t, d] of plans) {
    s.addShape(pres.shapes.OVAL, { x: 6.94, y: y + 0.09, w: 0.14, h: 0.14, fill: { color: ACCENT }, line: { color: ACCENT, width: 0 } });
    if (t !== "2027.5") s.addShape(pres.shapes.LINE, { x: 7.005, y: y + 0.26, w: 0, h: 0.62, line: { color: "C9D6E0", width: 1 } });
    s.addText(t, { x: 7.28, y, w: 1.55, h: 0.36, fontSize: 13.5, color: ACCENT, fontFace: F, bold: true, margin: 0 });
    s.addText(d, { x: 8.9, y: y - 0.02, w: 3.8, h: 0.86, fontSize: 12.5, color: TEXT, fontFace: F, lineSpacingMultiple: 1.2, margin: 0 });
    y += 0.92;
  }
  s.addText("对策：问题均已纳入下一阶段计划并明确责任人与时间点，无不可控风险。", { x: M, y: 6.65, w: 10.5, h: 0.35, fontSize: 13, color: MUTED, fontFace: F, margin: 0 });
  pageNum(s, 11);
  s.addNotes("问题讲实、措施讲细——每条问题都对应右侧计划里的一个时间点，体现可控性。");
}

// ============ S12 结束页 ============
{
  const s = pres.addSlide();
  s.background = { color: DARK };
  s.addShape(pres.shapes.OVAL, { x: -2.2, y: -2.6, w: 6.0, h: 6.0, fill: { color: ACCENT, transparency: 88 }, line: { color: ACCENT, width: 0 } });
  s.addText("恳请各位专家批评指正", { x: M, y: 2.5, w: W - 2 * M, h: 1.0, fontSize: 40, color: "FFFFFF", fontFace: F, bold: true, align: "center", margin: 0 });
  s.addText("基于入血预测的中医治疗儿童哮喘作用机制分析 · 中期检查汇报", { x: M, y: 3.7, w: W - 2 * M, h: 0.45, fontSize: 15, color: LIGHT, fontFace: F, align: "center", margin: 0 });
  hairline(s, 4.6, 4.75, 4.1);
  s.addText("项目组：张震翔　周俊峰　徐晨洋　李锦程　谢萌萌\n指导教师：丁有伟　赵玉男　　南京中医药大学　2026年10月", {
    x: M, y: 5.0, w: W - 2 * M, h: 1.0, fontSize: 13.5, color: LIGHT, fontFace: F, align: "center", lineSpacingMultiple: 1.5, margin: 0,
  });
  s.addNotes("致谢并进入答辩问答。");
}

pres.writeFile({ fileName: "../大创项目中期答辩PPT.pptx" }).then(() => console.log("PPT OK"));
