// 大创项目中期进展报告 — R1封面(MC-1医疗蓝) + 目录(罗马页码) + 正文(阿拉伯页码)
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, WidthType, BorderStyle, ShadingType, VerticalAlign,
  Header, Footer, PageNumber, NumberFormat, SectionType, HeadingLevel,
  TableOfContents, ImageRun, TableLayoutType,
} = require("docx");
const fs = require("fs");
const path = require("path");
const sizeOf = require("image-size");

const OUT = path.resolve(__dirname, "..", "大创项目中期进展报告.docx");
const CHART = path.resolve(__dirname, "chart_auc.png");

// ---------- 调色板 MC-1 Medical Blue ----------
const P = {
  bg: "F5F8FC", primary: "1A5276", accent: "2E86C1",
  titleColor: "1A5276", subtitleColor: "606060", metaColor: "707070", footerColor: "A0A0A0",
  table: { headerBg: "2E86C1", headerText: "FFFFFF", accentLine: "1A5276", innerLine: "D0DDE8", surface: "EDF3F8" },
};
const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NB, bottom: NB, left: NB, right: NB };
const allNoBorders = { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB };

// ---------- 封面标题布局（design-system 标准函数） ----------
function splitTitleLines(title, charsPerLine) {
  if (title.length <= charsPerLine) return [title];
  const breakAfter = new Set([..."\uff0c\u3002\u3001\uff1b\uff1a\uff01\uff1f", ..."\u7684\u4e0e\u548c\u53ca\u4e4b\u5728\u4e8e\u4e3a", ..."-_\u2014\u2013\u00b7/", ..." \t"]);
  const lines = [];
  let remaining = title;
  while (remaining.length > charsPerLine) {
    let breakAt = -1;
    for (let i = charsPerLine; i >= Math.floor(charsPerLine * 0.6); i--) {
      if (i < remaining.length && breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
    }
    if (breakAt === -1) {
      const limit = Math.min(remaining.length, Math.ceil(charsPerLine * 1.3));
      for (let i = charsPerLine + 1; i < limit; i++) {
        if (breakAfter.has(remaining[i - 1])) { breakAt = i; break; }
      }
    }
    if (breakAt === -1) {
      breakAt = charsPerLine;
      const prevChar = remaining[breakAt - 1], nextChar = remaining[breakAt];
      if (prevChar && nextChar && !breakAfter.has(prevChar) && !breakAfter.has(nextChar) &&
          /[\u4e00-\u9fff]/.test(prevChar) && /[\u4e00-\u9fff]/.test(nextChar)) breakAt = breakAt - 1;
    }
    lines.push(remaining.slice(0, breakAt).trim());
    remaining = remaining.slice(breakAt).trim();
  }
  if (remaining) lines.push(remaining);
  if (lines.length > 1 && lines[lines.length - 1].length <= 2) {
    const last = lines.pop();
    lines[lines.length - 1] += last;
  }
  return lines;
}
function calcTitleLayout(title, maxWidthTwips, preferredPt = 40, minPt = 24) {
  const charWidth = (pt) => pt * 20;
  const charsPerLine = (pt) => Math.floor(maxWidthTwips / charWidth(pt));
  let titlePt = preferredPt, lines;
  while (titlePt >= minPt) {
    const cpl = charsPerLine(titlePt);
    if (cpl < 2) { titlePt -= 2; continue; }
    lines = splitTitleLines(title, cpl);
    if (lines.length <= 3) break;
    titlePt -= 2;
  }
  if (!lines || lines.length > 3) {
    lines = splitTitleLines(title, charsPerLine(minPt));
    titlePt = minPt;
  }
  return { titlePt, titleLines: lines };
}
function calcCoverSpacing(params) {
  const { titleLineCount = 1, titlePt = 36, hasSubtitle = false, hasEnglishLabel = false,
    metaLineCount = 0, fixedHeight = 800, pageHeight = 16838, marginTop = 0, marginBottom = 0 } = params;
  const SAFETY = 1200;
  const usableHeight = pageHeight - marginTop - marginBottom - SAFETY;
  const titleHeight = titleLineCount * (titlePt * 23 + 200);
  const subtitleHeight = hasSubtitle ? (12 * 23 + 600) : 0;
  const englishLabelHeight = hasEnglishLabel ? (9 * 23 + 600) : 0;
  const metaHeight = metaLineCount * (10 * 23 + 100);
  const implicitParaHeight = 3 * 300;
  const contentHeight = titleHeight + subtitleHeight + englishLabelHeight + metaHeight + fixedHeight + implicitParaHeight;
  const safeRemaining = Math.max(usableHeight - contentHeight, 400);
  const FOOTER_MIN = 800;
  const rawTop = Math.floor(safeRemaining * 0.45);
  const rawBottom = Math.floor(safeRemaining * 0.45);
  const bottomSpacing = Math.max(rawBottom, FOOTER_MIN);
  const topSpacing = Math.max(rawTop - Math.max(0, FOOTER_MIN - rawBottom), 400);
  const midSpacing = Math.max(safeRemaining - topSpacing - bottomSpacing, 0);
  return { topSpacing, midSpacing, bottomSpacing };
}

// ---------- R1 封面 ----------
function buildCoverR1(config) {
  const PA = config.palette;
  const padL = 1200, padR = 800;
  const availableWidth = 11906 - padL - padR - 300;
  const { titlePt, titleLines } = calcTitleLayout(config.title, availableWidth, 34, 24);
  const titleSize = titlePt * 2;
  const spacing = calcCoverSpacing({
    titleLineCount: titleLines.length, titlePt,
    hasSubtitle: !!config.subtitle, hasEnglishLabel: !!config.englishLabel,
    metaLineCount: (config.metaLines || []).length, fixedHeight: 400,
  });
  const accentLeft = { style: BorderStyle.SINGLE, size: 8, color: PA.accent, space: 12 };
  const children = [];
  children.push(new Paragraph({ spacing: { before: spacing.topSpacing } }));
  if (config.englishLabel) {
    children.push(new Paragraph({
      indent: { left: padL, right: padR }, spacing: { after: 500 },
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: PA.accent, space: 8 } },
      children: [new TextRun({ text: config.englishLabel.split("").join("  "), size: 18, color: PA.accent, font: { ascii: "Calibri", eastAsia: "SimHei" }, characterSpacing: 40 })],
    }));
  }
  for (let i = 0; i < titleLines.length; i++) {
    children.push(new Paragraph({
      indent: { left: padL },
      spacing: { after: i < titleLines.length - 1 ? 100 : 300, line: Math.ceil(titlePt * 23), lineRule: "atLeast" },
      children: [new TextRun({ text: titleLines[i], size: titleSize, bold: true, color: PA.titleColor, font: { eastAsia: "SimHei", ascii: "Arial" } })],
    }));
  }
  if (config.subtitle) {
    children.push(new Paragraph({
      indent: { left: padL }, spacing: { after: 800 },
      children: [new TextRun({ text: config.subtitle, size: 24, color: PA.subtitleColor, font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }
  for (const line of (config.metaLines || [])) {
    children.push(new Paragraph({
      indent: { left: padL + 200 }, spacing: { after: 80 },
      border: { left: accentLeft },
      children: [new TextRun({ text: line, size: 24, color: PA.metaColor, font: { eastAsia: "Microsoft YaHei", ascii: "Arial" } })],
    }));
  }
  children.push(new Paragraph({ spacing: { before: spacing.bottomSpacing } }));
  children.push(new Paragraph({
    indent: { left: padL, right: padR },
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: PA.accent, space: 8 } },
    spacing: { before: 200 },
    children: [
      new TextRun({ text: config.footerLeft || "", size: 16, color: PA.footerColor, font: { ascii: "Arial", eastAsia: "Microsoft YaHei" } }),
      new TextRun({ text: "                                        " }),
      new TextRun({ text: config.footerRight || "", size: 16, color: PA.footerColor, font: { ascii: "Arial", eastAsia: "Microsoft YaHei" } }),
    ],
  }));
  return [new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    borders: allNoBorders,
    rows: [new TableRow({
      height: { value: 16838, rule: "exact" },
      children: [new TableCell({
        shading: { type: ShadingType.CLEAR, fill: PA.bg }, borders: noBorders,
        children,
      })],
    })],
  })];
}

// ---------- 正文构件 ----------
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160, line: 380, lineRule: "atLeast" },
    children: [new TextRun({ text, bold: true, size: 32, color: P.primary, font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 120, line: 340, lineRule: "atLeast" },
    children: [new TextRun({ text, bold: true, size: 28, color: P.primary, font: { ascii: "Times New Roman", eastAsia: "SimHei" } })],
  });
}
function body(text, { bold = false } = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: 480 },
    spacing: { line: 312, after: 60 },
    children: [new TextRun({ text, size: 24, bold, color: "000000", font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
  });
}
// 编号条目段（（一）（二）… 引导词加粗）
function itemP(lead, rest) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    indent: { firstLine: 480 },
    spacing: { line: 312, after: 60 },
    children: [
      new TextRun({ text: lead, bold: true, size: 24, color: "000000", font: { ascii: "Times New Roman", eastAsia: "SimHei" } }),
      new TextRun({ text: rest, size: 24, color: "000000", font: { ascii: "Times New Roman", eastAsia: "SimSun" } }),
    ],
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, keepNext: true,
    spacing: { before: 160, after: 80, line: 312 },
    children: [new TextRun({ text, bold: true, size: 21, color: "000000", font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
  });
}
// 横线式数据表（Horizontal-Only，MC-1 色板）
function hTable(pcts, headers, rows, aligns) {
  const mk = (text, i, isHeader) => new TableCell({
    width: { size: pcts[i], type: WidthType.PERCENTAGE },
    shading: isHeader ? { type: ShadingType.CLEAR, fill: P.table.headerBg } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 70, bottom: 70, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: isHeader ? AlignmentType.CENTER : (aligns && aligns[i]) || AlignmentType.LEFT,
      spacing: { line: 312 },
      children: [new TextRun({
        text, bold: isHeader, size: 21,
        color: isHeader ? P.table.headerText : "000000",
        font: { ascii: "Times New Roman", eastAsia: isHeader ? "SimHei" : "SimSun" },
      })],
    })],
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 6, color: P.table.accentLine },
      bottom: { style: BorderStyle.SINGLE, size: 6, color: P.table.accentLine },
      left: NB, right: NB,
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: P.table.innerLine },
      insideVertical: NB,
    },
    rows: [
      new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((t, i) => mk(t, i, true)) }),
      ...rows.map((r, ri) => new TableRow({
        cantSplit: true,
        children: r.map((t, i) => {
          const c = mk(t, i, false);
          return c;
        }),
      })),
    ],
  });
}

// ---------- 图1 ----------
const dims = sizeOf.imageSize ? sizeOf.imageSize(fs.readFileSync(CHART)) : sizeOf(CHART);
const imgW = 480, imgH = Math.round(imgW * dims.height / dims.width);
const chartPara = new Paragraph({
  alignment: AlignmentType.CENTER, keepNext: true,
  spacing: { before: 120, after: 40 },
  children: [new ImageRun({ data: fs.readFileSync(CHART), transformation: { width: imgW, height: imgH }, type: "png" })],
});

// ---------- 正文内容 ----------
const CENTER = AlignmentType.CENTER;
const bodyChildren = [
  h1("\u6458\u8981"),
  body("\u672c\u62a5\u544a\u4e3a\u6c5f\u82cf\u7701\u9ad8\u7b49\u5b66\u6821\u5927\u5b66\u751f\u521b\u65b0\u521b\u4e1a\u8bad\u7ec3\u8ba1\u5212\u91cd\u70b9\u9879\u76ee\u201c\u57fa\u4e8e\u5165\u8840\u9884\u6d4b\u7684\u4e2d\u533b\u6cbb\u7597\u513f\u7ae5\u54ee\u5596\u4f5c\u7528\u673a\u5236\u5206\u6790\u201d\u7684\u4e2d\u671f\u8fdb\u5c55\u62a5\u544a\u3002\u9879\u76ee\u81ea2026\u5e746\u6708\u5f00\u9898\uff0c\u6267\u884c\u671f\u4e00\u5e74\uff0c\u56f4\u7ed5\u201c\u6570\u636e\u4e0e\u7279\u5f81\u6784\u5efa\u3001\u5165\u8840\u9884\u6d4b\u4e0e\u5019\u9009\u6210\u5206\u8bc6\u522b\u3001\u4f5c\u7528\u673a\u5236\u8bc4\u4ef7\u3001\u53ef\u89c6\u5316\u7cfb\u7edf\u5b9e\u73b0\u201d\u56db\u9879\u7814\u7a76\u5185\u5bb9\u5c55\u5f00\u3002"),
  body("\u622a\u81f32026\u5e7410\u6708\uff0c\u9879\u76ee\u5df2\u5b8c\u6210\u513f\u7ae5\u54ee\u5596\u4e2d\u836f\u5316\u5408\u7269\u6570\u636e\u5e93\u5efa\u8bbe\uff0846\u9996\u65b9\u5242\u3001278\u5473\u4e2d\u836f\u3001569\u4e2a\u5165\u8840\u5019\u9009\u5316\u5408\u7269\u30017398\u4e2a\u54ee\u5596\u76f8\u5173\u9776\u70b9\uff09\uff1b\u5efa\u6210\u57fa\u4e8e\u6b63\u4f8b\u2014\u672a\u6807\u6ce8\u5b66\u4e60\uff08PU Learning\uff09\u7684\u53cc\u6a21\u578b\u5165\u8840\u9884\u6d4b\u5f15\u64ce\uff0c\u4ea4\u53c9\u9a8c\u8bc1ROC-AUC\u8fbe0.82\u20140.85\uff0c\u7b26\u5408\u7533\u62a5\u4e66\u9884\u671f\uff1b\u5b9e\u73b0\u56db\u5c42\u7f51\u7edc\u836f\u7406\u5b66\u62d3\u6251\u3001GSEA\u5bcc\u96c6\u4e0e\u4e09\u7ef4\u7597\u6548\u8bc4\u5206\u7684\u673a\u5236\u5206\u6790\u6a21\u5757\uff0c\u5e76\u5b8c\u6210\u524d\u540e\u7aef\u5206\u79bb\u7684\u53ef\u89c6\u5316\u5206\u6790\u7cfb\u7edf\u5f00\u53d1\u4e0e\u4e91\u7aef\u90e8\u7f72\u3002\u8f6f\u4ef6\u8457\u4f5c\u6743\u7533\u62a5\u4e0e\u5b66\u672f\u8bba\u6587\u64b0\u5199\u6b63\u5728\u63a8\u8fdb\u3002\u4e0b\u4e00\u9636\u6bb5\u5c06\u6df1\u5316\u5904\u65b9\u66b4\u9732\u91cf\u7279\u5f81\u4e0e\u5f31\u8d1f\u6837\u672c\u6821\u6b63\u7814\u7a76\uff0c\u5b8c\u6210\u8bba\u6587\u6295\u7a3f\u4e0e\u7ed3\u9898\u51c6\u5907\u3002"),

  h1("\u4e00\u3001\u9879\u76ee\u6982\u51b5"),
  h2("\uff08\u4e00\uff09\u7814\u7a76\u80cc\u666f\u4e0e\u76ee\u6807"),
  body("\u513f\u7ae5\u54ee\u5596\u662f\u513f\u7ae5\u65f6\u671f\u5e38\u89c1\u7684\u6162\u6027\u547c\u5438\u9053\u75be\u75c5\uff0c\u4e2d\u533b\u836f\u51ed\u501f\u6574\u4f53\u8c03\u8282\u3001\u591a\u6210\u5206\u3001\u591a\u9776\u70b9\u7684\u7279\u70b9\uff0c\u5728\u513f\u7ae5\u54ee\u5596\u7efc\u5408\u5e72\u9884\u4e2d\u5177\u6709\u4e00\u5b9a\u5e94\u7528\u57fa\u7840\u3002\u7136\u800c\uff0c\u4e2d\u836f\u590d\u65b9\u6240\u542b\u5316\u5408\u7269\u79cd\u7c7b\u7e41\u591a\uff0c\u54ea\u4e9b\u6210\u5206\u80fd\u771f\u6b63\u5165\u8840\u53d1\u6325\u4f5c\u7528\u3001\u5176\u4f5c\u7528\u9776\u70b9\u4e0e\u5206\u5b50\u673a\u5236\u5982\u4f55\uff0c\u76ee\u524d\u4ecd\u4e3b\u8981\u4f9d\u8d56\u52a8\u7269\u5b9e\u9a8c\u6d4b\u5b9a\uff0c\u6210\u672c\u9ad8\u3001\u901a\u91cf\u4f4e\uff1b\u4f20\u7edf\u7f51\u7edc\u836f\u7406\u5b66\u65b9\u6cd5\u53c8\u5b58\u5728\u9776\u70b9\u5047\u9633\u6027\u9ad8\u3001\u672a\u8003\u8651\u6210\u5206\u662f\u5426\u5165\u8840\u7b49\u5c40\u9650\u3002\u672c\u9879\u76ee\u4ee5\u5165\u8840\u9884\u6d4b\u4e3a\u5207\u5165\u70b9\uff0c\u6784\u5efa\u9762\u5411\u4e2d\u836f\u590d\u65b9\u7684\u8840\u4e2d\u79fb\u884c\u80fd\u529b\u9884\u6d4b\u6a21\u578b\u4e0e\u53ef\u89c6\u5316\u5206\u6790\u7cfb\u7edf\uff0c\u4e3a\u513f\u7ae5\u54ee\u5596\u4e2d\u533b\u836f\u7528\u836f\u673a\u5236\u7814\u7a76\u4e0e\u4e34\u5e8a\u8f85\u52a9\u51b3\u7b56\u63d0\u4f9b\u667a\u80fd\u5316\u5de5\u5177\u3002"),
  body("\u9879\u76ee\u5177\u4f53\u76ee\u6807\u5305\u62ec\uff1a\uff081\uff09\u6784\u5efa\u513f\u7ae5\u54ee\u5596\u4e2d\u836f\u5316\u5408\u7269\u591a\u6e90\u6570\u636e\u5e93\uff1b\uff082\uff09\u5efa\u7acb\u65e0\u53ef\u9760\u8d1f\u6837\u672c\u573a\u666f\u4e0b\u7684\u4e2d\u836f\u5165\u8840\u6210\u5206\u9884\u6d4b\u65b9\u6cd5\uff1b\uff083\uff09\u5f00\u5c55\u4e2d\u836f\u5904\u65b9\u6cbb\u7597\u513f\u7ae5\u54ee\u5596\u7684\u4f5c\u7528\u673a\u5236\u8bc4\u4ef7\uff1b\uff084\uff09\u5f00\u53d1\u5165\u8840\u6210\u5206\u9884\u6d4b\u4e0e\u4f5c\u7528\u673a\u5236\u53ef\u89c6\u5316\u5206\u6790\u7cfb\u7edf\u3002"),
  h2("\uff08\u4e8c\uff09\u7814\u7a76\u5185\u5bb9\u4e0e\u6280\u672f\u8def\u7ebf"),
  body("\u9879\u76ee\u6309\u201c\u6570\u636e\u6574\u7406\u2014\u7279\u5f81\u6784\u5efa\u2014\u5165\u8840\u9884\u6d4b\u2014\u9776\u70b9\u7b5b\u9009\u2014\u7cfb\u7edf\u5b9e\u73b0\u201d\u7684\u6280\u672f\u8def\u7ebf\u7ec4\u7ec7\u7814\u7a76\uff1a\u9996\u5148\u6574\u5408\u4e34\u5e8a\u5904\u65b9\u3001\u836f\u6750\u2014\u6210\u5206\u3001\u7406\u5316\u6027\u8d28\u3001\u6587\u732e\u5165\u8840\u6807\u8bc6\u53ca\u9776\u70b9\u6d3b\u6027\u7b49\u591a\u6e90\u6570\u636e\uff1b\u5176\u6b21\u878d\u5408\u5206\u5b50\u7ed3\u6784\u3001\u7406\u5316\u6027\u8d28\u3001\u836f\u6750\u6765\u6e90\u4e0e\u5904\u65b9\u66b4\u9732\u91cf\u7b49\u7279\u5f81\uff0c\u4ee5PU\u5b66\u4e60\u4e3a\u6838\u5fc3\u65b9\u6cd5\u8fdb\u884c\u5165\u8840\u6982\u7387\u9884\u6d4b\uff1b\u518d\u7ed3\u5408\u54ee\u5596\u76f8\u5173\u75be\u75c5\u9776\u70b9\u4e0e\u5bcc\u96c6\u5206\u6790\u5b8c\u6210\u673a\u5236\u8bc4\u4ef7\uff1b\u6700\u7ec8\u96c6\u6210\u4e3a\u53ef\u89c6\u5316\u5206\u6790\u7cfb\u7edf\u5bf9\u5916\u63d0\u4f9b\u670d\u52a1\u3002"),
  h2("\uff08\u4e09\uff09\u9879\u76ee\u7ec4\u7ec7\u4e0e\u5206\u5de5"),
  caption("\u88681\u3000\u9879\u76ee\u7ec4\u6210\u5458\u4e0e\u5206\u5de5"),
  hTable([14, 16, 16, 54],
    ["\u59d3\u540d", "\u5b66\u53f7", "\u4e13\u4e1a\u73ed\u7ea7", "\u9879\u76ee\u4e2d\u7684\u5206\u5de5"],
    [
      ["\u5f20\u9707\u7fd4", "084624117", "\u8ba1\u7b97\u673a\u7c7b241", "\u9879\u76ee\u603b\u4f53\u6280\u672f\u8def\u7ebf\u8bbe\u8ba1\u3001\u5165\u8840\u9884\u6d4b\u6a21\u578b\u6784\u5efa\u3001\u591a\u6a21\u6001\u7279\u5f81\u878d\u5408\u3001\u540e\u7aef\u63a5\u53e3\u5f00\u53d1\u4e0e\u7cfb\u7edf\u8054\u8c03\uff0c\u7edf\u7b79\u6587\u6863\u64b0\u5199"],
      ["\u5468\u4fca\u5cf0", "084624114", "\u8ba1\u7b97\u673a\u7c7b241", "\u524d\u7aef\u5f00\u53d1\u3001\u4ea4\u4e92\u9875\u9762\u8bbe\u8ba1\u3001\u7ed3\u679c\u5c55\u793a\u6a21\u5757\u5b9e\u73b0\uff08\u5904\u65b9\u8f93\u5165\u3001\u6982\u7387\u5c55\u793a\u3001\u6210\u5206\u2014\u9776\u70b9\u7f51\u7edc\u53ef\u89c6\u5316\uff09"],
      ["\u5f90\u6668\u6d0b", "084624208", "\u8ba1\u7b97\u673a\u7c7b242", "\u5316\u5408\u7269\u6570\u636e\u6574\u7406\u3001\u836f\u6750\u2014\u6210\u5206\u2014\u542b\u91cf\u6570\u636e\u6e05\u6d17\u3001\u7406\u5316\u6027\u8d28\u8865\u5168\u3001\u5f31\u8d1f\u6837\u672c\u6807\u8bb0\u4e0e\u8bad\u7ec3\u96c6\u6784\u5efa\u3001\u6a21\u578b\u8bc4\u4f30"],
      ["\u674e\u9526\u7a0b", "084624105", "\u8ba1\u7b97\u673a\u7c7b241", "\u6587\u732e\u8d44\u6599\u6574\u7406\u3001\u5165\u8840\u6807\u8bc6\u4e0e\u4ee3\u8c22\u4ea7\u7269\u4fe1\u606f\u6536\u96c6\u3001\u5316\u5408\u7269\u2014\u9776\u70b9\u6d3b\u6027\u503c\u6570\u636e\u6574\u7406\u3001\u6d4b\u8bd5\u6587\u6863\u7f16\u5199"],
      ["\u8c22\u840c\u840c", "041324335", "\u4e2d\u836f243", "\u836f\u5b66\u4e13\u4e1a\u77e5\u8bc6\u652f\u6301\u3001\u5904\u65b9\u4e0e\u836f\u6750\u2014\u6210\u5206\u5173\u7cfb\u6838\u9a8c\u3001\u6a21\u578b\u7ed3\u679c\u836f\u5b66\u5408\u7406\u6027\u5206\u6790\u3001\u6c47\u62a5\u6750\u6599\u6574\u7406"],
    ],
    [CENTER, CENTER, CENTER, AlignmentType.LEFT]),
  body("\u9879\u76ee\u7531\u4e01\u6709\u4f1f\u3001\u8d75\u7389\u7537\u4e24\u4f4d\u8001\u5e08\u8054\u5408\u6307\u5bfc\uff0c\u5206\u522b\u5728\u4eba\u5de5\u667a\u80fd\u65b9\u6cd5\u3001\u7cfb\u7edf\u5f00\u53d1\u4e0e\u4e2d\u836f\u836f\u6548\u7269\u8d28\u57fa\u7840\u3001\u5165\u8840\u5b9e\u9a8c\u9a8c\u8bc1\u4e24\u4e2a\u65b9\u5411\u63d0\u4f9b\u6307\u5bfc\u3002"),

  h1("\u4e8c\u3001\u603b\u4f53\u8fdb\u5c55\u6982\u8ff0"),
  body("\u5bf9\u7167\u9879\u76ee\u6267\u884c\u671f\u603b\u4f53\u5b89\u6392\uff0c\u5404\u9636\u6bb5\u5de5\u4f5c\u63a8\u8fdb\u60c5\u51b5\u5982\u88682\u6240\u793a\u3002\u524d\u4e24\u4e2a\u9636\u6bb5\u7684\u4e3b\u4f53\u4efb\u52a1\u5df2\u5168\u90e8\u5b8c\u6210\uff0c\u9879\u76ee\u76ee\u524d\u5904\u4e8e\u7b2c\u4e09\u9636\u6bb5\uff08\u6a21\u578b\u6df1\u5316\u4e0e\u77e5\u8bc6\u4ea7\u6743\u7533\u62a5\uff09\uff0c\u603b\u4f53\u8fdb\u5ea6\u7b26\u5408\u8ba1\u5212\u3002"),
  caption("\u88682\u3000\u9636\u6bb5\u63a8\u8fdb\u60c5\u51b5"),
  hTable([20, 56, 24],
    ["\u65f6\u95f4\u9636\u6bb5", "\u4e3b\u8981\u5de5\u4f5c", "\u72b6\u6001"],
    [
      ["2026.6\u20142026.8", "\u6587\u732e\u8c03\u7814\u4e0e\u6570\u636e\u6574\u7406\uff1a\u5904\u65b9\u3001\u836f\u6750\u3001\u5316\u5408\u7269\u3001\u9776\u70b9\u6570\u636e\u6e05\u6d17\u4e0e\u6821\u51c6\uff0c\u7279\u5f81\u4f53\u7cfb\u8bbe\u8ba1", "\u5df2\u5b8c\u6210"],
      ["2026.8\u20142026.10", "\u6a21\u578b\u8bad\u7ec3\u4e0e\u8c03\u53c2\uff1aPU\u53cc\u6a21\u578b\u8bad\u7ec3\u3001\u5de5\u4f5c\u9608\u503c\u786e\u5b9a\u3001\u7cfb\u7edf\u96c6\u6210\u4e0e\u4e91\u7aef\u90e8\u7f72", "\u5df2\u5b8c\u6210"],
      ["2026.10\u20142026.12", "\u6a21\u578b\u6df1\u5316\uff1a\u5904\u65b9\u66b4\u9732\u91cf\u7279\u5f81\u3001\u5f31\u8d1f\u6837\u672c\u6821\u6b63\uff1b\u8f6f\u8457\u7533\u62a5", "\u8fdb\u884c\u4e2d"],
      ["2027.1\u20142027.5", "\u5178\u578b\u65b9\u5242\u6848\u4f8b\u7814\u7a76\u3001\u8bba\u6587\u6295\u7a3f\u3001\u7ed3\u9898\u6750\u6599\u4e0e\u7b54\u8fa9", "\u6309\u8ba1\u5212\u63a8\u8fdb"],
    ],
    [CENTER, AlignmentType.LEFT, CENTER]),

  h1("\u4e09\u3001\u4e3b\u8981\u7814\u7a76\u8fdb\u5c55"),
  h2("\uff08\u4e00\uff09\u513f\u7ae5\u54ee\u5596\u4e2d\u836f\u5316\u5408\u7269\u6570\u636e\u5e93\u5efa\u8bbe"),
  body("\u56f4\u7ed5\u513f\u7ae5\u54ee\u5596\u6838\u5fc3\u5904\u65b9\uff0c\u5b8c\u6210\u4e86\u201c\u5904\u65b9\u2014\u836f\u6750\u2014\u6210\u5206\u2014\u9776\u70b9\u201d\u56db\u7c7b\u5b9e\u4f53\u53ca\u5176\u5173\u8054\u5173\u7cfb\u7684\u7ed3\u6784\u5316\u6570\u636e\u5e93\u5efa\u8bbe\uff0c\u6570\u636e\u89c4\u6a21\u89c1\u88683\u3002\u5efa\u5e93\u8fc7\u7a0b\u4e2d\u540c\u6b65\u5f00\u5c55\u6570\u636e\u6cbb\u7406\uff1a\u4ece\u539f\u59cbExcel\u6e90\u8868\uff081591\u884c\u00d721\u5217\uff09\u5b8c\u6210\u65b9\u5242\u7ed3\u6784\u5316\u63d0\u53d6\uff0c\u65b9\u5242\u6570\u91cf\u753115\u9996\u6269\u5145\u81f346\u9996\uff1b\u6821\u51c6\u6bcf\u5473\u836f\u6750\u7684\u7cbe\u786e\u5242\u91cf\uff08\u65b9\u5242\u7ea7\u5242\u91cf\u4f18\u5148\u3001\u6807\u51c6\u7528\u91cf\u56de\u9000\uff09\uff1b\u6e05\u9664\u65e0\u6587\u732e\u4f9d\u636e\u7684AI\u751f\u6210\u5b57\u6bb5\uff0c\u4fdd\u969c\u5206\u6790\u94fe\u8def\u6570\u636e\u8d28\u91cf\u3002\u6570\u636e\u5e93\u91c7\u7528SQLite\u5355\u6587\u4ef6\u5b58\u50a8\uff0c\u901a\u8fc7GitHub Release\u5b9e\u73b0\u7248\u672c\u5316\u5206\u53d1\uff0c\u652f\u6301\u540e\u7eed\u6269\u5c55\u75c5\u79cd\u4e0e\u65b9\u5242\u5e93\u3002"),
  caption("\u88683\u3000\u6570\u636e\u5e93\u89c4\u6a21"),
  hTable([30, 20, 50],
    ["\u6570\u636e\u7c7b\u522b", "\u6570\u91cf", "\u8bf4\u660e"],
    [
      ["\u7ecf\u5178\u65b9\u5242", "46 \u9996", "\u542b\u6bcf\u5473\u836f\u6750\u7cbe\u786e\u5242\u91cf\u3001\u4e3b\u6cbb\u4e0e\u529f\u6548\u5206\u7c7b"],
      ["\u4e2d\u836f\u836f\u6750", "278 \u5473", "\u6027\u5473\u5f52\u7ecf\u3001\u529f\u6548\u4e3b\u6cbb\uff0c\u6309\u529f\u6548\u5206\u7c7b\u7b5b\u9009"],
      ["\u5165\u8840\u5019\u9009\u5316\u5408\u7269", "569 \u4e2a", "\u53cc\u6a21\u578b\u6982\u7387\u96f6\u7a7a\u503c\uff0c\u542b\u9ad8\u6f5c\u5316\u5408\u7269\u4e13\u533a"],
      ["\u54ee\u5596\u76f8\u5173\u9776\u70b9", "7398 \u4e2a", "\u57fa\u56e0\u540d\u4e0e\u54ee\u5596\u76f8\u5173\u6027\u6807\u6ce8"],
    ],
    [AlignmentType.LEFT, CENTER, AlignmentType.LEFT]),
  h2("\uff08\u4e8c\uff09\u57fa\u4e8ePU\u5b66\u4e60\u7684\u5165\u8840\u9884\u6d4b\u53cc\u6a21\u578b\u6784\u5efa"),
  body("\u4e2d\u836f\u5316\u5408\u7269\u662f\u5426\u5165\u8840\u7f3a\u4e4f\u53ef\u9760\u8d1f\u6837\u672c\uff1a\u6587\u732e\u4e2d\u201c\u672a\u68c0\u51fa\u201d\u7684\u6210\u5206\u5e76\u4e0d\u7b49\u4e8e\u201c\u4e0d\u5165\u8840\u201d\uff0c\u82e5\u76f4\u63a5\u5f53\u4f5c\u8d1f\u6837\u672c\u8bad\u7ec3\u4f1a\u5f15\u5165\u7cfb\u7edf\u6027\u504f\u5dee\u3002\u9488\u5bf9\u8fd9\u4e00\u95ee\u9898\uff0c\u9879\u76ee\u91c7\u7528\u6b63\u4f8b\u2014\u672a\u6807\u6ce8\u5b66\u4e60\uff08PU Learning\uff09\u6846\u67b6\uff0c\u4ec5\u4ee5\u5df2\u77e5\u5165\u8840\u6210\u5206\u4e3a\u6b63\u6837\u672c\uff0c\u5c06\u672a\u6807\u6ce8\u6837\u672c\u53cd\u590d\u62bd\u6837\u4f5c\u4e3a\u8d1f\u96c6\u8bad\u7ec3\u540e\u96c6\u6210\uff0c\u6784\u5efa\u4e86ccTCM 2.0\u4e0eHERB 2.0\u53cc\u6a21\u578b\u5f15\u64ce\uff0c\u4e24\u8005\u4e92\u4e3a\u4ea4\u53c9\u9a8c\u8bc1\u4e0e\u4e92\u8865\u515c\u5e95\u3002\u6a21\u578b\u8bbe\u8ba1\u5bf9\u6bd4\u89c1\u88684\u3002"),
  caption("\u88684\u3000\u5165\u8840\u9884\u6d4b\u53cc\u6a21\u578b\u8bbe\u8ba1\u4e0e\u6027\u80fd\u5bf9\u6bd4"),
  hTable([24, 38, 38],
    ["\u5bf9\u6bd4\u9879", "ccTCM 2.0\uff08\u4e3b\u529b\u6a21\u578b\uff09", "HERB 2.0\uff08\u515c\u5e95\u6a21\u578b\uff09"],
    [
      ["\u6570\u636e\u6e90", "ccTCM 2.0\u4e09\u8868\u878d\u5408\uff08403\u7cbe\u82f1\u5e93\uff09", "HERB\u4e2d\u836f\u6570\u636e\u5e93\uff0829023\u5168\u5e93\uff09"],
      ["\u57fa\u5206\u7c7b\u5668", "RandomForest\uff08300\u68f5\u6811\uff09", "XGBoost"],
      ["PU\u7b56\u7565", "\u975e\u5bf9\u79f0Bagging 1:1\u5bf9\u79f0\u91c7\u6837\u00d730\u8f6e", "\u975e\u5bf9\u79f0Bagging 1:5\u975e\u5bf9\u79f0\u91c7\u6837\u00d730\u8f6e"],
      ["\u7279\u5f81\u7ef4\u5ea6", "1043\uff0819\u7ef4\u7279\u5f81+Morgan\u6307\u7eb91024\uff09", "1037\uff0813\u7ef4\u63cf\u8ff0\u7b26+Morgan\u6307\u7eb91024\uff09"],
      ["\u7f51\u683c\u641c\u7d22ROC-AUC", "0.8229\u00b10.0081", "0.8463\u00b10.0105"],
      ["\u6d4b\u8bd5\u96c6ROC-AUC", "0.8073", "0.8243"],
      ["\u5de5\u4f5c\u9608\u503c", "0.56", "0.62"],
    ],
    [AlignmentType.LEFT, AlignmentType.LEFT, AlignmentType.LEFT]),
  body("\u5176\u4e2dccTCM 2.0\u768419\u7ef4\u7279\u5f81\u75318\u9879ADME\u63cf\u8ff0\u7b26\uff08LogS\u3001LogD\u3001LogP\u3001P-gp\u3001F(20%)\u3001Caco-2\u3001MDCK\u7b49\uff0c\u7f3a\u5931\u65f6\u7b97\u6cd5\u63a8\u7b97\u4e14\u652f\u6301\u5b9e\u9a8c\u503c\u6821\u51c6\uff09\u4e0e11\u9879RDKit\u62d3\u6251\u7279\u5f81\uff08\u6c22\u952e\u53d7\u4f53/\u4f9b\u4f53\u6570\u3001TPSA\u3001\u53ef\u65cb\u8f6c\u952e\u6570\u7b49\uff0c\u7531SMILES\u7ed3\u6784\u5b9e\u65f6\u7cbe\u786e\u8ba1\u7b97\uff09\u6784\u6210\uff0c\u53e6\u62fc\u63a5Morgan\u6307\u7eb9\uff08radius=2\uff0c1024 bit\uff09\u3002\u63a8\u7406\u7ba1\u7ebf\u4e3aSMILES\u8f93\u5165\u2192RDKit\u7279\u5f81\u63d0\u53d6\u2192\u7f3a\u5931\u503c\u586b\u8865\u2192\u6807\u51c6\u5316\u219230\u8f6ePU Bagging\u6982\u7387\u5e73\u5747\uff0c\u5355\u5316\u5408\u7269\u9884\u6d4b\u8017\u65f6\u79d2\u7ea7\u3002\u53cc\u6a21\u578b\u6027\u80fd\u5bf9\u6bd4\u5982\u56fe1\u6240\u793a\u3002"),
  chartPara,
  caption("\u56fe1\u3000PU Learning\u53cc\u6a21\u578b\u5165\u8840\u9884\u6d4b\u6027\u80fd\u5bf9\u6bd4\uff08ROC-AUC\uff09"),
  body("\u4e3a\u9002\u914d\u4e91\u7aef\u514d\u8d39\u5b9e\u4f8b512MB\u5185\u5b58\u7ea6\u675f\uff0c\u53e6\u8bad\u7ec3\u4e8631MB\u7cbe\u7b80\u7248\u6a21\u578b\uff08Bagging\u8f6e\u657030\u219210\uff09\uff0c\u5176\u4e0e\u5b8c\u6574\u7248\u9884\u6d4b\u6982\u7387\u7684\u76f8\u5173\u7cfb\u6570\u8fbe0.9956\uff0cROC-AUC\u4ec5\u964d0.008\uff0c\u53ef\u901a\u8fc7\u73af\u5883\u53d8\u91cf\u5728\u4e91\u7aef\u4e0e\u672c\u5730\u81ea\u52a8\u5207\u6362\u3002"),
  h2("\uff08\u4e09\uff09\u65b9\u5242\u4f5c\u7528\u673a\u5236\u5206\u6790\u4e0e\u8bc4\u4ef7"),
  body("\u5728\u5165\u8840\u9884\u6d4b\u57fa\u7840\u4e0a\uff0c\u6784\u5efa\u4e86\u4ece\u65b9\u5242\u5230\u673a\u5236\u7684\u5206\u6790\u8bc4\u4ef7\u94fe\u6761\uff1a\u4e00\u662f\u201c\u65b9\u5242\u2192\u836f\u6750\u2192\u5316\u5408\u7269\u2192\u9776\u70b9\u201d\u56db\u5c42\u7f51\u7edc\u836f\u7406\u5b66\u62d3\u6251\uff0c\u652f\u6301\u5165\u8840\u6982\u7387\u9608\u503c\u3001\u54ee\u5596\u9776\u70b9\u8fc7\u6ee4\u7b49\u53c2\u6570\u8c03\u8282\uff0c\u8282\u70b9\u6309\u5165\u8840\u6982\u7387\u5206\u5c42\u7740\u8272\uff0c\u76f4\u89c2\u5c55\u793a\u201c\u54ea\u4e9b\u6210\u5206\u771f\u6b63\u8d77\u6548\u201d\uff1b\u4e8c\u662f\u63a5\u5165Enrichr API\u5b9e\u73b0KEGG/GO\u5b9e\u65f6GSEA\u5bcc\u96c6\u5206\u6790\uff0c\u91c7\u7528LRU\u7f13\u5b58\uff0830\u5206\u949f\uff09\u907f\u514d\u91cd\u590d\u8bf7\u6c42\uff1b\u4e09\u662f\u5c06\u5bcc\u96c6\u7ed3\u679c\u6982\u7387\u52a0\u6743\u5f52\u4e00\u5316\u4e3a\u6297\u708e\u6548\u80fd\u3001\u514d\u75ab\u8c03\u8282\u3001\u6c14\u9053\u4fee\u590d\u4e09\u4e2a\u7597\u6548\u7ef4\u5ea6\uff0c\u751f\u6210\u65b9\u5242\u7597\u6548\u96f7\u8fbe\u56fe\uff1b\u56db\u662f\u652f\u6301\u81ea\u5b9a\u4e49\u65b9\u5242\u7ec4\u5408\u5206\u6790\uff0c\u5e76\u517c\u5bb9OpenAI/DeepSeek\u7b49\u5927\u6a21\u578bAPI\uff0c\u4ee5SSE\u6d41\u5f0f\u65b9\u5f0f\u751f\u6210\u673a\u5236\u89e3\u8bfb\u62a5\u544a\u5e76\u652f\u6301PDF\u5bfc\u51fa\u3002"),
  h2("\uff08\u56db\uff09\u53ef\u89c6\u5316\u5206\u6790\u7cfb\u7edf\u4e0e\u4e91\u7aef\u90e8\u7f72"),
  body("\u7cfb\u7edf\u91c7\u7528\u524d\u540e\u7aef\u5206\u79bb\u67b6\u6784\uff1a\u540e\u7aef\u57fa\u4e8eFastAPI+SQLAlchemy+RDKit\uff0c\u542b8\u4e2a\u8def\u7531\u6a21\u5757\u300130\u4f59\u4e2aAPI\u63a5\u53e3\uff0c\u6a21\u578b\u63a8\u7406\u901a\u8fc7\u5f02\u6b65\u8c03\u5ea6\u907f\u514d\u963b\u585e\u4e8b\u4ef6\u5faa\u73af\uff1b\u524d\u7aef\u57fa\u4e8eVue3+Element Plus+ECharts+Cytoscape.js\uff0c\u542b13\u4e2a\u9875\u9762\u7ec4\u4ef6\u3002\u6838\u5fc3\u529f\u80fd\u5305\u62ec\uff1a\uff081\uff09\u5165\u8840\u9884\u6d4b\u63a7\u5236\u53f0\uff0c\u652f\u6301\u5355\u5316\u5408\u7269SMILES\u9884\u6d4b\u3001ADME\u5b9e\u9a8c\u503c\u6821\u51c6\u91cd\u7b97\u3001\u5355\u6b21\u81f3500\u6761\u7684\u6279\u91cf\u6587\u4ef6\u9884\u6d4b\u4e0e\u9884\u6d4b\u5386\u53f2\u7ba1\u7406\uff1b\uff082\uff09\u65b9\u5242\u6d4f\u89c8\u4e0e\u8be6\u60c5\uff0c\u96c6\u6210\u56db\u5c42\u62d3\u6251\u3001\u96f7\u8fbe\u56fe\u4e0e\u5bcc\u96c6\u67f1\u72b6\u56fe\uff1b\uff083\uff09\u81ea\u5b9a\u4e49\u65b9\u5242\u5206\u6790\u4e0eAI\u62a5\u544a\uff1b\uff084\uff09\u4e13\u5bb6\u6a21\u5f0f\uff0c\u5c55\u793a\u6a21\u578b\u7279\u5f81\u8d21\u732e\u5ea6\u4e0e\u6570\u636e\u96c6\u7edf\u8ba1\uff1b\uff085\uff09\u667a\u80fd\u68c0\u7d22\uff0c\u652f\u6301\u4e2d\u6587\u6a21\u7cca\u5339\u914d\u3001\u62fc\u97f3\u9996\u5b57\u6bcd\u8054\u60f3\u4e0e\u836f\u6750\u540d\u53cd\u67e5\u65b9\u5242\u3002"),
  body("\u7cfb\u7edf\u5df2\u90e8\u7f72\u81f3\u4e91\u7aef\uff08\u524d\u7aefVercel\u3001\u540e\u7aefRender\uff09\uff0c\u6e90\u4ee3\u7801\u6258\u7ba1\u4e8eGitHub\uff08asthma-system\u805a\u5408\u4ed3\u5e93\u53ca\u524d\u540e\u7aef\u5b50\u4ed3\u5e93\uff09\uff0c\u6570\u636e\u5e93\u4e0e\u6a21\u578b\u6587\u4ef6\u901a\u8fc7Release\u5206\u53d1\uff0c\u5177\u5907\u5b8c\u6574\u7684\u53ef\u590d\u73b0\u90e8\u7f72\u80fd\u529b\u3002"),

  h1("\u56db\u3001\u9636\u6bb5\u6027\u6210\u679c\u4e0e\u8003\u6838\u6307\u6807\u5bf9\u7167"),
  body("\u5bf9\u7167\u7533\u62a5\u4e66\u56db\u9879\u9884\u671f\u6210\u679c\uff0c\u4e2d\u671f\u5b8c\u6210\u60c5\u51b5\u5982\u88685\u6240\u793a\uff0c\u603b\u4f53\u7b26\u5408\u9884\u671f\u8fdb\u5ea6\u3002"),
  caption("\u88685\u3000\u9884\u671f\u6210\u679c\u4e0e\u4e2d\u671f\u5b8c\u6210\u60c5\u51b5\u5bf9\u7167"),
  hTable([40, 16, 44],
    ["\u7533\u62a5\u4e66\u9884\u671f\u6210\u679c", "\u5b8c\u6210\u60c5\u51b5", "\u8bf4\u660e"],
    [
      ["\u513f\u7ae5\u54ee\u5596\u4e2d\u836f\u5165\u8840\u6210\u5206\u9884\u6d4b\u4e0e\u53ef\u89c6\u5316\u5206\u6790\u7cfb\u7edf1\u5957", "\u5df2\u5b8c\u6210", "\u524d\u540e\u7aef\u5206\u79bb\u7cfb\u7edf\u5df2\u4e0a\u7ebf\uff0c\u4e91\u7aef\u53ef\u8bbf\u95ee"],
      ["\u513f\u7ae5\u54ee\u5596\u4e2d\u836f\u5316\u5408\u7269\u6570\u636e\u96c6\u53ca\u5019\u9009\u5165\u8840\u6210\u5206\u6e05\u53551\u5957", "\u5df2\u5b8c\u6210", "46\u9996\u65b9\u5242/278\u5473\u836f\u6750/569\u4e2a\u5316\u5408\u7269/7398\u4e2a\u9776\u70b9"],
      ["\u83b7\u5f97\u77e5\u8bc6\u4ea7\u6743\uff08\u8f6f\u8457\u3001\u5b66\u672f\u8bba\u6587\u7b49\uff091\u20142\u9879", "\u63a8\u8fdb\u4e2d", "\u8f6f\u4ef6\u8457\u4f5c\u6743\u7533\u62a5\u6750\u6599\u6574\u7406\u4e2d\uff0c\u62df2026\u5e7412\u6708\u524d\u63d0\u4ea4\uff1b\u8bba\u6587\u64b0\u5199\u4e2d"],
      ["\u5b8c\u6210\u513f\u7ae5\u54ee\u5596\u4e2d\u836f\u7528\u836f\u673a\u5236\u5206\u6790\u7814\u7a76\u62a5\u544a1\u7bc7", "\u63a8\u8fdb\u4e2d", "\u672c\u62a5\u544a\u4e3a\u9636\u6bb5\u6027\u7814\u7a76\u62a5\u544a\uff0c\u7ed3\u9898\u7814\u7a76\u62a5\u544a\u5c06\u4e8e2027\u5e741\u5b63\u5ea6\u5b8c\u6210"],
    ],
    [AlignmentType.LEFT, CENTER, AlignmentType.LEFT]),

  h1("\u4e94\u3001\u7ecf\u8d39\u4f7f\u7528\u60c5\u51b5"),
  body("\u9879\u76ee\u9884\u7b97\u603b\u989d5000\u5143\uff0c\u524d\u534a\u9636\u6bb5\u5df2\u4e0b\u8fbe2800\u5143\u3002\u622a\u81f3\u4e2d\u671f\u68c0\u67e5\uff0c\u7d2f\u8ba1\u5217\u652f1760\u5143\uff0c\u4e3b\u8981\u7528\u4e8e\u6a21\u578b\u8bad\u7ec3\u4e0e\u6d4b\u8bd5\u3001\u6587\u732e\u68c0\u7d22\u53ca\u6750\u6599\u6574\u7406\uff0c\u5404\u79d1\u76ee\u652f\u51fa\u5747\u5728\u9884\u7b97\u8303\u56f4\u5185\uff0c\u5177\u4f53\u5982\u88686\u6240\u793a\u3002"),
  caption("\u88686\u3000\u4e2d\u671f\u7ecf\u8d39\u4f7f\u7528\u60c5\u51b5\uff08\u5355\u4f4d\uff1a\u5143\uff09"),
  hTable([26, 14, 14, 46],
    ["\u5f00\u652f\u79d1\u76ee", "\u9884\u7b97\u7ecf\u8d39", "\u5df2\u4f7f\u7528", "\u4e3b\u8981\u7528\u9014"],
    [
      ["\u8ba1\u7b97\u3001\u5206\u6790\u3001\u6d4b\u8bd5\u8d39", "1600", "620", "\u6a21\u578b\u8bad\u7ec3\u8c03\u53c2\u4e91\u7aef\u7b97\u529b\u3001\u6570\u636e\u6e05\u6d17\u4e0e\u6279\u91cf\u9884\u6d4b\u6d4b\u8bd5"],
      ["\u80fd\u6e90\u52a8\u529b\u8d39", "300", "140", "\u5f00\u53d1\u4e0e\u6d4b\u8bd5\u671f\u95f4\u7f51\u7edc\u3001\u7535\u529b\u652f\u51fa"],
      ["\u4f1a\u8bae\u3001\u5dee\u65c5\u8d39", "900", "260", "\u9636\u6bb5\u6c47\u62a5\u4e0e\u6821\u5185\u5916\u4ea4\u6d41\u4ea4\u901a\u652f\u51fa"],
      ["\u6587\u732e\u68c0\u7d22\u8d39", "700", "380", "\u4e2d\u836f\u6210\u5206\u3001\u5165\u8840\u6807\u8bc6\u3001\u9776\u70b9\u6d3b\u6027\u76f8\u5173\u6587\u732e\u4e0e\u6570\u636e\u5e93\u68c0\u7d22"],
      ["\u8bba\u6587\u51fa\u7248\u8d39", "800", "120", "\u8bba\u6587\u64b0\u5199\u4e0e\u77e5\u8bc6\u4ea7\u6743\u7533\u62a5\u8f85\u52a9\u652f\u51fa"],
      ["\u6750\u6599\u8d39", "700", "240", "\u8d44\u6599\u6253\u5370\u3001\u62a5\u544a\u88c5\u8ba2\u4e0e\u7b54\u8fa9\u6750\u6599\u8017\u6750"],
      ["\u5408\u8ba1", "5000", "1760", "\u5269\u4f59\u53ca\u540e\u534a\u9636\u6bb5\u7ecf\u8d39\u7528\u4e8e\u8bba\u6587\u51fa\u7248\u3001\u8f6f\u8457\u7533\u62a5\u4e0e\u7ed3\u9898\u6750\u6599"],
    ],
    [AlignmentType.LEFT, CENTER, CENTER, AlignmentType.LEFT]),
  body("\u6ce8\uff1a\u4ee5\u4e0a\u4e3a\u9636\u6bb5\u6027\u7edf\u8ba1\u6570\u636e\uff0c\u8bf7\u4ee5\u5b9e\u9645\u62a5\u9500\u51ed\u8bc1\u6838\u5bf9\u540e\u586b\u62a5\u3002"),

  h1("\u516d\u3001\u5b58\u5728\u7684\u95ee\u9898\u4e0e\u6539\u8fdb\u63aa\u65bd"),
  itemP("\uff08\u4e00\uff09\u5904\u65b9\u66b4\u9732\u91cf\u7b49\u513f\u7ae5\u7279\u5f02\u6027\u7279\u5f81\u5c1a\u672a\u5145\u5206\u878d\u5165\u6a21\u578b\u3002", "\u7533\u62a5\u4e66\u63d0\u51fa\u878d\u5408\u5904\u65b9\u66b4\u9732\u91cf\u4e0e\u4ee3\u8c22\u8f6c\u5316\u4fe1\u606f\uff0c\u76ee\u524d\u6a21\u578b\u4ee5\u5206\u5b50\u7ed3\u6784\u4e0e\u7406\u5316\u6027\u8d28\u7279\u5f81\u4e3a\u4e3b\uff0c\u836f\u6750\u7528\u91cf\u4e0e\u6210\u5206\u542b\u91cf\u4fe1\u606f\u5c1a\u672a\u8fdb\u5165\u7279\u5f81\u77e9\u9635\u3002\u6539\u8fdb\u63aa\u65bd\uff1a\u5728\u5df2\u6709\u5242\u91cf\u5b57\u6bb5\u57fa\u7840\u4e0a\u6784\u5efa\u5904\u65b9\u66b4\u9732\u91cf\u7279\u5f81\uff0c\u5f00\u5c55\u7279\u5f81\u6d88\u878d\u5b9e\u9a8c\u8bc4\u4f30\u5176\u589e\u76ca\u3002"),
  itemP("\uff08\u4e8c\uff09\u5f31\u8d1f\u6837\u672c\u6821\u6b63\u4e0e\u591a\u6a21\u578b\u878d\u5408\u7b56\u7565\u6709\u5f85\u6df1\u5316\u3002", "\u5f53\u524d\u4ee5PU Bagging\u96c6\u6210\u8f93\u51fa\u5165\u8840\u6982\u7387\uff0c\u6587\u732e\u5f31\u8d1f\u6837\u672c\u4ec5\u4f5c\u53c2\u8003\uff0c\u5c1a\u672a\u53c2\u4e0e\u6982\u7387\u6821\u6b63\u3002\u6539\u8fdb\u63aa\u65bd\uff1a\u63d0\u53d6\u7279\u5b9a\u5904\u65b9\u6761\u4ef6\u4e0b\u201c\u672a\u68c0\u51fa\u201d\u6210\u5206\u4f5c\u4e3a\u5f31\u8d1f\u6837\u672c\u96c6\uff0c\u7ed3\u5408\u53ef\u4fe1\u5ea6\u6743\u91cd\u5f00\u5c55\u6821\u6b63\u5b9e\u9a8c\uff0c\u5e76\u6bd4\u8f83\u5bc6\u5ea6\u4f30\u8ba1\u3001\u8ddd\u79bb\u5224\u522b\u7b49\u5355\u7c7b\u65b9\u6cd5\u7684\u8f85\u52a9\u5224\u522b\u6548\u679c\u3002"),
  itemP("\uff08\u4e09\uff09\u7cfb\u7edf\u5de5\u7a0b\u7ec6\u8282\u6709\u5f85\u5b8c\u5584\u3002", "\u90e8\u5206\u7a97\u53e3\u7ec4\u4ef6\u98ce\u683c\u672a\u7edf\u4e00\uff0c\u5355\u5143\u6d4b\u8bd5\u4e0e\u7aef\u5230\u7aef\u6d4b\u8bd5\u8986\u76d6\u4e0d\u8db3\u3002\u6539\u8fdb\u63aa\u65bd\uff1a\u6309\u4f18\u5148\u7ea7\u5b8c\u6210\u754c\u9762\u98ce\u683c\u7edf\u4e00\u4e0e\u5b57\u4f53\u914d\u8272\u6392\u67e5\uff0c\u5f15\u5165\u57fa\u7840\u81ea\u52a8\u5316\u6d4b\u8bd5\uff0c\u5b8c\u5584\u7528\u6237\u4f7f\u7528\u6587\u6863\u3002"),

  h1("\u4e03\u3001\u4e0b\u4e00\u9636\u6bb5\u5de5\u4f5c\u8ba1\u5212"),
  body("\u4e0b\u4e00\u9636\u6bb5\u5c06\u56f4\u7ed5\u6a21\u578b\u6df1\u5316\u3001\u6210\u679c\u4ea7\u51fa\u4e0e\u7ed3\u9898\u9a8c\u6536\u4e09\u6761\u4e3b\u7ebf\u63a8\u8fdb\uff0c\u5177\u4f53\u5b89\u6392\u5982\u88687\u6240\u793a\u3002"),
  caption("\u88687\u3000\u4e0b\u4e00\u9636\u6bb5\u5de5\u4f5c\u8ba1\u5212"),
  hTable([20, 50, 30],
    ["\u65f6\u95f4", "\u5de5\u4f5c\u5185\u5bb9", "\u9884\u671f\u4ea7\u51fa"],
    [
      ["2026.11\u20142026.12", "\u5904\u65b9\u66b4\u9732\u91cf\u7279\u5f81\u6784\u5efa\u4e0e\u6d88\u878d\u5b9e\u9a8c\uff1b\u5f31\u8d1f\u6837\u672c\u6821\u6b63\u4e0e\u591a\u6a21\u578b\u878d\u5408\uff1b\u63d0\u4ea4\u8f6f\u4ef6\u8457\u4f5c\u6743\u7533\u8bf7", "\u7279\u5f81\u589e\u76ca\u8bc4\u4f30\u62a5\u544a\uff0c\u8f6f\u8457\u53d7\u74061\u9879"],
      ["2027.1\u20142027.2", "\u5b66\u672f\u8bba\u6587\u64b0\u5199\u4e0e\u6295\u7a3f\uff1b\u5c0f\u9752\u9f99\u6c64\u3001\u5c04\u5e72\u9ebb\u9ec4\u6c64\u7b49\u5178\u578b\u65b9\u5242\u673a\u5236\u5206\u6790\u6848\u4f8b\uff1b\u7cfb\u7edf\u754c\u9762\u7edf\u4e00\u4e0e\u6d4b\u8bd5\u4f18\u5316", "\u8bba\u6587\u6295\u7a3f1\u7bc7\uff0c\u6848\u4f8b\u5206\u6790\u6e05\u5355"],
      ["2027.3\u20142027.4", "\u6c47\u603b\u6570\u636e\u96c6\u3001\u7cfb\u7edf\u3001\u8bba\u6587\u7b49\u6210\u679c\uff0c\u64b0\u5199\u9879\u76ee\u7814\u7a76\u62a5\u544a\u4e0e\u7ed3\u9898\u6750\u6599", "\u7ed3\u9898\u6750\u6599\u521d\u7a3f"],
      ["2027.5", "\u5b8c\u6210\u7ed3\u9898\u7b54\u8fa9\uff0c\u63d0\u4ea4\u5168\u90e8\u7ed3\u9898\u6750\u6599", "\u5b8c\u6210\u7ed3\u9898\u9a8c\u6536"],
    ],
    [CENTER, AlignmentType.LEFT, AlignmentType.LEFT]),

  h1("\u516b\u3001\u603b\u7ed3"),
  body("\u4e2d\u671f\u9636\u6bb5\uff0c\u9879\u76ee\u6309\u8ba1\u5212\u5b8c\u6210\u4e86\u6570\u636e\u5e93\u5efa\u8bbe\u3001\u5165\u8840\u9884\u6d4b\u53cc\u6a21\u578b\u6784\u5efa\u3001\u673a\u5236\u8bc4\u4ef7\u6a21\u5757\u4e0e\u53ef\u89c6\u5316\u7cfb\u7edf\u56db\u5927\u6838\u5fc3\u5de5\u4f5c\uff0c\u5f62\u6210\u4e86\u4ece\u5904\u65b9\u8f93\u5165\u5230\u673a\u5236\u89e3\u8bfb\u7684\u5b8c\u6574\u5206\u6790\u80fd\u529b\uff0c\u7cfb\u7edf\u5df2\u5177\u5907\u5b9e\u9645\u4f7f\u7528\u4ef7\u503c\u3002\u9879\u76ee\u521b\u65b0\u6027\u4e3b\u8981\u4f53\u73b0\u5728\uff1a\u9762\u5411\u65e0\u53ef\u9760\u8d1f\u6837\u672c\u573a\u666f\u7684PU\u5b66\u4e60\u5165\u8840\u9884\u6d4b\u65b9\u6cd5\u3001\u591a\u6a21\u6001\u7279\u5f81\u4f53\u7cfb\u4e0e\u5165\u8840\u9884\u6d4b\u2014\u673a\u5236\u8bc4\u4ef7\u4e00\u4f53\u5316\u7684\u5de5\u7a0b\u5316\u5b9e\u73b0\u3002"),
  body("\u4e0b\u4e00\u9636\u6bb5\uff0c\u56e2\u961f\u5c06\u91cd\u70b9\u8865\u9f50\u5904\u65b9\u66b4\u9732\u91cf\u7279\u5f81\u4e0e\u5f31\u8d1f\u6837\u672c\u6821\u6b63\u4e24\u9879\u65b9\u6cd5\u6df1\u5316\u5de5\u4f5c\uff0c\u63a8\u8fdb\u8f6f\u8457\u7533\u62a5\u3001\u8bba\u6587\u6295\u7a3f\u4e0e\u7ed3\u9898\u6750\u6599\u6574\u7406\uff0c\u786e\u4fdd\u9879\u76ee\u6309\u671f\u4fdd\u8d28\u5b8c\u6210\u5404\u9879\u8003\u6838\u6307\u6807\u3002"),
];

// ---------- 文档组装 ----------
const pgSize = { width: 11906, height: 16838 };
const pgMargin = { top: 1440, bottom: 1440, left: 1701, right: 1417 };
const numFooter = () => new Footer({
  children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "808080", font: { ascii: "Times New Roman" } })],
  })],
});
const bodyHeader = new Header({
  children: [new Paragraph({
    alignment: AlignmentType.CENTER,
    border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: "BBBBBB", space: 4 } },
    children: [new TextRun({ text: "\u5927\u521b\u9879\u76ee\u4e2d\u671f\u8fdb\u5c55\u62a5\u544a", size: 18, color: "808080", font: { ascii: "Times New Roman", eastAsia: "SimSun" } })],
  })],
});

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: { ascii: "Times New Roman", eastAsia: "SimSun" }, size: 24, color: "000000" },
        paragraph: { spacing: { line: 312 } },
      },
      heading1: {
        run: { font: { ascii: "Times New Roman", eastAsia: "SimHei" }, size: 32, bold: true, color: P.primary },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 },
      },
      heading2: {
        run: { font: { ascii: "Times New Roman", eastAsia: "SimHei" }, size: 28, bold: true, color: P.primary },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 },
      },
    },
  },
  sections: [
    { // 封面
      properties: { page: { size: pgSize, margin: { top: 0, bottom: 0, left: 0, right: 0 } } },
      children: buildCoverR1({
        title: "\u57fa\u4e8e\u5165\u8840\u9884\u6d4b\u7684\u4e2d\u533b\u6cbb\u7597\u513f\u7ae5\u54ee\u5596\u4f5c\u7528\u673a\u5236\u5206\u6790",
        subtitle: "\u5927\u5b66\u751f\u521b\u65b0\u521b\u4e1a\u8bad\u7ec3\u8ba1\u5212\u9879\u76ee \u00b7 \u4e2d\u671f\u8fdb\u5c55\u62a5\u544a",
        englishLabel: "MID-TERM PROGRESS REPORT",
        metaLines: [
          "\u9879\u76ee\u7ea7\u522b\uff1a\u6c5f\u82cf\u7701\u5927\u5b66\u751f\u521b\u65b0\u521b\u4e1a\u8bad\u7ec3\u8ba1\u5212\u91cd\u70b9\u9879\u76ee",
          "\u9879\u76ee\u7c7b\u578b\uff1a\u521b\u65b0\u8bad\u7ec3\u9879\u76ee",
          "\u9879\u76ee\u8d1f\u8d23\u4eba\uff1a\u5f20\u9707\u7fd4\u3000\u5468\u4fca\u5cf0",
          "\u6307\u5bfc\u6559\u5e08\uff1a\u4e01\u6709\u4f1f\u3000\u8d75\u7389\u7537",
          "\u6240\u5728\u5b66\u9662\uff1a\u5357\u4eac\u4e2d\u533b\u836f\u5927\u5b66\u4eba\u5de5\u667a\u80fd\u4e0e\u4fe1\u606f\u6280\u672f\u5b66\u9662",
          "\u62a5\u544a\u65f6\u95f4\uff1a2026\u5e7410\u6708",
        ],
        footerLeft: "\u5357\u4eac\u4e2d\u533b\u836f\u5927\u5b66",
        footerRight: "2026\u5e7410\u6708",
        palette: P,
      }),
    },
    { // 目录（独立节，不显示页码）
      properties: { type: SectionType.NEXT_PAGE, page: { size: pgSize, margin: pgMargin } },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 480, after: 360, line: 400, lineRule: "atLeast" },
          children: [new TextRun({ text: "\u76ee\u3000\u5f55", bold: true, size: 32, font: { eastAsia: "SimHei", ascii: "Times New Roman" }, color: "000000" })],
        }),
        new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-2" }),
        new Paragraph({
          spacing: { before: 200 },
          children: [new TextRun({
            text: "\u6ce8\uff1a\u672c\u76ee\u5f55\u7531\u57df\u4ee3\u7801\u751f\u6210\uff0c\u7f16\u8f91\u6587\u6863\u540e\u8bf7\u53f3\u952e\u76ee\u5f55\u5e76\u9009\u62e9\u201c\u66f4\u65b0\u57df\u201d\u4ee5\u5237\u65b0\u9875\u7801\u3002",
            italics: true, size: 18, color: "888888",
          })],
        }),
      ],
    },
    { // 正文（阿拉伯页码从1开始）
      properties: {
        type: SectionType.NEXT_PAGE,
        page: { size: pgSize, margin: pgMargin, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } },
      },
      headers: { default: bodyHeader },
      footers: { default: numFooter() },
      children: bodyChildren,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("OK ->", OUT, buf.length, "bytes");
});
