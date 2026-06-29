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
TOTAL = 9
MARGIN = 72

# カラーパレット
BG_TOP   = (3,  5, 20)
BG_BOT   = (7,  3, 30)
GOLD     = (196, 168, 106)
GOLD_LT  = (232, 212, 155)
GOLD_DIM = (90,  72,  44)
CREAM    = (245, 242, 235)
MUTED    = (150, 143, 128)

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
    p = serif or sans
    s = sans  or serif
    if not p:
        print("WARNING: No CJK font found, using default", file=sys.stderr)
    return {
        "disp":  _f(p, 80),   # カード名
        "hero":  _f(p, 62),   # テーマ（フック）
        "title": _f(p, 52),   # セクションタイトル
        "body":  _f(p, 44),   # 本文
        "cap":   _f(p, 28),   # キャプション、ラベル
        "xs":    _f(p, 22),   # フッター
        "en_wm": _f(s, 280),  # 透かし
        "en_lg": _f(s, 50),   # 英語カード名
        "en_md": _f(s, 30),   # 英語ラベル
        "en_xs": _f(s, 22),   # 英語フッター
    }

# ─────────────────────────────────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────────────────────────────────
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
        lines.append(text[:lo])
        text = text[lo:]
    return lines

def put_center(draw, text, font, y, color, width=W):
    x = (width - tw(draw, text, font)) // 2
    draw.text((x, y), text, font=font, fill=color)

def put_block(draw, text, font, x, y, max_w, color=None, leading=1.75, max_h=None):
    color = color or CREAM
    lines = wrap(draw, text, font, max_w)
    lh = int(font.size * leading)
    for i, line in enumerate(lines):
        cy = y + i * lh
        if max_h and (cy - y + lh) > max_h:
            draw.text((x, cy - lh), "…", font=font, fill=color)
            return int(cy)
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
    ld.text((nx, ny), number, font=fonts["en_wm"], fill=(30, 18, 60))
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

    # テーマ（最重要コピー）
    body_w = W - 2*MARGIN - 20
    for line in wrap(draw, data["theme"], fonts["hero"], body_w):
        put_center(draw, line, fonts["hero"], y, CREAM)
        y += int(fonts["hero"].size * 1.2)
    y += 10

    # カード名
    card_line = f"{data['card']['number']}  ✦  {data['card']['nameJp']}"
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
    y += 30

    # テーマ引用スタイル
    put_center(draw, "「", fonts["title"], y, GOLD_DIM)
    y += 6
    for line in wrap(draw, data["theme"], fonts["title"], W-2*MARGIN-60):
        put_center(draw, line, fonts["title"], y, CREAM)
        y += int(fonts["title"].size * 1.3)
    y += 2
    put_center(draw, "」", fonts["title"], y - 8, GOLD_DIM)
    y += 42

    draw_hline(draw, y, x0=180, x1=W-180)
    y += 36

    # キーワードタグ（中央寄せ）
    draw_keyword_tags(draw, fonts, data["keywords"], y, center=True)

    draw_footer(draw, fonts, 2)
    return img

# ─────────────────────────────────────────────────────────────────────
# スライド 3 & 4 ── メッセージ（縦中央寄せ）
# ─────────────────────────────────────────────────────────────────────
def slide_message(data, fonts, slide_idx):
    n   = slide_idx + 3       # slide 3 or 4
    msg = data["message"][slide_idx] if slide_idx < len(data["message"]) \
          else data["message"][0]

    img, draw = make_canvas(seed=n)
    draw_corners(draw)

    # ── ヘッダー ──
    y_hdr = 90
    put_center(draw, "今週のメッセージ", fonts["cap"], y_hdr, GOLD)
    y_hdr += 36
    draw_hline(draw, y_hdr)

    # ── テキストを縦中央に配置 ──
    body_w = W - 2*MARGIN - 20
    lines  = wrap(draw, msg, fonts["body"], body_w)
    lh     = int(fonts["body"].size * 1.75)
    text_h = len(lines) * lh

    top_reserved = y_hdr + 40
    bot_reserved = 100
    avail = H - top_reserved - bot_reserved
    y_txt = top_reserved + max(30, (avail - text_h) // 2)

    for i, line in enumerate(lines):
        draw.text((MARGIN+10, y_txt + i*lh), line, font=fonts["body"], fill=CREAM)

    # スライド4のみ: 下部にキーワード装飾
    if slide_idx == 1 and data["keywords"]:
        kw_y = H - 160
        draw_hline(draw, kw_y - 18)
        draw_keyword_tags(draw, fonts, data["keywords"], kw_y, center=True)

    draw_footer(draw, fonts, n)
    return img

# ─────────────────────────────────────────────────────────────────────
# スライド 5–7 ── 総合運 / 仕事運 / 恋愛運（縦中央寄せ）
# ─────────────────────────────────────────────────────────────────────
FOCUS_CONFIG = [
    ("overall", "総合運", 5),
    ("work",    "仕事運", 6),
    ("love",    "恋愛運", 7),
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

    # ── テキストを縦中央に配置 ──
    body_w = W - 2*MARGIN - 20
    lines  = wrap(draw, text, fonts["body"], body_w)
    lh     = int(fonts["body"].size * 1.75)
    text_h = len(lines) * lh

    top_reserved = y_hdr + 40
    bot_reserved = 100
    avail = H - top_reserved - bot_reserved
    y_txt = top_reserved + max(30, (avail - text_h) // 2)

    for i, line in enumerate(lines):
        draw.text((MARGIN+10, y_txt + i*lh), line, font=fonts["body"], fill=CREAM)

    draw_footer(draw, fonts, slide_n)
    return img

# ─────────────────────────────────────────────────────────────────────
# スライド 8 ── ラッキー（ナンバリングスタイル）
# ─────────────────────────────────────────────────────────────────────
def slide_lucky(data, fonts):
    img, draw = make_canvas(seed=8)
    draw_corners(draw)

    # ── ヘッダー ──
    y_hdr = 90
    put_center(draw, "今週のラッキー", fonts["title"], y_hdr, GOLD)
    y_hdr += fonts["title"].size + 22
    draw_hline(draw, y_hdr)

    items = [
        ("01", "ラッキーカラー", data["lucky"]["color"]),
        ("02", "行動のヒント",   data["lucky"]["action"]),
        ("03", "キーワード",     data["lucky"]["keyword"]),
    ]

    # 各アイテムの高さを計算（縦均等配置のため）
    lx      = MARGIN + 86
    body_w  = W - lx - MARGIN
    lh_body = int(fonts["body"].size * 1.6)
    lh_cap  = fonts["cap"].size

    def item_height(val):
        n = len(wrap(draw, val, fonts["body"], body_w))
        return lh_cap + 16 + n * lh_body  # label + gap + val

    total_h   = sum(item_height(v) for _, _, v in items)
    avail     = H - (y_hdr + 30) - 100  # top → footer
    spacing   = (avail - total_h) // (len(items) + 1)
    spacing   = max(spacing, 30)

    y = y_hdr + 30 + spacing
    for num, lbl, val in items:
        # 番号（左側、薄いゴールド）
        draw.text((MARGIN, y - 4), num, font=fonts["en_lg"], fill=GOLD_DIM)
        # ラベル
        draw.text((lx, y), lbl, font=fonts["cap"], fill=GOLD)
        # 罫線
        line_y = y + lh_cap + 6
        draw_hline(draw, line_y, x0=lx, color=(45, 35, 20))
        # 値
        val_y = line_y + 10
        lines = wrap(draw, val, fonts["body"], body_w)
        for i, line in enumerate(lines):
            draw.text((lx, val_y + i*lh_body), line, font=fonts["body"], fill=CREAM)
        y += item_height(val) + spacing

    draw_footer(draw, fonts, 8)
    return img

# ─────────────────────────────────────────────────────────────────────
# スライド 9 ── CTA
# ─────────────────────────────────────────────────────────────────────
def slide_cta(data, fonts):
    img, draw = make_canvas(seed=9)
    draw_corners(draw)

    body_w = W - 2*MARGIN - 20

    # ── 上部: 来週のヒント ──
    y = 90
    put_center(draw, "来週のヒント", fonts["cap"], y, GOLD)
    y += 34
    draw_hline(draw, y)
    y += 30
    y = put_block(draw, data["nextHint"], fonts["body"],
                  MARGIN+10, y, body_w, max_h=220)

    # ── 中央セパレーター（動的位置: 上部コンテンツの下 or 最低 y=380）──
    sep_y = max(y + 44, 380)
    draw_hline(draw, sep_y)

    # ── 下部: CTA ブロック（残りスペースに縦中央寄せ）──
    # CTA コンテンツの総高さを先に見積もる
    cta_font_h = int(fonts["body"].size * 1.6)
    cap_font_h = int(fonts["cap"].size * 1.5)
    acc_font_h = fonts["disp"].size + 16
    total_cta  = cta_font_h * 2 + cap_font_h + 62 + acc_font_h

    avail_below  = H - 100 - (sep_y + 20)  # footer + sep
    cta_start    = sep_y + 20 + max(0, (avail_below - total_cta) // 2)

    y = int(cta_start)
    put_center(draw, "今週の投稿を保存して", fonts["body"], y, CREAM)
    y += cta_font_h
    put_center(draw, "毎週の流れを確認してください", fonts["body"], y, CREAM)
    y += cta_font_h + 10

    put_center(draw, "▸  フォローで毎週月曜にお届け", fonts["cap"], y, MUTED)
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

    return {
        "key":  monday_key,
        "card": {
            "number": e(r'number\s*:\s*"([^"]+)"', card_blk),
            "nameJp": e(r'nameJp\s*:\s*"([^"]+)"', card_blk),
            "nameEn": e(r'nameEn\s*:\s*"([^"]+)"', card_blk),
            "image":  e(r'image\s*:\s*"([^"]+)"',  card_blk),
        },
        "period":   e(r'period\s*:\s*"([^"]+)"',  block),
        "theme":    e(r'theme\s*:\s*"([^"]+)"',    block),
        "keywords": kws,
        "message":  msgs,
        "focus": {
            "overall": e(r'overall\s*:\s*"([^"]+)"', focus_blk),
            "work":    e(r'work\s*:\s*"([^"]+)"',    focus_blk),
            "love":    e(r'love\s*:\s*"([^"]+)"',    focus_blk),
        },
        "lucky": {
            "color":   e(r'color\s*:\s*"([^"]+)"',   lucky_blk),
            "action":  e(r'action\s*:\s*"([^"]+)"',  lucky_blk),
            "keyword": e(r'keyword\s*:\s*"([^"]+)"', lucky_blk),
        },
        "nextHint": e(r'nextHint\s*:\s*"([^"]+)"', block),
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
def build_caption(data):
    card  = data["card"]["nameJp"]
    theme = data["theme"]
    msg1  = (data["message"][0][:60] + "…") if data["message"] else ""
    over  = data["focus"]["overall"][:55] + "…"
    work  = data["focus"]["work"][:55] + "…"
    love  = data["focus"]["love"][:55] + "…"

    return (
        f"✦ 今週のタロット｜{card}「{theme}」\n\n"
        f"{msg1}\n\n"
        f"─────────────────\n"
        f"総合運　{over}\n"
        f"仕事運　{work}\n"
        f"恋愛運　{love}\n"
        f"─────────────────\n\n"
        f"ラッキーカラー：{data['lucky']['color']}\n"
        f"キーワード：{data['lucky']['keyword']}\n\n"
        f"─────────────────\n"
        f"投稿を保存して毎週見返してください\n"
        f"詳しい鑑定はプロフィールリンクから\n\n"
        f"#タロット #タロット占い #週間運勢 #今週の運勢 "
        f"#タロットリーディング #占い #運勢 #引き寄せ "
        f"#スピリチュアル #占い師 #タロットカード #週間タロット "
        f"#朝活 #自己啓発 #{card} #asumira #asumira占い\n"
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

    print("[4/4] Generating 9 slides...")
    slides = [
        slide_cover(data, fonts, card_img),
        slide_card_detail(data, fonts),
        slide_message(data, fonts, 0),
        slide_message(data, fonts, 1),
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
