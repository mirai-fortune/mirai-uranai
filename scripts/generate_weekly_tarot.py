import json
import os
import random
import re
import urllib.request
from datetime import date, timedelta

FILE = "占い/weekly/index.html"

CARDS = [
    {"nameEn": "The Fool", "nameJp": "愚者", "number": "0", "image": "fool.jpg"},
    {"nameEn": "The Magician", "nameJp": "魔術師", "number": "I", "image": "magician.jpg"},
    {"nameEn": "The High Priestess", "nameJp": "女教皇", "number": "II", "image": "highpriestess.jpg"},
    {"nameEn": "The Empress", "nameJp": "女帝", "number": "III", "image": "empress.jpg"},
    {"nameEn": "The Emperor", "nameJp": "皇帝", "number": "IV", "image": "emperor.jpg"},
    {"nameEn": "The Hierophant", "nameJp": "法王", "number": "V", "image": "hierophant.jpg"},
    {"nameEn": "The Lovers", "nameJp": "恋人", "number": "VI", "image": "lovers.jpg"},
    {"nameEn": "The Chariot", "nameJp": "戦車", "number": "VII", "image": "chariot.jpg"},
    {"nameEn": "Strength", "nameJp": "力", "number": "VIII", "image": "strength.jpg"},
    {"nameEn": "The Hermit", "nameJp": "隠者", "number": "IX", "image": "hermit.jpg"},
    {"nameEn": "Wheel of Fortune", "nameJp": "運命の輪", "number": "X", "image": "wheeloffortune.jpg"},
    {"nameEn": "Justice", "nameJp": "正義", "number": "XI", "image": "justice.jpg"},
    {"nameEn": "The Hanged Man", "nameJp": "吊るされた男", "number": "XII", "image": "hangedman.jpg"},
    {"nameEn": "Death", "nameJp": "死神", "number": "XIII", "image": "death.jpg"},
    {"nameEn": "Temperance", "nameJp": "節制", "number": "XIV", "image": "temperance.jpg"},
    {"nameEn": "The Devil", "nameJp": "悪魔", "number": "XV", "image": "devil.jpg"},
    {"nameEn": "The Tower", "nameJp": "塔", "number": "XVI", "image": "tower.jpg"},
    {"nameEn": "The Star", "nameJp": "星", "number": "XVII", "image": "star.jpg"},
    {"nameEn": "The Moon", "nameJp": "月", "number": "XVIII", "image": "moon.jpg"},
    {"nameEn": "The Sun", "nameJp": "太陽", "number": "XIX", "image": "sun.jpg"},
    {"nameEn": "Judgement", "nameJp": "審判", "number": "XX", "image": "judgement.jpg"},
    {"nameEn": "The World", "nameJp": "世界", "number": "XXI", "image": "world.jpg"},
]

REQUIRED_KEYS = {"theme", "keywords", "message", "focus", "lucky", "nextHint"}


def load_content():
    with open(FILE, encoding="utf-8") as f:
        return f.read()


def existing_keys(content):
    return sorted(re.findall(r'"(\d{4}-\d{2}-\d{2})":\s*\{', content))


def recent_card_names(content, keys, n=3):
    names = []
    for k in keys[-n:]:
        start = content.find(f'"{k}"')
        block = content[start:start + 400]
        m = re.search(r'nameEn:"([^"]+)"', block)
        if m:
            names.append(m.group(1))
    return names


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def build_prompt(card, period):
    return f"""あなたはASUMIRA占いサイトのタロットライターです。以下の条件で「今週のタロット」コンテンツを1件、JSON形式のみで出力してください。前置きや説明、コードブロックの```は不要です。JSONオブジェクトのみを出力してください。

## 今週のカード
{card['nameJp']}（{card['nameEn']}）

## 対象期間
{period}

## ブランドボイス
温かく、詩的で、読んだ人が「自分のことを言われている」と感じられる文章。ありきたりな表現は避ける。

## 出力するJSONの構造（このキーのみを出力）
{{
  "theme": "今週のテーマ（12〜18文字）",
  "keywords": ["キーワード1", "キーワード2", "キーワード3", "キーワード4"],
  "message": ["1段落目（100〜160字、カードのエネルギーと今週の全体的なメッセージ）", "2段落目（100〜160字、具体的な行動への示唆）"],
  "focus": {{
    "overall": "全体運（100〜150字）",
    "work": "仕事（100〜150字）",
    "love": "恋愛（100〜150字）"
  }},
  "lucky": {{"color": "ラッキーカラー", "action": "今週のアクション（25字以内）", "keyword": "キーワード（2〜4字）"}},
  "nextHint": "来週への一言ヒント（25〜50字）"
}}
"""


def call_claude(card, period):
    body = json.dumps({
        "model": "claude-sonnet-5",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": build_prompt(card, period)}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": os.environ["ANTHROPIC_API_KEY"],
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as res:
        result = json.loads(res.read())

    text = result["content"][0]["text"]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"JSONが見つかりませんでした: {text[:500]}")
    data = json.loads(match.group(0))

    missing = REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"レスポンスに必要なキーが不足しています: {missing}")
    return data


def build_entry_text(target_key, card, period, e):
    lines = [
        f'  "{target_key}": {{',
        f'    card: {{ number:{js_str(card["number"])}, nameJp:{js_str(card["nameJp"])}, '
        f'nameEn:{js_str(card["nameEn"])}, image:{js_str("../タロット/images/" + card["image"])} }},',
        f'    period: {js_str(period)},',
        f'    theme: {js_str(e["theme"])},',
        f'    keywords: {json.dumps(e["keywords"], ensure_ascii=False)},',
        f'    message: {json.dumps(e["message"], ensure_ascii=False)},',
        '    focus: {',
        f'      overall: {js_str(e["focus"]["overall"])},',
        f'      work: {js_str(e["focus"]["work"])},',
        f'      love: {js_str(e["focus"]["love"])}',
        '    },',
        f'    lucky: {{ color:{js_str(e["lucky"]["color"])}, action:{js_str(e["lucky"]["action"])}, '
        f'keyword:{js_str(e["lucky"]["keyword"])} }},',
        f'    nextHint: {js_str(e["nextHint"])}',
        '  }',
    ]
    return "\n".join(lines)


def insert_entry(content, entry_text):
    start = content.index("const WEEKLY_CONTENT")
    close_idx = content.index("\n};", start)
    before = content[:close_idx].rstrip()
    if not before.endswith(","):
        before += ","
    return before + "\n\n" + entry_text + "\n\n};" + content[close_idx + 3:]


def set_output(key, value):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def main():
    content = load_content()
    keys = existing_keys(content)

    if keys:
        target = date.fromisoformat(keys[-1]) + timedelta(days=7)
    else:
        today = date.today()
        target = today - timedelta(days=today.weekday())

    target_key = target.isoformat()

    if target_key in keys:
        print(f"{target_key} はすでに追加済みです。スキップします。")
        set_output("skipped", "true")
        return

    avoid = set(recent_card_names(content, keys))
    candidates = [c for c in CARDS if c["nameEn"] not in avoid] or CARDS
    card = random.choice(candidates)

    period_end = target + timedelta(days=6)
    period = f"{target.year}年{target.month}月{target.day}日（月）〜{period_end.month}月{period_end.day}日（日）"

    e = call_claude(card, period)
    entry_text = build_entry_text(target_key, card, period, e)
    new_content = insert_entry(content, entry_text)

    with open(FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    set_output("skipped", "false")
    set_output("target_date", target_key.replace("-", "/"))
    set_output("card_jp", card["nameJp"])
    set_output("theme", e["theme"])
    print(f"{target_key}: {card['nameJp']}「{e['theme']}」を追加しました。")


if __name__ == "__main__":
    main()
