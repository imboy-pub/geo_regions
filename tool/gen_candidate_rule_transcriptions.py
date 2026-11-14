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

OUT = Path("staging/ai-cand/ru-transcriptions.json")  # 4 locales: ja ko de fr
LOCALE = "ja"  # primary locale (kept for the doc header); ja+ko both emitted

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
# ko contested anchor removed: Свердловск (스베르들롭스크/스베르들로프스크 both attested)
# de contested anchor removed: Липецк (Lipetzk vs Lipezk — German tz orthography
# depends on vowel length; ц->z is the systematic base)


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


# ---- Korean (외래어 표기법 러시아어 표기법) ---------------------------------
# Syllables are composed from jamo: consonant row is identical across vowels
# (БЯ=뱌, ДЕ=데...), so only consonant->jamo + vowel->jamo maps are needed.
# Cluster rules encoded from standard forms:
# - sonorants н/м/л and в before a consonant attach as final consonant
#   (옴스크, 탐보프, 홀름스크, 하바롭스크, 레닌그라드, 카멘카);
#   н before к before a consonant assimilates to ㅇ and elides к (상트);
# - other consonants before a consonant become a standalone 으-row syllable
#   (모스크바 스, 이르쿠트스크 르, 스베르들로프스크 드);
# - word-final cluster: C1 as 으-row onset with C2 as final (야로슬라블 블);
# - word-final н/м/л/в attach to the previous syllable (카잔); other word-final
#   consonants are standalone 으-row syllables (옴스크 크, 탐보프 프);
# - Е is 예 word-initially and 에 after a consonant (예카테린부르크/페름);
# - й after a vowel is 이, word-final й after и merges (니즈니노브고로드);
# - word separators are dropped (니즈니노브고로드 joins).
CHO = {"б": "ㅂ", "в": "ㅂ", "г": "ㄱ", "д": "ㄷ", "ж": "ㅈ", "з": "ㅈ",
       "к": "ㅋ", "л": "ㄹ", "м": "ㅁ", "н": "ㄴ", "п": "ㅍ", "р": "ㄹ",
       "с": "ㅅ", "т": "ㅌ", "ф": "ㅍ", "х": "ㅎ", "ц": "ㅊ", "ч": "ㅊ",
       "ш": "ㅅ", "щ": "ㅅ", "й": "ㅇ"}
JONG_JAMO = {"н": "ㄴ", "м": "ㅁ", "л": "ㄹ", "в": "ㅂ", "р": "ㄹ", "г": "ㄱ",
             "к": "ㄱ", "д": "ㄷ", "т": "ㄷ", "б": "ㅂ", "п": "ㅍ", "с": "ㅅ",
             "з": "ㅈ", "ф": "ㅍ", "х": "ㅎ", "ж": "ㅈ", "ч": "ㅊ", "ц": "ㅊ",
             "ш": "ㅅ", "щ": "ㅅ"}
# Unicode jamo slot indices derived from reference syllables (the hardcoded
# 18-letter order is WRONG: the Unicode initial set has a gap at index 8)
CHO_IDX = {c: (ord(ref) - 0xAC00) // 588 for c, ref in
           {"ㄱ": "가", "ㄲ": "까", "ㄴ": "나", "ㄷ": "다", "ㄸ": "따", "ㄹ": "라",
            "ㅁ": "마", "ㅂ": "바", "ㅅ": "사", "ㅆ": "싸", "ㅇ": "아", "ㅈ": "자",
            "ㅉ": "짜", "ㅊ": "차", "ㅋ": "카", "ㅌ": "타", "ㅍ": "파", "ㅎ": "하"}.items()}
JUNG_IDX = {v: ((ord(ref) - 0xAC00) % 588) // 28 for v, ref in
            {"ㅏ": "가", "ㅐ": "개", "ㅑ": "갸", "ㅒ": "걔", "ㅓ": "거", "ㅔ": "게",
             "ㅕ": "겨", "ㅖ": "계", "ㅗ": "고", "ㅘ": "과", "ㅙ": "괘", "ㅚ": "괴",
             "ㅛ": "교", "ㅜ": "구", "ㅝ": "궈", "ㅞ": "궤", "ㅟ": "귀", "ㅠ": "규",
             "ㅡ": "그", "ㅢ": "긔", "ㅣ": "기"}.items()}
JONG_IDX = {"": 0, "ㄱ": 1, "ㄲ": 2, "ㄴ": 4, "ㄷ": 7, "ㄹ": 8, "ㅁ": 16, "ㅂ": 17,
            "ㅅ": 19, "ㅇ": 21, "ㅈ": 22, "ㅊ": 23, "ㅋ": 24, "ㅌ": 25, "ㅍ": 26, "ㅎ": 27}
JUNG = {"а": "ㅏ", "я": "ㅑ", "о": "ㅗ", "ё": "ㅛ", "у": "ㅜ", "ю": "ㅠ",
        "э": "ㅔ", "е": "ㅔ", "ы": "ㅣ", "и": "ㅣ"}
BATCHIM_SOFT = {"р": "ㄹ", "л": "ㄹ", "м": "ㅁ", "н": "ㄴ"}
# word-final devoicing/aspiration (Псков->프스코프, Тамбов->탐보프,
# Оренбург->오렌부르크: б/в->ㅍ, г/к->ㅋ; д stays ㄷ 레닌그라드->레닌그라드)
WORD_FINAL_CHO = {"б": "ㅍ", "в": "ㅍ", "г": "ㅋ", "з": "ㅅ", "ж": "ㅅ",
                  "к": "ㅋ", "п": "ㅍ", "ф": "ㅍ"}


def _compose(onset: str, jung: str, jong: str = "") -> str:
    code = 0xAC00 + 21 * 28 * CHO_IDX[onset] + 28 * JUNG_IDX[jung] + JONG_IDX[jong]
    return chr(code)


def _vowel_only_jamo(v: str) -> str:
    # vowel-only syllable: composed with ㅇ onset (아 이 요 ...)
    return _compose("ㅇ", JUNG[v])


def transcribe_ko(word: str) -> str:
    word = unicodedata.normalize("NFC", word).strip()
    units: list[tuple[str, str, str]] = []  # (onset, jung, jong)
    chars = list(word.lower())
    i = 0
    at_word_start = True

    def at_word_end(pos: int) -> bool:
        return pos >= len(chars) or chars[pos] in ("-", " ", "–", "ь", "ъ")

    while i < len(chars):
        c = chars[i]
        if c in "ьъ":
            i += 1
            continue
        if c in ("-", " ", "–"):
            at_word_start = True  # Korean joins multi-part names: emit nothing
            i += 1
            continue
        if c == "д" and i + 1 < len(chars) and chars[i + 1] == "ж":
            i += 2
            if i < len(chars) and chars[i] in JUNG:
                units.append(("ㅈ", JUNG[chars[i]], ""))
                i += 1
            else:
                units.append(("ㅈ", "ㅡ", ""))
            at_word_start = False
            continue
        if c in CHO:
            nxt = chars[i + 1] if i + 1 < len(chars) else None
            nxt2 = chars[i + 2] if i + 2 < len(chars) else None
            soft = nxt == "ь"
            if soft and nxt2 is not None and nxt2 in JUNG:  # palatalized C+V
                units.append((CHO[c], JUNG[nxt2], ""))
                i += 3
                at_word_start = False
                continue
            if soft:  # word-final soft consonant
                if c in ("р", "л") and nxt2 is None:  # Тверь->트베리: final рь -> 리
                    units.append(("ㄹ", "ㅣ", ""))
                elif units and c in BATCHIM_SOFT:  # нь/мь/ль+C -> final (노릴스크)
                    units[-1] = (units[-1][0], units[-1][1], BATCHIM_SOFT[c])
                i += 2
                at_word_start = False
                continue
            if nxt in JUNG:
                vowel = "ㅖ" if (c == "е" and at_word_start) else JUNG[nxt]
                if c == "л" and units and i > 0 and (chars[i - 1] in JUNG or chars[i - 1] in CONSONANTS):
                    # 볼로그다/슬라블/들로: л doubles -> ㄹ batchim + ㄹ-onset
                    units[-1] = (units[-1][0], units[-1][1], "ㄹ")
                units.append((CHO[c], vowel, ""))
                i += 2
                at_word_start = False
                continue
            # consonant before a consonant or word end
            if c == "н" and nxt == "к" and nxt2 is not None and nxt2 not in JUNG \
                    and nxt2 not in ("ь", "ъ", "-", " ", "–"):
                if units:  # 상트: нк assimilates to ㅇ, к elides,
                    units[-1] = (units[-1][0], units[-1][1], "ㅇ")
                    units.append((CHO[nxt2], "ㅡ", ""))  # surviving C stays 으-row
                    i += 3
                    at_word_start = False
                    continue
            if c == "й":
                if not at_word_end(i + 1):  # word-final й merges (니즈니)
                    units.append(("ㅇ", "ㅣ", ""))
                i += 1
                at_word_start = False
                continue
            if at_word_end(i + 1):
                if units and c in ("н", "м", "л"):  # Урал->우랄, Казань->카잔
                    units[-1] = (units[-1][0], units[-1][1], JONG_JAMO[c])
                elif units and c == "й":
                    pass  # word-final й merges (니즈니)
                else:
                    units.append((WORD_FINAL_CHO.get(c, CHO[c]), "ㅡ", ""))
                i += 1
                at_word_start = False
                continue
            if c == "в" and nxt is not None and nxt in CHO and at_word_end(i + 2):
                # word-final в+cluster: single syllable 으-row+batchim (вл+ь -> 블)
                units.append((CHO[c], "ㅡ", JONG_JAMO.get(nxt, "ㅇ")))
                i += 2
                if i < len(chars) and chars[i] in "ьъ":
                    i += 1
                at_word_start = False
                continue
            if c == "в" and units and nxt in ("с", "ш", "ц"):
                units[-1] = (units[-1][0], units[-1][1], "ㅂ")  # 하바롭스크
            elif c in ("н", "м", "л") and units:
                units[-1] = (units[-1][0], units[-1][1], JONG_JAMO[c])
            else:
                units.append((CHO[c], "ㅡ", ""))
            at_word_start = False
            i += 1
            continue
        if c in JUNG:
            if c == "е" and at_word_start:
                units.append(("ㅇ", "ㅖ", ""))
            else:
                units.append(("ㅇ", JUNG[c], ""))
            i += 1
            at_word_start = False
            continue
        raise ValueError(f"unhandled character {c!r} in {word!r}")
    return "".join(_compose(o, j, g) for o, j, g in units)


KO_EVAL = {
    "Москва": "모스크바",
    "Новосибирск": "노보시비르스크",
    "Хабаровск": "하바롭스크",
    "Сочи": "소치",
    "Казань": "카잔",
    "Омск": "옴스크",
    "Уфа": "우파",
    "Пермь": "페름",
    "Псков": "프스코프",
    "Курск": "쿠르스크",
    "Тверь": "트베리",
    "Рязань": "랴잔",
    "Вологда": "볼로그다",
    "Кострома": "코스트로마",
    "Ярославль": "야로슬라블",
    "Липецк": "리페츠크",
    "Бийск": "비이스크",
    "Тамбов": "탐보프",
    "Магнитогорск": "마그니토고르스크",
    "Челябинск": "첼랴빈스크",
    "Красноярск": "크라스노야르스크",
    "Норильск": "노릴스크",
    "Ачинск": "아친스크",
    "Кемерово": "케메로보",
    "Барнаул": "바르나울",
    "Курган": "쿠르간",
    "Оренбург": "오렌부르크",
    "Владивосток": "블라디보스토크",
    "Санкт-Петербург": "상트페테르부르크",
    "Тула": "툴라",
    "Иркутск": "이르쿠트스크",
    "Нижний Новгород": "니즈니노브고로드",
}


# ---- German / French Latin romanization (DIN-style / French conventions) ---
# Letter-level maps from the Cyrillic native; ь is dropped (French) or j before
# a vowel (German Iljinski); й is j/i/'' in German by context, ï in French;
# separators (space/hyphen) are preserved verbatim.
DE_MAP = {"а": "a", "б": "b", "в": "w", "г": "g", "д": "d", "е": "e", "ё": "jo",
          "ж": "sch", "з": "s", "и": "i", "к": "k", "л": "l", "м": "m", "н": "n",
          "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f",
          "х": "ch", "ц": "z", "ч": "tsch", "ш": "sch", "щ": "schtsch", "ы": "y",
          "э": "e", "ю": "ju", "я": "ja", "й": "j"}
FR_MAP = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "ïo",
          "ж": "j", "з": "z", "и": "i", "й": "ï", "к": "k", "л": "l", "м": "m",
          "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "ou",
          "ф": "f", "х": "kh", "ц": "ts", "ч": "tch", "ш": "ch", "щ": "chtch",
          "ы": "y", "э": "e", "ю": "iou", "я": "ia"}
LAT_PURITY = re.compile(r"[A-Za-zÀ-ÿ' -]+")


def _transcribe_latin(word: str, cmap: dict[str, str], soft_ь_j: bool,
                      е_initial: str) -> str:
    word = unicodedata.normalize("NFC", word).strip()
    out: list[str] = []
    chars = list(word.lower())
    i = 0
    at_word_start = True
    while i < len(chars):
        c = chars[i]
        if c == "ь":
            if soft_ь_j and i + 1 < len(chars) and chars[i + 1] in "аеёиоуыэюя":
                out.append("j")  # Ильинский -> Iljinski (German)
            i += 1
            continue
        if c == "ъ":
            i += 1
            continue
        if c in ("-", " ", "–"):
            out.append(c)
            at_word_start = True
            i += 1
            continue
        if c == "д" and i + 1 < len(chars) and chars[i + 1] == "ж":
            out.append({"de": "dsch", "fr": "dj"}[soft_ь_j and "de" or "fr"])
            i += 2
            at_word_start = False
            continue
        if c in cmap:
            if c == "е" and at_word_start:
                out.append(е_initial)
                i += 1
                at_word_start = False
                continue
            elif c == "й" and cmap is DE_MAP:
                prev_v = i > 0 and chars[i - 1] in "аеёиоуыэюя"
                at_word_end = i + 1 >= len(chars) or chars[i + 1] in ("-", " ", "–")
                if at_word_end:
                    pass  # word-final й drops (Nischni)
                elif prev_v and chars[i + 1] in "аеёиоуыэюя":
                    out.append("j")  # Krasnojarsk
                elif prev_v:
                    out.append("i")  # Biisk
                else:
                    out.append("j")
                i += 1
                at_word_start = False
                continue
            if c == "я" and cmap is FR_MAP and i > 0 and \
                    chars[i - 1] in "аеёиоуыэюя":
                out.append("ïa")  # hiatus break: Krasnoïarsk
            elif c == "й" and cmap is FR_MAP:
                at_word_end = i + 1 >= len(chars) or chars[i + 1] in ("-", " ", "–")
                if (at_word_end and out and i > 0 and chars[i - 1] == "и"
                        and out[-1].endswith("i")):
                    out[-1] = out[-1][:-1]  # word-final ий merges to ï (Nijnï)
                out.append("ï")  # mid-word и+й keeps both (Biïsk)
            else:
                out.append(cmap[c])
            i += 1
            at_word_start = False
            continue
        raise ValueError(f"unhandled character {c!r} in {word!r}")
    return _capitalize_latin("".join(out))


def _capitalize_latin(s: str) -> str:
    # proper-name convention: first letter of every word segment uppercased
    parts = re.split(r"([ -])", s)
    return "".join(p[0].upper() + p[1:] if p and p[0].islower() else p for p in parts)


def transcribe_de(word: str) -> str:
    return _transcribe_latin(word, DE_MAP, soft_ь_j=True, е_initial="je")


def transcribe_fr(word: str) -> str:
    return _transcribe_latin(word, FR_MAP, soft_ь_j=False, е_initial="e")


DE_EVAL = {
    "Москва": "Moskwa",
    "Новосибирск": "Nowosibirsk",
    "Хабаровск": "Chabarowsk",
    "Сочи": "Sotschi",
    "Казань": "Kasan",
    "Омск": "Omsk",
    "Уфа": "Ufa",
    "Пермь": "Perm",
    "Псков": "Pskow",
    "Курск": "Kursk",
    "Тверь": "Twer",
    "Рязань": "Rjasan",
    "Вологда": "Wologda",
    "Кострома": "Kostroma",
    "Ярославль": "Jaroslawl",
    "Бийск": "Biisk",
    "Тамбов": "Tambow",
    "Магнитогорск": "Magnitogorsk",
    "Челябинск": "Tscheljabinsk",
    "Красноярск": "Krasnojarsk",
    "Норильск": "Norilsk",
    "Ачинск": "Atschinsk",
    "Кемерово": "Kemerowo",
    "Барнаул": "Barnaul",
    "Курган": "Kurgan",
    "Оренбург": "Orenburg",
    "Иркутск": "Irkutsk",
    "Тула": "Tula",
    "Владивосток": "Wladiwostok",
    "Нижний Новгород": "Nischni Nowgorod",
    "Тюмень": "Tjumen",
    "Ильинский": "Iljinski",
    "Санкт-Петербург": "Sankt-Peterburg",
}
FR_EVAL = {
    "Москва": "Moskva",
    "Хабаровск": "Khabarovsk",
    "Сочи": "Sotchi",
    "Казань": "Kazan",
    "Омск": "Omsk",
    "Оренбург": "Orenbourg",
    "Тамбов": "Tambov",
    "Псков": "Pskov",
    "Курск": "Koursk",
    "Курган": "Kourgan",
    "Тула": "Toula",
    "Уфа": "Oufa",
    "Иркутск": "Irkoutsk",
    "Тюмень": "Tioumen",
    "Рязань": "Riazan",
    "Кемерово": "Kemerovo",
    "Челябинск": "Tcheliabinsk",
    "Красноярск": "Krasnoïarsk",
    "Нижний Новгород": "Nijnï Novgorod",
    "Вологда": "Vologda",
    "Кострома": "Kostroma",
    "Ярославль": "Iaroslavl",
    "Липецк": "Lipetsk",
    "Магнитогорск": "Magnitogorsk",
    "Норильск": "Norilsk",
    "Ачинск": "Atchinsk",
    "Барнаул": "Barnaoul",
    "Бийск": "Biïsk",
    "Пермь": "Perm",
    "Тверь": "Tver",
    "Владивосток": "Vladivostok",
    "Елабуга": "Elabouga",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    cyr = re.compile(r"[\u0400-\u04FF]")

    for name, fn, expected in ([(k, transcribe, v) for k, v in EVAL.items()] +
                               [(k, transcribe_ko, v) for k, v in KO_EVAL.items()] +
                               [(k, transcribe_de, v) for k, v in DE_EVAL.items()] +
                               [(k, transcribe_fr, v) for k, v in FR_EVAL.items()]):
        got = fn(name)
        if got != expected:
            print(f"EVAL FAIL {name!r}: got {got!r} want {expected!r}")
            return 1
    print(f"eval sets: ja {len(EVAL)}/{len(EVAL)}, ko {len(KO_EVAL)}/{len(KO_EVAL)}, "
          f"de {len(DE_EVAL)}/{len(DE_EVAL)}, fr {len(FR_EVAL)}/{len(FR_EVAL)} anchors pass",
          flush=True)

    purity_res = {"ja": re.compile(r"[ァ-ヴー・]+"), "ko": re.compile(r"[가-힣]+"),
                  "de": LAT_PURITY, "fr": LAT_PURITY}
    fns = {"ja": transcribe, "ko": transcribe_ko,
           "de": transcribe_de, "fr": transcribe_fr}
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
            labels = {}
            for locale, fn in fns.items():
                try:
                    value = fn(native)
                except ValueError as err:
                    print(f"SKIP {locale} {kind}/{row['id']}: {err}")
                    continue
                if not purity_res[locale].fullmatch(value):
                    print(f"PURITY FAIL {locale} {row['id']} {native!r} -> {value!r}")
                    continue
                labels[locale] = value
            if labels:
                nodes[f"{prefix}{row['id']}"] = {"source": native, "labels": labels}

    document = {
        "generator": "tool/gen_candidate_rule_transcriptions.py",
        "ruleVersion": "ru-ja-ko-de-fr-1",
        "retrievedAt": "2026-11-14",
        "quality": "machine-candidate",
        "humanReviewVerified": False,
        "license": "self-generated (rule-table transcription, no upstream bytes)",
        "locales": ["ja", "ko", "de", "fr"],
        "evalAnchors": len(EVAL) + len(KO_EVAL),
        "evalPassed": len(EVAL) + len(KO_EVAL),
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
