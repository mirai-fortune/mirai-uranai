#!/usr/bin/env python3
"""
Instagram投稿画像生成 & Google Driveアップロード
Weekly Tarot content → カルーセル8枚 + caption.txt → Drive → LINE通知
"""
import json
import re
import os
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── 定数 ─────────────────────────────────────────────────────────────
W, H = 1080, 1080

BG       = (3, 6, 17)
GOLD     = (196, 168, 106)
GOLD_DIM = (80, 65, 40)
CREAM    = (245, 242, 235)
MUTED    = (155, 150, 138)
PANEL    = (12, 10, 8)

MARGIN   = 80
CONTENT_X = MARGIN + 28
CONTENT_W = W - CONTENT_X - MARGIN

OUTPUT_DIR = Path("instagram_output")
OUTPUT_DIR.mkdir(exist_ok=True)

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── フォントパス ──────────────────────────────────────────────────────
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

def _find(candidates):
    for p in candidates:
        if Path(p).exists():
            return p
    return None

def _font(path, size):
    if path is None:
        return ImageFont.load_default()
    if path.endswith(".ttc"):
        return ImageFont.truetype(path, size, index=0)
    return ImageFont.truetype(path, size)

def load_fonts():
    serif = _find(SERIF_CANDIDATES)
    sans  = _find(SANS_CANDIDATES)
    prim  = serif or sans
    sec   = sans or serif
    if not prim:
        print("⚠ フォントなし：デフォルト使用", file=sys.stderr)
    return {
        "xl":    _font(prim,  68),
        "lg":    _font(prim,  48),
        "md":    _font(prim,  34),
        "body":  _font(prim,  27),
        "sm":    _font(prim,  21),
        "xs":    _font(prim,  16),
        "en_lg": _font(sec,   52),
        "en_md": _font(sec,   34),
        "en_sm": _font(sec,   19),
    }

# ── ユーティリティ ────────────────────────────────────────────────────
def text_w(draw, text, font):
    try:
        return draw.textlength(text, font=font)
    except AttributeError:
        return draw.textsize(text, font=font)[0]

def wrap_text(draw, text, font, max_width):
    lines = []
    while text:
        lo, hi = 1, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if text_w(draw, text[:mid], font) <= max_width:
                lo = mid
            else:
                hi = mid - 1
        lines.append(text[:lo])
        text = text[lo:]
    return lines

def draw_block(draw, text, font, x, y, max_w, color=CREAM, leading=1.72, max_h=None):
    lines = wrap_text(draw, text, font, max_w)
    try:
        lh = font.size * leading
    except Exception:
        lh = 32
    for i, line in enumerate(lines):
        cy = y + i * lh
        if max_h and (cy - y + lh) > max_h:
            draw.text((x, cy - lh), "…", font=font, fill=color)
            return cy
        draw.text((x, cy), line, font=font, fill=color)
    return y + len(lines) * lh

def center_x(draw, text, font, width=W):
    return (width - text_w(draw, text, font)) // 2

# ── 共通パーツ ────────────────────────────────────────────────────────
def base_canvas():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    # 微妙なトップグロー
    for i in range(180):
        a = int(9 * (1 - i / 180))
        draw.line([(0, i), (W, i)], fill=(40, 30, 90, a) if a else BG)
    return img, draw

def corners(draw, size=18):
    pts = [(MARGIN, MARGIN), (W - MARGIN, MARGIN),
           (MARGIN, H - MARGIN), (W - MARGIN, H - MARGIN)]
    for px, py in pts:
        draw.line([(px - size//2, py), (px + size//2, py)], fill=GOLD_DIM, width=1)
        draw.line([(px, py - size//2), (px, py + size//2)], fill=GOLD_DIM, width=1)

def hline(draw, y, x0=MARGIN, x1=W - MARGIN):
    draw.line([(x0, y), (x1, y)], fill=GOLD_DIM, width=1)

def logo(draw, fonts):
    txt = "ASUMIRA 占い"
    draw.text((center_x(draw, txt, fonts["xs"]), H - 42), txt, font=fonts["xs"], fill=MUTED)

def slide_num(draw, fonts, n, total=8):
    txt = f"{n:02d} / {total:02d}"
    draw.text((center_x(draw, txt, fonts["en_sm"]), H - 68), txt, font=fonts["en_sm"], fill=GOLD_DIM)

def swipe_arrow(draw, fonts):
    draw.text((W - MARGIN - 54, H - 100), "swipe →", font=fonts["en_sm"], fill=GOLD_DIM)

def left_accent(draw):
    draw.rectangle([MARGIN, 80, MARGIN + 3, H - 80], fill=GOLD_DIM)

def section_label(draw, fonts, text, x=CONTENT_X, y=108):
    draw.text((x, y), text, font=fonts["sm"], fill=GOLD)
    return y + 38

# ── スライド1：Hook ───────────────────────────────────────────────────
def slide_cover(data, fonts, card_img):
    img, draw = base_canvas()
    corners(draw)

    # カード画像（上部）
    card_y = 68
    if card_img:
        ch = 370
        cw = int(ch * card_img.width / card_img.height)
        card_r = card_img.resize((cw, ch), Image.LANCZOS)
        cx = (W - cw) // 2
        pad = 5
        draw.rectangle([cx - pad, card_y - pad, cx + cw + pad, card_y + ch + pad],
                       outline=GOLD_DIM, width=1)
        img.paste(card_r, (cx, card_y))

    y = 470

    # "WEEKLY TAROT" ラベル
    lbl = "WEEKLY TAROT"
    draw.text((center_x(draw, lbl, fonts["en_sm"]), y), lbl, font=fonts["en_sm"], fill=GOLD)
    y += 32

    hline(draw, y, x0=200, x1=W - 200)
    y += 20

    # テーマ（メインコピー）
    for line in wrap_text(draw, data["theme"], fonts["lg"], W - 2 * MARGIN - 40):
        draw.text((center_x(draw, line, fonts["lg"]), y), line, font=fonts["lg"], fill=CREAM)
        y += 58
    y += 4

    hline(draw, y, x0=200, x1=W - 200)
    y += 18

    # カード名
    card_txt = f"{data['card']['number']}  {data['card']['nameJp']}"
    draw.text((center_x(draw, card_txt, fonts["md"]), y), card_txt, font=fonts["md"], fill=GOLD)
    y += 46

    # 英語カード名
    en = data["card"]["nameEn"]
    draw.text((center_x(draw, en, fonts["en_md"]), y), en, font=fonts["en_md"], fill=MUTED)
    y += 44

    # 期間
    draw.text((center_x(draw, data["period"], fonts["sm"]), y),
              data["period"], font=fonts["sm"], fill=MUTED)

    logo(draw, fonts)
    slide_num(draw, fonts, 1)
    swipe_arrow(draw, fonts)
    return img

# ── スライド2-3：メッセージ ──────────────────────────────────────────
def slide_message(data, fonts, idx):
    img, draw = base_canvas()
    corners(draw)
    left_accent(draw)

    y = section_label(draw, fonts, "今週のメッセージ")

    # カード名サブタイトル
    draw.text((CONTENT_X, y), f"✦  {data['card']['nameJp']}", font=fonts["xs"], fill=MUTED)
    y += 38

    hline(draw, y)
    y += 30

    msg = data["message"][idx] if idx < len(data["message"]) else data["message"][0]
    y = draw_block(draw, msg, fonts["body"], CONTENT_X, y, CONTENT_W, max_h=600)

    # スライド2のみキーワード表示
    if idx == 0 and data["keywords"]:
        y += 36
        hline(draw, y)
        y += 22
        kw = "  ·  ".join(data["keywords"])
        draw.text((CONTENT_X, y), kw, font=fonts["sm"], fill=GOLD)

    logo(draw, fonts)
    slide_num(draw, fonts, 2 + idx)
    swipe_arrow(draw, fonts)
    return img

# ── スライド4-6：フォーカスエリア ────────────────────────────────────
FOCUS_CONFIG = [
    ("overall", "総合運", "🌟"),
    ("work",    "仕事運", "💼"),
    ("love",    "恋愛運", "💕"),
]

def slide_focus(data, fonts, idx):
    key, label, icon = FOCUS_CONFIG[idx]
    img, draw = base_canvas()
    corners(draw)
    left_accent(draw)

    y = 100
    draw.text((CONTENT_X, y), f"{icon}  {label}", font=fonts["md"], fill=GOLD)
    y += 60

    hline(draw, y)
    y += 30

    text = data["focus"].get(key, "")
    draw_block(draw, text, fonts["body"], CONTENT_X, y, CONTENT_W, max_h=680)

    logo(draw, fonts)
    slide_num(draw, fonts, 4 + idx)
    swipe_arrow(draw, fonts)
    return img

# ── スライド7：ラッキー情報 ──────────────────────────────────────────
def slide_lucky(data, fonts):
    img, draw = base_canvas()
    corners(draw)

    y = 96
    title = "今週のラッキー"
    draw.text((center_x(draw, title, fonts["lg"]), y), title, font=fonts["lg"], fill=GOLD)
    y += 68

    hline(draw, y)
    y += 50

    items = [
        ("🎨  ラッキーカラー", data["lucky"]["color"]),
        ("✨  行動のヒント",   data["lucky"]["action"]),
        ("🔑  キーワード",     data["lucky"]["keyword"]),
    ]

    for lbl, val in items:
        draw.text((MARGIN + 20, y), lbl, font=fonts["sm"], fill=GOLD)
        y += 38
        # 値ボックス
        box_h = 64
        draw.rectangle([MARGIN + 20, y, W - MARGIN - 20, y + box_h],
                       outline=GOLD_DIM, width=1)
        draw.text((MARGIN + 40, y + (box_h - fonts["body"].size) // 2),
                  val, font=fonts["body"], fill=CREAM)
        y += box_h + 28

    logo(draw, fonts)
    slide_num(draw, fonts, 7)
    swipe_arrow(draw, fonts)
    return img

# ── スライド8：CTA ────────────────────────────────────────────────────
def slide_cta(data, fonts):
    img, draw = base_canvas()
    corners(draw)

    y = 96
    title = "来週のヒント"
    draw.text((center_x(draw, title, fonts["md"]), y), title, font=fonts["md"], fill=GOLD)
    y += 55

    hline(draw, y)
    y += 32

    y = draw_block(draw, data["nextHint"], fonts["body"], MARGIN + 20, y,
                   W - 2 * MARGIN - 40, max_h=220)

    y += 52
    hline(draw, y)
    y += 48

    cta_items = [
        ("💫  投稿を保存して、今週の流れを確認してください", fonts["sm"], CREAM),
        ("👥  フォローで毎週お届けします", fonts["sm"], CREAM),
        ("", None, None),
        ("@asumira_uranai", fonts["md"], GOLD),
    ]

    for txt, fnt, col in cta_items:
        if not txt:
            y += 16
            continue
        draw.text((MARGIN + 20, y), txt, font=fnt, fill=col)
        y += (50 if fnt == fonts["md"] else 40)

    logo(draw, fonts)
    slide_num(draw, fonts, 8)
    return img

# ── コンテンツ抽出 ────────────────────────────────────────────────────
def parse_weekly(monday_key=None):
    if monday_key is None:
        today = date.today()
        monday = today - timedelta(days=today.weekday())
        monday_key = monday.strftime("%Y-%m-%d")

    html_path = REPO_ROOT / "占い" / "weekly" / "index.html"
    content = html_path.read_text(encoding="utf-8")

    # 対象週ブロックをブレース対応で抽出
    start = content.find(f'"{monday_key}"')
    if start == -1:
        print(f"今週（{monday_key}）のコンテンツが見つかりません", file=sys.stderr)
        sys.exit(1)

    brace_start = content.index("{", start)
    depth, end = 0, brace_start
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

    card_blk  = extr(r"card\s*:\s*\{([^}]+)\}")
    focus_m   = re.search(r"focus\s*:\s*\{(.*?)\}(?=\s*,\s*lucky)", block, re.DOTALL)
    focus_blk = focus_m.group(1) if focus_m else ""
    lucky_m   = re.search(r"lucky\s*:\s*\{([^}]+)\}", block)
    lucky_blk = lucky_m.group(1) if lucky_m else ""

    kw_m   = re.search(r"keywords\s*:\s*\[([^\]]+)\]", block)
    kws    = re.findall(r'"([^"]+)"', kw_m.group(1)) if kw_m else []

    msg_m  = re.search(r"message\s*:\s*\[(.*?)\]", block, re.DOTALL)
    msgs   = re.findall(r'"([^"]+)"', msg_m.group(0)) if msg_m else []

    def e(pat, src):
        m = re.search(pat, src)
        return m.group(1) if m else ""

    return {
        "key": monday_key,
        "card": {
            "number": e(r'number\s*:\s*"([^"]+)"', card_blk),
            "nameJp": e(r'nameJp\s*:\s*"([^"]+)"', card_blk),
            "nameEn": e(r'nameEn\s*:\s*"([^"]+)"', card_blk),
            "image":  e(r'image\s*:\s*"([^"]+)"',  card_blk),
        },
        "period":   e(r'period\s*:\s*"([^"]+)"',   block),
        "theme":    e(r'theme\s*:\s*"([^"]+)"',     block),
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
    print(f"⚠ カード画像が見つかりません: {path}", file=sys.stderr)
    return None

# ── キャプション生成 ──────────────────────────────────────────────────
def build_caption(data):
    kw    = " / ".join(data["keywords"])
    msg1  = data["message"][0][:55] + "…" if data["message"] else ""
    over  = data["focus"]["overall"][:55] + "…"
    work  = data["focus"]["work"][:55] + "…"
    love  = data["focus"]["love"][:55] + "…"
    card  = data["card"]["nameJp"]

    return f"""\
✦ 今週のタロット｜{card}「{data["theme"]}」

{msg1}

─────────────────
🌟 総合運　{over}
💼 仕事運　{work}
💕 恋愛運　{love}
─────────────────

🎨 ラッキーカラー：{data["lucky"]["color"]}
🔑 キーワード：{data["lucky"]["keyword"]}

─────────────────
💫 投稿を保存して毎週見返してください
👇 詳しい鑑定はプロフィールリンクから

#タロット #タロット占い #週間運勢 #今週の運勢 #タロットリーディング #占い #運勢 #引き寄せ #スピリチュアル #占い師 #タロットカード #週間タロット #朝活 #自己啓発 #{card} #asumira #asumira占い
"""

# ── Google Drive アップロード ──────────────────────────────────────────
def upload_to_drive(file_paths, creds_json_str, folder_id, week_key):
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = service_account.Credentials.from_service_account_info(
        json.loads(creds_json_str),
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    svc = build("drive", "v3", credentials=creds)

    # 週別サブフォルダ作成
    sub = svc.files().create(
        body={
            "name": f"instagram_{week_key.replace('-', '')}",
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [folder_id],
        },
        fields="id",
    ).execute()
    sub_id = sub["id"]

    # 全員閲覧可に設定（スマホからそのままDLできる）
    svc.permissions().create(
        fileId=sub_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    for fp in file_paths:
        fp = Path(fp)
        mime = "image/png" if fp.suffix == ".png" else "text/plain; charset=utf-8"
        svc.files().create(
            body={"name": fp.name, "parents": [sub_id]},
            media_body=MediaFileUpload(str(fp), mimetype=mime),
        ).execute()
        print(f"  ✓ {fp.name}")

    return f"https://drive.google.com/drive/folders/{sub_id}"

# ── LINE通知 ─────────────────────────────────────────────────────────
def notify_line(text):
    token   = os.environ.get("LINE_CHANNEL_TOKEN")
    user_id = os.environ.get("LINE_USER_ID")
    if not (token and user_id):
        print("⚠ LINE_CHANNEL_TOKEN/LINE_USER_ID 未設定 → スキップ")
        return
    body = json.dumps({
        "to": user_id,
        "messages": [{"type": "text", "text": text}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/push",
        data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        print(f"LINE通知送信: {res.status}")

# ── メイン ────────────────────────────────────────────────────────────
def main():
    monday_key = sys.argv[1] if len(sys.argv) > 1 else None

    print("▶ コンテンツ取得中...")
    data = parse_weekly(monday_key)
    print(f"  {data['key']} | {data['card']['nameJp']} ─ {data['theme']}")

    print("▶ フォント読み込み中...")
    fonts = load_fonts()

    print("▶ カード画像読み込み中...")
    card_img = load_card_image(data["card"]["image"])

    print("▶ スライド生成中...")
    slides = [
        slide_cover(data, fonts, card_img),
        slide_message(data, fonts, 0),
        slide_message(data, fonts, 1),
        slide_focus(data, fonts, 0),
        slide_focus(data, fonts, 1),
        slide_focus(data, fonts, 2),
        slide_lucky(data, fonts),
        slide_cta(data, fonts),
    ]

    saved = []
    for i, slide in enumerate(slides, 1):
        p = OUTPUT_DIR / f"slide_{i:02d}.png"
        slide.save(p, "PNG")
        saved.append(p)
        print(f"  ✓ slide_{i:02d}.png")

    caption_path = OUTPUT_DIR / "caption.txt"
    caption_path.write_text(build_caption(data), encoding="utf-8")
    print("  ✓ caption.txt")
    saved.append(caption_path)

    # Google Drive アップロード
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    folder_id  = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

    if creds_json and folder_id:
        print("▶ Google Driveにアップロード中...")
        drive_url = upload_to_drive(saved, creds_json, folder_id, data["key"])
        print(f"  ✓ {drive_url}")

        notify_line(
            f"📸 Instagram投稿セット準備完了\n\n"
            f"✦ カード：{data['card']['nameJp']}\n"
            f"テーマ：{data['theme']}\n\n"
            f"▼ 画像＆キャプション（Googleドライブ）\n"
            f"{drive_url}\n\n"
            f"💡 caption.txt をコピペしてください\n"
            f"⏰ 今日17〜19時の投稿が効果的です"
        )
    else:
        print(f"ℹ Drive未設定 → ローカル保存のみ: {OUTPUT_DIR}/")

    print("▶ 完了")


if __name__ == "__main__":
    main()
