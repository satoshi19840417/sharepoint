import PptxGenJS from "pptxgenjs";

// Initialize the presentation
const pres = new PptxGenJS();

// Set common properties
pres.layout = "LAYOUT_16x9";
pres.title = "Skills導入のメリット";
pres.subject = "AI Study Promo";

// Colors
const COLOR_PRIMARY = "0078D4"; // SharePoint/Microsoft Blue-ish
const COLOR_ACCENT = "E67E22"; // Orange
const COLOR_TEXT = "333333";
const COLOR_BG = "FFFFFF";

// -------------------------------------------------------------
// Slide 1: Title
// -------------------------------------------------------------
const s1 = pres.addSlide();
s1.background = { color: "F3F2F1" };

s1.addText("AIをもっと頼れる「相棒」に", {
    x: 1, y: 2.5, w: 9, h: 1,
    fontSize: 32,
    color: COLOR_PRIMARY,
    bold: true,
    align: "center"
});

s1.addText("Skills（スキルズ）で変わる私たちの仕事", {
    x: 1, y: 3.5, w: 9, h: 1,
    fontSize: 24,
    color: COLOR_TEXT,
    bold: true,
    align: "center"
});

s1.addText("専門知識は不要！今日から使えるAI活用術", {
    x: 1, y: 5.0, w: 9, h: 0.5,
    fontSize: 18,
    color: COLOR_ACCENT,
    align: "center"
});

// -------------------------------------------------------------
// Slide 2: Status Quo (Problems)
// -------------------------------------------------------------
const s2 = pres.addSlide();
s2.addText("今、こんな悩みありませんか？", {
    x: 0.5, y: 0.5, w: 9, h: 0.8,
    fontSize: 24,
    color: COLOR_PRIMARY,
    bold: true,
    border: { pt: 0, color: "FFFFFF", bottom: { pt: 2, color: COLOR_PRIMARY } }
});

s2.addText("日々の業務で、こんな「もどかしさ」感じていませんか？", {
    x: 0.5, y: 1.5, w: 9, h: 0.5,
    fontSize: 14,
    color: COLOR_TEXT
});

s2.addText([
    { text: "• 「AIにレポートを書かせたいけど、決まった形式にする指示を書くのが面倒…」\n", options: { breakLine: true } },
    { text: "• 「『もっといい感じに』と頼んでも、通じなくて修正ばかり…」\n", options: { breakLine: true } },
    { text: "• 「AIを使いたいけど、難しそうで何から始めればいいかわからない…」", options: { breakLine: false } }
], {
    x: 1, y: 2.2, w: 8, h: 2,
    fontSize: 16,
    color: COLOR_TEXT,
    lineSpacing: 32
});

// Box for solution
s2.addShape(pres.ShapeType.rect, {
    x: 1, y: 4.5, w: 8, h: 2,
    fill: { color: "E1F5FE" },
    line: { color: COLOR_PRIMARY, width: 2 }
});

s2.addText("その悩み、「Skills（スキルズ）」を使えば解決できます！", {
    x: 1.2, y: 4.8, w: 7.6, h: 0.5,
    fontSize: 18,
    color: COLOR_PRIMARY,
    bold: true,
    align: "center"
});

s2.addText("AIがあなたの業務ルールを理解した「専属アシスタント」に早変わりします。", {
    x: 1.2, y: 5.5, w: 7.6, h: 0.5,
    fontSize: 16,
    color: COLOR_TEXT,
    align: "center"
});

// -------------------------------------------------------------
// Slide 3: Concept
// -------------------------------------------------------------
const s3 = pres.addSlide();
s3.addText("Skills（スキルズ）とは？", {
    x: 0.5, y: 0.5, w: 9, h: 0.8,
    fontSize: 24,
    color: COLOR_PRIMARY,
    bold: true,
    border: { pt: 0, color: "FFFFFF", bottom: { pt: 2, color: COLOR_PRIMARY } }
});

s3.addText("Skills ＝ AIに入れる「スマホアプリ」", {
    x: 0.5, y: 1.5, w: 9, h: 0.5,
    fontSize: 18,
    color: COLOR_ACCENT,
    bold: true
});

// Left: Phone metaphor
s3.addText("📱スマートフォン + アプリ", {
    x: 0.5, y: 2.2, w: 4, h: 0.5,
    fontSize: 14,
    color: COLOR_TEXT,
    bold: true
});
s3.addText("→ 地図が見れる！\n→ ゲームができる！", {
    x: 0.5, y: 2.8, w: 4, h: 1,
    fontSize: 14,
    color: COLOR_TEXT
});

// Right: AI metaphor
s3.addText("🤖 AIエージェント + Skill", {
    x: 5, y: 2.2, w: 4, h: 0.5,
    fontSize: 14,
    color: COLOR_TEXT,
    bold: true
});
s3.addText("→ 論文校正ができる！\n→ 規程チェックができる！", {
    x: 5, y: 2.8, w: 4, h: 1,
    fontSize: 14,
    color: COLOR_TEXT,
    bold: true,
    color: "E74C3c" // Highlight
});

// Points
s3.addText([
    { text: "1. プログラミング不要: ", options: { bold: true } },
    { text: "難しいコードを書く必要は一切ありません。\n", options: { breakLine: true } },
    { text: "2. 選んで入れるだけ: ", options: { bold: true } },
    { text: "「これ使いたい！」と思った機能を選ぶだけ。\n", options: { breakLine: true } },
    { text: "3. 専門家のノウハウ: ", options: { bold: true } },
    { text: "世界中の専門家が作った「上手な仕事のやり方」が詰まっています。", options: { breakLine: false } }
], {
    x: 0.5, y: 4.5, w: 9, h: 2.2,
    fontSize: 14,
    color: COLOR_TEXT,
    fill: { color: "F3F2F1" },
    inset: 0.2
});


// -------------------------------------------------------------
// Slide 4: Selection (How to)
// -------------------------------------------------------------
const s4 = pres.addSlide();
s4.addText("直感的でわかりやすい！Skillsの選び方", {
    x: 0.5, y: 0.5, w: 9, h: 0.8,
    fontSize: 24,
    color: COLOR_PRIMARY,
    bold: true,
    border: { pt: 0, color: "FFFFFF", bottom: { pt: 2, color: COLOR_PRIMARY } }
});

s4.addText("ネットショッピング感覚で、必要な機能を探そう", {
    x: 0.5, y: 1.5, w: 9, h: 0.5,
    fontSize: 14,
    color: COLOR_TEXT
});

s4.addText([
    { text: "• 見やすいカタログ: ", options: { bold: true } },
    { text: "どんなことができるか、カード形式でひと目でわかります。\n", options: {} },
    { text: "• ランキング形式: ", options: { bold: true } },
    { text: "今みんなが使っている人気のスキルがすぐに分かります。", options: {} }
], {
    x: 0.5, y: 2.2, w: 4.5, h: 2,
    fontSize: 14, color: COLOR_TEXT, lineSpacing: 24
});

s4.addShape(pres.ShapeType.rect, {
    x: 5.5, y: 2.2, w: 4, h: 2.5,
    fill: { color: "DDDDDD" },
    line: { color: "AAAAAA", dashType: "dash" }
});
s4.addText("(ここに skills.sh のブラウザ画面などを貼ると効果的です)", {
    x: 5.5, y: 2.2, w: 4, h: 2.5,
    fontSize: 12, color: "666666", align: "center", valign: "middle"
});

s4.addText("黒い画面にコマンドを打ち込むような「エンジニアの作業」ではありません。\nカタログを見て「これ便利そう！」と選ぶ、ワクワクする体験です。", {
    x: 0.5, y: 5.2, w: 9, h: 1,
    fontSize: 14,
    color: COLOR_PRIMARY,
    bold: true,
    align: "center",
    fill: { color: "FFF3E0" }
});


// -------------------------------------------------------------
// Slide 5: Use Cases
// -------------------------------------------------------------
const s5 = pres.addSlide();
s5.addText("私たちの業務でどう使える？", {
    x: 0.5, y: 0.5, w: 9, h: 0.8,
    fontSize: 24,
    color: COLOR_PRIMARY,
    bold: true,
    border: { pt: 0, color: "FFFFFF", bottom: { pt: 2, color: COLOR_PRIMARY } }
});

// Case 1
s5.addShape(pres.ShapeType.rect, {
    x: 0.5, y: 1.8, w: 4.4, h: 3.5,
    fill: { color: "FFFFFF" },
    line: { color: "AAAAAA" }
});
s5.addText("【CASE 1: 研究員の皆様】", {
    x: 0.6, y: 2.0, w: 4, h: 0.4,
    fontSize: 14, color: COLOR_PRIMARY, bold: true
});
s5.addText("論文執筆の強力なサポーター", {
    x: 0.6, y: 2.5, w: 4, h: 0.4,
    fontSize: 12, color: COLOR_TEXT, bold: true
});
s5.addText("・データをしてのフォーマット（APAスタイル等）に整えて\n・英語文献を読んで、要点だけを日本語で箇条書きにして", {
    x: 0.6, y: 3.0, w: 4, h: 1,
    fontSize: 11, color: "666666"
});
s5.addText("👉 面倒な形式調整や翻訳作業から\n解放され、研究そのものに集中！", {
    x: 0.6, y: 4.2, w: 4, h: 0.8,
    fontSize: 12, color: COLOR_ACCENT, bold: true, align: "center"
});


// Case 2
s5.addShape(pres.ShapeType.rect, {
    x: 5.1, y: 1.8, w: 4.4, h: 3.5,
    fill: { color: "FFFFFF" },
    line: { color: "AAAAAA" }
});
s5.addText("【CASE 2: 管理部門の皆様】", {
    x: 5.2, y: 2.0, w: 4, h: 0.4,
    fontSize: 14, color: COLOR_PRIMARY, bold: true
});
s5.addText("ミスの許されない確認作業に", {
    x: 5.2, y: 2.5, w: 4, h: 0.4,
    fontSize: 12, color: COLOR_TEXT, bold: true
});
s5.addText("・契約書案、社内規定の第3条に違反していないかチェックして\n・経費データを読み込んで、費目ごとの集計表をExcelで作って", {
    x: 5.2, y: 3.0, w: 4, h: 1,
    fontSize: 11, color: "666666"
});
s5.addText("👉 目視確認の負担を減らし、\nヒューマンエラーを防ぐ！", {
    x: 5.2, y: 4.2, w: 4, h: 0.8,
    fontSize: 12, color: COLOR_ACCENT, bold: true, align: "center"
});


// -------------------------------------------------------------
// Slide 6: Benefits
// -------------------------------------------------------------
const s6 = pres.addSlide();
s6.addText("導入のメリット - 「楽・速・確」", {
    x: 0.5, y: 0.5, w: 9, h: 0.8,
    fontSize: 24,
    color: COLOR_PRIMARY,
    bold: true,
    border: { pt: 0, color: "FFFFFF", bottom: { pt: 2, color: COLOR_PRIMARY } }
});

const benefits = [
    { title: "【楽（ラク）】", sub: "指示出しのストレスゼロ", desc: "「〇〇スキルを使って」の一言で通じます。" },
    { title: "【速（ハヤイ）】", sub: "ゼロから作らなくていい", desc: "誰かが作った解決策で、試行錯誤する時間を大幅に節約。" },
    { title: "【確（カクジツ）】", sub: "品質のバラつきを防ぐ", desc: "実績のあるスキルなら、誰がやっても高品質な結果に。" }
];

benefits.forEach((b, i) => {
    const yPos = 1.8 + (i * 1.5);

    // Circle/Number placeholder
    s6.addShape(pres.ShapeType.ellipse, {
        x: 0.5, y: yPos, w: 0.8, h: 0.8,
        fill: { color: COLOR_PRIMARY }
    });
    s6.addText(`${i + 1}`, {
        x: 0.5, y: yPos, w: 0.8, h: 0.8,
        fontSize: 20, color: "FFFFFF", align: "center", valign: "middle", bold: true
    });

    // Content
    s6.addText(b.title, {
        x: 1.5, y: yPos, w: 2.5, h: 0.5,
        fontSize: 16, color: COLOR_PRIMARY, bold: true
    });
    s6.addText(b.sub, {
        x: 4.0, y: yPos, w: 5, h: 0.5,
        fontSize: 16, color: COLOR_TEXT, bold: true
    });
    s6.addText(b.desc, {
        x: 1.5, y: yPos + 0.5, w: 7.5, h: 0.5,
        fontSize: 14, color: "666666"
    });
});


// -------------------------------------------------------------
// Slide 7: Summary
// -------------------------------------------------------------
const s7 = pres.addSlide();
s7.background = { color: "F3F2F1" };

s7.addText("まずは「使ってみる」ことから始めよう", {
    x: 1, y: 1.5, w: 8, h: 1,
    fontSize: 24,
    color: COLOR_PRIMARY,
    bold: true,
    align: "center"
});

s7.addText([
    { text: "Skillsは、エンジニアだけのものではありません。\n", options: { breakLine: true } },
    { text: "私たち全員の", options: {} },
    { text: "「業務改善ツール箱」", options: { bold: true, color: COLOR_ACCENT, fontSize: 18 } },
    { text: "です。", options: { breakLine: true } },
], {
    x: 1, y: 3.0, w: 8, h: 1.5,
    fontSize: 16,
    color: COLOR_TEXT,
    align: "center"
});

s7.addText("まずはカタログサイト (skills.sh) を覗いて、\n「これ、私の仕事に使えそう！」を探してみませんか？", {
    x: 1, y: 4.5, w: 8, h: 1.5,
    fontSize: 16,
    color: COLOR_TEXT,
    align: "center"
});

s7.addText("興味を持った方は、社内のサポートデスクまでお声がけください！", {
    x: 0, y: 6.5, w: 10, h: 0.5,
    fontSize: 12,
    color: "999999",
    align: "center"
});


// Save the presentation
// Use 'AI-study-room/presentation_editable.pptx' based on current CWD logic in other tools, 
// but script is running from root usually.
// PptxGenJS writes file relative to execution or strict absolute.
// writefile is async
pres.writeFile({ fileName: "AI-study-room/presentation_editable.pptx" })
    .then((fileName) => {
        console.log(`Created file: ${fileName}`);
    })
    .catch((err) => {
        console.error(err);
    });
