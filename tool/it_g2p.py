#!/usr/bin/env python3
"""Italian g2p -> Hangul (ko) renderer for IT communes.

Fills the IT ko cells the upstream/Wikidata channels miss (315 as of round
36: communes + the 4 new Sardinian provinces).  Italian orthography is
near-phonemic, so the engine maps graphemes straight to syllable chunks
(no IPA intermediate):

ko  -- 국립국어원 「외래어 표기법」 제2장 이탈리아어 자모 + 제3장 이탈리아어
       표기 세칙.  Established conventions encoded:
       * 어중 l/r/m/n -> ㄹ/ㅁ/ㄴ batchim merge + plain onset (Milano
         밀라노 / Bologna 볼로냐 / Salerno 살레르노)
       * coda consonants -> batchim (Ancona 안코나 / Alba 알바)
       * c/g soft before e/i (체/치: Genova 제노바), hard elsewhere
         (카/가: Catania 카타니아); ch/gh = ㅋ/ㄱ
       * gn+V = 니+palatal V (냐/뇨/뉴: Bologna 볼로냐)
       * gli spelling = 리+V (famiglia-class); sc+e/i = 셰/시 (Brescia
         브레시아) but sch+e/i = 스케/스키 (Peschiera 페스키에라)
       * z = ts-class 치/체/차/초/추 (Vicenza 비첸차 / Venezia 베네치아);
         로렌조/라자냐 dz-forms are documented divergences
       * qu = 콰/쿠에 (Quarto 콰르토); gu+e/i = 구에
       * h silent; final vowels pronounced (Roma 로마)

Machine-candidate, eval-gated (selfcheck anchors), provisional; never
flips to approved.  Unknown graphemes raise ValueError -> the caller keeps
the cell honestly missing.
"""
from __future__ import annotations

import re

_VOWELS = "aeiouàèéìíòóùúy"
_CONS = "bcdfghjklmnpqrstvwz"

def segment(word: str) -> list[str]:
    """word -> chunk list: vowels are their own chunks, consonant digraphs
    (gn/gli/sc/ch/gh/qu/gu/sch) and single consonants are onset/coda chunks.
    Geminate doubles collapse first (Messina 메시나, Mammola 마몰라)."""
    text = re.sub(r"([bcdfglmpqrstvz])\1+", r"\1", word.lower())
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        nxt2 = text[i + 2] if i + 2 < n else ""
        if c in _VOWELS:
            out.append(c)
            i += 1
            continue
        if c in ("'", "-",):
            i += 1
            continue
        if c == "s" and nxt == "c" and nxt2 == "h":
            out.append("sch")
            i += 3
            continue
        if c == "g" and nxt == "l" and nxt2 == "i":
            out.append("gli")
            i += 3
            continue
        two = c + nxt
        if two in ("gn", "gl", "sc", "ch", "gh", "qu"):
            out.append(two)
            i += 2
            continue
        if c == "g" and nxt == "u" and nxt2 in _VOWELS:
            out.append("gu")
            i += 2
            continue
        if c in _CONS:
            out.append(c)
            i += 1
            continue
        raise ValueError(f"unhandled grapheme {c!r} in {word!r}")
    return out


_KO_V = {"a": "아", "e": "에", "è": "에", "é": "에", "i": "이", "ì": "이",
         "í": "이", "o": "오", "ò": "오", "ó": "오", "u": "우", "ù": "우",
         "ú": "우", "à": "아", "y": "이"}

_KO_CV = {
    "b": {"a": "바", "e": "베", "i": "비", "o": "보", "u": "부"},
    "p": {"a": "파", "e": "페", "i": "피", "o": "포", "u": "푸"},
    "d": {"a": "다", "e": "데", "i": "디", "o": "도", "u": "두"},
    "t": {"a": "타", "e": "테", "i": "티", "o": "토", "u": "투"},
    "f": {"a": "파", "e": "페", "i": "피", "o": "포", "u": "푸"},
    "v": {"a": "바", "e": "베", "i": "비", "o": "보", "u": "부"},
    "m": {"a": "마", "e": "메", "i": "미", "o": "모", "u": "무"},
    "n": {"a": "나", "e": "네", "i": "니", "o": "노", "u": "누"},
    "r": {"a": "라", "e": "레", "i": "리", "o": "로", "u": "루"},
    "s": {"a": "사", "e": "세", "i": "시", "o": "소", "u": "수"},
    "z": {"a": "차", "e": "체", "i": "치", "o": "초", "u": "추"},
    "l": {"a": "라", "e": "레", "i": "리", "o": "로", "u": "루"},
    # hard c/g (palatal handled via the ç/ğ soft rows below)
    "c": {"a": "카", "o": "코", "u": "쿠"},
    "g": {"a": "가", "o": "고", "u": "구"},
    "ç": {"a": "차", "e": "체", "i": "치", "o": "초", "u": "추"},
    "ğ": {"a": "자", "e": "제", "i": "지", "o": "조", "u": "주"},
    "j": {"a": "야", "e": "예", "i": "이", "o": "요", "u": "유"},
}
_KO_CH = {"e": "케", "i": "키", "a": "카", "o": "코", "u": "쿠"}
_KO_GH = {"e": "게", "i": "기", "a": "가", "o": "고", "u": "구"}
_KO_SC = {"a": "스카", "e": "셰", "i": "시", "o": "스코", "u": "스쿠"}
_KO_SCH = {"a": "스카", "e": "스케", "i": "스키", "o": "스코", "u": "스쿠"}
_KO_GN = {"a": "냐", "e": "네", "i": "니", "o": "뇨", "u": "뉴"}
_KO_GLI = {"a": "리아", "e": "리에", "i": "리", "o": "리오", "u": "리우"}
_KO_GLE = {"a": "글라", "e": "글레", "i": "글리", "o": "글로", "u": "글루"}
_KO_QU = {"a": "콰", "e": "쿠에", "i": "쿠이", "o": "콰", "u": "쿠"}
_KO_GU = {"a": "구아", "e": "구에", "i": "귀", "o": "구오", "u": "구우"}

# codas split two ways (established): liquids/nasals merge as batchim
# (Alba 알바 / Ancona 안코나 / Montecatini 몬테), obstruents render as
# standalone ㅡ-syllables (Parma 파르마 / Caserta 카세르타 / Quarto 콰르토)
_KO_CODA_BATCH = {"l": "ㄹ", "gl": "ㄹ", "gli": "ㄹ", "n": "ㄴ", "m": "ㅁ"}
_KO_CODA_STAND = {"r": "르", "s": "스", "t": "트", "d": "드", "b": "브",
                  "p": "프", "c": "크", "g": "그", "v": "브", "f": "프",
                  "z": "치"}
_CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
_JONG_IDX = {"ㄹ": 8, "ㅁ": 16, "ㄴ": 4}
_MERGE_DOUBLE = {"l", "gl", "gli"}


def _patch_jong(syl: str, jong: str) -> str:
    if len(syl) != 1:
        return syl
    idx = ord(syl) - 0xAC00
    if not (0 <= idx < 11172):
        return syl
    ci, ji = divmod(idx // 28, 21)
    return chr(0xAC00 + (ci * 21 + ji) * 28 + _JONG_IDX[jong])


def _syl(c: str, v: str, word: str) -> str:
    """onset consonant chunk + vowel -> one Hangul syllable string"""
    v = {"è": "e", "é": "e", "ì": "i", "í": "i", "ò": "o", "ó": "o",
         "ù": "u", "ú": "u", "à": "a", "y": "i"}.get(v, v)
    if c == "c" and v in "ei":
        return _KO_CV["ç"][v]
    if c == "g" and v in "ei":
        return _KO_CV["ğ"][v]
    table = {"ch": _KO_CH, "gh": _KO_GH, "sc": _KO_SC, "sch": _KO_SCH,
             "gn": _KO_GN, "gli": _KO_GLI, "gl": _KO_GLE, "qu": _KO_QU,
             "gu": _KO_GU}.get(c)
    if table is not None:
        cell = table.get(v)
        if cell is None:
            raise ValueError(f"{c}+{v!r} unhandled in {word!r}")
        return cell
    row = _KO_CV.get(c)
    cell = row.get(v) if row else None
    if cell is None:
        raise ValueError(f"{c}+{v!r} unhandled in {word!r}")
    return cell


def _raise(msg: str):
    raise ValueError(msg)


def transcribe_it_ko(word: str) -> str:
    if " " in word:
        return "-".join(transcribe_it_ko(part)
                        for part in word.split() if part)
    chunks = segment(word)
    out: list[str] = []
    i = 0
    n = len(chunks)
    while i < n:
        c = chunks[i]
        prev = chunks[i - 1] if i else ""
        nxt = chunks[i + 1] if i + 1 < n else ""
        nxt2 = chunks[i + 2] if i + 2 < n else ""
        if c in _VOWELS:
            out.append(_KO_V[c])
            i += 1
            continue
        if nxt and nxt in _VOWELS:
            # g + i + vowel: the glide absorbs (perugia 페루자=자 not 지아)
            if c == "g" and nxt == "i" and nxt2 and nxt2 in _VOWELS:
                g_v = {"è": "e", "é": "e", "ì": "i", "í": "i", "ò": "o",
                       "ó": "o", "ù": "u", "ú": "u", "à": "a",
                       "y": "i"}.get(nxt2, nxt2)
                out.append(_KO_CV["ğ"].get(g_v)
                           or _raise(f"g+{nxt2!r} unhandled in {word!r}"))
                i += 3
                continue
            syl = _syl(c, nxt, word)
            # 어중 double: intervocalic l/gl merges as batchim on the
            # previous syllable plus its own plain onset (밀라노/칼리아리)
            if prev and prev in _VOWELS and out and c in _MERGE_DOUBLE:
                cho = _CHO[(ord(syl[0]) - 0xAC00) // 588]
                if cho in _JONG_IDX:
                    out[-1] = _patch_jong(out[-1], cho)
            out.append(syl)
            i += 2
            continue
        if c in ("c", "g") and nxt in ("ç", "ğ") and nxt2 in _VOWELS:
            # soft c/g written across chunks (should not occur post-segment;
            # kept as a defensive path)
            row = _KO_CV["ç"] if c == "c" else _KO_CV["ğ"]
            out.append(row[nxt2])
            i += 3
            continue
        batch = _KO_CODA_BATCH.get(c)
        if batch is not None:
            if out:
                out[-1] = _patch_jong(out[-1], batch)
            else:
                out.append(batch)
            if c in ("gl", "gli"):
                # gl+i before a consonant: the i belongs to the second /ʎ/
                # (Figline 피리네 — [fiʎ.ʎi.ne])
                out.append("리")
                i += 1
                continue
            i += 1
            continue
        cell = _KO_CODA_STAND.get(c)
        if cell is None:
            raise ValueError(f"coda {c!r} unhandled in {word!r}")
        out.append(cell)
        i += 1
        continue
    return "".join(out)


IT_KO_EVAL = {
    "Roma": "로마", "Milano": "밀라노", "Napoli": "나폴리", "Torino": "토리노",
    "Venezia": "베네치아", "Firenze": "피렌체", "Genova": "제노바",
    "Bologna": "볼로냐", "Palermo": "팔레르모", "Catania": "카타니아",
    "Bari": "바리", "Perugia": "페루자", "Ancona": "안코나",
    "Trieste": "트리에스테", "Padova": "파도바", "Verona": "베로나",
    "Messina": "메시나", "Cagliari": "칼리아리", "Rimini": "리미니",
    "Modena": "모데나", "Parma": "파르마", "Pisa": "피사",
    "Siena": "시에나", "Salerno": "살레르노", "Caserta": "카세르타",
    "Potenza": "포텐차", "Trento": "트렌토", "Udine": "우디네",
    "Pescara": "페스카라", "Vicenza": "비첸차", "Aosta": "아오스타",
    "Alba": "알바", "Quarto": "콰르토", "Varese": "바레세",
    "Peschiera": "페스키에라", "Brescia": "브레시아", "Cortina": "코르티나",
}


def selfcheck() -> int:
    fails = 0
    for name, want in IT_KO_EVAL.items():
        got = transcribe_it_ko(name)
        if got != want:
            print(f"IT-KO EVAL FAIL {name!r}: got {got!r} want {want!r}")
            fails += 1
    print(f"it_g2p ko anchors: {len(IT_KO_EVAL) - fails}/{len(IT_KO_EVAL)} green")
    return fails


if __name__ == "__main__":
    raise SystemExit(1 if selfcheck() else 0)
