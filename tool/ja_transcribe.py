#!/usr/bin/env python3
"""Katakana -> Hangul / Cyrillic transcribers for JP municipalities.

Fills the JP ko/ru cells the CSC upstream translations miss (360 each as of
round 33: 15 ward rows + 345 city rows whose CSC inheritance failed).  Both
transcriptions are codified national/scholarly systems, not inventions:

ko  -- 국립국어원 「외래어 표기법」 제2장 일람표 (표1 청음/탁음·반탁음,
       표2 요음) + 제3장 제6절 일본어 표기 세칙 (제1항 촉음 [ッ]->ㅅ 받침,
       제2항 장모음 무표기).  korean.go.kr/front/page/pageView.do?page_id=P000129
       어두/어중·어말 split applies per name unit (도쿄: ト word-initial -> 도).
       Administrative suffixes are translated semantically (市->시 町->정
       村->촌 区->구, attached without space; ward level separated with a
       space: 삿포로시 주오구), mirroring the dominant style of the existing
       CSC-inherited ko cells (고타정 / 치쿠시노시 / 미하마구).
ru  -- Поливанов system (Практическая транскрипция японского языка):
       シ->си ジ->дзи チ->ти ツ->цу ヂ->дзи ヅ->дзу; word-initial ヨ->йо
       (Йокогама convention); vowel+イ diphthongs -> ай/ой/уй (Сайтама,
       Вакканай); orthographic lengths dropped except いい->ии (Ниигата,
       Осака, Токио); sokuon doubles the next onset (Саппоро); ward suffix
       区 transliterated -ку (ru.wikipedia «Районы городов Японии»: Тюо-ку,
       Кита-ку, Минами-ку).  ru.wiki practical divergences frozen verbatim
       (Ацубецу/Теине/Сироси vs strict Ацубэцу/Тэйнэ/Сиройси).

Machine-candidate, eval-gated (selfcheck anchors, ~50), provisional; never
flips to approved.  Unknown katakana raises ValueError -> the caller keeps
the cell honestly missing (fill-missing overlay, upstream cells untouched).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# katakana inventory helpers
# ---------------------------------------------------------------------------

# vowel row of each plain kana (あ段/い段/う段/え段/お段)
_ROW = {
    "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o",
    "カ": "a", "キ": "i", "ク": "u", "ケ": "e", "コ": "o",
    "ガ": "a", "ギ": "i", "グ": "u", "ゲ": "e", "ゴ": "o",
    "サ": "a", "シ": "i", "ス": "u", "セ": "e", "ソ": "o",
    "ザ": "a", "ジ": "i", "ズ": "u", "ゼ": "e", "ゾ": "o",
    "タ": "a", "チ": "i", "ツ": "u", "テ": "e", "ト": "o",
    "ダ": "a", "ヂ": "i", "ヅ": "u", "デ": "e", "ド": "o",
    "ナ": "a", "ニ": "i", "ヌ": "u", "ネ": "e", "ノ": "o",
    "ハ": "a", "ヒ": "i", "フ": "u", "ヘ": "e", "ホ": "o",
    "バ": "a", "ビ": "i", "ブ": "u", "ベ": "e", "ボ": "o",
    "パ": "a", "ピ": "i", "プ": "u", "ペ": "e", "ポ": "o",
    "マ": "a", "ミ": "i", "ム": "u", "メ": "e", "モ": "o",
    "ヤ": "a", "ユ": "u", "ヨ": "o",
    "ラ": "a", "リ": "i", "ル": "u", "レ": "e", "ロ": "o",
    "ワ": "a", "ヰ": "i", "ヱ": "e", "ヲ": "o",
    "ン": "N",
}
_SMALL = "ャュョ"
_YOON_VOWEL = {"ャ": "a", "ュ": "u", "ョ": "o"}

# ---------------------------------------------------------------------------
# unit parsing: kana string -> [(unit, kind)] with kind in
# "sokuon" | "yoon" | "plain" | "bar"
# ---------------------------------------------------------------------------

def _units(kana: str) -> list[tuple[str, str]]:
    chars = list(kana)
    out: list[tuple[str, str]] = []
    i = 0
    while i < len(chars):
        c = chars[i]
        if c == "ッ":
            out.append(("ッ", "sokuon"))
            i += 1
        elif c == "ー":
            out.append(("ー", "bar"))
            i += 1
        elif i + 1 < len(chars) and chars[i + 1] in _SMALL:
            out.append((c + chars[i + 1], "yoon"))
            i += 2
        elif c in _ROW:
            out.append((c, "plain"))
            i += 1
        else:
            raise ValueError(f"unknown katakana char {c!r} in {kana!r}")
    return out


_BARE = {"ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o"}


def _vowel_of(unit: str, kind: str) -> str:
    """vowel row for the orthographic-length pass."""
    if kind == "sokuon":
        return "Q"                      # blocks length pairing
    if kind == "yoon":
        return _YOON_VOWEL[unit[1]]
    if kind == "bar":
        return "|"
    return _ROW[unit]


def strip_length(units: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Drop the second kana of orthographic long-vowel spellings.  The second
    kana must be a BARE vowel (あ行): かあ/にい/くう/べい/とう/きょう -- CV+V.
    Bare-vowel doubling (おお/ああ) is also a length.  po+ro (ポロ) is NOT a
    length: two onsets.  Second kana re-tagged len2/len2-ii/len2-ei/len2-ou
    so renderers can treat いい specially."""
    out = []
    i = 0
    while i < len(units):
        u, k = units[i]
        if i + 1 < len(units):
            u2, k2 = units[i + 1]
            if (k2 == "plain" and u2 in _BARE) and k in ("plain", "yoon"):
                r1 = _vowel_of(u, k)
                r2 = _BARE[u2]
                if r1 == r2 or (r1 == "o" and r2 == "u") or (r1 == "e" and r2 == "i"):
                    tag = "len2"
                    if r1 == "i" or (r1 == "e" and r2 == "i"):
                        tag = "len2-ii" if r1 == "i" else "len2-ei"
                    elif r1 == "o" and r2 == "u":
                        tag = "len2-ou"
                    out.append((u, k))
                    out.append((u2, tag))
                    i += 2
                    continue
        out.append((u, k))
        i += 1
    return out


# ---------------------------------------------------------------------------
# administrative suffix stripping (kana + kanji must agree)
# ---------------------------------------------------------------------------

_SUFFIX_KIND = {"チョウ": "cho", "マチ": "machi", "ムラ": "mura",
                "シ": "shi", "ク": "ku"}
_KANJI_KIND = {"市": "shi", "町": "town", "村": "mura", "区": "ku"}
_KO_SUFFIX = {"shi": "시", "town": "정", "mura": "촌", "ku": "구"}


def split_suffix(kana: str, kanji: str) -> tuple[str, str]:
    """(body kana, suffix kind); raises when kana and kanji endings disagree."""
    kanji_kind = _KANJI_KIND.get(kanji[-1:]) if kanji else None
    body = kana
    kind = None
    for suf in ("チョウ", "マチ", "ムラ", "シ", "ク"):
        if body.endswith(suf) and len(body) > len(suf):
            body = body[: -len(suf)]
            kind = _SUFFIX_KIND[suf]
            break
    if kind is None:
        raise ValueError(f"no suffix kana in {kana!r} (kanji {kanji!r})")
    if kind in ("cho", "machi"):
        kanji_ok = kanji_kind == "town"
    else:
        kanji_ok = kanji_kind == kind
    if not kanji_ok:
        raise ValueError(f"kana suffix {kind} vs kanji {kanji[-1:]!r} mismatch")
    return body, ("town" if kind in ("cho", "machi") else kind)


# ---------------------------------------------------------------------------
# ko renderer: 국립국어원 외래어 표기법 (표1 + 표2 + 세칙)
# ---------------------------------------------------------------------------

# 표1 청음: 어두 vs 어중·어말
_KO_ONSET = {
    "ア": "아", "イ": "이", "ウ": "우", "エ": "에", "オ": "오",
    "カ": "가", "キ": "기", "ク": "구", "ケ": "게", "コ": "고",
    "サ": "사", "シ": "시", "ス": "스", "セ": "세", "ソ": "소",
    "タ": "다", "チ": "치", "ツ": "쓰", "テ": "데", "ト": "도",
    "ナ": "나", "ニ": "니", "ヌ": "누", "ネ": "네", "ノ": "노",
    "ハ": "하", "ヒ": "히", "フ": "후", "ヘ": "헤", "ホ": "호",
    "マ": "마", "ミ": "미", "ム": "무", "メ": "메", "モ": "모",
    "ヤ": "야", "ユ": "유", "ヨ": "요",
    "ラ": "라", "リ": "리", "ル": "루", "レ": "레", "ロ": "로",
    "ワ": "와", "ヰ": "이", "ヱ": "에", "ヲ": "오",
}
_KO_MEDIAL = {
    "ア": "아", "イ": "이", "ウ": "우", "エ": "에", "オ": "오",
    "カ": "카", "キ": "키", "ク": "쿠", "ケ": "케", "コ": "코",
    "サ": "사", "シ": "시", "ス": "스", "セ": "세", "ソ": "소",
    "タ": "타", "チ": "치", "ツ": "쓰", "テ": "테", "ト": "토",
    "ナ": "나", "ニ": "니", "ヌ": "누", "ネ": "네", "ノ": "노",
    "ハ": "하", "ヒ": "히", "フ": "후", "ヘ": "헤", "ホ": "호",
    "マ": "마", "ミ": "미", "ム": "무", "メ": "메", "モ": "모",
    "ヤ": "야", "ユ": "유", "ヨ": "요",
    "ラ": "라", "リ": "리", "ル": "루", "レ": "레", "ロ": "로",
    "ワ": "와", "ヰ": "이", "ヱ": "에", "ヲ": "오",
}
# 표1 계속 탁음·반탁음 (어두/어중 동일)
for _k, _v in {"ガ": "가", "ギ": "기", "グ": "구", "ゲ": "게", "ゴ": "고",
               "ザ": "자", "ジ": "지", "ズ": "즈", "ゼ": "제", "ゾ": "조",
               "ダ": "다", "ヂ": "지", "ヅ": "즈", "デ": "데", "ド": "도",
               "バ": "바", "ビ": "비", "ブ": "부", "ベ": "베", "ボ": "보",
               "パ": "파", "ピ": "피", "プ": "푸", "ペ": "페", "ポ": "포"}.items():
    _KO_ONSET[_k] = _KO_MEDIAL[_k] = _v

# 표2 요음: 어두 / 어중
_KO_YOON_ONSET = {
    "キャ": "갸", "キュ": "규", "キョ": "교",
    "ギャ": "갸", "ギュ": "규", "ギョ": "교",
    "シャ": "샤", "シュ": "슈", "ショ": "쇼",
    "ジャ": "자", "ジュ": "주", "ジョ": "조",
    "チャ": "차", "チュ": "츄", "チョ": "초",
    "ニャ": "냐", "ニュ": "뉴", "ニョ": "뇨",
    "ヒャ": "햐", "ヒュ": "휴", "ヒョ": "효",
    "ビャ": "뱌", "ビュ": "뷰", "ビョ": "뵤",
    "ピャ": "퍄", "ピュ": "퓨", "ピョ": "표",
    "ミャ": "먀", "ミュ": "뮤", "ミョ": "묘",
    "リャ": "랴", "リュ": "류", "リョ": "료",
}
_KO_YOON_MEDIAL = {
    "キャ": "캬", "キュ": "큐", "キョ": "쿄",
    "ギャ": "갸", "ギュ": "규", "ギョ": "교",
    "シャ": "샤", "シュ": "슈", "ショ": "쇼",
    "ジャ": "자", "ジュ": "주", "ジョ": "조",
    "チャ": "차", "チュ": "츄", "チョ": "초",
    "ニャ": "냐", "ニュ": "뉴", "ニョ": "뇨",
    "ヒャ": "햐", "ヒュ": "휴", "ヒョ": "효",
    "ビャ": "뱌", "ビュ": "뷰", "ビョ": "뵤",
    "ピャ": "퍄", "ピュ": "퓨", "ピョ": "표",
    "ミャ": "먀", "ミュ": "뮤", "ミョ": "묘",
    "リャ": "랴", "リュ": "류", "リョ": "료",
}

_CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
_JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
_JONG = "×ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"


def _compose(cho: str, jung: str, jong: str = "×") -> str:
    ci, ji, gi = _CHO.index(cho), _JUNG.index(jung), _JONG.index(jong)
    return chr(0xAC00 + (ci * 21 + ji) * 28 + gi)


def _patch_jong(syl: str, jong: str) -> str:
    """Set/override the final consonant of an existing Hangul syllable."""
    idx = ord(syl) - 0xAC00
    if not (0 <= idx < 11172):
        raise ValueError(f"cannot patch jongseong on {syl!r}")
    ci, ji = divmod(idx // 28, 21)
    return _compose(_CHO[ci], _JUNG[ji], jong)


def _ko_body(body: str) -> str:
    """Render one name body (suffix already stripped). 어두 applies to the
    first unit; 촉음 -> ㅅ 받침, ン -> ㄴ 받침 per 세칙."""
    units = strip_length(_units(body))
    syls: list[str] = []
    for u, k in units:
        if k == "sokuon":
            if not syls:
                raise ValueError(f"word-initial sokuon in {body!r}")
            syls[-1] = _patch_jong(syls[-1], "ㅅ")
            continue
        if k == "bar" or k.startswith("len2"):
            continue                        # 제2항: 장모음 따로 표기 않음
        if u == "ン":
            if not syls:
                raise ValueError(f"word-initial ン in {body!r}")
            syls[-1] = _patch_jong(syls[-1], "ㄴ")
            continue
        if k == "yoon":
            syl = (_KO_YOON_ONSET if not syls else _KO_YOON_MEDIAL)[u]
        else:
            syl = (_KO_ONSET if not syls else _KO_MEDIAL)[u]
        syls.append(syl)
    return "".join(syls)


# ru.wiki practical divergence freezes: verbatim overrides.
_RU_FREEZE = {
    "アツベツ": "Ацубецу",                  # strict Ацубэцу
    "テイネ": "Тэине",                      # strict Тэйнэ
    "シロイシ": "Сироси",                   # ru.wiki simplification of Сироиси
    "トウキョウ": "Токио",                  # established exonym; strict Токё
}
_RU_FREEZE_WARD = {
    ("アツベツ", "ク"): "Ацубецу-ку",
    ("テイネ", "ク"): "Тэине-ку",
    ("シロイシ", "ク"): "Сироси-ку",
}


_RU_UNIT = {
    "ア": "а", "イ": "и", "ウ": "у", "エ": "э", "オ": "о",
    "カ": "ка", "キ": "ки", "ク": "ку", "ケ": "кэ", "コ": "ко",
    "ガ": "га", "ギ": "ги", "グ": "гу", "ゲ": "гэ", "ゴ": "го",
    "サ": "са", "シ": "си", "ス": "су", "セ": "сэ", "ソ": "со",
    "ザ": "дза", "ジ": "дзи", "ズ": "дзу", "ゼ": "дзэ", "ゾ": "дзо",
    "タ": "та", "チ": "ти", "ツ": "цу", "テ": "тэ", "ト": "то",
    "ダ": "да", "ヂ": "дзи", "ヅ": "дзу", "デ": "дэ", "ド": "до",
    "ナ": "на", "ニ": "ни", "ヌ": "ну", "ネ": "нэ", "ノ": "но",
    "ハ": "ха", "ヒ": "хи", "フ": "фу", "ヘ": "хэ", "ホ": "хо",
    "バ": "ба", "ビ": "би", "ブ": "бу", "ベ": "бэ", "ボ": "бо",
    "パ": "па", "ピ": "пи", "プ": "пу", "ペ": "пэ", "ポ": "по",
    "マ": "ма", "ミ": "ми", "ム": "му", "メ": "мэ", "モ": "мо",
    "ヤ": "я", "ユ": "ю", "ヨ": "ё",
    "ラ": "ра", "リ": "ри", "ル": "ру", "レ": "рэ", "ロ": "ро",
    "ワ": "ва", "ヰ": "и", "ヱ": "э", "ヲ": "о",
    "ン": "н",
    # 拗音 (Поливанов)
    "キャ": "кя", "キュ": "кю", "キョ": "кё",
    "ギャ": "гя", "ギュ": "гю", "ギョ": "гё",
    "シャ": "ся", "シュ": "сю", "ショ": "сё",
    "ジャ": "дзя", "ジュ": "дзю", "ジョ": "дзё",
    "チャ": "тя", "チュ": "тю", "チョ": "тё",
    "ニャ": "ня", "ニュ": "ню", "ニョ": "нё",
    "ヒャ": "хя", "ヒュ": "хю", "ヒョ": "хё",
    "ビャ": "бя", "ビュ": "бю", "ビョ": "бё",
    "ピャ": "пя", "ピュ": "пю", "ピョ": "пё",
    "ミャ": "мя", "ミュ": "мю", "ミョ": "мё",
    "リャ": "ря", "リュ": "рю", "リョ": "рё",
}


def _ru_body(body: str) -> str:
    """Поливанов rendering of one name body (suffix already stripped):
    word-initial ё->йо (Йокогама), sokuon doubles the next onset (Саппоро),
    vowel+イ -> й-form at word-initial cluster or word-final only (Сайтама,
    Вакканай; mid-word stays и: Йоккаити), lengths dropped except いい->ии
    (Ниигата)."""
    units = strip_length(_units(body))
    out: list[str] = []
    pending_gem = False
    n = len(units)
    for j, (u, k) in enumerate(units):
        if k == "sokuon":
            if not out:
                raise ValueError(f"word-initial sokuon in {body!r}")
            pending_gem = True
            continue
        if k == "bar" or k in ("len2", "len2-ei", "len2-ou"):
            continue
        if k == "len2-ii":
            out.append("и")                 # Ниигата keeps the double и
            continue
        text = _RU_UNIT[u]
        if u == "ヨ" and not out:
            text = "йо"                     # Russian has no word-initial ё
        if pending_gem:
            text = text[0] + text           # п + по -> ппо
            pending_gem = False
        if (u == "イ" and out and out[-1][-1] in "аеёиоуыэюя"
                and (j == 1 or j == n - 1)):
            text = "й"                      # diphthong: initial/final only
        out.append(text)
    rendered = "".join(out)
    return rendered[:1].upper() + rendered[1:]


def _ru_body_frozen(body: str) -> str:
    return _RU_FREEZE.get(body) or _ru_body(body)


# ---------------------------------------------------------------------------
# public fill API
# ---------------------------------------------------------------------------

def ko_muni(city_kana: str, city_kanji: str,
            ward_kana: str = "", ward_kanji: str = "") -> str:
    """삿포로시 주오구 / 코타정 -- transcription + semantic suffix."""
    body, kind = split_suffix(city_kana, city_kanji)
    out = _ko_body(body) + _KO_SUFFIX[kind]
    if ward_kana:
        wbody, wkind = split_suffix(ward_kana, ward_kanji)
        if wkind != "ku":
            raise ValueError(f"ward kind {wkind}? {ward_kana!r}")
        out += " " + _ko_body(wbody) + _KO_SUFFIX["ku"]
    return out


def ru_muni(city_kana: str, city_kanji: str,
            ward_kana: str = "", ward_kanji: str = "") -> str:
    """Саппоро Тюо-ку / Вакканай -- Поливанов, ward suffix -ку."""
    body, kind = split_suffix(city_kana, city_kanji)
    if ward_kana:
        wbody, wkind = split_suffix(ward_kana, ward_kanji)
        if wkind != "ku":
            raise ValueError(f"ward kind {wkind}? {ward_kana!r}")
        frozen = _RU_FREEZE_WARD.get((body, "ク"))
        wname = frozen if frozen else _ru_body_frozen(wbody)
        return _ru_body(body) + " " + wname + "-ку"
    return _ru_body_frozen(body)


# ---------------------------------------------------------------------------
# eval anchors
# ---------------------------------------------------------------------------

# official 세칙 examples + ward forms (rule-derived, ward bodies restart 어두)
_KO_BODY_EVAL = [
    ("サッポロ", "삿포로"), ("トットリ", "돗토리"), ("ヨッカイチ", "욧카이치"),
    ("キュウシュウ", "규슈"), ("ニイガタ", "니가타"), ("トウキョウ", "도쿄"),
    ("オオサカ", "오사카"), ("チュウオウ", "츄오"), ("キタ", "기타"),
    ("ヒガシ", "히가시"), ("シロイシ", "시로이시"), ("トヨヒラ", "도요히라"),
    ("ミナミ", "미나미"), ("ニシ", "니시"), ("アツベツ", "아쓰베쓰"),
    ("テイネ", "데네"), ("キヨタ", "기요타"), ("センダイ", "센다이"),
    ("アオバ", "아오바"), ("ミヤギノ", "미야기노"), ("ワカバヤシ", "와카바야시"),
    ("タイハク", "다이하쿠"), ("イズミ", "이즈미"), ("ワッカナイ", "왓카나이"),
    ("コウタ", "고타"), ("チクシノ", "치쿠시노"), ("ミハマ", "미하마"),
    ("アサギリ", "아사기리"), ("カモガワ", "가모가와"), ("サカイデ", "사카이데"),
]

_RU_BODY_EVAL = [
    ("サッポロ", "Саппоро"), ("トットリ", "Тоттори"), ("ヨッカイチ", "Йоккаити"),
    ("キュウシュウ", "Кюсю"), ("ニイガタ", "Ниигата"), ("トウキョウ", "Токио"),
    ("オオサカ", "Осака"), ("チュウオウ", "Тюо"), ("キタ", "Кита"),
    ("ヒガシ", "Хигаси"), ("トヨヒラ", "Тоёхира"), ("ミナミ", "Минами"),
    ("ニシ", "Ниси"), ("キヨタ", "Киёта"), ("センダイ", "Сэндай"),
    ("アオバ", "Аоба"), ("ミヤギノ", "Миягино"), ("ワカバヤシ", "Вакабаяси"),
    ("タイハク", "Тайхаку"), ("イズミ", "Идзуми"), ("ワッカナイ", "Вакканай"),
    ("アツベツ", "Ацубецу"),          # freeze: ru.wiki (strict Ацубэцу)
    ("テイネ", "Тэине"),              # freeze: ru.wiki (strict Тэйнэ)
    ("シロイシ", "Сироси"),           # freeze: ru.wiki (strict Сиройси)
    ("コモロ", "Коморо"), ("ハスダ", "Хасуда"), ("ムツザワ", "Муцудзава"),
    ("イチハラ", "Итихара"), ("アンド", "Андо"),
]

_MUNI_EVAL = [
    # (city_kana, city_kanji, ward_kana, ward_kanji, ko, ru)
    ("サッポロシ", "札幌市", "チュウオウク", "中央区", "삿포로시 츄오구", "Саппоро Тюо-ку"),
    ("サッポロシ", "札幌市", "キタク", "北区", "삿포로시 기타구", "Саппоро Кита-ку"),
    ("サッポロシ", "札幌市", "シロイシク", "白石区", "삿포로시 시로이시구", "Саппоро Сироси-ку"),
    ("サッポロシ", "札幌市", "アツベツク", "厚別区", "삿포로시 아쓰베쓰구", "Саппоро Ацубецу-ку"),
    ("サッポロシ", "札幌市", "テイネク", "手稲区", "삿포로시 데네구", "Саппоро Тэине-ку"),
    ("センダイシ", "仙台市", "タイハクク", "太白区", "센다이시 다이하쿠구", "Сэндай Тайхаку-ку"),
    ("コウタチョウ", "幸田町", "", "", "고타정", "Кота"),
    ("ワッカナイシ", "稚内市", "", "", "왓카나이시", "Вакканай"),
    ("アサギリチョウ", "あさぎり町", "", "", "아사기리정", "Асагири"),
]


def selfcheck() -> int:
    fails = 0
    for body, want in _KO_BODY_EVAL:
        got = _ko_body(body)
        if got != want:
            print(f"KO FAIL {body}: {got!r} != {want!r}")
            fails += 1
    for body, want in _RU_BODY_EVAL:
        got = _ru_body_frozen(body)
        if got != want:
            print(f"RU FAIL {body}: {got!r} != {want!r}")
            fails += 1
    for ck, kj, wk, wj, ko, ru in _MUNI_EVAL:
        got_ko = ko_muni(ck, kj, wk, wj)
        got_ru = ru_muni(ck, kj, wk, wj)
        if got_ko != ko:
            print(f"MUNI-KO FAIL {ck}+{wk}: {got_ko!r} != {ko!r}")
            fails += 1
        if got_ru != ru:
            print(f"MUNI-RU FAIL {ck}+{wk}: {got_ru!r} != {ru!r}")
            fails += 1
    total = len(_KO_BODY_EVAL) + len(_RU_BODY_EVAL) + 2 * len(_MUNI_EVAL)
    print(f"ja_transcribe selfcheck: {total - fails}/{total} green, "
          f"ko {len(_KO_BODY_EVAL)} ru {len(_RU_BODY_EVAL)} muni {2 * len(_MUNI_EVAL)}")
    return fails


if __name__ == "__main__":
    raise SystemExit(1 if selfcheck() else 0)
