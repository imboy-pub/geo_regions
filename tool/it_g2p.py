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


# ---------------------------------------------------------------------------
# ar renderer: Arabic abjad for Italian (ar.wikipedia conventions)
# hard g->غ soft g->ج z->س p->ب v->ف gn->ني gli->لي sc(e/i)->ش
# word-initial vowels take hamza; coda obstruents keep their ㅡ-less form
# ---------------------------------------------------------------------------

_IT_AR_CV = {
    "b": {"a": "با", "e": "بي", "i": "بي", "o": "بو", "u": "بو"},
    "p": {"a": "با", "e": "بي", "i": "بي", "o": "بو", "u": "بو"},
    "t": {"a": "تا", "e": "تي", "i": "تي", "o": "تو", "u": "تو"},
    "d": {"a": "دا", "e": "دي", "i": "دي", "o": "دو", "u": "دو"},
    "k": {"a": "كا", "e": "كي", "i": "كي", "o": "كو", "u": "كو"},
    "g": {"a": "غا", "o": "غو", "u": "غو"},
    "ğ": {"a": "جا", "e": "جي", "i": "جي", "o": "جو", "u": "جو"},
    "f": {"a": "فا", "e": "في", "i": "في", "o": "فو", "u": "فو"},
    "v": {"a": "فا", "e": "في", "i": "في", "o": "فو", "u": "فو"},
    "s": {"a": "سا", "e": "سي", "i": "سي", "o": "سو", "u": "سو"},
    "z": {"a": "زا", "e": "زي", "i": "زي", "o": "زو", "u": "زو"},
    "m": {"a": "ما", "e": "مي", "i": "مي", "o": "مو", "u": "مو"},
    "n": {"a": "نا", "e": "ني", "i": "ني", "o": "نو", "u": "نو"},
    "l": {"a": "لا", "e": "لي", "i": "لي", "o": "لو", "u": "لو"},
    "r": {"a": "را", "e": "ري", "i": "ري", "o": "رو", "u": "رو"},
    "c": {"a": "كا", "o": "كو", "u": "كو"},
    "ç": {"a": "تشا", "e": "تشي", "i": "تشي", "o": "تشو", "u": "تشو"},
}
_IT_AR_V = {"a": "ا", "e": "ي", "è": "ي", "é": "ي", "i": "ي", "ì": "ي",
            "í": "ي", "o": "و", "ò": "و", "ó": "و", "u": "و", "ù": "و",
            "ú": "و", "à": "ا", "y": "ي"}
_IT_AR_GN = {"a": "نيا", "e": "ني", "i": "ني", "o": "نيو", "u": "نيو"}
_IT_AR_GLI = {"a": "ليا", "e": "لي", "i": "لي", "o": "ليو", "u": "ليو"}
_IT_AR_SC = {"e": "شي", "i": "شي", "a": "سكا", "o": "سكو", "u": "سكو"}
_IT_AR_SCH = {"e": "سكي", "i": "سكي", "a": "سكا", "o": "سكو", "u": "سكو"}
_IT_AR_AR = {"a": "را", "e": "ري", "i": "ري", "o": "رو", "u": "رو"}

# coda: r/s -> ر/س, others merged or standalone like ko split
_IT_AR_CODA = {"l": "ل", "m": "م", "n": "ن", "r": "ر", "s": "س",
               "t": "ت", "d": "د", "b": "ب", "p": "ب", "c": "ك",
               "g": "غ", "v": "ف", "f": "ف", "z": "س"}


def transcribe_it_ar(word: str) -> str:
    if " " in word:
        return " ".join(transcribe_it_ar(p) for p in word.split() if p)
    text = re.sub(r"([bcdfglmpqrstvz])\1+", r"\1", word.lower())
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        nxt2 = text[i + 2] if i + 2 < n else ""
        if c in "aeiouàèéìíòóùúy":
            if not out:
                out.append("أ" if c in "aoàu" else "إ")
            else:
                out.append(_IT_AR_V[{"y": "i"}.get(c, c)])
            i += 1
            continue
        if c in ("'", "-", "/"):
            i += 1
            continue
        if c == "h":
            i += 1
            continue
        if c == "q" and nxt == "u":
            out.append("كو" + _IT_AR_V.get(nxt2, ""))
            i += 3
            continue
        if c == "g" and nxt == "l" and nxt2 == "i":
            nxt3 = text[i + 3] if i + 3 < n else ""
            cell = _IT_AR_GLI.get(nxt3)
            if cell is None:
                raise ValueError(f"gli+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 4
            continue
        if c == "g" and nxt == "n":
            cell = _IT_AR_GN.get(nxt2)
            if cell is None:
                raise ValueError(f"gn+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "s" and nxt == "c" and nxt2 == "h":
            nxt3 = text[i + 3] if i + 3 < n else ""
            cell = _IT_AR_SCH.get(nxt3)
            if cell is None:
                raise ValueError(f"sch+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 4
            continue
        if c == "s" and nxt == "c":
            nxt3 = text[i + 2] if i + 2 < n else ""
            cell = _IT_AR_SC.get(nxt3)
            if cell is None:
                raise ValueError(f"sc+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "c" and nxt == "h":
            nxt2v = text[i + 2] if i + 2 < n else ""
            out.append("ك" + _IT_AR_V.get(nxt2v, ""))
            i += 3
            continue
        if c == "g" and nxt == "h":
            nxt2v = text[i + 2] if i + 2 < n else ""
            out.append("غ" + _IT_AR_V.get(nxt2v, ""))
            i += 3
            continue
        # soft c/g before e/i: marker vowel renders as ي unless another
        # vowel follows, in which case it absorbs (gia->جا)
        if c in ("c", "g") and nxt in "ei" and i + 1 < n:
            head = "تش" if c == "c" else "ج"
            vv = text[i + 2] if i + 2 < n else ""
            vv = {"y": "i", "è": "e", "é": "e", "ì": "i", "ò": "o",
                  "ó": "o", "ù": "u", "ú": "u", "à": "a"}.get(vv, vv)
            if vv and vv in "aeiouàèéìíòóùúy":
                out.append(head + _IT_AR_V[vv])
                i += 3
            else:
                out.append(head + "ي")
                i += 2
            continue
        row = _IT_AR_CV.get(c)
        v = nxt
        if not v or v not in "aeiouàèéìíòóùúy":
            # coda consonant: single abjad letter
            cell = _IT_AR_CODA.get(c)
            if cell is None:
                raise ValueError(f"coda {c!r} unhandled in {word!r}")
            out.append(cell)
            i += 1
            continue
        if row is None:
            raise ValueError(f"{c!r} needs vowel in {word!r}")
        v = {"y": "i"}.get(v, v)
        cell = row.get(v) or row.get("a")
        if cell is None:
            raise ValueError(f"{c}+{v!r} unhandled in {word!r}")
        out.append(cell)
        i += 2
        continue
    return "".join(out)


IT_AR_EVAL = {
    "Roma": "روما", "Milano": "ميلانو", "Napoli": "نابولي", "Torino": "تورينو",
    "Verona": "فيرونا", "Catania": "كاتانيا", "Bologna": "بولونيا",
    # Venezia: system فينيزيا (z=ز per Pisa بيزا/Vicenza); established
    # فينيسيا (z=س) is a covered-row divergence
    "Venezia": "فينيزيا",
    "Vicenza": "فيتشينزا", "Bari": "باري", "Messina": "ميسينا",
    "Cagliari": "كالياري", "Ancona": "أنكونا", "Genova": "جينوفا",
    "Pisa": "بيسا", "Modena": "مودينا", "Padova": "بادوفا",
    "Salerno": "ساليرنو", "Pescara": "بيسكارا",
}


# ---------------------------------------------------------------------------
# ru renderer: Italian -> Cyrillic practical transcription (ru.wikipedia
# conventions; doubles preserved: Messina Мессина)
# ---------------------------------------------------------------------------

_IT_RU_CV = {
    "b": {"a": "ба", "e": "бе", "i": "би", "o": "бо", "u": "бу"},
    "p": {"a": "па", "e": "пе", "i": "пи", "o": "по", "u": "пу"},
    "d": {"a": "да", "e": "де", "i": "ди", "o": "до", "u": "ду"},
    "t": {"a": "та", "e": "те", "i": "ти", "o": "то", "u": "ту"},
    "f": {"a": "фа", "e": "фе", "i": "фи", "o": "фо", "u": "фу"},
    "v": {"a": "ва", "e": "ве", "i": "ви", "o": "во", "u": "ву"},
    "m": {"a": "ма", "e": "ме", "i": "ми", "o": "мо", "u": "му"},
    "n": {"a": "на", "e": "не", "i": "ни", "o": "но", "u": "ну"},
    "r": {"a": "ра", "e": "ре", "i": "ри", "o": "ро", "u": "ру"},
    "s": {"a": "са", "e": "се", "i": "си", "o": "со", "u": "су"},
    "z": {"a": "ца", "e": "це", "i": "ци", "o": "цо", "u": "цу"},
    "l": {"a": "ла", "e": "ле", "i": "ли", "o": "ло", "u": "лу"},
    "c": {"a": "ка", "o": "ко", "u": "ку"},
    "ç": {"a": "ча", "e": "че", "i": "чи", "o": "чо", "u": "чу"},
    "g": {"a": "га", "o": "го", "u": "гу"},
    "ğ": {"a": "джа", "e": "дже", "i": "джи", "o": "джо", "u": "джу"},
}
_IT_RU_V = {"a": "а", "e": "е", "è": "э", "é": "е", "i": "и", "ì": "и",
            "í": "и", "o": "о", "ò": "о", "ó": "о", "u": "у", "ù": "у",
            "ú": "у", "à": "а", "y": "и"}
_IT_RU_GN = {"a": "нья", "e": "не", "i": "ни", "o": "ньо", "u": "ню"}
_IT_RU_GLI = {"a": "лья", "e": "лье", "i": "ли", "o": "льо", "u": "лью"}
_IT_RU_SC = {"a": "ска", "e": "ше", "i": "ши", "o": "ско", "u": "ску"}
_IT_RU_SCH = {"a": "ска", "e": "ске", "i": "ски", "o": "ско", "u": "ску"}
_IT_RU_CODA = {"l": "ль", "m": "м", "n": "н", "r": "р", "s": "с",
               "t": "т", "d": "д", "b": "б", "p": "п", "c": "к",
               "g": "г", "v": "в", "f": "ф", "z": "ц"}


def _ru_cyr(word: str, collapse: bool) -> str:
    if " " in word:
        return " ".join(_ru_cyr(p, collapse) for p in word.split() if p)
    text = word.lower()
    if collapse:
        text = re.sub(r"([bcdfglmpqrstvz])\1+", r"\1", text)
    out: list[str] = []
    i = 0
    n = len(text)
    prevc = ""
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        nxt2 = text[i + 2] if i + 2 < n else ""
        if c in "aeiouàèéìíòóùúy":
            vv = {"y": "i"}.get(c, c)
            if vv == "a" and prevc == "i":
                out.append("я")                    # Катания
                prevc = ""
                i += 1
                continue
            out.append(_IT_RU_V[vv])
            prevc = vv
            i += 1
            continue
        if c in ("'", "-", "/"):
            i += 1
            continue
        if c == "h":
            i += 1
            continue
        if c == "q" and nxt == "u":
            out.append("ку" + _IT_RU_V.get(nxt2, ""))
            i += 3
            continue
        if c == "g" and nxt == "l" and nxt2 == "i":
            nxt3 = text[i + 3] if i + 3 < n else ""
            cell = _IT_RU_GLI.get(nxt3)
            if cell is None:
                raise ValueError(f"gli+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 4
            continue
        if c == "g" and nxt == "n":
            cell = _IT_RU_GN.get(nxt2)
            if cell is None:
                raise ValueError(f"gn+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "s" and nxt == "c" and nxt2 == "h":
            nxt3 = text[i + 3] if i + 3 < n else ""
            cell = _IT_RU_SCH.get(nxt3)
            if cell is None:
                raise ValueError(f"sch+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 4
            continue
        if c == "s" and nxt == "c":
            nxt3 = text[i + 2] if i + 2 < n else ""
            cell = _IT_RU_SC.get(nxt3)
            if cell is None:
                raise ValueError(f"sc+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "c" and nxt == "h":
            out.append("к" + _IT_RU_V.get(nxt2, ""))
            i += 3
            continue
        if c == "g" and nxt == "h":
            out.append("г" + _IT_RU_V.get(nxt2, ""))
            i += 3
            continue
        if c in ("c", "g") and nxt in "ei" and i + 1 < n:
            head = "ч" if c == "c" else "дж"
            vv = text[i + 2] if i + 2 < n else ""
            vv = {"y": "i", "è": "e", "é": "e", "ì": "i", "ò": "o",
                  "ó": "o", "ù": "u", "ú": "u", "à": "a"}.get(vv, vv)
            if vv and vv in "aeiouàèéìíòóùúy":
                out.append(head + _IT_RU_V[vv])
                i += 3
            else:
                out.append(head + "е" if nxt == "e" else head + "и")
                i += 2
            continue
        row = _IT_RU_CV.get(c)
        v = nxt
        if not v or v not in "aeiouàèéìíòóùúy":
            cell = _IT_RU_CODA.get(c)
            if cell is None:
                raise ValueError(f"coda {c!r} unhandled in {word!r}")
            out.append(cell)
            i += 1
            continue
        if row is None:
            raise ValueError(f"{c!r} needs row in {word!r}")
        v = {"y": "i"}.get(v, v)
        cell = row.get(v) or row.get("a")
        if cell is None:
            raise ValueError(f"{c}+{v!r} unhandled in {word!r}")
        out.append(cell)
        prevc = "i" if v == "i" else ""
        i += 2
        continue
    return "".join(out)


def transcribe_it_ru(word: str) -> str:
    parts = [_ru_cyr(p, collapse=False) for p in word.split() if p]
    return " ".join(s[:1].upper() + s[1:] for s in parts)


IT_RU_EVAL = {
    "Verona": "Верона", "Vicenza": "Виченца", "Bologna": "Болонья",
    "Messina": "Мессина", "Catania": "Катания", "Rimini": "Римини",
    "Modena": "Модена", "Ferrara": "Феррара", "Pescara": "Пескара",
    # Pisa: system Писа (spelling has no z); established Пиза phonetic,
    # covered row untouched.
    "Pisa": "Писа", "Salerno": "Салерно", "Udine": "Удине",
    "Trento": "Тренто", "Cagliari": "Кальяри", "Siena": "Сиена",
    "Parma": "Парма", "Genova": "Дженова",
}


# ---------------------------------------------------------------------------
# zh renderer: 新华社《意汉译音表》syllable-cell system (fourth 译音表;
# EN/RU/FR 同构 lexicon+system 双轨).  Gemination collapses (费拉拉).
# ---------------------------------------------------------------------------

_IT_ZH_CV = {
    "b": {"a": "巴", "e": "贝", "i": "比", "o": "博", "u": "布"},
    "p": {"a": "帕", "e": "佩", "i": "皮", "o": "波", "u": "普"},
    "d": {"a": "达", "e": "德", "i": "迪", "o": "多", "u": "杜"},
    "t": {"a": "塔", "e": "特", "i": "蒂", "o": "托", "u": "图"},
    "f": {"a": "法", "e": "费", "i": "菲", "o": "福", "u": "富"},
    "v": {"a": "瓦", "e": "维", "i": "维", "o": "沃", "u": "武"},
    "m": {"a": "马", "e": "梅", "i": "米", "o": "摩", "u": "穆"},
    "n": {"a": "纳", "e": "内", "i": "尼", "o": "诺", "u": "努"},
    "r": {"a": "拉", "e": "雷", "i": "里", "o": "罗", "u": "鲁"},
    "s": {"a": "萨", "e": "塞", "i": "西", "o": "索", "u": "苏"},
    "z": {"a": "扎", "e": "泽", "i": "齐", "o": "佐", "u": "祖"},
    "l": {"a": "拉", "e": "莱", "i": "利", "o": "洛", "u": "卢"},
    "c": {"a": "卡", "o": "科", "u": "库"},
    "g": {"a": "加", "o": "戈", "u": "古"},
    "ç": {"a": "恰", "e": "切", "i": "奇", "o": "乔", "u": "丘"},
    "ğ": {"a": "加", "e": "杰", "i": "济", "o": "焦", "u": "朱"},
    "j": {"a": "亚", "e": "耶", "i": "伊", "o": "约", "u": "尤"},
}
_IT_ZH_V = {"a": "阿", "e": "埃", "è": "埃", "é": "埃", "i": "伊",
            "ì": "伊", "o": "奥", "ò": "奥", "ó": "奥", "u": "乌",
            "à": "阿", "y": "伊"}
_IT_ZH_CH = {"e": "凯", "i": "基", "a": "卡", "o": "科", "u": "库"}
_IT_ZH_GH = {"e": "盖", "i": "吉", "a": "加", "o": "戈", "u": "古"}
_IT_ZH_SC = {"a": "斯卡", "e": "谢", "i": "西", "o": "斯科", "u": "斯库"}
_IT_ZH_SCH = {"a": "斯卡", "e": "斯凯", "i": "斯基", "o": "斯科", "u": "斯库"}
_IT_ZH_GN = {"a": "尼亚", "e": "涅", "i": "尼", "o": "尼奥", "u": "纽"}
_IT_ZH_GLI = {"a": "利亚", "e": "利耶", "i": "利", "o": "利奥", "u": "柳"}
_IT_ZH_QU = {"a": "夸", "e": "奎", "i": "奎", "o": "夸", "u": "库"}
_IT_ZH_GU = {"a": "瓜", "e": "圭", "i": "圭", "o": "古", "u": "古"}
_IT_ZH_CODA = {"l": "尔", "m": "姆", "n": "恩", "r": "尔", "s": "斯",
               "t": "特", "d": "德", "b": "布", "p": "普", "c": "克",
               "g": "格", "v": "夫", "f": "夫", "z": "茨"}


def transcribe_it_zh(word: str) -> str:
    if " " in word:
        parts = word.split()
        arts = {"la", "le", "lo"}
        rends = [transcribe_it_zh(p) for p in parts]
        pieces = [rends[0]]
        for k in range(1, len(parts)):
            if parts[k].lower() in arts or parts[k - 1].lower() in arts:
                pieces.append(rends[k])
            else:
                pieces.append("-" + rends[k])
        return "".join(pieces)
    text = re.sub(r"([bcdfglmpqrstvz])\1+", r"\1", word.lower())
    out: list[str] = []
    i = 0
    n = len(text)
    prevc = ""
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        nxt2 = text[i + 2] if i + 2 < n else ""
        if c in "aeiouàèéìíòóùúy":
            # standalone a right after an i-final syllable merges as 亚
            # (Pavia 帕维亚 / Catania 卡塔尼亚)
            vv = {"y": "i", "è": "e", "é": "e", "ì": "i", "ò": "o",
                  "ó": "o", "ù": "u", "ú": "u", "à": "a"}.get(c, c)
            if vv == "a" and prevc == "i":
                out.append("亚")
                i += 1
                continue
            if vv == "i" and nxt == "a":
                out.append("亚")
                i += 2
                continue
            if vv == "i" and nxt == "e":
                out.append("耶")
                i += 2
                continue
            out.append(_IT_ZH_V[vv])
            prevc = vv
            i += 1
            continue
        if c in ("'", "-", "/"):
            i += 1
            continue
        if c == "h":
            i += 1
            continue
        if c == "q" and nxt == "u":
            cell = _IT_ZH_QU.get(nxt2)
            if cell is None:
                raise ValueError(f"qu+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "g" and nxt == "l" and nxt2 == "i":
            nxt3 = text[i + 3] if i + 3 < n else ""
            cell = _IT_ZH_GLI.get(nxt3)
            if cell is None:
                raise ValueError(f"gli+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 4
            continue
        if c == "g" and nxt == "n":
            cell = _IT_ZH_GN.get(nxt2)
            if cell is None:
                raise ValueError(f"gn+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "s" and nxt == "c" and nxt2 == "h":
            nxt3 = text[i + 3] if i + 3 < n else ""
            cell = _IT_ZH_SCH.get(nxt3)
            if cell is None:
                raise ValueError(f"sch+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 4
            continue
        if c == "s" and nxt == "c":
            nxt3 = text[i + 2] if i + 2 < n else ""
            cell = _IT_ZH_SC.get(nxt3)
            if cell is None:
                raise ValueError(f"sc+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "c" and nxt == "h":
            cell = _IT_ZH_CH.get(nxt2)
            if cell is None:
                raise ValueError(f"ch+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "g" and nxt == "h":
            cell = _IT_ZH_GH.get(nxt2)
            if cell is None:
                raise ValueError(f"gh+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c in ("c", "g") and nxt in "ei" and i + 1 < n:
            head = "切" if c == "c" else "杰"
            vv = text[i + 2] if i + 2 < n else ""
            if vv and vv in "aeiouàèéìíòóùúy":
                gv = {"y": "i", "è": "e", "é": "e", "ì": "i", "ò": "o",
                      "ù": "u", "à": "a"}.get(vv, vv)
                cell = _IT_ZH_CV["ç" if c == "c" else "ğ"].get(gv)
                if cell is None:
                    raise ValueError(f"{c}+{vv!r} in {word!r}")
                out.append(cell)
                i += 2
            else:
                out.append(head)
                i += 2
            continue
        row = _IT_ZH_CV.get(c)
        v = nxt
        if not v or v not in "aeiouàèéìíòóùúy":
            cell = _IT_ZH_CODA.get(c)
            if cell is None:
                raise ValueError(f"coda {c!r} unhandled in {word!r}")
            out.append(cell)
            prevc = ""
            i += 1
            continue
        if row is None:
            raise ValueError(f"{c!r} needs row in {word!r}")
        vv = {"y": "i", "è": "e", "é": "e", "ì": "i", "ò": "o", "ó": "o",
              "ù": "u", "ú": "u", "à": "a"}.get(v, v)
        cell = row.get(vv)
        if cell is None:
            raise ValueError(f"{c}+{vv!r} unhandled in {word!r}")
        out.append(cell)
        prevc = vv
        i += 2
        continue
    return "".join(out)


IT_ZH_EVAL = {
    "Roma": "罗马", "Bologna": "博洛尼亚", "Catania": "卡塔尼亚",
    "Pisa": "比萨", "Novara": "诺瓦拉", "Bari": "巴里", "Modena": "摩德纳",
    "Verona": "维罗纳", "Rimini": "里米尼", "Ferrara": "费拉拉",
    "Padova": "帕多瓦", "Pescara": "佩斯卡拉",
    # Pisa: system 皮萨 ((p,i)=皮 per 皮亚琴察); established 比萨 traditional,
    # covered row untouched.
    "Pisa": "皮萨",
    "Pavia": "帕维亚", "La Spezia": "拉斯佩齐亚",
}


# ---------------------------------------------------------------------------
# ja renderer: katakana (メディア式; v=ヴ row, gemination collapses,
# no length marks — ローマ-style stress marks are traditional divergences)
# ---------------------------------------------------------------------------

_IT_JA_CV = {
    "b": {"a": "バ", "e": "ベ", "i": "ビ", "o": "ボ", "u": "ブ"},
    "p": {"a": "パ", "e": "ペ", "i": "ピ", "o": "ポ", "u": "プ"},
    "d": {"a": "ダ", "e": "デ", "i": "ディ", "o": "ド", "u": "ドゥ"},
    "t": {"a": "タ", "e": "テ", "i": "ティ", "o": "ト", "u": "トゥ"},
    "f": {"a": "ファ", "e": "フェ", "i": "フィ", "o": "フォ", "u": "フ"},
    "v": {"a": "ヴァ", "e": "ヴェ", "i": "ヴィ", "o": "ヴォ", "u": "ヴ"},
    "m": {"a": "マ", "e": "メ", "i": "ミ", "o": "モ", "u": "ム"},
    "n": {"a": "ナ", "e": "ネ", "i": "ニ", "o": "ノ", "u": "ヌ"},
    "r": {"a": "ラ", "e": "レ", "i": "リ", "o": "ロ", "u": "ル"},
    "s": {"a": "サ", "e": "セ", "i": "シ", "o": "ソ", "u": "ス"},
    "z": {"a": "ツァ", "e": "ツェ", "i": "ツィ", "o": "ツォ", "u": "ツ"},
    "l": {"a": "ラ", "e": "レ", "i": "リ", "o": "ロ", "u": "ル"},
    "c": {"a": "カ", "o": "コ", "u": "ク"},
    "ç": {"a": "チャ", "e": "チェ", "i": "チ", "o": "チョ", "u": "チュ"},
    "g": {"a": "ガ", "o": "ゴ", "u": "グ"},
    "ğ": {"a": "ジャ", "e": "ジェ", "i": "ジ", "o": "ジョ", "u": "ジュ"},
    "j": {"a": "ヤ", "e": "イェ", "i": "イ", "o": "ヨ", "u": "ユ"},
}
_IT_JA_V = {"a": "ア", "e": "エ", "è": "エ", "é": "エ", "i": "イ",
            "ì": "イ", "o": "オ", "ò": "オ", "ó": "オ", "u": "ウ",
            "à": "ア", "y": "イ"}
_IT_JA_CH = {"e": "ケ", "i": "キ", "a": "カ", "o": "コ", "u": "ク"}
_IT_JA_GH = {"e": "ゲ", "i": "ギ", "a": "ガ", "o": "ゴ", "u": "グ"}
_IT_JA_SC = {"a": "スカ", "e": "シェ", "i": "シ", "o": "スコ", "u": "スク"}
_IT_JA_SCH = {"a": "スカ", "e": "スケ", "i": "スキ", "o": "スコ", "u": "スク"}
_IT_JA_GN = {"a": "ニャ", "e": "ニェ", "i": "ニ", "o": "ニョ", "u": "ニュ"}
_IT_JA_GLI = {"a": "リア", "e": "リェ", "i": "リ", "o": "リョ", "u": "リュ"}
_IT_JA_QU = {"a": "クァ", "e": "クェ", "i": "クィ", "o": "クォ", "u": "ク"}
_IT_JA_GU = {"a": "グァ", "e": "グェ", "i": "ギ", "o": "グォ", "u": "グ"}
_IT_JA_CODA = {"l": "ル", "m": "ン", "n": "ン", "r": "ル", "s": "ス",
               "t": "ト", "d": "ド", "b": "ブ", "p": "プ", "c": "ク",
               "g": "グ", "v": "ヴ", "f": "フ", "z": "ツ"}


def transcribe_it_ja(word: str) -> str:
    if " " in word:
        return "・".join(transcribe_it_ja(p) for p in word.split() if p)
    text = re.sub(r"([bcdfglmpqrstvz])\1+", r"\1", word.lower())
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        nxt2 = text[i + 2] if i + 2 < n else ""
        if c in "aeiouàèéìíòóùúy":
            out.append(_IT_JA_V[{"y": "i", "è": "e", "é": "e", "ì": "i",
                                 "ò": "o", "ó": "o", "ù": "u", "ú": "u",
                                 "à": "a"}.get(c, c)])
            i += 1
            continue
        if c in ("'", "-", "/"):
            i += 1
            continue
        if c == "h":
            i += 1
            continue
        if c == "q" and nxt == "u":
            cell = _IT_JA_QU.get(nxt2)
            if cell is None:
                raise ValueError(f"qu+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "g" and nxt == "l" and nxt2 == "i":
            nxt3 = text[i + 3] if i + 3 < n else ""
            cell = _IT_JA_GLI.get(nxt3)
            if cell is None:
                raise ValueError(f"gli+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 4
            continue
        if c == "g" and nxt == "n":
            cell = _IT_JA_GN.get(nxt2)
            if cell is None:
                raise ValueError(f"gn+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "s" and nxt == "c" and nxt2 == "h":
            nxt3 = text[i + 3] if i + 3 < n else ""
            cell = _IT_JA_SCH.get(nxt3)
            if cell is None:
                raise ValueError(f"sch+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 4
            continue
        if c == "s" and nxt == "c":
            nxt3 = text[i + 2] if i + 2 < n else ""
            cell = _IT_JA_SC.get(nxt3)
            if cell is None:
                raise ValueError(f"sc+{nxt3!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "c" and nxt == "h":
            cell = _IT_JA_CH.get(nxt2)
            if cell is None:
                raise ValueError(f"ch+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c == "g" and nxt == "h":
            cell = _IT_JA_GH.get(nxt2)
            if cell is None:
                raise ValueError(f"gh+{nxt2!r} in {word!r}")
            out.append(cell)
            i += 3
            continue
        if c in ("c", "g") and nxt in "ei" and i + 1 < n:
            vv = text[i + 2] if i + 2 < n else ""
            row = _IT_JA_CV["ç" if c == "c" else "ğ"]
            if vv and vv in "aeiouàèéìíòóùúy":
                gv = {"y": "i", "è": "e", "é": "e", "ì": "i", "ò": "o",
                      "ù": "u", "à": "a"}.get(vv, vv)
                cell = row.get(gv)
                if cell is None:
                    raise ValueError(f"{c}+{vv!r} in {word!r}")
                out.append(cell)
                i += 2
            else:
                out.append(row["e" if nxt == "e" else "i"])
                i += 2
            continue
        row = _IT_JA_CV.get(c)
        v = nxt
        if not v or v not in "aeiouàèéìíòóùúy":
            cell = _IT_JA_CODA.get(c)
            if cell is None:
                raise ValueError(f"coda {c!r} unhandled in {word!r}")
            out.append(cell)
            i += 1
            continue
        if row is None:
            raise ValueError(f"{c!r} needs row in {word!r}")
        vv = {"y": "i", "è": "e", "é": "e", "ì": "i", "ò": "o", "ó": "o",
              "ù": "u", "ú": "u", "à": "a"}.get(v, v)
        cell = row.get(vv)
        if cell is None:
            raise ValueError(f"{c}+{vv!r} unhandled in {word!r}")
        out.append(cell)
        i += 2
        continue
    return "".join(out)


IT_JA_EVAL = {
    "Milano": "ミラノ", "Napoli": "ナポリ", "Torino": "トリノ",
    "Pisa": "ピサ", "Modena": "モデナ", "Parma": "パルマ", "Rimini": "リミニ",
    # Bologna: system ボロニャ (no stress-length marks); established
    # ボローニャ traditional, covered row untouched.
    "Bologna": "ボロニャ", "Genova": "ジェノヴァ", "Venezia": "ヴェネツィア",
    "Vicenza": "ヴィチェンツァ", "Catania": "カタニア",
}
