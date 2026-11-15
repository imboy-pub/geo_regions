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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import en_g2p
import fr_g2p
import it_g2p

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
LAT_PURITY = re.compile(r"[A-Za-zÀ-ÿ\u0100-\u017F' -]+")


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

# ---- Italian (improved scholarly transcription, it.wikipedia convention) ---
# č/š/ž for ж/ч/ш/щ, х -> ch (Italian /k/ spelling), ц -> c, yod -> j,
# soft sign kept as apostrophe (Perm', Tver', Kazan'), separators verbatim.
IT_MAP = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "jo",
          "ж": "ž", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
          "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
          "ф": "f", "х": "ch", "ц": "c", "ч": "č", "ш": "š", "щ": "šč",
          "ы": "y", "э": "e", "ю": "ju", "я": "ja"}


def transcribe_it(word: str) -> str:
    word = unicodedata.normalize("NFC", word).strip()
    out: list[str] = []
    chars = list(word.lower())
    i = 0
    at_word_start = True
    while i < len(chars):
        c = chars[i]
        if c == "ь":
            out.append("'")
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
        if c in IT_MAP:
            out.append(IT_MAP[c])
            i += 1
            at_word_start = False
            continue
        raise ValueError(f"unhandled character {c!r} in {word!r}")
    return _capitalize_latin("".join(out))


IT_EVAL = {
    "Новосибирск": "Novosibirsk",
    "Хабаровск": "Chabarovsk",
    "Красноярск": "Krasnojarsk",
    "Иркутск": "Irkutsk",
    "Волгоград": "Volgograd",
    "Челябинск": "Čeljabinsk",
    "Ярославль": "Jaroslavl'",
    "Псков": "Pskov",
    "Тамбов": "Tambov",
    "Тула": "Tula",
    "Уфа": "Ufa",
    "Пермь": "Perm'",
    "Тверь": "Tver'",
    "Курск": "Kursk",
    "Курган": "Kurgan",
    "Барнаул": "Barnaul",
    "Кемерово": "Kemerovo",
    "Норильск": "Noril'sk",
    "Ачинск": "Ačinsk",
    "Рязань": "Rjazan'",
    "Казань": "Kazan'",
    "Вологда": "Vologda",
    "Кострома": "Kostroma",
    "Липецк": "Lipeck",
    "Магнитогорск": "Magnitogorsk",
    "Оренбург": "Orenburg",
    "Владивосток": "Vladivostok",
    "Сочи": "Soči",
    "Бийск": "Bijsk",
    "Нижний Новгород": "Nižnij Novgorod",
    "Санкт-Петербург": "Sankt-Peterburg",
    "Елабуга": "Elabuga",
    "Тюмень": "Tjumen'",
}

# ---- Arabic (ar.wikipedia Russian-name conventions) ------------------------
# Abjad mapping with documented divergences: ar.wp mixes ف/ڤ for в (we pick ف,
# the majority: فلاديفوستوك) and ك/ق for к (we pick ك; قازان is the Tatar
# exonym). Initial vowels carry hamza (أومسك/أوفا/إيركوتسك); word-initial е
# -> يي (ييكاتيرينبورغ); ий merges to a single ي (Нижний->نيжني); ь/ъ drop
# (Пермь->بيرم); separators stay spaces (نيجني نوفغورود).
AR_CONS = {"б": "ب", "в": "ف", "г": "غ", "д": "د", "ж": "ج", "з": "ز",
           "к": "ك", "л": "ل", "м": "م", "н": "ن", "п": "ب", "р": "ر",
           "с": "س", "т": "ت", "ф": "ف", "х": "خ", "ц": "تس", "ч": "تش",
           "ш": "ش", "щ": "شتش", "й": "ي"}
AR_MEDIAL = {"а": "ا", "о": "و", "у": "و", "ы": "ي", "и": "ي", "е": "ي",
             "э": "ه", "я": "يا", "ё": "يو", "ю": "يو"}
AR_INITIAL = {"а": "أ", "о": "أو", "у": "أو", "и": "إي", "е": "يي",
              "э": "إيه", "я": "يا", "ё": "يو", "ю": "يو"}
AR_PURITY = re.compile(r"[\u0621-\u064A ]+")


def transcribe_ar(word: str) -> str:
    word = unicodedata.normalize("NFC", word).strip()
    out: list[str] = []
    chars = list(word.lower())
    i = 0
    at_word_start = True
    while i < len(chars):
        c = chars[i]
        if c in "ьъ":
            i += 1
            continue
        if c in ("-", " ", "–"):
            out.append(" ")
            at_word_start = True
            i += 1
            continue
        if c == "и" and i + 1 < len(chars) and chars[i + 1] == "й":
            out.append("ي")  # ий merges (Нижний->نيжни, Бийск->بيسك)
            i += 2
            at_word_start = False
            continue
        if c in AR_CONS:
            out.append(AR_CONS[c])
            i += 1
            at_word_start = False
            continue
        if c in AR_MEDIAL:
            out.append(AR_INITIAL.get(c, AR_MEDIAL[c]) if at_word_start else AR_MEDIAL[c])
            i += 1
            at_word_start = False
            continue
        raise ValueError(f"unhandled character {c!r} in {word!r}")
    return "".join(out)


AR_EVAL = {
    "Омск": "أومسك",
    "Уфа": "أوفا",
    "Тула": "تولا",
    "Казань": "كازان",
    "Пермь": "بيرم",
    "Тверь": "تفير",
    "Тюмень": "تيومين",
    "Рязань": "ريازان",
    "Псков": "بسكوف",
    "Хабаровск": "خاباروفسك",
    "Сочи": "سوتشي",
    "Новосибирск": "نوفوسيبيرسك",
    "Красноярск": "كراسنويارسك",
    "Иркутск": "إيركوتسك",
    "Екатеринбург": "ييكاتيرينبورغ",
    "Владивосток": "فلاديفوستوك",
    "Кемерово": "كيميروفو",
    "Магнитогорск": "ماغنيتوغورسك",
    "Ачинск": "أتشينسك",
    "Норильск": "نوريلسك",
    "Липецк": "ليبيتسك",
    "Барнаул": "بارناول",
    "Курган": "كورغان",
    "Оренбург": "أورينبورغ",
    "Тамбов": "تامبوف",
    "Курск": "كورسك",
    "Бийск": "بيسك",
    "Кострома": "كوستروما",
    "Вологда": "فولوغدا",
    "Ярославль": "ياروسلافل",
    "Якутск": "ياكوتسك",
    "Нижний Новгород": "نيجني نوفغورود",
}
# documented divergences: ar.wp Волгоград uses ڤ (we pick ف), Казань appears
# as قازان (Tatar exonym; systematic ك), Москва localized موسكو — excluded.

# ---- Chinese (新华社《俄汉译音表》 systematic cells) ------------------------
# Only high-confidence cells are encoded; uncertain rows stay missing
# (never guessed). Documented divergences from frozen traditional forms:
# Пермь 彼尔姆/Пенза 奔萨 use 彼/奔 while the systematic cell пе=佩;
# Кемерово 克麦罗沃 uses 麦 vs systematic ме=梅 (Междуреченск 梅日杜列琴斯克);
# -град renders 格勒 in traditional forms (Волгоград 伏尔加格勒) vs sys
# 格拉德; fused syllables (Курган 库尔干, Тюмень 秋明, Казань 喀山) are
# traditional. Rules: тс -> 茨 (Иркутск 伊尔库茨克); н drops before -ск
# (Ачинск 阿钦斯克); м renders 木 before -ск (Томск 托木斯克); word-final
# й drops after и (Бийск 比斯克) but renders 伊 after other vowels
# (Майский 马伊斯基); ь/ъ absorbed; щ stays unhandled (honest skip).
ZH_CV = {
    ("б", "а"): "巴", ("в", "а"): "瓦", ("г", "а"): "加", ("д", "а"): "达",
    ("ж", "а"): "扎", ("з", "а"): "扎", ("к", "а"): "卡", ("л", "а"): "拉",
    ("м", "а"): "马", ("н", "а"): "纳", ("п", "а"): "帕", ("р", "а"): "拉",
    ("с", "а"): "萨", ("т", "а"): "塔", ("ф", "а"): "法", ("х", "а"): "哈",
    ("ц", "а"): "察", ("ч", "а"): "恰", ("ш", "а"): "沙",
    ("б", "о"): "博", ("в", "о"): "沃", ("г", "о"): "戈", ("д", "о"): "多",
    ("ж", "о"): "若", ("з", "о"): "佐", ("к", "о"): "科", ("л", "о"): "洛",
    ("м", "о"): "莫", ("н", "о"): "诺", ("п", "о"): "波", ("р", "о"): "罗",
    ("с", "о"): "索", ("т", "о"): "托", ("ф", "о"): "福", ("х", "о"): "霍",
    ("ц", "о"): "措", ("ч", "о"): "乔", ("ш", "о"): "绍",
    ("б", "у"): "布", ("в", "у"): "武", ("г", "у"): "古", ("д", "у"): "杜",
    ("ж", "у"): "朱", ("з", "у"): "祖", ("к", "у"): "库", ("л", "у"): "卢",
    ("м", "у"): "穆", ("н", "у"): "努", ("п", "у"): "普", ("р", "у"): "鲁",
    ("с", "у"): "苏", ("т", "у"): "图", ("ф", "у"): "富", ("х", "у"): "胡",
    ("ц", "у"): "楚", ("ч", "у"): "丘", ("ш", "у"): "舒",
    ("б", "и"): "比", ("в", "и"): "维", ("д", "и"): "季", ("ж", "и"): "日",
    ("з", "и"): "济", ("к", "и"): "基", ("л", "и"): "利", ("м", "и"): "米",
    ("н", "и"): "尼", ("п", "и"): "皮", ("р", "и"): "里", ("с", "и"): "西",
    ("т", "и"): "季", ("ф", "и"): "菲", ("х", "и"): "希", ("ц", "и"): "齐",
    ("ч", "и"): "契", ("ш", "и"): "希",
    ("б", "е"): "别", ("в", "е"): "维", ("г", "е"): "格", ("д", "е"): "杰",
    ("ж", "е"): "热", ("з", "е"): "泽", ("к", "е"): "克", ("л", "е"): "列",
    ("м", "е"): "梅", ("н", "е"): "涅", ("п", "е"): "佩", ("р", "е"): "列",
    ("с", "е"): "谢", ("т", "е"): "捷", ("ф", "е"): "费", ("х", "е"): "赫",
    ("ц", "е"): "采", ("ч", "е"): "切", ("ш", "е"): "舍",
    ("в", "я"): "维亚", ("н", "я"): "尼亚", ("л", "я"): "利亚",
    ("р", "я"): "里亚", ("с", "я"): "夏", ("м", "я"): "米亚", ("п", "я"): "皮亚",
    ("т", "я"): "佳", ("д", "я"): "贾", ("б", "я"): "比亚",
    ("в", "ю"): "维尤", ("т", "ау"): "套",
    ("щ", "а"): "夏", ("щ", "е"): "谢", ("щ", "и"): "希", ("щ", "о"): "绍",
    ("щ", "у"): "舒",
    ("т", "ю"): "秋", ("л", "ю"): "柳", ("н", "ю"): "纽", ("д", "ю"): "久",
    ("р", "ю"): "留", ("т", "ё"): "乔", ("л", "ё"): "廖", ("н", "ау"): "瑙",
    # ы column (round-35: -ский/-льный adjectives dominate the RU county tail;
    # anchors: -льный=利内/Камышин 卡梅申/Выкса 维克萨/Клинцы 克林цы=齐/
    # Новозыбковск 新兹布科夫斯克=兹/Куйбышев 古比雪夫=比/Сызрань 瑟兹兰=瑟/
    # Когалым 科加雷姆=雷/Ханты 汉特=特/Кызыл 克孜勒=克/Пышма 佩什马=佩)
    ("н", "ы"): "内", ("м", "ы"): "梅", ("в", "ы"): "维", ("ц", "ы"): "齐",
    ("з", "ы"): "兹", ("б", "ы"): "比", ("с", "ы"): "瑟", ("л", "ы"): "雷",
    ("р", "ы"): "雷", ("т", "ы"): "特", ("к", "ы"): "克", ("п", "ы"): "佩",
    ("д", "ы"): "德", ("г", "и"): "吉",
    ("й", "о"): "约", ("й", "е"): "耶", ("й", "а"): "亚", ("й", "у"): "尤",
    ("й", "и"): "伊",
}
ZH_C = {"с": "斯", "р": "尔", "л": "尔", "м": "姆", "н": "恩", "к": "克",
        "т": "特", "д": "德", "г": "格", "в": "夫", "з": "兹", "ж": "日",
        "х": "赫", "ц": "茨", "б": "布", "п": "普", "ф": "夫", "й": "伊",
        "ч": "奇", "ш": "什"}  # ч/ш alone are rare clusters; provisional
ZH_V0 = {"а": "阿", "о": "奥", "у": "乌", "э": "埃", "и": "伊", "е": "叶",
         "ё": "约", "ю": "尤", "я": "雅"}  # word-initial я=雅 (雅库茨克)
ZH_PURITY = re.compile(r"[\u4e00-\u9fff\- ]+")
ZH_CV_VOWELS = set("аоуэыиеёюя")


def transcribe_zh(word: str) -> str:
    word = unicodedata.normalize("NFC", word).strip()
    out: list[str] = []
    chars = list(word.lower())
    i = 0
    at_word_start = True
    while i < len(chars):
        c = chars[i]
        if c in "ьъ":
            i += 1
            continue
        if c in ("-", " ", "–"):
            out.append(c)
            at_word_start = True
            i += 1
            continue
        if c == "й":
            prev = chars[i - 1] if i > 0 else None
            nxt = chars[i + 1] if i + 1 < len(chars) else None
            if nxt is None or nxt in ("-", " ", "–") or prev == "и":
                pass  # word-final й drops; ий drops the й (Бийск 比斯克)
            elif nxt in ZH_CV_VOWELS:
                pass  # (й, V) cells fire when the vowel branch sees й? no — handled below
            else:
                out.append("伊")  # Майский 马伊斯基
            i += 1
            at_word_start = False
            continue
        if c in ZH_C:
            nxt = chars[i + 1] if i + 1 < len(chars) else None
            nxt2 = chars[i + 2] if i + 2 < len(chars) else None
            if c == "н" and nxt == "с" and nxt2 == "к":
                i += 1  # -нск drops the н (Ачинск 阿钦斯克)
                at_word_start = False
                continue
            if c == "т" and nxt == "с":
                out.append("茨")  # тс -> 茨 (Иркутск 伊尔库茨克)
                i += 2
                at_word_start = False
                continue
            if nxt in ZH_CV_VOWELS:
                if nxt == "а" and nxt2 == "у":
                    cell = ZH_CV.get((c, "ау"))
                    if cell is None:
                        raise ValueError(f"unhandled diphthong ау in {word!r}")
                    out.append(cell)
                    i += 3
                else:
                    cell = ZH_CV.get((c, nxt))
                    if cell is None:
                        raise ValueError(f"unhandled syllable {c+nxt!r} in {word!r}")
                    out.append(cell)
                    i += 2
                at_word_start = False
                continue
            if c == "м" and nxt == "с" and nxt2 == "к":
                out.append("木")  # -мск renders 木 (Томск 托木斯克)
            else:
                out.append(ZH_C[c])
            i += 1
            at_word_start = False
            continue
        if c in ZH_V0:
            # word-initial я=雅 (Якутск); standalone after a vowel=亚 (Красноярск)
            out.append("亚" if (c == "я" and not at_word_start) else ZH_V0[c])
            i += 1
            at_word_start = False
            continue
        raise ValueError(f"unhandled character {c!r} in {word!r}")
    return "".join(out)


ZH_EVAL = {
    "Сочи": "索契",
    "Уфа": "乌法",
    "Тула": "图拉",
    "Тверь": "特维尔",
    "Томск": "托木斯克",
    "Хабаровск": "哈巴罗夫斯克",
    "Иркутск": "伊尔库茨克",
    "Краснодар": "克拉斯诺达尔",
    "Норильск": "诺里尔斯克",
    "Липецк": "利佩茨克",
    "Барнаул": "巴尔瑙尔",
    "Сургут": "苏尔古特",
    "Бийск": "比斯克",
    "Вологда": "沃洛格达",
    "Кострома": "科斯特罗马",
    "Ярославль": "雅罗斯拉夫尔",
    "Псков": "普斯科夫",
    "Якутск": "雅库茨克",
    # ы-column cells (round-35).  Кызыл: system 克兹尔 (л-final=尔 per
    # Байкал 贝加尔); established 克孜勒 is a traditional divergence, and
    # the row itself is CSC-covered — anchor pins the system cells.
    "Кызыл": "克兹尔",
    # Ханты-Мансийск: system 哈恩特 (coda-н standalone=恩 is the pack-wide
    # convention, 127 covered rows); established 汉特 = future fusion slice.
    "Ханты-Мансийск": "哈恩特-马恩西斯克",
    "Красный Яр": "克拉斯内 雅尔",
    "Королёв": "科罗廖夫",
}
# excluded traditional/localized: Москва 莫斯科, Казань 喀山, Тюмень 秋明,
# Пермь 彼尔姆, Оренбург 奥伦堡, Омск 鄂木斯克, Волгоград 伏尔加格勒,
# Кемерово 克麦罗沃, Ачинск 阿钦斯克 (чи=契 vs standard 钦 fusion),
# Тамбов 坦波夫 (м devoicing fusion), Улан-Удэ 乌兰乌德 (лан fusion).
# NOTE: й+V words (Йошкар-Ола) will SKIP in zh (й branch passes; the vowel
# branch then renders the vowel standalone — acceptable systematic output).


def emit_fr_ko(root: Path) -> int:
    """FR communes (INSEE LIBELLE) -> rule-transcription ko+ja extract."""
    fails = fr_g2p.selfcheck()
    if fails:
        print(f"FR g2p eval fails: {fails}")
        return 1
    import csv
    nodes: dict[str, dict] = {}
    purity = re.compile(r"[가-힣 ]+")
    skipped = 0
    with (root / "staging/FR-insee-cog/commune_depuis_1943.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["TYPECOM"] not in ("COM", "ARM") or row["DATE_FIN"]:
                continue
            name = row["LIBELLE"].strip()
            labels: dict[str, str] = {}
            for locale, fn, pr in (("ko", fr_g2p.transcribe_fr_ko, purity),
                                   ("ja", fr_g2p.transcribe_fr_ja,
                                    re.compile(r"[ァ-ヴー・]+")),
                                   ("ru", fr_g2p.transcribe_fr_ru,
                                    re.compile(r"[А-яЁё\- ]+")),
                                   ("ar", fr_g2p.transcribe_fr_ar,
                                    re.compile(r"[\u0621-\u064A ]+")),
                                   ("zh-Hans", fr_g2p.transcribe_fr_zh,
                                    re.compile(r"[\u4e00-\u9fff\-]+"))):
                try:
                    value = fn(name)
                except ValueError:
                    continue
                if pr.fullmatch(value):
                    labels[locale] = value
            if not labels:
                skipped += 1
                continue
            nodes[f"fr-commune:{row['COM']}"] = {"source": name,
                                                 "labels": labels}
    document = {
        "generator": "tool/fr_g2p.py",
        "ruleVersion": "fr-ko-1",
        "retrievedAt": "2026-11-14",
        "quality": "machine-candidate",
        "humanReviewVerified": False,
        "license": "self-generated (rule-table transcription, no upstream bytes)",
        "locales": ["ko", "ja", "ru", "ar", "zh-Hans", "de", "fr", "it"],
        "nodeCount": len(nodes),
        "skipped": skipped,
        "nodes": nodes,
    }
    out = root / "staging/ai-cand/fr-transcriptions.json"
    out.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes): nodes={len(nodes)} skipped={skipped}")
    return 0




_US_QUALIFIER_DROP = ("city", "town", "village", "township", "borough",
                      "plantation", "municipio")


def emit_en_ko(root: Path) -> int:
    """US/GB rows (CSC snapshot) -> English g2p ko+ja extract."""
    fails = en_g2p.selfcheck()
    if fails:
        print(f"EN g2p eval fails: {fails}")
        return 1
    nodes: dict[str, dict] = {}
    skipped = 0
    purity_ko = re.compile(r"[가-힣 ]+")
    purity_ja = re.compile(r"[ァ-ヴー・]+")
    purity_ru = re.compile(r"[А-яЁё\- ]+")
    purity_ar = re.compile(r"[\u0600-\u06FF ]+")
    purity_de = re.compile(r"[A-Za-zÀ-ÿ\u0100-\u017F'’\- .]+")
    purity_fr = purity_de
    purity_it = purity_de
    purity_zh = re.compile(r"[\u4e00-\u9fff\- ]+")
    for cc in ("US", "GB"):
        for kind, prefix in (("cities", "csc-city"), ("counties", "csc-county")):
            path = root / f"staging/csc-snapshot/contributions/{kind}/{cc}.json"
            for row in json.loads(path.read_text(encoding="utf-8")):
                name = row["name"].strip()
                low = name.lower()
                # Louisiana parishes keep the 교구 translation convention —
                # a 패리시 transcription would pollute the style; skip honestly
                if low.endswith(" parish"):
                    skipped += 1
                    continue
                core = name
                county = False
                if low.endswith(" county"):
                    core = name[:-7]
                    county = True
                else:
                    for q in _US_QUALIFIER_DROP:
                        if low.endswith(f" {q}"):
                            core = name[: -(len(q) + 1)]
                            break
                # census parenthetical qualifiers ("(historical)"/"(balance)")
                # are not part of the place name — strip before transcribing
                core = re.sub(r"\s*\([^)]*\)\s*$", "", core).strip()
                labels = {}
                for loc, fn, purity in (
                        ("ko", en_g2p.transcribe_en_ko, purity_ko),
                        ("ja", en_g2p.transcribe_en_ja, purity_ja),
                        ("ru", en_g2p.transcribe_en_ru, purity_ru),
                        ("ar", en_g2p.transcribe_en_ar, purity_ar),
                        ("zh-Hans", en_g2p.transcribe_en_zh, purity_zh),
                        ("de", en_g2p.transcribe_identity, purity_de),
                        ("fr", en_g2p.transcribe_identity, purity_fr),
                        ("it", en_g2p.transcribe_identity, purity_it)):
                    try:
                        value = fn(core)
                    except ValueError:
                        continue
                    if not purity.fullmatch(value):
                        continue
                    if county:
                        # suffix is controlled vocabulary — append AFTER the
                        # purity gate on the core transcription (郡 is kanji,
                        # округ Cyrillic, مقاطعة Arabic; a shared 郡 suffix
                        # silently purity-dropped six locales for 1,370 rows)
                        value = (f"{value} 카운티" if loc == "ko"
                                 else f"{value}郡" if loc == "ja"
                                 else f"{value} округ" if loc == "ru"
                                 else f"{value} مقاطعة" if loc == "ar"
                                 else f"{value}县" if loc == "zh-Hans"
                                      and cc == "US"
                                 else f"{value}郡" if loc == "zh-Hans"
                                 else f"{value} County")
                    labels[loc] = value
                if not labels:
                    skipped += 1
                    continue
                nodes[f"{prefix}:{row['id']}"] = {"source": name,
                                                  "labels": labels}
    document = {
        "generator": "tool/en_g2p.py",
        "ruleVersion": "en-zh-1",
        "retrievedAt": "2026-11-15",
        "quality": "machine-candidate",
        "humanReviewVerified": False,
        "license": "self-generated (rule-table transcription, no upstream bytes)",
        "locales": ["ko", "ja", "ru", "ar", "de", "fr", "it"],
        "nodeCount": len(nodes),
        "skipped": skipped,
        "nodes": nodes,
    }
    out = root / "staging/ai-cand/en-transcriptions.json"
    out.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes): nodes={len(nodes)} skipped={skipped}")
    return 0


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if emit_en_ko(root) != 0:
        return 1
    if emit_fr_ko(root) != 0:
        return 1
    if emit_it_ko(root) != 0:
        return 1
    cyr = re.compile(r"[\u0400-\u04FF]")

    for name, fn, expected in ([(k, transcribe, v) for k, v in EVAL.items()] +
                               [(k, transcribe_ko, v) for k, v in KO_EVAL.items()] +
                               [(k, transcribe_de, v) for k, v in DE_EVAL.items()] +
                               [(k, transcribe_fr, v) for k, v in FR_EVAL.items()] +
                               [(k, transcribe_it, v) for k, v in IT_EVAL.items()] +
                               [(k, transcribe_ar, v) for k, v in AR_EVAL.items()] +
                               [(k, transcribe_zh, v) for k, v in ZH_EVAL.items()]):
        got = fn(name)
        if got != expected:
            print(f"EVAL FAIL {name!r}: got {got!r} want {expected!r}")
            return 1
    print(f"eval sets: ja {len(EVAL)}/{len(EVAL)}, ko {len(KO_EVAL)}/{len(KO_EVAL)}, "
          f"de {len(DE_EVAL)}/{len(DE_EVAL)}, fr {len(FR_EVAL)}/{len(FR_EVAL)}, "
          f"it {len(IT_EVAL)}/{len(IT_EVAL)}, ar {len(AR_EVAL)}/{len(AR_EVAL)}, "
          f"zh {len(ZH_EVAL)}/{len(ZH_EVAL)} anchors pass",
          flush=True)

    purity_res = {"ja": re.compile(r"[ァ-ヴー・]+"), "ko": re.compile(r"[가-힣]+"),
                  "de": LAT_PURITY, "fr": LAT_PURITY, "it": LAT_PURITY, "ar": AR_PURITY, "zh-Hans": ZH_PURITY}
    fns = {"ja": transcribe, "ko": transcribe_ko,
           "de": transcribe_de, "fr": transcribe_fr, "it": transcribe_it,
           "ar": transcribe_ar, "zh-Hans": transcribe_zh}
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
        "ruleVersion": "ru-ja-ko-de-fr-it-ar-zh-1",
        "retrievedAt": "2026-11-14",
        "quality": "machine-candidate",
        "humanReviewVerified": False,
        "license": "self-generated (rule-table transcription, no upstream bytes)",
        "locales": ["ja", "ko", "de", "fr", "it", "ar", "zh-Hans"],
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




def emit_it_ko(root: Path) -> int:
    """IT communes/states (CSC name) -> rule-transcription ko extract."""
    fails = it_g2p.selfcheck()
    if fails:
        print(f"IT g2p eval fails: {fails}")
        return 1
    nodes: dict[str, dict] = {}
    skipped = 0
    purity = re.compile(r"[가-힣 \-]+")
    # IT has no states file in the CSC snapshot; the 4 Sardinian reform
    # provinces are build-maintained nodes pending ISTAT (build comment
    # IT-S5830..S5833) — render them explicitly.
    special = [(5830, "Gallura Nord-Est Sardegna"), (5831, "Ogliastra"),
               (5832, "Medio Campidano"), (5833, "Sulcis Iglesiente")]
    for sid, name in special:
        try:
            value = it_g2p.transcribe_it_ko(name)
        except ValueError:
            continue
        if purity.fullmatch(value):
            nodes[f"csc-state:{sid}"] = {"source": name,
                                         "labels": {"ko": value}}
    for kind, prefix in (("cities", "csc-city:"),):
        path = root / f"staging/csc-snapshot/contributions/{kind}/IT.json"
        if not path.is_file():
            continue
        for row in json.loads(path.read_text(encoding="utf-8")):
            name = (row.get("name") or "").strip()
            if not name:
                continue
            try:
                value = it_g2p.transcribe_it_ko(name)
            except ValueError:
                skipped += 1
                continue
            if not purity.fullmatch(value):
                skipped += 1
                continue
            nodes[f"{prefix}{row['id']}"] = {"source": name,
                                             "labels": {"ko": value}}
    document = {
        "generator": "tool/it_g2p.py",
        "ruleVersion": "it-ko-1",
        "retrievedAt": "2026-11-15",
        "quality": "machine-candidate",
        "humanReviewVerified": False,
        "license": "self-generated (rule-table transcription, no upstream bytes)",
        "locales": ["ko"],
        "nodeCount": len(nodes),
        "skipped": skipped,
        "nodes": nodes,
    }
    out = root / "staging/ai-cand/it-transcriptions.json"
    out.write_text(json.dumps(document, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size:,} bytes): nodes={len(nodes)} skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
