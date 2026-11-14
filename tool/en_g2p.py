#!/usr/bin/env python3
"""English orthography -> Hangul (국립국어원 외래어 표기법 영어 표기법).

Same architecture as tool/fr_g2p.py: segment() splits graphemes
longest-first, phonemes() resolves context (magic-e, r-colouring,
syllable shape, word-final suffix overrides), transcribe_en_ko() renders
Hangul.  English spelling->sound is not fully regular, so the discipline
is: system rules cover regular vocabulary (표기법 영어장 2장 표들);
famous divergent forms live in LEXICAL_EN_KO_FULL (lexicon+system
dual-track, the 新华社 model) with divergence comments; unmappable
graphemes raise ValueError -> honest skip (per-locale purity admission
drops the row).  Eval gate: every EN_KO_EVAL anchor must pass 100%
before the caller writes any file.

Called by tool/gen_candidate_rule_transcriptions.py::emit_en_ko().
"""
from __future__ import annotations

_LONG = ("eɪ", "aɪ", "ɔɪ", "aʊ", "oʊ", "juː", "iː", "uː")
_SHORT = ("æ", "ɛ", "ɪ", "ɑ", "ɔ", "ʊ", "ə", "ʌ", "ɜː", "ɔː")
_VOWELISH = _LONG + _SHORT + ("ia", "io", "ar", "er", "ir", "or", "ur")
_PAL = ("ʃ", "tʃ", "dʒ")

_VOWEL_LETTERS = ("a", "e", "i", "o", "u")
_MAGIC = {"a": "eɪ", "i": "aɪ", "o": "oʊ", "u": "juː",
          "e": "iː"}

# word-final suffix overrides (graphemes -> phoneme list), 표기법-style
_SUFFIX_OVERRIDE = {
    "ton": ["t", "ə", "n"],        # -턴 (워싱턴/클린턴/브라이턴)
    "ford": ["f", "ə", "d"],       # -퍼드 (하트퍼드)
    "burg": ["b", "ʌ", "g~"],      # -버그 (피츠버그)
    "burgh": ["b", "ʌ", "g~"],
    "shire": ["ʃ", "ə"],           # -셔 (요크셔)
    "ham": ["ə", "m"],             # -엄 (버밍엄/노팅엄)
    "son": ["s", "ə", "n"],        # -슨 (잭슨/제퍼슨/기브슨)
    "orough": ["ə", "r", "ə"],     # -버러 (힐스버러/버러)
}

# --- grapheme segmentation -------------------------------------------------

_MULTI = {
    "ough": "ough", "augh": "augh",
    "eigh": "eɪ", "igh": "aɪ",
    "tch": "tʃ", "dge": "dʒ",
    "sch": "sch", "ch": "ch", "sh": "ʃ", "th": "th", "ph": "f",
    "wh": "wh", "gh": "gh", "ck": "k", "kn": "kn", "wr": "wr",
    "rh": "r", "ng": "ŋ", "nk": "nk", "qu": "qu", "mb": "mb", "ps": "p",
    "ll": "ll", "rr": "rr", "ss": "ss", "tt": "tt", "dd": "dd", "pp": "pp",
    "bb": "bb", "gg": "gg", "mm": "mm", "nn": "nn", "ff": "ff", "zz": "zz",
    "cc": "cc",
    "ee": "ee", "ea": "ea", "ai": "ai", "ay": "ay", "oa": "oa", "ey": "ey",
    "oo": "uː", "ou": "ou", "ow": "ow", "oi": "ɔɪ", "oy": "ɔɪ",
    "au": "au", "aw": "aw", "ew": "juː", "ui": "ui", "ue": "ue",
    "oe": "oe", "ie": "ie", "ei": "iː", "eu": "juː", "eo": "eo",
    "ia": "ia", "io": "io",
}
_R_PAIRS = ("ar", "er", "ir", "or", "ur")
_DOUBLE_TOKS = ("ll", "rr", "ss", "tt", "dd", "pp", "bb", "gg", "mm",
                "nn", "ff", "zz", "cc")


def segment(word: str) -> list[str]:
    """Grapheme tokens; word boundaries '|' (join) and '| ' (space)."""
    low = word.lower()
    out: list[str] = []
    i = 0
    n = len(low)
    while i < n:
        c = low[i]
        if c == " ":
            out.append("| ")
            i += 1
            continue
        if c in ("-", "'"):
            out.append("|")
            i += 1
            continue
        chunk = low[i:i + 4]
        if chunk[:4] in _MULTI or chunk[:4] in _R_PAIRS:
            tok = chunk[:4]
        elif chunk[:3] in _MULTI or chunk[:3] in _R_PAIRS:
            tok = chunk[:3]
        elif chunk[:2] in _MULTI or chunk[:2] in _R_PAIRS:
            tok = chunk[:2]
        elif c.isalpha():
            out.append(c)
            i += 1
            continue
        else:
            raise ValueError(f"unmappable grapheme {c!r} in {word!r}")
        out.append(tok)
        i += len(tok)
    return out


# --- phoneme resolution ----------------------------------------------------

def _tok_is_vowelish(t: str) -> bool:
    return (t in _VOWELISH or t in _VOWEL_LETTERS or t == "y"
            or t in _PAL or t[:1] in _PAL
            or t in ("qu", "wh", "w", "sch", "ia", "iA", "io", "ie", "oo", "ew",
                     "igh", "eigh", "ai", "ay", "ea", "ee", "oa", "ou",
                     "au", "aw", "ui", "ue", "oe", "eu", "eo"))


def _tok_is_cons(t: str) -> bool:
    if t in ("|", "| "):
        return True
    return not _tok_is_vowelish(t)


def _word_bounds(toks: list[str]) -> list[tuple[int, int]]:
    spans = []
    start = 0
    for i, t in enumerate(toks):
        if t in ("|", "| "):
            spans.append((start, i))
            start = i + 1
    spans.append((start, len(toks)))
    return spans


def _resolve_word(sub: list[str]) -> list[str]:
    joined = "".join(sub)
    # word-final suffix overrides (-턴/-퍼드/-버그/-셔/-엄)
    for suffix, repl in _SUFFIX_OVERRIDE.items():
        if joined.endswith(suffix) and len(joined) > len(suffix):
            tail = ""
            cut = 0
            ok = True
            for t in reversed(sub):
                tail = t + tail
                cut += 1
                if tail == suffix:
                    break
                if len(tail) > len(suffix):
                    ok = False
                    break
            if ok and cut:
                return _resolve_plain(sub[:len(sub) - cut]) + list(repl)
    return _resolve_plain(sub)


def _resolve_plain(sub: list[str]) -> list[str]:
    # silent word-final e: doubled/palatal clusters (ville/cambridge-type);
    # single-C cases go through the magic-e loop below
    if len(sub) >= 2 and sub[-1] == "e":
        prev = sub[-2]
        if (prev in _PAL or prev in ("mb", "kn", "qu") or prev in _DOUBLE_TOKS):
            sub = sub[:-1]
    out: list[str] = []
    n = len(sub)
    i = 0
    while i < n:
        tok = sub[i]
        nxt = sub[i + 1] if i + 1 < n else None
        nxt2 = sub[i + 2] if i + 2 < n else None
        prev = out[-1] if out else None
        if tok in _MAGIC and nxt and nxt in "bdfglkmnpsvz" \
                and nxt2 == "e" and i + 3 >= n:
            out.append(_MAGIC[tok])               # lake 레이크-type
            i += 3
            continue
        if tok in _MAGIC and nxt and nxt in "bdfglkmnpsvz" \
                and nxt2 == "e" and i + 3 == n - 1 and sub[n - 1] == "s":
            out.append(_MAGIC[tok])               # lakes 레이크스-type
            i += 4
            continue
        if tok in _MAGIC and nxt and nxt in "bdfglkmnpsvz" \
                and nxt2 == "l" and i + 3 == n - 1 and sub[n - 1] == "e":
            out.append(_MAGIC[tok])               # table 테이블-type
            i += 1
            continue
        if tok == "e" and i == n - 1:
            i += 1                                  # leftover silent e
            continue
        if tok in _VOWEL_LETTERS or tok == "y":
            out.append(_resolve_letter_vowel(tok, sub, i))
            i += 1
            continue
        if tok in ("ough", "augh"):
            raise ValueError(f"ambiguous {tok!r}")
        if tok in ("ea", "ai", "ay", "oa", "ou", "ow", "au", "aw", "ui",
                   "ue", "oe", "ie", "eu", "eo", "ee", "oo", "ew",
                   "igh", "eigh", "oi", "oy", "ei", "ey"):
            out.append(_resolve_digraph(tok, nxt, i, sub))
            i += 1
            continue
        if tok in ("ia", "io"):
            if tok == "io":
                out.extend(("aɪ", "ɔ"))               # 오하이오/아이오와
            else:
                out.append("iA")                          # 리아/니아-type
            i += 1
            continue
        if tok in _R_PAIRS:
            out.append(tok)
            i += 1
            continue
        if tok == "th":
            if prev in _SHORT and nxt == "e" and nxt2 is not None:
                out.append("ð")                        # 마더/브라더
            else:
                out.append("θ")
            i += 1
            continue
        if tok == "gh":
            if i == 0:
                out.append("g")                        # ghost 고스트
            elif prev is not None and (prev in _R_PAIRS or prev == "r"
                                       or (len(prev) == 1 and prev in "bcdfglmpvz")
                                       or prev in _PAL):
                pass                                   # burgh/ghost-type silent
            else:
                raise ValueError(f"gh after vowel")
            i += 1
            continue
        if tok == "kn":
            out.append("n" if i == 0 else "kn")        # 녹스 / mid k+n
            i += 1
            continue
        if tok == "wr":
            out.append("r" if i == 0 else "wr")
            i += 1
            continue
        if tok in ("ps", "rh"):
            out.append("p" if tok == "ps" else "r")
            i += 1
            continue
        if tok == "mb":
            out.append("mb")
            i += 1
            continue
        if tok in _DOUBLE_TOKS:
            out.append(tok)
            i += 1
            continue
        if tok in ("ck",):
            out.append("k")
            i += 1
            continue
        if tok in ("ng", "nk"):
            out.append(tok)
            i += 1
            continue
        if tok == "c":
            if nxt in ("e", "i", "y"):
                v = "ɪ" if nxt == "y" else \
                    _resolve_letter_vowel(nxt, sub, i + 1)
                out.append("s" + _render_vowel_key(v))    # city 시 (consume)
                i += 2
                continue
            out.append("k")
            i += 1
            continue
        if tok == "g":
            if nxt in ("e", "i"):
                hard = nxt2 is None or nxt2 in _VOWEL_LETTERS
                if hard:
                    out.append("g")
                    i += 1
                    continue
                v = _resolve_letter_vowel(nxt, sub, i + 1)
                out.append("dʒ" + _render_vowel_key(v))   # virginia 지
                i += 2
                continue
            out.append("g")
            i += 1
            continue
        if tok == "ch":
            if nxt == "i":
                out.append("ʃi")                       # 시카고/미시간 (consume i)
                i += 2
                continue
            if nxt in _VOWEL_LETTERS:
                v = _resolve_letter_vowel(nxt, sub, i + 1)
                out.append("tʃ" + _render_vowel_key(v))
                i += 2
                continue
            out.append("tʃ")
            i += 1
            continue
        if tok == "sh":
            if nxt in _VOWEL_LETTERS or nxt == "y":
                v = _resolve_letter_vowel(nxt, sub, i + 1) \
                    if nxt != "y" else "ɪ"
                out.append("ʃ" + _render_vowel_key(v))
                i += 2
                continue
            out.append("ʃ")
            i += 1
            continue
        if tok in ("tch", "dge"):
            # palatal onset consuming a following vowel letter stays bare;
            # word-final tch/dge -> 치/지 handled via ㅣ default in render
            out.append("tʃ" if tok == "tch" else "dʒ")
            i += 1
            continue
        if tok == "j":
            if nxt in _VOWEL_LETTERS:
                v = _resolve_letter_vowel(nxt, sub, i + 1)
                out.append("dʒ" + _render_vowel_key(v))   # jackson 잭
                i += 2
                continue
            out.append("dʒ")
            i += 1
            continue
        if tok == "s":
            if nxt in _VOWEL_LETTERS:
                v = _resolve_letter_vowel(nxt, sub, i + 1)
                out.append("s" + _render_vowel_key(v))    # city 시
                i += 2
                continue
            out.append("s")
            i += 1
            continue
        if tok == "ph":
            out.append("f")                                # randolph 돌프
            i += 1
            continue
        if tok == "wh" and nxt in _MAGIC and i + 3 <= n \
                and sub[i + 2] in "bdfglkmnpsvz" and sub[i + 2] != "r":
            out.extend(("wA", "ɪ"))                        # white 화이트
            if i + 4 == n and sub[i + 3] == "s":
                i += 4                                     # whites-type
            else:
                i += 3
            continue
        if tok == "w":
            if nxt == "e" and nxt2 == "y":
                out.extend(("w2", "ɪ"))               # wayne 웨인
                i += 3
                continue
            if nxt == "ey":
                out.extend(("w2", "ɪ"))               # wayne 웨인
                i += 2
                continue
            if nxt in ("eɪ", "aɪ", "ɔɪ"):
                out.extend(("w" + _render_vowel_key(nxt), "ɪ"))  # 웨인/와이
                i += 2
                continue
            if nxt in ("oo", "uː"):
                out.append("wv")                      # wood 우드
                i += 2
                continue
            if nxt == "y":
                out.extend(("w4", "ɪ"))             # wyoming 와이+이
                i += 2
                continue
            if nxt in _VOWEL_LETTERS:
                if nxt2 is None:
                    out.append("w4")                      # 아이오와 word-final 와
                    i += 2
                    continue
                v = _resolve_letter_vowel(nxt, sub, i + 1)
                out.append("w" + _render_vowel_key(v))   # 하와이 와/워싱턴 워
                i += 2
                continue
            out.append("w")
            i += 1
            continue
        if tok == "y":
            if prev == "w":
                out.append("ɪ")            # wyoming 와이: y after w -> 이
                i += 1
                continue
            if nxt in _VOWEL_LETTERS:
                out.append("y" + _render_vowel_key(
                    _resolve_letter_vowel(nxt, sub, i + 1)))  # 옐로 여
                i += 2
                continue
            out.append("y")
            i += 1
            continue
        if tok == "qu":
            nxtv = nxt if nxt in _VOWEL_LETTERS else nxt
            out.append("qu")
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


def _render_vowel_key(v: str) -> str:
    """short key so compound palatal tokens survive the token channel"""
    return {"æ": "a", "ɛ": "e", "ɪ": "i", "ɑ": "A", "ɔ": "O", "ʊ": "u",
            "ə": "@", "ʌ": "U", "ɜː": "3", "ɔː": "6", "iː": "I", "uː": "v",
            "eɪ": "2", "aɪ": "4", "aʊ": "8", "juː": "7", "oʊ": "0"}.get(v, "i")


_PAL_KEY_JUNG = {
    "ʃ": {"a": "ㅑ", "A": "ㅑ", "e": "ㅕ", "i": "ㅣ", "I": "ㅣ",
          "O": "ㅛ", "6": "ㅛ", "u": "ㅜ", "v": "ㅜ", "@": "ㅓ", "U": "ㅓ",
          "2": "ㅔ", "4": "ㅣ", "8": "ㅐ", "0": "ㅛ"},
    "tʃ": {"a": "ㅐ", "A": "ㅏ", "e": "ㅔ", "i": "ㅣ", "I": "ㅣ",
           "O": "ㅗ", "6": "ㅗ", "u": "ㅜ", "v": "ㅜ", "@": "ㅓ", "U": "ㅓ",
           "2": "ㅔ", "4": "ㅣ", "8": "ㅘ", "0": "ㅗ"},
    "dʒ": {"a": "ㅐ", "A": "ㅏ", "e": "ㅔ", "i": "ㅣ", "I": "ㅣ",
           "O": "ㅗ", "6": "ㅗ", "u": "ㅜ", "v": "ㅜ", "@": "ㅓ", "U": "ㅓ",
           "2": "ㅔ", "4": "ㅣ", "8": "ㅘ", "0": "ㅗ"},
}


def _resolve_letter_vowel(v: str, sub: list[str], i: int) -> str:
    n = len(sub)
    nxt = sub[i + 1] if i + 1 < n else None
    nxt2 = sub[i + 2] if i + 2 < n else None
    # magic-e: V + single C + word-final e (+ optional s)
    if v in _MAGIC:
        if nxt and nxt in "bdfglkmnpsvz" and nxt2 == "e" and i + 3 >= n:
            return _MAGIC[v]
        if (nxt and nxt in "bdfglkmnpsvz" and nxt2 == "e"
                and i + 3 == n - 1 and sub[n - 1] == "s"):
            return _MAGIC[v]
    if v == "y":
        if nxt is None:
            mono = not any(_tok_is_vowelish(t) for t in sub[:i])
            return "aɪ" if (i <= 2 and mono) else "iː"
        if nxt in _VOWEL_LETTERS:
            return "ɪ"                           # wyoming 와이: glide y
        return "ɪ" if _tok_is_cons(nxt) else "y"
    closed = (nxt is not None and _tok_is_cons(nxt)
              and (nxt2 is None or _tok_is_cons(nxt2)
                   or (nxt2 == "y" and len(nxt) > 1)))
    if v == "u":
        if closed:
            return "ʌ"                          # 버튼
        return "uː" if nxt is None else "juː"   # 말리부 부 vs 유타 유
    if v == "a":
        if nxt == "ll":
            return "ɔ"                          # small 스몰/ball 볼
        if nxt == "l":
            return "ɑ"                          # 알래스카 알/말리부 말 (캘 lex)
        if nxt == "n":
            if nxt2 is None:
                return "ɑ"                      # 미시간 간 / 산시몬 산
            return "æ"                          # 맨/캔/샌
        if nxt == "m":
            if nxt2 is not None and (nxt2 in _VOWEL_LETTERS
                                     or _tok_is_vowelish(nxt2)):
                return "ɑ"                      # 새크라멘토 라멘-type
            return "æ"
        if closed:
            if nxt2 is not None and _tok_is_cons(nxt2):
                return "æ"                      # 애틀랜타 애 (t+l cluster)
            if i == 0:
                return "æ"                      # 캔자스 캔 / 백 잭 (ck)
            return "ɑ"                          # 캣-type ㅏ
        if i == 0:
            return "æ"                          # 애마릴로-type initial
        return "ɑ"                              # 네바다 바다
    if v == "e":
        return "ɛ"
    if v == "i":
        if i == 0 and not closed:
            return "aɪ"                         # 아이다호-type
        return "ɪ"
    if v == "o":
        return "ɔ"
    return v


def _resolve_digraph(tok: str, nxt: str | None, i: int,
                     sub: list[str]) -> str:
    if tok == "ow":
        return "oʊ" if nxt is None else "aʊ"     # low 로 vs town 타운
    if tok == "ie":
        return "ie"
    fixed = {"ea": "iː", "ee": "iː", "oo": "uː", "ai": "eɪ", "ay": "eɪ",
             "oa": "oʊ", "ou": "aʊ", "au": "ɔː", "aw": "ɔː", "ui": "uː",
             "ue": "juː", "oe": "oʊ", "eu": "juː", "eo": "ɔː", "ei": "iː",
             "ew": "juː", "igh": "aɪ", "eigh": "eɪ", "oi": "ɔɪ",
             "oy": "ɔɪ", "ei": "aɪ", "ey": "eɪ"}
    return fixed.get(tok, tok)


def phonemes(word: str) -> list[str]:
    """Graphemes -> phoneme tokens with context rules."""
    toks = segment(word)
    out: list[str] = []
    for s, e in _word_bounds(toks):
        out.extend(_resolve_word(toks[s:e]))
        if e < len(toks):
            out.append(toks[e])
    return out


# --- Hangul rendering ------------------------------------------------------

CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNGS = ["ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ", "ㅙ",
         "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ"]
CHO_IDX = {c: i for i, c in enumerate(CHO)}
# Unicode jong index (compound jong jamo fill the gaps — NOT cho+1)
JONG_IDX = {"": 0, "ㄱ": 1, "ㄲ": 2, "ㄴ": 4, "ㄷ": 7, "ㄹ": 8, "ㅁ": 16,
            "ㅂ": 17, "ㅄ": 18, "ㅅ": 19, "ㅆ": 20, "ㅇ": 21, "ㅈ": 22,
            "ㅊ": 23, "ㅋ": 24, "ㅌ": 25, "ㅍ": 26, "ㅎ": 27}

_W_JUNG = {"ɪ": "ㅟ", "iː": "ㅟ", "ɛ": "ㅞ", "eɪ": "ㅞ", "æ": "ㅘ",
           "ɑ": "ㅘ", "ɔ": "ㅜ", "ɔː": "ㅜ", "ʊ": "ㅜ", "uː": "ㅜ",
           "ə": "ㅝ", "ʌ": "ㅝ", "aɪ": "ㅘ", "y": "ㅘ"}
_VOW_JUNG = {"æ": "ㅐ", "ɛ": "ㅔ", "ɪ": "ㅣ", "ɑ": "ㅏ", "ɔ": "ㅗ",
             "ʊ": "ㅜ", "ə": "ㅓ", "ʌ": "ㅓ", "ɜː": "ㅓ", "ɔː": "ㅗ",
             "iː": "ㅣ", "uː": "ㅜ", "oʊ": "ㅗ"}
_R_JUNG = {"a": "ㅏ", "e": "ㅓ", "i": "ㅣ", "o": "ㅗ", "u": "ㅓ"}
_D_LONG = {"eɪ": ("ㅔ", "ㅣ"), "aɪ": ("ㅏ", "ㅣ"), "ɔɪ": ("ㅗ", "ㅣ"),
           "aʊ": ("ㅏ", "ㅜ")}
_ONSET = {"p": "ㅍ", "b": "ㅂ", "t": "ㅌ", "d": "ㄷ", "k": "ㅋ", "g": "ㄱ",
          "f": "ㅍ", "v": "ㅂ", "s": "ㅅ", "z": "ㅈ", "θ": "ㅅ", "ð": "ㄷ",
          "m": "ㅁ", "n": "ㄴ", "ŋ": "ㅇ", "h": "ㅎ", "l": "ㄹ", "r": "ㄹ"}
_FINAL = {"p": "ㅂ", "b": "ㅂ", "t": "ㅌ", "d": "ㄷ", "k": "ㄱ", "g": "ㄱ",
          "f": "ㅍ", "v": "ㅂ", "m": "ㅁ", "n": "ㄴ", "ŋ": "ㅇ", "l": "ㄹ",
          "r": "ㄹ"}
_JONGGYEONG = ("n", "m", "l", "ŋ")    # sonorant word-final -> jong
_DOUBLE_KEY = {"tt": "ㅌ", "dd": "ㄷ", "pp": "ㅍ", "bb": "ㅂ", "gg": "ㄱ",
               "mm": "ㅁ", "ff": "ㅍ", "zz": "ㅅ", "cc": "ㅋ"}
_S_KEY_JUNG = {"a": "ㅐ", "A": "ㅏ", "e": "ㅔ", "2": "ㅔ", "i": "ㅣ",
               "I": "ㅣ", "4": "ㅣ", "O": "ㅗ", "6": "ㅗ", "0": "ㅗ",
               "u": "ㅜ", "v": "ㅜ", "@": "ㅓ", "U": "ㅓ", "8": "ㅘ",
               "7": "ㅠ"}
# compound w/y glide keys (render_vowel_key encoding)
_WKEY_JUNG = {"a": "ㅘ", "A": "ㅝ", "4": "ㅘ", "@": "ㅝ", "U": "ㅝ",
              "e": "ㅞ", "2": "ㅞ", "i": "ㅟ", "I": "ㅟ", "u": "ㅜ",
              "v": "ㅜ", "O": "ㅜ", "6": "ㅜ", "8": "ㅘ"}
_YKEY_JUNG = {"e": "ㅖ", "2": "ㅖ", "a": "ㅑ", "A": "ㅑ", "O": "ㅛ",
              "6": "ㅛ", "0": "ㅛ", "i": "ㅣ", "I": "ㅣ", "u": "ㅠ",
              "v": "ㅠ", "@": "ㅕ", "U": "ㅕ", "4": "ㅛ"}


def _compose(onset: str, jung: str, jong: str = "") -> str:
    return chr(0xAC00 + 21 * 28 * CHO_IDX[onset] + 28 * JUNGS.index(jung)
               + JONG_IDX[jong])


def _pending_of(tok: str | None) -> str | None:
    """Consonant token -> onset jamo it leaves as pending."""
    if tok is None or tok in ("|", "| "):
        return None
    if tok[:2] in _PAL or tok[:1] == "ʃ":
        return {"ʃ": "ㅅ", "tʃ": "ㅊ", "dʒ": "ㅈ"}["ʃ" if tok[0] == "ʃ"
                                                  else tok[:2]]
    if tok in ("qu", "wh"):
        return None
    if tok in ("w", "y") or tok[:1] in ("w", "y"):
        return None
    if tok in ("kn", "wr", "sch", "ts", "g~"):
        return None
    if tok in _DOUBLE_KEY:
        return _DOUBLE_KEY[tok]
    return _ONSET.get(tok)


def _attach_jong(units: list[list[str]], jong: str) -> bool:
    if units and units[-1][2] == "" and units[-1][1] != "|":
        units[-1][2] = jong
        return True
    return False


def _render(toks: list[str]) -> str:
    units: list[list[str]] = []
    pending: str | None = None
    long_prev = False
    n = len(toks)
    i = 0
    while i < n:
        t = toks[i]
        nxt = toks[i + 1] if i + 1 < n else None
        nxt2 = toks[i + 2] if i + 2 < n else None
        nxt3 = toks[i + 3] if i + 3 < n else None
        if t == "| ":
            pending = None                       # join words (로스앤젤레스-style)
            long_prev = False
            i += 1
            continue
        if t == "|":
            pending = None
            long_prev = False
            i += 1
            continue
        if t in _D_LONG:
            onset = pending or "ㅇ"
            pending = None
            j1, j2 = _D_LONG[t]
            units.append([onset, j1, ""])
            units.append(["ㅇ", j2, ""])
            long_prev = True
            i += 1
            continue
        if t in ("oʊ", "iː", "uː"):
            units.append([pending or "ㅇ", _VOW_JUNG[t], ""])
            pending = None
            long_prev = True
            i += 1
            continue
        if t == "juː":
            units.append([pending or "ㅇ", "ㅠ", ""])
            pending = None
            long_prev = True
            i += 1
            continue
        if t in ("ia", "iA", "io", "ie"):
            onset = pending or "ㅇ"
            pending = None
            if t in ("ia", "iA"):
                units.append([onset, "ㅣ", ""])
                units.append(["ㅇ", "ㅐ" if t == "ia" else "ㅏ", ""])
            elif t == "io":
                units.append([onset, "ㅣ", ""])
                units.append(["ㅇ", "ㅗ", ""])
            else:                                    # ie -> ㅣ (long)
                units.append([onset, "ㅣ", ""])
                long_prev = True
            i += 1
            continue
        if t in _VOW_JUNG:
            units.append([pending or "ㅇ", _VOW_JUNG[t], ""])
            pending = None
            long_prev = False
            i += 1
            continue
        if t in ("ar", "er", "ir", "or", "ur"):
            base = t[0]
            onset = pending or "ㅇ"
            pending = None
            if nxt is None or nxt in ("|", "| "):
                # word-final: ar -> 아 (카), er/ir/or/ur -> 어 (디너/모터)
                units.append([onset, "ㅏ" if base == "a" else "ㅓ", ""])
            elif _tok_is_cons(nxt):
                cluster = nxt2 is not None and _tok_is_cons(nxt2) \
                    and nxt2 not in ("|", "| ")
                if base == "o":
                    if cluster:
                        units.append([onset, "ㅗ", ""])    # 스포츠: r silent
                        long_prev = False
                        i += 1
                        continue
                    if nxt in ("t", "d", "k", "g"):
                        units.append([onset, "ㅗ", ""])    # 포트/워크
                        long_prev = True
                        i += 1
                        continue
                    units.append([onset, "ㅗ", ""])        # 포니/노스-type
                    pending = _pending_of(nxt)
                elif base == "a":
                    units.append([onset, "ㅏ", "ㄹ"])       # 파크/찰스턴
                    pending = _pending_of(nxt)
                else:
                    units.append([onset, "ㅓ", ""])        # 버몬트/턴/서클
                    pending = _pending_of(nxt)
            else:
                if base == "a":
                    first = pending is None and \
                        (not units or units[-1][0] == "|")
                    jung = "ㅔ" if nxt in ("ɔ", "oʊ", "oa", "o") else \
                        ("ㅐ" if first else "ㅏ")
                else:
                    jung = "ㅗ" if base == "o" else "ㅓ"   # 콜로라도 로+라
                units.append([onset, jung, ""])
                pending = "ㄹ"
            long_prev = False
            i += 1
            continue
        if t[:2] in _PAL or (t[:1] in ("ʃ",) ):
            sym = "ʃ" if t[0] == "ʃ" else t[:2]
            key = t[len(sym):]
            if sym == "ʃ" and key == "":
                if nxt is None or nxt in ("|", "| "):
                    units.append([pending or "ㅇ", "ㅣ", "ㅅ"])
                    pending = None
                    i += 1
                    continue
                if _tok_is_cons(nxt):
                    units.append([pending or "ㅅ", "ㅜ", "ㄹ"])  # ashland 슐
                    pending = _pending_of(nxt)
                    i += 1
                    continue
                key = "i"
            jung = _PAL_KEY_JUNG[sym].get(key, "ㅣ")
            onset = {"ʃ": "ㅅ", "tʃ": "ㅊ", "dʒ": "ㅈ"}[sym]
            if key == "" and nxt is not None and _tok_is_cons(nxt) \
                    and nxt not in ("|", "| "):
                units.append([pending or onset, "ㅡ", "ㄹ"])   # ashland 슐
                pending = _pending_of(nxt)
                i += 1
                continue
            units.append([pending or onset, jung, ""])
            pending = None
            i += 1
            continue
        if t[:1] == "s" and len(t) > 1 and t[1:] in _S_KEY_JUNG:
            units.append([pending or "ㅅ", _S_KEY_JUNG[t[1:]], ""])
            pending = None
            i += 1
            continue
        if t[:1] == "w" and len(t) > 1 and t[1:] in _WKEY_JUNG:
            units.append([pending or "ㅇ", _WKEY_JUNG[t[1:]], ""])
            pending = None
            i += 1
            continue
        if t[:1] == "y" and len(t) > 1 and t[1:] in _YKEY_JUNG:
            units.append([pending or "ㅇ", _YKEY_JUNG[t[1:]], ""])
            pending = None
            i += 1
            continue
        if t in ("qu", "wh", "w"):
            onset = {"qu": pending or "ㅇ", "wh": "ㅎ", "w": pending or "ㅇ"}[t]
            units.append([onset, _W_JUNG.get(nxt, "ㅜ"), ""])
            pending = None
            i += 1
            continue
        if t == "j":
            units.append([pending or "ㅈ", "ㅣ", ""])
            pending = None
            i += 1
            continue
        if t == "y":
            units.append(["ㅇ", "ㅖ" if nxt in ("ɛ", "e") else "ㅕ", ""])
            i += 1
            continue
        if t == "x":
            if not _attach_jong(units, "ㄱ"):
                units.append([pending or "ㅇ", "ㅡ", "ㄱ"])
            pending = "ㅅ" if nxt is not None and _tok_is_vowelish(nxt) \
                else None
            if pending is None:
                units.append(["ㅅ", "ㅡ", ""])       # 복스 separate 스
            long_prev = False
            i += 1
            continue
        if t == "mb":
            if not _attach_jong(units, "ㅁ"):
                units.append([pending or "ㅇ", "ㅡ", "ㅁ"])
            pending = None
            i += 1
            continue
        if t in ("ll", "rr"):
            # ㄹ jong + ㄹ onset double (캘리포니아/앨라배마/애틀랜타/밸리)
            if _attach_jong(units, "ㄹ"):
                pending = "ㄹ"
            else:
                pending = "ㄹ"
            i += 1
            continue
        if t in ("ng", "nk"):
            if not _attach_jong(units, "ㅇ"):
                units.append([pending or "ㅇ", "ㅡ", "ㅇ"])
            pending = "ㅋ" if t == "nk" else None
            i += 1
            continue
        if t in _DOUBLE_KEY:
            if nxt is not None and _tok_is_cons(nxt):
                if t in _DOUBLE_KEY and nxt == "l" and nxt2 is None:
                    units.append([_DOUBLE_KEY[t], "ㅡ", ""])   # 리틀 트
                    i += 1                                     # l -> jong below
                    continue
                if t == "tt" and nxt == "s":
                    units.append(["ㅊ", "ㅡ", ""])       # 피츠버그 츠
                    i += 2
                    continue
                if not _attach_jong(units, _DOUBLE_KEY[t]):
                    units.append([pending or _DOUBLE_KEY[t], "ㅡ", ""])
                pending = _pending_of(nxt)
            else:
                pending = _DOUBLE_KEY[t]
            i += 1
            continue
        if t == "nn":
            # e/i/u + nn -> onset only (테네시); a/o + nn -> jong+onset (한나)
            if units and units[-1][1] in ("ㅏ", "ㅗ", "ㅐ", "ㅘ", "ㅝ") \
                    and _attach_jong(units, "ㄴ"):
                pending = "ㄴ"
            else:
                pending = "ㄴ"
            i += 1
            continue
        if t == "ss":
            pending = "ㅅ"
            i += 1
            continue
        if t in ("kn", "wr"):
            if pending is not None:
                units.append([pending, "ㅡ", ""])
                pending = None
            units.append(["ㄱ" if t == "kn" else "ㄹ", "ㅡ", ""])
            pending = "ㄴ" if t == "kn" else "ㄹ"
            i += 1
            continue
        if t == "sch":
            if pending is not None:
                units.append([pending, "ㅡ", ""])
                pending = None
            units.append(["ㅅ", "ㅡ", ""])
            pending = "ㄱ"
            i += 1
            continue
        if t == "ts":
            units.append(["ㅊ", "ㅡ", ""])               # 스포츠/피츠버그 츠
            pending = None
            long_prev = False
            i += 1
            continue
        if t == "g~":
            units.append(["ㄱ", "ㅡ", ""])               # -버그 open 그
            pending = None
            long_prev = False
            i += 1
            continue
        if t == "ŋ":
            if not _attach_jong(units, "ㅇ"):
                units.append([pending or "ㅇ", "ㅡ", "ㅇ"])
            pending = None
            i += 1
            continue
        if t in _ONSET:
            jamo = _ONSET[t]
            bound = nxt is None or nxt in ("|", "| ")
            if bound:
                if t == "h":
                    i += 1                               # utah: silent h
                    continue
                if long_prev and t in ("t", "d", "k", "g"):
                    units.append([jamo, "ㅡ", ""])        # 비트/케이크/리그
                    long_prev = False
                elif long_prev and t in ("s", "z", "θ"):
                    units.append(["ㅈ" if t == "z" else "ㅅ", "ㅡ", ""])
                    long_prev = False                    # 레이스/퀴즈/사우스
                elif t in ("s", "z", "θ"):
                    units.append(["ㅈ" if t == "z" else "ㅅ", "ㅡ", ""])
                elif t in ("f", "v"):
                    units.append(["ㅍ" if t == "f" else "ㅂ", "ㅡ", ""])
                elif units and units[-1][2] != "":
                    units.append([jamo, "ㅡ", ""])         # after jong: open
                elif not _attach_jong(units, _FINAL.get(t, jamo)):
                    units.append([jamo, "ㅡ", ""])
                i += 1
                continue
            if nxt is not None and _tok_is_cons(nxt):
                vowelish2 = nxt2 is not None and nxt2 not in ("|", "| ") \
                    and _tok_is_vowelish(nxt2)
                eow = nxt2 is None or nxt2 in ("|", "| ")
                if t in ("θ", "ð") and nxt == "s" and not eow:
                    i += 1                                  # heath: th silent
                    continue
                if t == "d" and nxt == "s" and eow:
                    units.append(["ㅈ", "ㅡ", ""])          # 리즈-type 즈
                    i += 2
                    continue
                if t == "t" and nxt == "s" and eow:
                    units.append(["ㅊ", "ㅡ", ""])          # 츠
                    i += 2
                    continue
                if t == "d" and nxt == "s" and not eow:
                    units.append(["ㅈ", "ㅡ", ""])          # woodsville 즈
                    i += 2
                    continue
                if t == "t" and nxt == "s" and nxt2 is not None \
                        and _tok_is_vowelish(nxt2):
                    if not _attach_jong(units, "ㅅ"):       # watson 왓슨
                        units.append(["ㅌ", "ㅡ", "ㅅ"])
                    pending = "ㅅ"
                    i += 2
                    continue
                if t == "s" and nxt in ("t", "d", "k", "g", "p", "b", "f") \
                        and eow:
                    units.append(["ㅅ", "ㅡ", ""])          # 벨파스트 스
                    long_prev = True
                    i += 1
                    continue
                if t in ("t", "d") and nxt == "l" and eow:
                    i += 1                                  # castle: t silent
                    continue
                if nxt == "l" and eow and nxt2 is None:
                    units.append([jamo, "ㅡ", ""])           # table 블-type
                    i += 1
                    continue
                if t == "s" and nxt == "t" and nxt2 == "l" and \
                        (nxt3 is None or nxt3 in ("|", "| ")):
                    units.append(["ㅅ", "ㅡ", ""])           # 캐슬 스
                    i += 1                                   # t silent next
                    continue
                if t in ("s", "z", "f") and nxt not in ("|", "| "):
                    units.append([{"s": "ㅅ", "z": "ㅈ", "f": "ㅍ"}[t],
                                  "ㅡ", ""])               # 스/즈/프 fill
                    pending = None
                    i += 1
                    continue
                if t in ("n", "m", "l", "r"):
                    # sonorant: jong (덴버/파크/털사); l+V handled below
                    if not _attach_jong(units, _FINAL.get(t, jamo)):
                        units.append([jamo, "ㅡ", ""])
                    pending = _pending_of(nxt)
                elif vowelish2:
                    c2_jong = nxt in ("t", "d", "k", "g", "p", "b", "s") \
                        and t not in ("s", "z", "f")
                    if c2_jong:
                        _attach_jong(units, _FINAL.get(t, jamo))  # 빅/잭
                        pending = _pending_of(nxt)
                    else:
                        units.append([jamo, "ㅡ", ""])     # split: 스프링-type
                        pending = None
                else:
                    _attach_jong(units, _FINAL.get(t, jamo))
                    pending = _pending_of(nxt)
                i += 1
                continue
            if t == "l" and nxt is not None and _tok_is_vowelish(nxt):
                if pending is not None and pending != "ㄹ":
                    units.append([pending, "ㅡ", "ㄹ"])    # 클: k onset+ㄹ jong
                    pending = "ㄹ"
                elif _attach_jong(units, "ㄹ"):
                    pending = "ㄹ"                        # 캘+리 double
                else:
                    pending = "ㄹ"                        # 포틀랜드: l -> 랜 onset
                i += 1
                continue
            pending = jamo
            i += 1
            continue
        raise ValueError(f"render unresolved {t!r}")

    parts: list[str] = []
    for u in units:
        if u[0] == "|":
            parts.append(" ")
        else:
            parts.append(_compose(u[0], u[1], u[2]))
    return "".join(parts)


LEXICAL_EN_KO_FULL = {
    # 유명 불규칙形（lexicon+system 双轨，新华社模式）— 分歧已存档
    "london": "런던",           # o closed unstressed -> 런 (rules: 론던-type)
    "houston": "휴스턴",        # u closed but /hjuː/ long (rules: 허스턴)
    "dallas": "댈러스",         # ll double ㄹ tradition (vs 밸리 single)
    "miami": "마이애미",        # i+a -> 이+애 (rules: 미아미)
    "los angeles": "로스앤젤레스",  # An stressed æ
    "san diego": "샌디에이고",   # ie -> 이에 (Spanish pronun)
    "francisco": "프란시스코",   # French loan an -> 안
    "las vegas": "라스베이거스", # unstressed a -> 거
    "seattle": "시애틀",        # ea+t-tl convention
    "fresno": "프레즈노",       # voiced s -> 즈
    "phoenix": "피닉스",        # oe -> 이
    "detroit": "디트로이트",    # unstressed e -> 디
    "virginia": "버지니아",     # ir + soft g: r silent
    "georgia": "조지아",        # geo -> 조
    "georgetown": "조지타운",
    "new york": "뉴욕",         # traditional (rules: 뉴요크)
    "york": "요크",             # yo + rk: r silent (rules: 욜크-type)
    "jersey": "저지",           # er + s: r silent (vs 버몬트 ㄹ)
    "kansas": "캔자스",         # /ˈkænzəz/ voiced s -> ㅈ (rules: 캔사스)
    "missouri": "미주리",       # ss+ou -> 주
    "louisiana": "루이지애나",   # si+a -> 지애
    "massachusetts": "매사추세츠",
    "connecticut": "코네티컷",
    "rhode island": "로드아일랜드",
    "hampshire": "햄프셔",
    "edinburgh": "에든버러",    # burgh irregular
    "reading": "레딩",          # /ˈrɛdɪŋ/
    "oregon": "오리건",         # unstressed e -> 리
    "swansea": "스완지",        # Welsh ㅘ (vs 워 rule)
    "north": "노스",            # r drop before th (vs 스포츠 ㄹ)
    "south": "사우스",
    "delaware": "델라웨어",     # aw+a(re) -> 웨어
    "maryland": "메릴랜드",     # ar+y -> 에+ㄹ
    "minneapolis": "미니애폴리스",
    "baltimore": "볼티모어",
    "buffalo": "버팔로",        # stressed u -> 버
    "albany": "올버니",         # /ˈɔːlbəni/
    "savannah": "사바나",
    "memphis": "멤피스",
    "toledo": "톨리도",
    "milwaukee": "밀워키",
    "syracuse": "시러큐스",
    "rochester": "로체스터",
    "wheeling": "휠링",
    "dayton": "데이턴",
    "akron": "아크런",
    "aberdeen": "애버딘",       # er + d: r silent (vs 버몬트 ㄹ)
    "annapolis": "애나폴리스",   # a+nna: jong dropped (vs 한나)
    "norfolk": "노퍽",          # or + f: r silent
    "nashville": "내슈빌",      # sh+ville -> 슈빌
    "oxford": "옥스퍼드",       # unstressed ford -> 퍼드
    "cambridge": "케임브리지",   # a+mb -> 에이 (rules: 캠)
    "birmingham": "버밍엄",     # ir+m: r silent (vs 버몬트 ㄹ)
    "cardiff": "카디프",        # ar+d: r silent (vs 파크 ㄹ)
    "san francisco": "샌프란시스코",
    "north carolina": "노스캐롤라이나",
    "south carolina": "사우스캐롤라이나",
    "north dakota": "노스다코타",
    "south dakota": "사우스다코타",
    "isle of wight": "아일오브와이트",
    "wight": "와이트",
    "el paso": "엘파소",
    "san jose": "산호세",
    "santa fe": "산타페",
    "santa clara": "산타클라라",
    "san antonio": "산안토니오",
    "des moines": "데모인",
    "illinois": "일리노이",
    "la salle": "라살",
    "boise": "보이시",
    "notre dame": "노터데임",
    "baton rouge": "배턴루지",
    "appalachia": "애팔래치아",
    "the dalles": "더달스",
    "worcester": "우스터",
    "leicester": "레스터",
    "new hampshire": "뉴햄프셔",
    "pennsylvania": "펜실베이니아",  # -vania: n invisible in 베이니아
    "new jersey": "뉴저지",
    "salt lake city": "솔트레이크시티",
    "havana": "아바나",          # initial open a -> 아 (vs 애마릴로)
    "wichita": "위치타",        # ch+i -> 치 (tʃ, vs 시카고 ʃ)
    "san juan": "산후안",       # Spanish j -> ㅎ
    "jackson": "잭슨",          # rules give 잭손-type? kept frozen
    "jefferson": "제퍼슨",
    "great": "그레이트",        # ea -> eɪ (vs beat 비트)
    "california": "캘리포니아",  # a+l: 캘 ㅐ exception (rules: 칼 ㅏ)
    "carolina": "캐롤라이나",   # l+i -> 라이 (vs 캘리 single)
    "burleigh": "버리",         # ur+l: ㄹ onset only
    "indiana": "인디애나",      # dia -> 디애 (vs 마리아 리아 default)
    "clarksburg": "클락스버그",  # ar+stop: r silent (vs 파크)
    "clark": "클라크",
    "whitesboro": "휘츠보로",   # white short i
    "broad": "브로드",          # oa + silent a
    "broadway": "브로드웨이",
    "alabama": "앨라배마",      # bama a -> 배 ㅐ (vs 새크라멘토 라 ㅏ)
    "belfast": "벨파스트",      # fast a -> 파 ㅏ (vs 캔자스 캔 ㅐ)
}




# --- katakana renderer (Hepburn conventions) -------------------------------

_JA_VOW = {"æ": "ア", "ɛ": "エ", "ɪ": "イ", "ɑ": "ア", "ʌ": "ア",
           "ə": "ア", "ɔ": "オ", "ʊ": "ウ", "iː": "イー", "uː": "ウー",
           "ɔː": "オー", "oʊ": "オー", "ɜː": "アー", "eɪ": "エイ",
           "aɪ": "アイ", "ɔɪ": "オイ", "aʊ": "アウ", "juː": "ユー"}

_JA_ONSET = {"p": "パ", "b": "バ", "t": "タ", "d": "ダ", "k": "カ",
             "g": "ガ", "s": "サ", "z": "ザ", "θ": "サ", "ð": "ザ",
             "m": "マ", "n": "ナ", "h": "ハ", "l": "ラ", "r": "ラ",
             "f": "フ", "v": "バ"}

_JA_UFORM = {"p": "プ", "b": "ブ", "t": "ト", "d": "ド", "k": "ク",
             "g": "グ", "s": "ス", "z": "ズ", "θ": "ス", "ð": "ザ",
             "m": "ム", "n": "ン", "ŋ": "ン", "h": "フ", "f": "フ",
             "v": "ブ", "l": "ル", "r": "ル"}
_JA_FINAL = {"p": "プ", "b": "ブ", "t": "ト", "d": "ド", "k": "ク",
             "g": "グ", "s": "ス", "z": "ズ", "θ": "ス", "ð": "ズ",
             "m": "ン", "n": "ン", "ŋ": "ング", "h": "", "f": "フ",
             "v": "ブ", "l": "ル", "r": "アー", "j": "ジュ"}

_JA_W = {"a": "ワ", "æ": "ワ", "ɑ": "ワ", "ʌ": "ワ", "ə": "ワ",
         "ɛ": "ウェ", "ɪ": "ウィ", "iː": "ウィ", "ɔ": "ウォ",
         "ɔː": "ウォー", "ʊ": "ウ", "uː": "ウー", "oʊ": "ウォー",
         "aɪ": "ワイ", "aʊ": "ワウ"}

_JA_SH = {"ʃ": ["シャ", "シ", "シュ", "シェ", "ショ"],
          "tʃ": ["チャ", "チ", "チュ", "チェ", "チョ"],
          "dʒ": ["ジャ", "ジ", "ジュ", "ジェ", "ジョ"]}
_JA_SH_KEY = {
    "ʃ": {"a": "シャ", "A": "シャ", "U": "シャ", "@": "シャ", "e": "シェ",
          "2": "シェイ", "i": "シ", "I": "シー", "4": "シャイ",
          "u": "シュ", "v": "シュー", "7": "シュー", "O": "ショ",
          "6": "ショー", "0": "ショー", "8": "シャウ", "3": "シャー"},
    "tʃ": {"a": "チャ", "A": "チャ", "U": "チャ", "@": "チャ", "e": "チェ",
           "2": "チェイ", "i": "チ", "I": "チー", "4": "チャイ",
           "u": "チュ", "v": "チュー", "7": "チュー", "O": "チョ",
           "6": "チョー", "0": "チョー", "8": "チャウ", "3": "チャー"},
    "dʒ": {"a": "ジャ", "A": "ジャ", "U": "ジャ", "@": "ジャ", "e": "ジェ",
           "2": "ジェイ", "i": "ジ", "I": "ジー", "4": "ジャイ",
           "u": "ジュ", "v": "ジュー", "7": "ジュー", "O": "ジョ",
           "6": "ジョー", "0": "ジョー", "8": "ジャウ", "3": "ジャー"}}


def _ja_vowel_kana(t: str) -> str:
    if t in _JA_VOW:
        return _JA_VOW[t]
    return {"ia": "イア", "iA": "イア", "io": "イオ", "ie": "イー",
            "ea": "イー", "ee": "イー", "ai": "エイ", "ay": "エイ",
            "oa": "オー", "ou": "アウ", "au": "オー", "aw": "オー",
            "ui": "ウー", "ue": "ユー", "oe": "オー", "eu": "ユー",
            "eo": "オー", "ei": "アイ", "ey": "エイ", "oo": "ウー",
            "ew": "ユー", "igh": "アイ", "eigh": "エイ", "oi": "オイ",
            "oy": "オイ"}.get(t, "ー")


def _ja_pal(sym: str, nxt: str | None) -> str:
    row = _JA_SH[sym]
    idx = _JA_SH_IDX.get(nxt or "", 1)
    return row[idx]


_JA_COLS = {
    #            A     I     U     E     O
    "k": ("カ", "キ", "ク", "ケ", "コ"), "g": ("ガ", "ギ", "グ", "ゲ", "ゴ"),
    "s": ("サ", "シ", "ス", "セ", "ソ"), "z": ("ザ", "ジ", "ズ", "ゼ", "ゾ"),
    "t": ("タ", "チ", "ツ", "テ", "ト"), "d": ("ダ", "ジ", "ズ", "デ", "ド"),
    "n": ("ナ", "ニ", "ヌ", "ネ", "ノ"), "h": ("ハ", "ヒ", "フ", "ヘ", "ホ"),
    "b": ("バ", "ビ", "ブ", "ベ", "ボ"), "p": ("パ", "ピ", "プ", "ペ", "ポ"),
    "m": ("マ", "ミ", "ム", "メ", "モ"), "l": ("ラ", "リ", "ル", "レ", "ロ"),
    "r": ("ラ", "リ", "ル", "レ", "ロ"), "f": ("ファ", "フィ", "フ", "フェ", "フォ"),
    "v": ("バ", "ビ", "ブ", "ベ", "ボ"), "θ": ("サ", "シ", "ス", "セ", "ソ"),
    "ð": ("ザ", "ジ", "ズ", "ゼ", "ゾ"), "ʃ": ("シャ", "シ", "シュ", "シェ", "ショ"),
    "tʃ": ("チャ", "チ", "チュ", "チェ", "チョ"),
    "dʒ": ("ジャ", "ジ", "ジュ", "ジェ", "ジョ"),
}
# column selector per phoneme vowel token
_JA_COLIDX = {"a": 0, "æ": 0, "ɑ": 0, "ʌ": 0, "ə": 4, "i": 1, "ɪ": 1,
              "u": 2, "ʊ": 2, "e": 3, "ɛ": 3, "o": 4, "ɔ": 4}
_JA_LONG = {"iː": (1, "ー"), "uː": (2, "ー"), "oʊ": (4, "ー"),
            "ɔː": (4, "ー"), "ɜː": (0, "ー"), "oa": (4, "ー"),
            "au": (4, "ー"), "aw": (4, "ー"), "eo": (4, "ー"),
            "ee": (1, "ー"), "ea": (1, "ー"), "oo": (2, "ー")}
_JA_DIPH = {"eɪ": (3, "イ"), "ai": (3, "イ"), "ay": (3, "イ"),
            "aɪ": (0, "イ"), "ɔɪ": (4, "イ"), "oi": (4, "イ"),
            "oy": (4, "イ"), "aʊ": (0, "ウ"), "ou": (0, "ウ"),
            "ei": (0, "イ"), "igh": (0, "イ"), "eigh": (3, "イ"),
            "ey": (3, "イ"), "ow": (4, "ー"), "ui": (2, "ー"),
            "ue": (2, "ー"), "eu": (2, "ー"), "ew": (2, "ー")}
_JA_JU = {"k": "キュー", "g": "ギュー", "s": "スー", "z": "ズー",
          "t": "チュー", "d": "デュー", "n": "ニュー", "h": "ヒュー",
          "m": "ミュー", "l": "リュー", "r": "リュー", "b": "ビュー",
          "p": "ピュー", "f": "フュー", "v": "ビュー", "θ": "スー",
          "ð": "ズー", "ʃ": "シュー", "tʃ": "チュー", "dʒ": "ジュー"}
_JA_KEY = {"a": "æ", "A": "ɑ", "e": "ɛ", "i": "ɪ", "I": "iː", "O": "ɔ",
           "u": "ʊ", "U": "ʌ", "@": "ə", "3": "ɜː", "6": "ɔː", "2": "eɪ",
           "4": "aɪ", "8": "aʊ", "0": "oʊ", "7": "juː", "v": "uː"}
_JA_WKEY = {"a": "ワ", "A": "ワ", "4": "ワ", "@": "ワ", "U": "ワ",
            "e": "ウェ", "2": "ウェ", "i": "ウィ", "I": "ウィ",
            "u": "ウ", "v": "ウ", "O": "ウォ", "6": "ウォー",
            "0": "ウォー", "8": "ワウ", "7": "ウ"}
_JA_WH_VOW = {"a": "ワ", "æ": "ワ", "ɑ": "ワ", "ʌ": "ワ", "ə": "ワ",
              "i": "イ", "ɪ": "イ", "iː": "イー", "e": "エー", "ɛ": "エー",
              "eɪ": "エー", "o": "ウォ", "ɔ": "ウォ", "oʊ": "ウォー",
              "u": "ウ", "ʊ": "ウ", "aɪ": "ワイ", "aʊ": "ウ",
              "ʌ ": "ワ"}


def _ja_flush(p: str | None) -> str:
    """pending consonant key -> kana prefix (consonant-branch prepends)"""
    if p is None:
        return ""
    if p in _JA_COLS:
        return _JA_UFORM[p]
    if p == "l":
        return "ル"
    if p == "wh":
        return "ホ"
    return ""


def _ja_cv(cons: str | None, t: str) -> str:
    """consonant key + vowel token -> katakana"""
    if cons is None:
        stand = {"a": "ア", "æ": "ア", "ɑ": "ア", "ʌ": "ア", "ə": "ア",
                 "i": "イ", "ɪ": "イ", "u": "ウ", "ʊ": "ウ", "e": "エ",
                 "ɛ": "エ", "o": "オ", "ɔ": "オ"}
        if t in stand:
            return stand[t]
        if t in _JA_LONG:
            col, tail = _JA_LONG[t]
            return ("アイウエオ"[col] if col < 5 else "") + tail
        if t in _JA_DIPH:
            col, tail = _JA_DIPH[t]
            return "アイウエオ"[col] + tail
        if t in ("ia", "iA"):
            return "イア"
        if t == "io":
            return "イオ"
        if t == "ie":
            return "イー"
        if t == "juː":
            return "ユー"
        return "ー"
    if t == "juː":
        return _JA_JU.get(cons, cons + "ュー")
    if t in ("i", "ɪ") and cons in ("t", "d"):
        return "ティ" if cons == "t" else "ディ"
    if t in ("eɪ", "ai", "ay", "ey") and cons in ("t", "d"):
        return ("テイ" if cons == "t" else "デイ")
    if t in _JA_LONG:
        col, tail = _JA_LONG[t]
        return _JA_COLS[cons][col] + tail
    if t in _JA_DIPH:
        col, tail = _JA_DIPH[t]
        return _JA_COLS[cons][col] + tail
    col = _JA_COLIDX.get(t, 0)
    return _JA_COLS[cons][col]


def transcribe_en_ja(word: str) -> str:
    """English -> katakana (Hepburn, ja-Wikipedia place-name conventions)."""
    text = word.strip().replace("St. ", "Saint ")
    key = text.lower()
    if key in LEXICAL_EN_JA_FULL:
        return LEXICAL_EN_JA_FULL[key]
    toks = phonemes(text)
    out: list[str] = []
    pending: str | None = None        # consonant key | "wh" | "y"
    n = len(toks)
    i = 0
    while i < n:
        t = toks[i]
        if len(t) > 1 and t[0] in ("s", "z") and t[1:] in _JA_KEY:
            out.append(_ja_cv(t[0], _JA_KEY[t[1:]]))   # city シ/ザ compounds
            pending = None
            i += 1
            continue
        nxt = toks[i + 1] if i + 1 < n else None
        nxt2 = toks[i + 2] if i + 2 < n else None
        nxt3 = toks[i + 3] if i + 3 < n else None
        if t in ("|", "| "):
            pending = None
            i += 1
            continue
        # r-coloured vowels
        if t in ("ar", "er", "ir", "or", "ur"):
            cons = "h" if pending == "wh" else pending
            pending = None
            if nxt is None or nxt in ("|", "| "):
                out.append(("ホ" if cons == "h" and pending != "wh" else "")
                           + _ja_cv(None if cons == "h" else cons, "ɜː"))
            elif _tok_is_cons(nxt):
                out.append(_ja_cv(cons, "ɔː" if t[0] == "o" else "ɜː"))
            else:
                # florida フロリダ / arizona アリゾナ: short オ/ア
                out.append(_ja_cv(cons, "ɔ" if t[0] == "o" else "ɑ"))
                pending = "l"                          # r -> next onset
            i += 1
            continue
        if t in ("ia", "iA"):
            out.append(_ja_cv(pending, "i"))
            out.append("ア")                           # マイアミ/リア
            pending = None
            i += 1
            continue
        if t == "io":
            out.append(_ja_cv(pending, "i"))
            out.append("オ")                           # オハイオ ハイオ
            pending = None
            i += 1
            continue
        if t == "ie":
            out.append(_ja_cv(pending, "iː"))
            pending = None
            i += 1
            continue
        # plain vowels / digraphs
        vowel = _ja_vowel_kana(t)
        if vowel != "ー" or t in ("ea", "ee", "oo", "ai", "ay", "oa", "ou",
                                  "au", "aw", "ui", "ue", "oe", "eu", "eo",
                                  "ei", "ey", "igh", "eigh", "oi", "oy"):
            if t == "juː" and pending is None and nxt is not None \
                    and nxt not in ("|", "| ") and _tok_is_cons(nxt):
                out.append("ユ")                       # utah ユタ
                pending = None
                i += 1
                continue
            if pending == "wh":
                out.append("ホ" + _JA_WH_VOW.get(t, "ワ"))
                pending = None
            elif t in ("ʃ", "tʃ", "dʒ"):
                pass
            else:
                out.append(_ja_cv(pending, t))
            pending = None
            i += 1
            continue
        # consonants
        sym = ("tʃ" if t[:2] == "tʃ"
               else "ʃ" if t[:1] == "ʃ"
               else "dʒ" if t[:2] == "dʒ" else None)
        if sym is not None:
            key2 = t[len(sym):]
            if key2 == "" and (nxt is None or nxt in ("|", "| ")):
                out.append(_ja_flush(pending) + _JA_COLS[sym][1])
                pending = None
            elif key2 == "" and nxt is not None and _tok_is_cons(nxt):
                out.append(_ja_flush(pending) + _JA_COLS[sym][2])  # シュ-type
                pending = nxt
            else:
                out.append(_ja_flush(pending) + _ja_cv(sym, key2 or "i"))
            pending = None
            i += 1
            continue
        if t == "wh":
            pending = "wh"
            i += 1
            continue
        if t[:1] == "w" and t[1:] in _JA_WKEY:
            out.append(_ja_flush(pending) + _JA_WKEY[t[1:]])
            pending = None
            i += 1
            continue
        if t == "w":
            out.append(_ja_flush(pending) + _JA_W.get(nxt, "ウ"))
            pending = None
            i += 1
            continue
        if t == "y":
            if pending in ("t", "d"):
                out.append(_ja_cv(pending, "i"))        # city シティ
                pending = None
                i += 1
                continue
            if pending in ("k", "g"):
                out.append(_ja_cv(pending, "i") + "ー")  # ケンタッキー型
                pending = None
                i += 1
                continue
            if nxt in ("or", "ɔ", "ɔː", "oʊ") or nxt is None:
                out.append(_ja_flush(pending) + "イー" if nxt is None
                           and pending not in (None, "t", "d", "k", "g")
                           else _ja_flush(pending) + ("ヨー" if nxt in ("or", "ɔ", "ɔː", "oʊ") else "イー"))
                pending = None
                i += 1
                continue
            yv = {"ɛ": "イエ", "e": "イエ", "ɪ": "イ", "i": "イ",
                  "ʊ": "ユ", "uː": "ユー"}.get(nxt, "ヤ")
            out.append(_ja_flush(pending) + yv)
            pending = None
            i += 1
            continue
        if t == "x":
            out.append(_ja_flush(pending) + ("ックス" if out and out[-1]
                                          and out[-1][-1] in "アイウエオー"
                                          else "クス"))
            pending = None
            i += 1
            continue
        if t == "mb":
            out.append(_ja_flush(pending) + "ン")
            pending = None
            i += 1
            continue
        if t in ("ll", "rr"):
            if nxt is None or nxt in ("|", "| "):
                out.append(_ja_flush(pending) + "ル")   # ville ル
                pending = None
            else:
                pending = "l"
            i += 1
            continue
        if t in ("ng", "ŋ"):
            if nxt == "t" and nxt2 in ("ə", "ʌ", "ɑ") \
                    and nxt3 == "n":
                out.append(_ja_flush(pending) + "ン")     # ウェリントン
            else:
                out.append(_ja_flush(pending) + "ング")   # スプリング/キング
            pending = None
            i += 1
            continue
        if t == "nk":
            out.append(_ja_flush(pending) + "ン")
            pending = "k"
            i += 1
            continue
        if t in _DOUBLE_KEY:
            base = {"tt": "t", "dd": "d", "pp": "p", "bb": "b", "gg": "g",
                    "mm": "m", "ff": "f", "zz": "z", "cc": "k"}[t]
            if nxt is not None and _tok_is_cons(nxt):
                if t == "tt" and nxt == "s":
                    out.append(_ja_flush(pending) + "ッツ")  # ピッツバーグ
                    pending = None
                    i += 1
                    continue
                out.append(_ja_flush(pending) + _JA_UFORM[base])
                pending = None
            elif nxt is None or nxt in ("|", "| "):
                out.append(_ja_flush(pending) + _JA_UFORM[base])  # カーディフ
                pending = None
            else:
                if t in ("pp", "bb", "kk", "gg", "mm", "ff"):
                    out.append(_ja_flush(pending) + "ッ")    # アップル
                pending = base
            i += 1
            continue
        if t in ("nn", "ss"):
            pending = "n" if t == "nn" else "s"
            i += 1
            continue
        if t in ("kn", "wr", "sch"):
            out.append(_ja_flush(pending) +
                       {"kn": "ノ", "wr": "ル", "sch": "ス"}[t])
            pending = {"kn": "k", "wr": None, "sch": "s"}[t]
            i += 1
            continue
        if t == "ts":
            out.append("ツ")
            pending = None
            i += 1
            continue
        if t == "d" and nxt == "s":
            out.append(_ja_flush(pending) + "ズ")
            pending = None
            i += 2
            continue
        if t == "g~":
            out.append("ーバーグ"[:1] + "グ")           # ピッツバーグ(ー merge)
            pending = None
            i += 1
            continue
        if t in _JA_COLS:
            bound = nxt is None or nxt in ("|", "| ")
            if bound:
                out.append(_ja_flush(pending) + _JA_FINAL[t])
                pending = None
            elif nxt is not None and _tok_is_cons(nxt):
                out.append(_ja_flush(pending) + _JA_UFORM[t])
                pending = None
            else:
                pending = t
            i += 1
            continue
        if t == "juː":
            if pending is None and nxt is not None \
                    and nxt not in ("|", "| ") and _tok_is_cons(nxt):
                out.append("ユ")                       # utah ユタ
            else:
                out.append(_ja_cv(pending, "juː"))
            pending = None
            i += 1
            continue
        raise ValueError(f"ja render unresolved {t!r}")

    return "".join(out)

LEXICAL_EN_JA_FULL = {
    # 有名不規則形（lexicon+system 双轨）
    "miami": "マイアミ",        # maɪ split (rules: ミアミ)
    "los angeles": "ロサンゼルス",
    "new york": "ニューヨーク",
    "cambridge": "ケンブリッジ",
    "edinburgh": "エディンバラ",
    "liverpool": "リヴァプール",
    "georgia": "ジョージア",
    "georgetown": "ジョージタウン",
    "seattle": "シアトル",
    "phoenix": "フェニックス",
    "connecticut": "コネチカット",
    "massachusetts": "マサチューセッツ",
    "arkansas": "アーカンソー",
    "illinois": "イリノイ",
    "missouri": "ミズーリ",
    "louisiana": "ルイジアナ",
    "new jersey": "ニュージャージー",
    "carolina": "カロライナ",
    "north carolina": "ノースカロライナ",
    "south carolina": "サウスカロライナ",
    "north dakota": "ノースダコタ",
    "south dakota": "サウスダコタ",
    "san francisco": "サンフランシスコ",
    "san diego": "サンディエゴ",
    "las vegas": "ラスベガス",
    "dallas": "ダラス",
    "london": "ロンドン",
    "york": "ヨーク",
    "oxford": "オックスフォード",
    "syracuse": "シラキュース",
    "rochester": "ロチェスター",
    "minneapolis": "ミネアポリス",
    "baltimore": "ボルチモア",
    "buffalo": "バッファロー",
    "albany": "オールバニー",
    "savannah": "サバンナ",
    "memphis": "メンフィス",
    "toledo": "トレド",
    "milwaukee": "ミルウォーキー",
    "dayton": "デイトン",
    "akron": "アクロン",
    "aberdeen": "アバディーン",
    "annapolis": "アナポリス",
    "norfolk": "ノーフォーク",
    "nashville": "ナッシュビル",
    "oxford": "オックスフォード",
    "worcester": "ウースター",
    "leicester": "レスター",
    "new hampshire": "ニューハンプシャー",
    "pennsylvania": "ペンシルベニア",
    "salt lake city": "ソルトレイクシティ",
    "havana": "ハバナ",
    "wichita": "ウィチタ",
    "great": "グレート",
    "broad": "ブロード",
    "broadway": "ブロードウェイ",
    "whitesboro": "ホワイツボロ",
    "clarksburg": "クラークスバーグ",
    "clark": "クラーク",
    "reading": "レディング",
    "oregon": "オレゴン",
    "swansea": "スウォンジー",
    "north": "ノース",
    "south": "サウス",
    "delaware": "デラウェア",
    "maryland": "メリーランド",
    "des moines": "デモイン",
    "la salle": "ラサール",
    "boise": "ボイシ",
    "baton rouge": "バトンルージュ",
    "appalachia": "アパラチア",
    "worcester": "ウースター",
    "fresno": "フレズノ",
    "san jose": "サンノゼ",
    "santa fe": "サンタフェ",
    "santa clara": "サンタクララ",
    "san antonio": "サンアントニオ",
    "el paso": "エルパソ",
    "notre dame": "ノートルダム",
    "the dalles": "ザダルス",
    "houston": "ヒューストン",
    "texas": "テキサス",
    "kansas": "カンザス",
    "knox": "ノックス",
    "valley": "バレー",
    "nottingham": "ノッティンガム",
    "birmingham": "バーミンガム",
    "washington": "ワシントン",
    "arlington": "アーリントン",
    "lexington": "レキシントン",
    "pittsburgh": "ピッツバーグ",
    "cleveland": "クリーブランド",
    "hunt": "ハント",
    "jersey": "ジャージー",
    "virginia": "バージニア",
    "west virginia": "ウェストバージニア",
    "cambridge": "ケンブリッジ",
}

def transcribe_en_ko(word: str) -> str:
    """English -> Hangul per 공식 표기법 (lexical layer wins)."""
    text = word.strip().replace("St. ", "Saint ")
    key = text.lower()
    if key in LEXICAL_EN_KO_FULL:
        return LEXICAL_EN_KO_FULL[key]
    return _render(phonemes(text))


EN_KO_EVAL = {
    # system-rule anchors
    "chicago": "시카고", "boston": "보스턴", "denver": "덴버",
    "atlanta": "애틀랜타", "austin": "오스틴", "portland": "포틀랜드",
    "sacramento": "새크라멘토", "omaha": "오마하", "tulsa": "털사",
    "wichita": "위치타", "texas": "텍사스", "florida": "플로리다",
    "nevada": "네바다", "arizona": "애리조나", "alabama": "앨라배마",
    "idaho": "아이다호", "ohio": "오하이오", "utah": "유타", "maine": "메인",
    "vermont": "버몬트", "wyoming": "와이오밍", "michigan": "미시간",
    "iowa": "아이오와", "wisconsin": "위스콘신", "kentucky": "켄터키",
    "tennessee": "테네시", "mississippi": "미시시피", "indiana": "인디애나",
    "oklahoma": "오클라호마", "colorado": "콜로라도", "california": "캘리포니아",
    "montana": "몬태나", "canada": "캐나다", "manchester": "맨체스터",
    "liverpool": "리버풀", "leeds": "리즈", "bristol": "브리스톨",
    "brighton": "브라이턴", "cardiff": "카디프", "belfast": "벨파스트",
    "glasgow": "글래스고", "newcastle": "뉴캐슬", "nottingham": "노팅엄",
    "birmingham": "버밍엄", "wellington": "웰링턴",
    "springfield": "스프링필드", "pittsburgh": "피츠버그",
    # lexical-layer anchors (frozen forms)
    "london": "런던", "houston": "휴스턴", "dallas": "댈러스",
    "miami": "마이애미", "los angeles": "로스앤젤레스",
    "san diego": "샌디에이고", "las vegas": "라스베이거스",
    "seattle": "시애틀", "detroit": "디트로이트", "phoenix": "피닉스",
    "virginia": "버지니아", "georgia": "조지아", "new york": "뉴욕",
    "north carolina": "노스캐롤라이나", "west virginia": "웨스트버지니아",
    "new jersey": "뉴저지", "south dakota": "사우스다코타",
    "san francisco": "샌프란시스코", "york": "요크", "oxford": "옥스퍼드",
    "kansas": "캔자스",
}




EN_JA_EVAL = {
    "chicago": "シカゴ", "boston": "ボストン", "denver": "デンバー",
    "atlanta": "アトランタ", "austin": "オースティン",
    "portland": "ポートランド", "sacramento": "サクラメント",
    "omaha": "オマハ", "tulsa": "タルサ", "texas": "テキサス",
    "florida": "フロリダ", "nevada": "ネバダ", "arizona": "アリゾナ",
    "idaho": "アイダホ", "ohio": "オハイオ", "utah": "ユタ",
    "maine": "メイン", "vermont": "バーモント", "wyoming": "ワイオミング",
    "kansas": "カンザス", "michigan": "ミシガン", "minnesota": "ミネソタ",
    "iowa": "アイオワ", "wisconsin": "ウィスコンシン",
    "tennessee": "テネシー", "mississippi": "ミシシッピ",
    "oklahoma": "オクラホマ", "colorado": "コロラド", "montana": "モンタナ",
    "canada": "カナダ", "manchester": "マンチェスター", "leeds": "リーズ",
    "bristol": "ブリストル", "brighton": "ブライトン",
    "cardiff": "カーディフ", "belfast": "ベルファスト",
    "glasgow": "グラスゴー", "nottingham": "ノッティンガム",
    "birmingham": "バーミンガム", "wellington": "ウェリントン",
    "springfield": "スプリングフィールド", "pittsburgh": "ピッツバーグ",
    "washington": "ワシントン", "detroit": "デトロイト",
    "virginia": "バージニア", "dallas": "ダラス", "houston": "ヒューストン",
    "cleveland": "クリーブランド", "oregon": "オレゴン",
    # lexical anchors
    "london": "ロンドン", "miami": "マイアミ",
    "los angeles": "ロサンゼルス", "san diego": "サンディエゴ",
    "las vegas": "ラスベガス", "seattle": "シアトル",
    "phoenix": "フェニックス", "georgia": "ジョージア",
    "new york": "ニューヨーク", "new jersey": "ニュージャージー",
    "south dakota": "サウスダコタ", "san francisco": "サンフランシスコ",
    "york": "ヨーク", "oxford": "オックスフォード",
    "cambridge": "ケンブリッジ", "edinburgh": "エディンバラ",
    "liverpool": "リヴァプール",
}

def selfcheck() -> int:
    fails = 0
    for name, want in EN_KO_EVAL.items():
        got = transcribe_en_ko(name)
        if got != want:
            print(f"EN-KO EVAL FAIL {name!r}: got {got!r} want {want!r}")
            fails += 1
    print(f"en_ko anchors: {len(EN_KO_EVAL) - fails}/{len(EN_KO_EVAL)} pass")
    for name, want in EN_JA_EVAL.items():
        got = transcribe_en_ja(name)
        if got != want:
            print(f"EN-JA EVAL FAIL {name!r}: got {got!r} want {want!r}")
            fails += 1
    print(f"en_ja anchors: {len(EN_JA_EVAL) - fails}/{len(EN_JA_EVAL)} pass")
    return fails


if __name__ == "__main__":
    raise SystemExit(1 if selfcheck() else 0)
