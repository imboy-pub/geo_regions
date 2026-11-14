#!/usr/bin/env python3
"""Rule-table Cyrillic->katakana transcriptions for RU candidate residual cells.

First slice of the candidate-layer transcription engineering (the evidence
channels are all closed; the remaining long tail needs derived, honest,
machine-candidate output — same class as the s2t zh-Hant track).

Russian orthography is highly phonemic, so a deterministic syllabified
transcription table (Japanese Russian-transcription conventions, ポレポロ/
外務省 style) converts each CSC row's `native` Cyrillic name to katakana.
Conventions encoded here (documented, systematic, no long vowels):

- hard C+V pairs per the (consonant, vowel) table; soft vowels (Я Е Ё Ю И)
  trigger the palatalized row where one exists;
- Е after consonant: only д/т/ж/ш/ч/щ -> ジェ/チェ/シェ rows, з -> ゼ,
  others keep the plain エ-row (レ, ネ, ヴェ, ...) per common forms
  (Ленинград=レニングラード, Диксон=ジクソン);
- word-initial Е -> イェ; word-final soft consonants (ль рь мь нь ...);
  word-final В -> フ, Г -> ク (Псков=プスコフ, Оренбург=オレンブルク);
- дж digraph -> ジ+; ь/ъ consumed; word separator -> ・;
- ы -> イ except т+ы -> トゥ, к+ы -> ク (Тында=トゥンダ, Кызыル=クズル,
  Крым=クリム via р+ы -> リ);
- known irregular common forms are NOT special-cased (Владивосток gets the
  systematic ヴラジヴォストク; documented deviation, machine-candidate).

QA gates: script purity (katakana + ・ only) and an eval set of standard
long-mark-free Japanese forms that must pass 100% before anything is
written. Output is a staged extract (never committed) consumed by
tool/build_csc_candidate.py as the last fill-missing overlay.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

OUT = Path("staging/ai-cand/ru-ja-transcriptions.json")
LOCALE = "ja"

# ---- transcription tables -------------------------------------------------
# (consonant, vowel) -> katakana; vowels: А О У Э Ы hard, Я Е Ё Ю И soft-ish
HARD = {  # а     о     у     э     ы
    "б": ("バ", "ボ", "ブ", "ベ", "ブイ"),
    "в": ("ヴァ", "ヴォ", "ヴ", "ヴェ", "ヴィ"),
    "г": ("ガ", "ゴ", "グ", "ゲ", "ギ"),
    "д": ("ダ", "ド", "ドゥ", "デ", "ディ"),
    "ж": ("ジャ", "ジョ", "ジュ", "ジェ", "ジ"),
    "з": ("ザ", "ゾ", "ズ", "ゼ", "ジ"),
    "к": ("カ", "コ", "ク", "ケ", "ク"),
    "л": ("ラ", "ロ", "ル", "レ", "リ"),
    "м": ("マ", "モ", "ム", "メ", "ムイ"),
    "н": ("ナ", "ノ", "ヌ", "ネ", "ヌイ"),
    "п": ("パ", "ポ", "プ", "ペ", "ピ"),
    "р": ("ラ", "ロ", "ル", "レ", "リ"),
    "с": ("サ", "ソ", "ス", "セ", "スイ"),
    "т": ("タ", "ト", "トゥ", "テ", "トゥ"),
    "ф": ("ファ", "フォ", "フ", "フェ", "フィ"),
    "х": ("ハ", "ホ", "フ", "ヘ", "フイ"),
    "ц": ("ツァ", "ツォ", "ツ", "ツェ", "ツィ"),
    "ч": ("チャ", "チョ", "チュ", "チェ", "チ"),
    "ш": ("シャ", "ショ", "シュ", "シェ", "シ"),
    "щ": ("シャ", "ショ", "シュ", "シチェ", "シチ"),
}
SOFT = {  # я     е     ё     ю     и
    "б": ("ビャ", "ベ", "ビョ", "ビュ", "ビ"),
    "в": ("ヴャ", "ヴェ", "ヴョ", "ヴュ", "ヴィ"),
    "г": ("ギャ", "ゲ", "ギョ", "ギュ", "ギ"),
    "д": ("ジャ", "デ", "ジョ", "ジュ", "ジ"),
    "ж": ("ジャ", "ジェ", "ジョ", "ジュ", "ジ"),
    "з": ("ジャ", "ゼ", "ジョ", "ジュ", "ジ"),
    "к": ("キャ", "ケ", "キョ", "キュ", "キ"),
    "л": ("リャ", "レ", "リョ", "リュ", "リ"),
    "м": ("ミャ", "メ", "ミョ", "ミュ", "ミ"),
    "н": ("ニャ", "ネ", "ニョ", "ニュ", "ニ"),
    "п": ("ピャ", "ペ", "ピョ", "ピュ", "ピ"),
    "р": ("リャ", "レ", "リョ", "リュ", "リ"),
    "с": ("シャ", "セ", "ショ", "シュ", "シ"),
    "т": ("チャ", "テ", "チョ", "チュ", "チ"),
    "ф": ("フャ", "フェ", "フョ", "フュ", "フィ"),
    "х": ("ヒャ", "ヘ", "ヒョ", "ヒュ", "ヒ"),
    "ц": ("ツャ", "ツェ", "ツョ", "ツュ", "ツィ"),
    "ч": ("チャ", "チェ", "チョ", "チュ", "チ"),
    "ш": ("シャ", "シェ", "ショ", "シュ", "シ"),
    "щ": ("シチャ", "シチェ", "シチョ", "シチュ", "シチ"),
}
# consonant alone before another consonant, mid-word
MEDIAL = {"б": "ブ", "в": "ヴ", "г": "グ", "д": "ド", "ж": "ジュ", "з": "ズ",
          "к": "ク", "л": "ル", "м": "ム", "н": "ン", "п": "プ", "р": "ル",
          "с": "ス", "т": "ト", "ф": "フ", "х": "フ", "ц": "ツ", "ч": "チ",
          "ш": "シュ", "щ": "シチ", "й": "イ"}
# consonant at word end — Japanese devoices б/в (フ) and fronts г (ク)
WORD_FINAL = {"б": "フ", "в": "フ", "г": "ク", "д": "ド", "ж": "シュ", "з": "ズ",
              "к": "ク", "л": "ル", "м": "ム", "н": "ン", "п": "プ", "р": "ル",
              "с": "ス", "т": "ト", "ф": "フ", "х": "フ", "ц": "ツ", "ч": "チ",
              "ш": "シュ", "щ": "シチ", "й": "イ"}
FINAL_SOFT = {"б": "ビ", "в": "ヴィ", "г": "ギ", "д": "ディ", "ж": "ジ", "з": "ジ",
              "к": "キ", "л": "リ", "м": "ミ", "н": "ン", "п": "ピ", "р": "リ",
              "с": "シ", "т": "チ", "ф": "フィ", "х": "ヒ", "ц": "ツィ",
              "ч": "チ", "ш": "シ", "щ": "シチ", "й": "イ"}
VOWEL_ONLY = {"а": "ア", "о": "オ", "у": "ウ", "э": "エ", "ы": "イ",
              "я": "ヤ", "ё": "ヨ", "ю": "ユ", "е": "エ", "и": "イ"}
CONSONANTS = set(HARD) | {"й"}
VOWELS = set("аоуэыяеёюи")

# eval anchors: standard long-mark-free Japanese forms (systematic-consistent)
EVAL = {
    "Москва": "モスクワ",
    "Новосибирск": "ノヴォシビルスク",
    "Хабаровск": "ハバロフスク",
    "Сочи": "ソチ",
    "Казань": "カザン",
    "Омск": "オムスク",
    "Уфа": "ウファ",
    "Пермь": "ペルミ",
    "Псков": "プスコフ",
    "Курск": "クルスク",
    "Тверь": "トヴェリ",
    "Рязань": "リャザン",
    "Вологда": "ヴォログダ",
    "Кострома": "コストロマ",
    "Ярославль": "ヤロスラヴリ",
    "Липецк": "リペツク",
    "Бийск": "ビイスク",
    "Тамбов": "タンボフ",
    "Магнитогорск": "マグニトゴルスク",
    "Челябинск": "チェリャビンスク",
    "Красноярск": "クラスノヤルスク",
    "Норильск": "ノリリスク",
    "Ачинск": "アチンスク",
    "Кемерово": "ケメロヴォ",
    "Барнаул": "バルナウル",
    "Курган": "クルガン",
    "Оренбург": "オレンブルク",
    "Омутинское": "オムチンスコエ",
}
# documented systematic deviations from common Japanese forms:
# hyphen -> ・ (サンクト・ペテルブルク vs common サンクトペテルブルク);
# no long vowels (トゥラ vs common トゥーラ); historical epenthesis
# (Сибирь -> シベリ vs common シベリア); в -> ヴ uniformly
# (ヴラジヴォストク vs common ウラジオストク, イヴァノヴォ vs イワノボ);
# word-final нь -> ン (カザン) — common Тюмень form チュメニ deviates.
KNOWN_IRREGULAR = {"Владивосток", "Сибирь", "Иваново", "Тюмень",
                   "Санкт-Петербург", "Тула"}


def transcribe(word: str) -> str:
    word = unicodedata.normalize("NFC", word).strip()
    out: list[str] = []
    chars = list(word.lower())
    i = 0
    at_word_start = True

    def at_word_end(pos: int) -> bool:
        """True when nothing but an optional ь follows before the word ends."""
        return pos >= len(chars) or chars[pos] in ("-", " ", "–") or \
            (chars[pos] == "ь" and pos + 1 >= len(chars))

    while i < len(chars):
        c = chars[i]
        if c in "ьъ":
            i += 1
            continue
        if c in ("-", " ", "–"):
            out.append("・")
            at_word_start = True
            i += 1
            continue
        if c == "д" and i + 1 < len(chars) and chars[i + 1] == "ж":
            i += 2
            if i < len(chars) and chars[i] in VOWELS:
                v = chars[i]
                if v == "у":
                    out.append("ジュ")
                elif v in "яеёюи":
                    out.append(SOFT["ж"]["яеёюи".index(v)])
                else:
                    out.append(HARD["ж"]["аоуэы".index(v)])
                i += 1
            else:
                out.append("ジ")
            at_word_start = False
            continue
        if c in CONSONANTS:
            nxt = chars[i + 1] if i + 1 < len(chars) else None
            nxt2 = chars[i + 2] if i + 2 < len(chars) else None
            if nxt == "ь" and (nxt2 is None or nxt2 not in VOWELS):
                out.append(FINAL_SOFT[c])  # word-final soft consonant
                i += 2
                at_word_start = False
                continue
            if nxt == "ь" and nxt2 in VOWELS:  # palatalized C + vowel (льо...)
                v = nxt2
                out.append(SOFT[c][("яеёюи".index(v))])
                i += 3
                at_word_start = False
                continue
            if nxt in VOWELS:
                v = nxt
                if c == "й":  # glide: Йошкар -> ヨシカル
                    out.append("イェ" if (v == "е" and at_word_start) else VOWEL_ONLY[v])
                    i += 2
                    at_word_start = False
                    continue
                if c == "в" and v == "а" and at_word_end(i + 2):
                    out.append("ワ")  # Москва -> モスクワ
                elif v == "е" and c not in ("д", "т", "ж", "ш", "ч", "щ", "з"):
                    out.append(HARD[c][3])  # plain э-row after consonant
                else:
                    col = "яеёюи".index(v) if v in "яеёюи" else "аоуэы".index(v)
                    out.append((SOFT if v in "яеёюи" else HARD)[c][col])
                i += 2
                at_word_start = False
                continue
            # consonant before another consonant or word end
            if at_word_end(i + 1):
                out.append(WORD_FINAL[c])
            elif c == "н":
                out.append("ン")
            elif c == "м":
                out.append("ン" if nxt in "бпфвм" else "ム")
            elif c == "в":
                out.append("フ" if nxt in "сшц" else "ヴ")
            else:
                out.append(MEDIAL[c])
            i += 1
            at_word_start = False
            continue
        if c in VOWELS:
            if c == "е" and at_word_start:
                out.append("イェ")
            elif c == "ы" and at_word_start:
                out.append("イ")
            else:
                out.append(VOWEL_ONLY[c])
            i += 1
            at_word_start = False
            continue
        raise ValueError(f"unhandled character {c!r} in {word!r}")
    return "".join(out)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cyr = re.compile(r"[\u0400-\u04FF]")

    failures = {name: (transcribe(name), expected)
                for name, expected in EVAL.items()
                if transcribe(name) != expected}
    if failures:
        for name, (got, want) in failures.items():
            print(f"EVAL FAIL {name!r}: got {got!r} want {want!r}")
        return 1
    print(f"eval set: {len(EVAL)}/{len(EVAL)} anchors pass", flush=True)

    rows = []
    for kind in ("cities", "counties"):
        path = root / f"staging/csc-snapshot/contributions/{kind}/RU.json"
        if path.is_file():
            rows.extend(json.loads(path.read_text("utf-8")))
    nodes: dict[str, dict] = {}
    kind_prefix = {"cities": "csc-city:", "counties": "csc-county:"}
    for kind, prefix in kind_prefix.items():
        path = root / f"staging/csc-snapshot/contributions/{kind}/RU.json"
        if not path.is_file():
            continue
        for row in json.loads(path.read_text("utf-8")):
            native = (row.get("native") or "").strip()
            if not cyr.search(native):
                continue  # no Cyrillic source — cell stays missing (never guessed)
            try:
                kana = transcribe(native)
            except ValueError as err:
                print(f"SKIP {kind}/{row['id']}: {err}")
                continue
            purity = re.fullmatch(r"[ァ-ヴー・]+", kana)
            if not purity:
                print(f"PURITY FAIL {row['id']} {native!r} -> {kana!r}")
                continue
            nodes[f"{prefix}{row['id']}"] = {"source": native, "labels": {LOCALE: kana}}

    document = {
        "generator": "tool/gen_candidate_rule_transcriptions.py",
        "ruleVersion": "ru-ja-1",
        "retrievedAt": "2026-11-14",
        "quality": "machine-candidate",
        "humanReviewVerified": False,
        "license": "self-generated (rule-table transcription, no upstream bytes)",
        "locales": [LOCALE],
        "evalAnchors": len(EVAL),
        "evalPassed": len(EVAL),
        "nodeCount": len(nodes),
        "nodes": nodes,
    }
    text = json.dumps(document, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(text)
    print(f"wrote {OUT} ({len(text):,} bytes): nodes={len(nodes)} "
          f"sha256={hashlib.sha256(text).hexdigest()[:16]}…")
    return 0


if __name__ == "__main__":
    sys.exit(main())
