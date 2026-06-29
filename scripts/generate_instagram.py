#!/usr/bin/env python3
"""
Instagram投稿画像生成 v2 — Premium Redesign
フォロワー獲得特化のプレミアムカルーセル（9枚）
"""
import re
import sys
import random
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

# ─────────────────────────────────────────────────────────────────────
# キャンバス定数
# ─────────────────────────────────────────────────────────────────────
W, H = 1080, 1080
TOTAL = 7
MARGIN = 88

# カラーパレット
BG_TOP   = (3,  5, 20)
BG_BOT   = (7,  3, 30)
GOLD        = (196, 168, 106)
GOLD_LT     = (232, 212, 155)
GOLD_DIM    = (90,  72,  44)
GOLD_BRIGHT = (245, 200, 30)   # アクションチェック番号用（高コントラスト）
CREAM       = (245, 242, 235)
MUTED       = (150, 143, 128)

OUTPUT_DIR = Path("instagram_output")
OUTPUT_DIR.mkdir(exist_ok=True)
REPO_ROOT = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────
# フォント
# ─────────────────────────────────────────────────────────────────────
SERIF_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSerifCJKjp-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSerifCJKjp-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSerifCJKjp-Regular.otf",
]
SANS_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJKjp-Regular.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.otf",
]

def _find(cands):
    for p in cands:
        if Path(p).exists():
            return p
    return None

def _f(path, size):
    if path is None:
        return ImageFont.load_default()
    return ImageFont.truetype(path, size, index=0) if path.endswith(".ttc") \
        else ImageFont.truetype(path, size)

def load_fonts():
    serif = _find(SERIF_CANDIDATES)
    sans  = _find(SANS_CANDIDATES)
    p = serif or sans    # serif優先：明朝体で高級感・内省的な雰囲気
    s = sans  or serif   # 数字・英字ラベル用
    if not p:
        print("WARNING: No CJK font found, using default", file=sys.stderr)
    return {
        "disp":  _f(p, 70),   # カード名
        "hero":  _f(p, 54),   # テーマ（フック）
        "title": _f(p, 46),   # セクションタイトル
        "body":    _f(p, 39),   # 本文
        "body_sm": _f(p, 34),  # スライド2専用（挨拶文との共存用コンパクトサイズ）
        "cap":     _f(p, 25),  # キャプション、ラベル
        "xs":    _f(p, 20),   # フッター
        "en_wm": _f(s, 280),  # 透かし
        "en_lg": _f(s, 44),   # 英語カード名
        "en_md": _f(s, 27),   # 英語ラベル
        "en_xs": _f(s, 20),   # 英語フッター
    }

# ─────────────────────────────────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────────────────────────────────
KINSOKU = set('。、！？」』）】…ー・ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ')

def tw(draw, text, font):
    try:
        return int(draw.textlength(text, font=font))
    except AttributeError:
        return draw.textsize(text, font=font)[0]

def wrap(draw, text, font, max_w):
    lines = []
    while text:
        lo, hi = 1, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if tw(draw, text[:mid], font) <= max_w:
                lo = mid
            else:
                hi = mid - 1
        # 禁則処理：次行先頭が行頭禁則文字なら現行に繰り込む
        if lo < len(text) and text[lo] in KINSOKU and lo > 1:
            lo -= 1
        lines.append(text[:lo])
        text = text[lo:]
    return lines

def smart_wrap(draw, text, font, max_w):
    """\\n による明示的改行を優先し、各セグメントを wrap で折り返す"""
    lines = []
    for seg in text.split("\n"):
        lines.extend(wrap(draw, seg, font, max_w) if seg else [""])
    return lines

def explicit_lines(text):
    """自動折り返しなし：\\n のみで分割。意味改行を完全にコンテンツ側で制御する"""
    return text.split("\n")

def generate_greeting():
    """実行日の月・時期に合わせた温かみのある挨拶文を動的生成"""
    today = date.today()
    m = today.month
    d = today.day
    t = "early" if d <= 10 else ("mid" if d <= 20 else "late")
    table = {
        (1, "early"): "新年、あけましておめでとうございます。\n今年も一緒に、一歩ずつ進んでいきましょう。",
        (1, "mid"):   "お正月の余韻も落ち着いてきた頃ですね。\n今週もお疲れ様でした。",
        (1, "late"):  "1月もあとわずかですね。\n寒い日が続きますが、体調はいかがですか？",
        (2, "early"): "立春を過ぎ、春の気配が感じられますね。\n今週もお疲れ様でした。",
        (2, "mid"):   "バレンタインの時期ですね。\n自分自身へのギフトも大切にしてください。",
        (2, "late"):  "2月もそろそろ終わりですね。\nよく頑張った自分を、少し褒めてあげてください。",
        (3, "early"): "3月に入りましたね。春の息吹を感じる季節です。\n今週もお疲れ様でした。",
        (3, "mid"):   "春めいてきましたね。\n心も体も、少しずつほぐれてきた頃でしょうか。",
        (3, "late"):  "年度末の忙しい時期ですね。\n無理せず、今週も一歩ずつ進みましょう。",
        (4, "early"): "新年度が始まりましたね。\n新しい環境に慣れるまで、自分を労わってください。",
        (4, "mid"):   "春の陽気が気持ちいい季節ですね。\n今週もお疲れ様でした。",
        (4, "late"):  "ゴールデンウィークが近づいてきましたね。\nもう少し、一緒に頑張りましょう。",
        (5, "early"): "ゴールデンウィーク明け、お疲れではないですか？\n自分のペースで、ゆっくり戻っていきましょう。",
        (5, "mid"):   "五月晴れが続く季節ですね。\n今週もお疲れ様でした。",
        (5, "late"):  "5月もあとわずかですね。\n新緑の季節に、少し深呼吸してみましょう。",
        (6, "early"): "6月が始まりましたね。\n雨の季節も、心は穏やかに過ごしていきましょう。",
        (6, "mid"):   "梅雨の季節ですね。\n気圧の変化で、体が重く感じる日もあるかと思います。",
        (6, "late"):  "6月もあとわずかですね。\n今週もよく頑張りました。お疲れ様でした。",
        (7, "early"): "7月に入り、夏が近づいてきましたね。\n水分をしっかり補って、今週も一緒に進みましょう。",
        (7, "mid"):   "暑い日が続いていますね。\n体調はいかがですか？無理せず過ごしてください。",
        (7, "late"):  "夏の暑さが本格的になってきましたね。\n今週もお疲れ様でした。",
        (8, "early"): "お盆の季節ですね。\nゆっくりと自分を振り返る時間を取ってみてください。",
        (8, "mid"):   "夏の後半に入りましたね。\n少しずつ秋の気配も感じられる頃でしょうか。",
        (8, "late"):  "8月もあとわずかですね。\n夏の疲れが出やすい時期です。自分を労わってください。",
        (9, "early"): "9月に入りましたね。\n少しずつ涼しくなってきた頃でしょうか。",
        (9, "mid"):   "秋分の日が近いですね。\n季節の変わり目、体調はいかがですか？",
        (9, "late"):  "9月もあとわずかですね。\n秋の夜長に、自分と向き合う時間を作ってみましょう。",
        (10, "early"): "10月が始まりましたね。実りの秋です。\n今週もお疲れ様でした。",
        (10, "mid"):   "秋が深まってきましたね。\n少しずつ肌寒くなってきた頃でしょうか。",
        (10, "late"):  "10月もあとわずかですね。\n今週も自分を大切にしながら過ごしましょう。",
        (11, "early"): "11月に入り、秋も深まってきましたね。\n体調はいかがですか？",
        (11, "mid"):   "肌寒い日が増えてきましたね。\n温かくして、今週も一歩ずつ進みましょう。",
        (11, "late"):  "11月もあとわずかですね。\n年末に向けて、自分のペースで整えていきましょう。",
        (12, "early"): "12月に入りましたね。\n一年の締めくくりに向けて、自分を労わりながら進みましょう。",
        (12, "mid"):   "年末が近づいてきましたね。\n忙しい時期ですが、無理せず過ごしてください。",
        (12, "late"):  "いよいよ年の瀬ですね。\n今年も一年、本当にお疲れ様でした。",
    }
    return table.get((m, t), "今週もお疲れ様でした。\n新しい週の始まりに、一緒に前を向いていきましょう。")

def put_center(draw, text, font, y, color, width=W):
    x = (width - tw(draw, text, font)) // 2
    draw.text((x, y), text, font=font, fill=color)

def put_block(draw, text, font, x, y, max_w, color=None, leading=1.75, max_h=None):
    color = color or CREAM
    lines = smart_wrap(draw, text, font, max_w)
    lh = int(font.size * leading)
    for i, line in enumerate(lines):
        cy = y + i * lh
        if max_h and (cy - y + lh) > max_h:
            if i > 0:
                draw.text((x, y + (i-1)*lh), "…", font=font, fill=color)
            return int(cy)
        if line:
            draw.text((x, cy), line, font=font, fill=color)
    return int(y + len(lines) * lh)

def vcenter_y(line_count, font_size, leading=1.75,
              top_reserved=160, bottom_reserved=100):
    """テキストブロックの縦中央配置Y座標"""
    text_h = line_count * int(font_size * leading)
    avail  = H - top_reserved - bottom_reserved
    return top_reserved + max(0, (avail - text_h) // 2)

# ─────────────────────────────────────────────────────────────────────
# ベースキャンバス（グラデーション + 星）
# ─────────────────────────────────────────────────────────────────────
def make_canvas(seed=42):
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    for y in range(H):
        t = y / H
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    random.seed(seed)
    for _ in range(80):
        sx  = random.randint(8, W-8)
        sy  = random.randint(8, H-8)
        brt = random.randint(55, 160)
        sz  = random.choices([0, 1, 2], weights=[65, 25, 10])[0]
        col = (brt, int(brt * 0.88), int(brt * 0.62))
        if sz == 0:
            draw.point((sx, sy), fill=col)
        elif sz == 1:
            draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=col)
        else:
            draw.line([(sx-2, sy), (sx+2, sy)], fill=col, width=1)
            draw.line([(sx, sy-2), (sx, sy+2)], fill=col, width=1)

    return img, draw

# ─────────────────────────────────────────────────────────────────────
# 共通パーツ
# ─────────────────────────────────────────────────────────────────────
def draw_corners(draw, size=22):
    for px, py in [(MARGIN, MARGIN), (W-MARGIN, MARGIN),
                   (MARGIN, H-MARGIN), (W-MARGIN, H-MARGIN)]:
        draw.line([(px-size//2, py), (px+size//2, py)], fill=GOLD_DIM, width=1)
        draw.line([(px, py-size//2), (px, py+size//2)], fill=GOLD_DIM, width=1)

def draw_hline(draw, y, x0=None, x1=None, color=None):
    draw.line([(x0 or MARGIN, y), (x1 or W-MARGIN, y)], fill=color or GOLD_DIM, width=1)

def draw_footer(draw, fonts, n, swipe=True):
    draw.text((MARGIN, H-46), "ASUMIRA 占い", font=fonts["en_xs"], fill=MUTED)
    put_center(draw, f"{n:02d} / {TOTAL:02d}", fonts["en_xs"], H-46, MUTED)
    if swipe and n < TOTAL:
        sw = "swipe  ▷"
        draw.text((W - MARGIN - tw(draw, sw, fonts["en_xs"]), H-46),
                  sw, font=fonts["en_xs"], fill=GOLD_DIM)

def draw_section_header(draw, fonts, label, y):
    """─── タイトル ─── スタイル"""
    lw  = tw(draw, label, fonts["title"])
    cx  = (W - lw) // 2
    mid = y + fonts["title"].size // 2
    gap = 22
    draw.line([(MARGIN, mid), (cx - gap, mid)], fill=GOLD_DIM, width=1)
    draw.line([(cx + lw + gap, mid), (W-MARGIN, mid)], fill=GOLD_DIM, width=1)
    draw.text((cx, y), label, font=fonts["title"], fill=GOLD)
    return y + fonts["title"].size + 28

def draw_wm_number(img, fonts, number):
    """ローマ数字透かし（加算合成）"""
    if not number:
        return img
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    ld    = ImageDraw.Draw(layer)
    nw    = tw(ld, number, fonts["en_wm"])
    nx    = (W - nw) // 2
    ny    = (H - fonts["en_wm"].size) // 2 - 30
    ld.text((nx, ny), number, font=fonts["en_wm"], fill=(14, 8, 28))
    layer = layer.filter(ImageFilter.GaussianBlur(radius=6))
    return ImageChops.add(img, layer)

def draw_keyword_tags(draw, fonts, keywords, y, center=False):
    """キーワードタグ横並び（centerで全体を中央寄せ）"""
    pad_x, pad_y, gap = 14, 8, 10
    font = fonts["cap"]
    # 全タグの総幅を計算して中央に配置するか左寄せにするか
    total_w = sum(tw(draw, kw, font) + pad_x*2 for kw in keywords) + gap*(len(keywords)-1)
    x = (W - total_w) // 2 if center else MARGIN
    row_h = 0
    for kw in keywords:
        kw_w  = tw(draw, kw, font)
        box_w = kw_w + pad_x * 2
        box_h = font.size + pad_y * 2
        row_h = box_h
        if x + box_w > W - MARGIN:
            x  = (W - total_w) // 2 if center else MARGIN
            y += box_h + 8
        draw.rectangle([x, y, x+box_w, y+box_h], outline=GOLD_DIM, width=1)
        draw.text((x+pad_x, y+pad_y), kw, font=font, fill=GOLD)
        x += box_w + gap
    return y + row_h + 6

def draw_deco_star(draw, y=None, x=None, color=None, size=14):
    """中央に装飾的な ✦ を描画"""
    color = color or GOLD_DIM
    x     = x or W//2
    y     = y or H//2
    # 十字
    draw.line([(x-size, y), (x+size, y)], fill=color, width=1)
    draw.line([(x, y-size), (x, y+size)], fill=color, width=1)
    # 斜め
    s = size // 2
    draw.line([(x-s, y-s), (x+s, y+s)], fill=color, width=1)
    draw.line([(x+s, y-s), (x-s, y+s)], fill=color, width=1)

# ─────────────────────────────────────────────────────────────────────
# スライド 1 ── カバー / HOOK
# ─────────────────────────────────────────────────────────────────────
def slide_cover(data, fonts, card_img):
    img, draw = make_canvas(seed=1)
    draw_corners(draw)

    # タロットカード（上部 40%）
    card_h = 390
    cy     = 68
    if card_img:
        cw     = int(card_h * card_img.width / card_img.height)
        card_r = card_img.resize((cw, card_h), Image.LANCZOS)
        cx     = (W - cw) // 2
        pad    = 6
        draw.rectangle([cx-pad-1, cy-pad-1, cx+cw+pad+1, cy+card_h+pad+1],
                       outline=GOLD, width=1)
        img.paste(card_r, (cx, cy))

    # ─ テキストブロック（残りの 56% を使う）─
    y = 496
    draw_hline(draw, y, x0=160, x1=W-160)
    y += 20

    lbl = "W E E K L Y   T A R O T"
    put_center(draw, lbl, fonts["en_xs"], y, GOLD)
    y += 34

    draw_hline(draw, y, x0=160, x1=W-160)
    y += 26

    # テーマ（最重要コピー） ─ explicit_linesで自動折り返し無効
    body_w = W - 2*MARGIN - 20
    for line in explicit_lines(data["theme"]):
        if line:
            put_center(draw, line, fonts["hero"], y, CREAM)
        y += int(fonts["hero"].size * 1.22)
    y += 10

    # カード名
    card_line = f"{data['card']['number']}  ◇  {data['card']['nameJp']}"
    put_center(draw, card_line, fonts["cap"], y, GOLD)
    y += 36

    # 英語名
    put_center(draw, data["card"]["nameEn"], fonts["en_md"], y, MUTED)
    y += 38

    # 期間
    put_center(draw, data["period"], fonts["xs"], y, MUTED)
    y += 48

    # キーワードタグ（空白を埋める）
    if data["keywords"]:
        draw_keyword_tags(draw, fonts, data["keywords"], y, center=True)

    draw_footer(draw, fonts, 1)
    return img

# ─────────────────────────────────────────────────────────────────────
# スライド 2 ── カード詳細
# ─────────────────────────────────────────────────────────────────────
def slide_card_detail(data, fonts):
    img, draw = make_canvas(seed=2)
    img  = draw_wm_number(img, fonts, data["card"]["number"])
    draw = ImageDraw.Draw(img)
    draw_corners(draw)

    y = 90
    put_center(draw, "C A R D   O F   T H E   W E E K", fonts["en_xs"], y, GOLD_DIM)
    y += 34
    draw_hline(draw, y)
    y += 36

    # カード名（大）
    put_center(draw, data["card"]["nameJp"], fonts["disp"], y, GOLD)
    y += fonts["disp"].size + 14

    put_center(draw, data["card"]["nameEn"], fonts["en_lg"], y, MUTED)
    y += fonts["en_lg"].size + 36

    draw_hline(draw, y, x0=180, x1=W-180)
    y += 36

    # テーマ引用スタイル（シンプルな上下ラインで囲む）
    theme_lines = wrap(draw, data["theme"], fonts["hero"], W-2*MARGIN-60)
    draw_hline(draw, y - 4, x0=200, x1=W-200)
    y += 10
    for line in theme_lines:
        put_center(draw, line, fonts["hero"], y, CREAM)
        y += int(fonts["hero"].size * 1.25)
    y += 10
    draw_hline(draw, y, x0=200, x1=W-200)
    y += 42

    # キーワードタグ（中央寄せ）
    draw_keyword_tags(draw, fonts, data["keywords"], y, center=True)

    draw_footer(draw, fonts, 2)
    return img

# ─────────────────────────────────────────────────────────────────────
# スライド 3 ── 今週の行動指針（メッセージ統合・コーチング型）
# ─────────────────────────────────────────────────────────────────────
def slide_msg_combined(data, fonts):
    img, draw = make_canvas(seed=3)
    draw_corners(draw)

    body_w = W - 2*MARGIN - 20

    # ── ヘッダー ──
    y = 90
    put_center(draw, "今週のメッセージ", fonts["cap"], y, GOLD)
    y += 36
    draw_hline(draw, y)
    y += 34

    # ── 挨拶文（動的生成・季節・時期に応じた労いの言葉）──
    greeting = generate_greeting()
    lh_greet = int(fonts["cap"].size * 1.65)
    for line in explicit_lines(greeting):
        if line:
            draw.text((MARGIN+10, y), line, font=fonts["cap"], fill=MUTED)
        y += lh_greet
    y += 6
    draw_hline(draw, y, x0=MARGIN+10, x1=W-MARGIN-10)
    y += 16

    # ── message[0]: コーチング本文（body_sm 34px, cream）── explicit_linesで自動折り返し無効
    msg0 = data["message"][0] if data["message"] else ""
    lines0 = explicit_lines(msg0)
    lh0 = int(fonts["body_sm"].size * 1.68)
    for line in lines0:
        if line:
            draw.text((MARGIN+10, y), line, font=fonts["body_sm"], fill=CREAM)
        y += lh0

    # ── 仕切り線 ──
    y += 14
    draw_hline(draw, y, x0=W//4, x1=W*3//4)
    y += 16

    # ── message[1]: アクションアイテム（cap, gold, インデント付き）──
    msg1 = data["message"][1] if len(data["message"]) > 1 else ""
    indent_x = MARGIN + 30
    item_w   = W - indent_x - MARGIN
    if "◇" in msg1:
        parts = [p.strip() for p in msg1.split("◇") if p.strip()]
        lh1 = int(fonts["cap"].size * 1.85)
        for part in parts:
            if part:
                draw.text((indent_x, y), "◇  " + part, font=fonts["cap"], fill=GOLD_DIM)
            y += lh1 + 3
    else:
        put_block(draw, msg1, fonts["cap"], indent_x, y, item_w, color=GOLD_DIM, leading=1.85)

    draw_footer(draw, fonts, 2)
    return img

# ─────────────────────────────────────────────────────────────────────
# スライド 3–5 ── 総合運 / 仕事運 / 恋愛運（縦中央寄せ）
# ─────────────────────────────────────────────────────────────────────
FOCUS_CONFIG = [
    ("overall", "総合運", 3),
    ("work",    "仕事運", 4),
    ("love",    "恋愛運", 5),
]

def slide_focus(data, fonts, idx):
    key, label, slide_n = FOCUS_CONFIG[idx]
    text = data["focus"].get(key, "")

    img, draw = make_canvas(seed=4 + idx)
    draw_corners(draw)

    # ── ヘッダー ──
    y_hdr = 90
    y_hdr = draw_section_header(draw, fonts, label, y_hdr)
    draw_hline(draw, y_hdr)

    # ── テキストを縦中央に配置 ── explicit_linesで自動折り返し無効
    body_w = W - 2*MARGIN - 20
    lines  = explicit_lines(text)
    lh     = int(fonts["body"].size * 1.85)
    text_h = len(lines) * lh

    top_reserved = y_hdr + 44
    bot_reserved = 100
    avail = H - top_reserved - bot_reserved
    y_txt = top_reserved + max(30, (avail - text_h) // 2)

    for i, line in enumerate(lines):
        if line:
            draw.text((MARGIN+10, y_txt + i*lh), line, font=fonts["body"], fill=CREAM)

    draw_footer(draw, fonts, slide_n)
    return img

# ─────────────────────────────────────────────────────────────────────
# スライド 7 ── 今週のアクションチェック
# ─────────────────────────────────────────────────────────────────────
def slide_lucky(data, fonts):
    img, draw = make_canvas(seed=6)
    draw_corners(draw)

    # ── ヘッダー ──
    y_hdr = 90
    put_center(draw, "今週のアクションチェック", fonts["title"], y_hdr, GOLD)
    y_hdr += fonts["title"].size + 22
    draw_hline(draw, y_hdr)

    items = [
        ("01", "ラッキーカラー",   data["lucky"]["color"]),
        ("02", "今週の習慣",       data["lucky"]["action"]),
        ("03", "今週のキーワード", data["lucky"]["keyword"]),
    ]

    # 各アイテムの高さを計算（縦均等配置のため）
    lx      = MARGIN + 86
    body_w  = W - lx - MARGIN
    lh_body = int(fonts["body"].size * 1.6)
    lh_cap  = fonts["cap"].size

    def item_height(val):
        n = len([l for l in explicit_lines(val) if l])  # 空行は高さなし
        n = max(n, 1)
        return lh_cap + 16 + n * lh_body  # label + gap + val

    total_h   = sum(item_height(v) for _, _, v in items)
    avail     = H - (y_hdr + 30) - 100  # top → footer
    spacing   = (avail - total_h) // (len(items) + 1)
    spacing   = max(spacing, 30)

    y = y_hdr + 30 + spacing
    for num, lbl, val in items:
        # 番号（左側・明るいゴールド・1pxオフセットで太字感を演出）
        for ox, oy in ((0,0),(1,0),(0,1)):
            draw.text((MARGIN+ox, y-4+oy), num, font=fonts["en_lg"], fill=GOLD_BRIGHT)
        # ラベル
        draw.text((lx, y), lbl, font=fonts["cap"], fill=GOLD)
        # 罫線
        line_y = y + lh_cap + 6
        draw_hline(draw, line_y, x0=lx, color=(45, 35, 20))
        # 値（explicit_linesで自動折り返し無効）
        val_y = line_y + 10
        vi = 0
        for line in explicit_lines(val):
            if line:
                draw.text((lx, val_y + vi*lh_body), line, font=fonts["body"], fill=CREAM)
                vi += 1
        y += item_height(val) + spacing

    draw_footer(draw, fonts, 6)
    return img

# ─────────────────────────────────────────────────────────────────────
# スライド 7 ── CTA（来週予告 + フォロー誘導）
# ─────────────────────────────────────────────────────────────────────
def slide_cta(data, fonts):
    img, draw = make_canvas(seed=7)
    draw_corners(draw)

    body_w = W - 2*MARGIN - 20

    # ── 上部: 来週の予告（保存する明確な理由）──
    y = 90
    put_center(draw, "来週のテーマ予告", fonts["cap"], y, GOLD)
    y += 34
    draw_hline(draw, y)
    y += 30
    y = put_block(draw, data["nextHint"], fonts["body"],
                  MARGIN+10, y, body_w, max_h=220)

    # ── コメント誘導CTA（週次のエンゲージメント問いかけ）──
    if data.get("commentCTA"):
        y += 28
        lh_cta = int(fonts["cap"].size * 1.75)
        for line in explicit_lines(data["commentCTA"]):
            if line:
                put_center(draw, line, fonts["cap"], y, GOLD_LT)
            y += lh_cta

    # ── 中央セパレーター ──
    sep_y = max(y + 36, 440)
    draw_hline(draw, sep_y)

    # ── 下部: CTA ブロック（残りスペースに縦中央寄せ）──
    cta_font_h = int(fonts["body"].size * 1.6)
    cap_font_h = int(fonts["cap"].size * 1.5)
    acc_font_h = fonts["disp"].size + 16
    total_cta  = cta_font_h * 2 + cap_font_h + 62 + acc_font_h

    avail_below  = H - 100 - (sep_y + 20)
    cta_start    = sep_y + 20 + max(0, (avail_below - total_cta) // 2)

    y = int(cta_start)
    put_center(draw, "今週の投稿を保存して", fonts["body"], y, CREAM)
    y += cta_font_h
    put_center(draw, "月曜日に見返してください", fonts["body"], y, CREAM)
    y += cta_font_h + 10

    put_center(draw, "▷  フォローで毎週月曜にお届け", fonts["cap"], y, MUTED)
    y += 62

    draw_hline(draw, y, x0=200, x1=W-200)
    y += 24

    # アカウント名（最大フォント・金色）
    put_center(draw, "@asumira_uranai", fonts["disp"], y, GOLD_LT)

    draw_footer(draw, fonts, TOTAL, swipe=False)
    return img

# ─────────────────────────────────────────────────────────────────────
# コンテンツ解析
# ─────────────────────────────────────────────────────────────────────
def parse_weekly(monday_key=None):
    if monday_key is None:
        today  = date.today()
        monday = today - timedelta(days=today.weekday())
        monday_key = monday.strftime("%Y-%m-%d")

    html_path = REPO_ROOT / "占い" / "weekly" / "index.html"
    content   = html_path.read_text(encoding="utf-8")

    start = content.find(f'"{monday_key}"')
    if start == -1:
        print(f"Content not found for {monday_key}", file=sys.stderr)
        sys.exit(1)

    brace_start = content.index("{", start)
    depth, end  = 0, brace_start
    for i in range(brace_start, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    block = content[start:end]

    def extr(pat, src=block):
        m = re.search(pat, src, re.DOTALL)
        return m.group(1).strip() if m else ""

    def e(pat, src):
        m = re.search(pat, src)
        return m.group(1) if m else ""

    card_blk  = extr(r"card\s*:\s*\{([^}]+)\}")
    focus_m   = re.search(r"focus\s*:\s*\{(.*?)\}(?=\s*,\s*lucky)", block, re.DOTALL)
    focus_blk = focus_m.group(1) if focus_m else ""
    lucky_m   = re.search(r"lucky\s*:\s*\{([^}]+)\}", block)
    lucky_blk = lucky_m.group(1) if lucky_m else ""
    kw_m      = re.search(r"keywords\s*:\s*\[([^\]]+)\]", block)
    kws       = re.findall(r'"([^"]+)"', kw_m.group(1)) if kw_m else []
    msg_m     = re.search(r"message\s*:\s*\[(.*?)\]", block, re.DOTALL)
    msgs      = re.findall(r'"([^"]+)"', msg_m.group(0)) if msg_m else []

    def nl(s):
        return s.replace("\\n", "\n")

    return {
        "key":  monday_key,
        "card": {
            "number": e(r'number\s*:\s*"([^"]+)"', card_blk),
            "nameJp": e(r'nameJp\s*:\s*"([^"]+)"', card_blk),
            "nameEn": e(r'nameEn\s*:\s*"([^"]+)"', card_blk),
            "image":  e(r'image\s*:\s*"([^"]+)"',  card_blk),
        },
        "period":   e(r'period\s*:\s*"([^"]+)"',  block),
        "theme":    nl(e(r'theme\s*:\s*"([^"]+)"',    block)),
        "keywords": kws,
        "message":  [nl(m) for m in msgs],
        "focus": {
            "overall": nl(e(r'overall\s*:\s*"([^"]+)"', focus_blk)),
            "work":    nl(e(r'work\s*:\s*"([^"]+)"',    focus_blk)),
            "love":    nl(e(r'love\s*:\s*"([^"]+)"',    focus_blk)),
        },
        "lucky": {
            "color":   e(r'color\s*:\s*"([^"]+)"',   lucky_blk),
            "action":  nl(e(r'action\s*:\s*"([^"]+)"',  lucky_blk)),
            "keyword": e(r'keyword\s*:\s*"([^"]+)"', lucky_blk),
        },
        "nextHint":   nl(e(r'nextHint\s*:\s*"([^"]+)"',   block)),
        "commentCTA": nl(e(r'commentCTA\s*:\s*"([^"]+)"', block)),
    }

def load_card_image(image_path_str):
    filename = Path(image_path_str).name
    path = REPO_ROOT / "占い" / "タロット" / "images" / filename
    if path.exists():
        return Image.open(path).convert("RGB")
    print(f"WARNING: Card image not found: {path}", file=sys.stderr)
    return None

# ─────────────────────────────────────────────────────────────────────
# キャプション
# ─────────────────────────────────────────────────────────────────────
def _first_sentence(text, max_len=40):
    """フォーカステキストの最初の一文を取得。句点で自然に区切る"""
    segs = [s.strip() for s in text.split("\n") if s.strip()]
    if not segs:
        return ""
    first = segs[0]
    # 句点（。）で終わっていれば最初のセグメントをそのまま使用
    if "。" in first:
        return first[:first.index("。")+1]
    # 読点（、）で終わっている場合は次のセグメントと結合して文を完成
    if first and first[-1] in "、，" and len(segs) > 1:
        combined = first + segs[1]
        end = combined.find("。")
        if end != -1:
            return combined[:end+1]
        return combined[:max_len] + ("…" if len(combined) > max_len else "")
    return first[:max_len] + ("…" if len(first) > max_len else "")

def build_caption(data):
    card_jp   = data["card"]["nameJp"]
    card_en   = data["card"]["nameEn"]
    greeting  = generate_greeting()                 # 季節・時期の挨拶（動的）
    hook_line = greeting.split("\n")[0]             # 1行目のみフック用に使用
    over_pt   = _first_sentence(data["focus"]["overall"])
    work_pt   = _first_sentence(data["focus"]["work"])
    love_pt   = _first_sentence(data["focus"]["love"])
    keyword   = data["lucky"]["keyword"]
    comment   = data.get("commentCTA", "").replace("\n", "\n")

    # キーワードからダイナミックハッシュタグを生成
    kw_tags = " ".join(f"#{kw.replace(' ','')}" for kw in data.get("keywords", []))

    # ベースハッシュタグ（固定）
    base_tags = (
        "#タロット占い #週間運勢 #自己分析 #マインドフルネス "
        "#習慣化 #メンタルケア #タロットリーディング #asumira占い "
        f"#内省 #コーチング #自己肯定感 #{card_jp}のカード"
    )

    return (
        f"{hook_line}\n"
        f"今週のタロットは、そのぜんぶを手放すためのカードでした。\n\n"
        f"─────────────────\n\n"
        f"今週引いたのは「{card_jp}（{card_en}）」。\n\n"
        f"▷ 今週のポイント\n\n"
        f"✦ 総合運\n{over_pt}\n\n"
        f"✦ 仕事運\n{work_pt}\n\n"
        f"✦ 恋愛運\n{love_pt}\n\n"
        f"─────────────────\n\n"
        f"月曜の朝、または疲れた夜に見返すために\n"
        f"この投稿を🔖保存しておいてください。\n\n"
        f"─────────────────\n\n"
        f"{comment}\n\n"
        f"─────────────────\n\n"
        f"より詳しい鑑定はプロフィールリンクから。\n"
        f"毎週月曜更新中 → フォローしておくと便利です。\n\n"
        f"@asumira_uranai\n\n"
        f"{base_tags} {kw_tags}\n"
    )

# ─────────────────────────────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────────────────────────────
def main():
    monday_key = sys.argv[1] if len(sys.argv) > 1 else None

    print("[1/4] Parsing content...")
    data = parse_weekly(monday_key)
    print(f"  {data['key']} | {data['card']['nameEn']} - {data['theme']}")

    print("[2/4] Loading fonts...")
    fonts = load_fonts()

    print("[3/4] Loading card image...")
    card_img = load_card_image(data["card"]["image"])

    print("[4/4] Generating 7 slides...")
    slides = [
        slide_cover(data, fonts, card_img),
        slide_msg_combined(data, fonts),
        slide_focus(data, fonts, 0),
        slide_focus(data, fonts, 1),
        slide_focus(data, fonts, 2),
        slide_lucky(data, fonts),
        slide_cta(data, fonts),
    ]

    for i, slide in enumerate(slides, 1):
        p = OUTPUT_DIR / f"slide_{i:02d}.png"
        slide.save(p, "PNG", optimize=True)
        print(f"  OK slide_{i:02d}.png")

    caption_path = OUTPUT_DIR / "caption.txt"
    caption_path.write_text(build_caption(data), encoding="utf-8")
    print("  OK caption.txt")
    print("Done.")


if __name__ == "__main__":
    main()
