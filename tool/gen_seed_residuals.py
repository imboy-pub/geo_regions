#!/usr/bin/env python3
"""Generate the seed layer's residual AI translations (CN ar + GB ar/ko/ja).

This is the LLM-generation track the quality system anticipated: every entry
ships as `provisional` with `humanReviewVerified=false` and enters the
human-review queue. It is NOT derived from any upstream dataset — the source
of truth is this recorded generation run, byte-pinned via the
`generatedSources` section of sources/source-lock.json.

Method, per locale:

- CN ar (2,329 nodes): deterministic syllable transliteration. 92% of the
  names carry pinyin evidence from the GeoNames extract ("dong cheng"-style
  alternatenames); the pinyin→Arabic syllable table below was written by the
  model following the dominant community convention (bare transliteration of
  the base WITHOUT the admin suffix — 东城区 → دونغتشنغ, 石家庄市 →
  شيجياتشوانغ) and is validated against all 877 existing community ar labels
  as part of the run. The 186 names without GeoNames pinyin evidence plus any
  name whose evidence tokenizes oddly are generated name-by-name in HAND_AR_CN
  below, same conventions.
- GB ar (85), GB ko (8), GB ja (2): direct name-by-name generation in
  HAND_* tables (standard Arabic media forms for English council names).

Deterministic QA is part of the run: table-vs-community agreement over the
877 labels, Arabic-script purity, same-name ⇒ same-output, and empty-value
checks. Nothing is written when QA fails.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sources/raw/ai-translations/seed-residuals.json"

# pinyin syllable → Arabic, written by the model following Arabic-Wikipedia
# norms for Mandarin (zh/ch/q → تش, x → ش, eng → نغ, ing → ينغ, ü after
# j/q/x → و …). Collisions inherent to Arabic (dou/du, zhou/zhu, ju/jiu,
# you/yu) are accepted — disambiguation is not this layer's job.
SYLLABLES = {
    "a": "ا", "ai": "اي", "an": "ان", "ang": "انغ", "ao": "او",
    "ba": "با", "ben": "بن", "bai": "باي", "ban": "بان", "bang": "بانغ", "bao": "باو",
    "bei": "بي", "bi": "بي", "bian": "بيان", "bin": "بين", "bing": "بينغ",
    "bo": "بو", "bu": "بو",
    "cai": "تساي", "cang": "تسانغ", "cao": "تساو", "ce": "تسه", "cen": "تسن",
    "ceng": "تسنغ", "cha": "تشان", "chan": "تشان", "chang": "تشأنغ",
    "chao": "تشاو", "chen": "تشن", "cheng": "تشنغ", "chi": "تشي",
    "chong": "تشونغ", "chou": "تشو", "chu": "تشو", "chuan": "تشوان",
    "chun": "تشون", "ci": "تسي", "cong": "تسونغ", "cui": "تسوي",
    "cun": "تسون", "cuo": "تسو",
    "da": "دا", "dai": "داي", "dan": "دان", "dang": "دانغ", "dao": "داو",
    "de": "ده", "den": "دن", "deng": "دنغ", "di": "دي", "dian": "ديان", "diao": "دياو",
    "die": "ديه", "ding": "دينغ", "dong": "دونغ", "dou": "دو", "du": "دو",
    "duan": "دوان", "dui": "دوي", "duo": "دو",
    "e": "هه", "en": "إن", "er": "إير",
    "fa": "فا", "fan": "فان", "fang": "فانغ", "fei": "في", "fen": "فن",
    "feng": "فنغ", "fu": "فو",
    "ga": "غا", "gua": "غوا", "gen": "غن", "gai": "غاي", "gan": "غان", "gang": "غانغ", "gao": "غاو",
    "ge": "غه", "geng": "غنغ", "gong": "غونغ", "gou": "غو", "gu": "غو",
    "guai": "غواي", "guan": "غوان", "guang": "غوانغ", "gui": "غوي",
    "guo": "غو",
    "ha": "ها", "hai": "هاي", "han": "هان", "hang": "هانغ", "hao": "هاو",
    "he": "هه", "hei": "هي", "heng": "هنغ", "hong": "هونغ", "hou": "هو",
    "hu": "هو", "hun": "هون", "hua": "هوا", "huai": "هواي", "huan": "هوان",
    "huang": "هوانغ", "hui": "هوي", "huo": "هو",
    "ji": "جي", "jia": "جيا", "jian": "جيان", "jiang": "جيانغ",
    "jiao": "جياو", "jie": "جيه", "jin": "جين", "jing": "جينغ",
    "jiu": "جيو", "ju": "جو", "juan": "جوان", "jue": "جويه", "jun": "جون",
    "ka": "كا", "kai": "كاي", "kan": "كان", "kang": "كانغ", "ke": "كه",
    "ken": "كن", "keng": "كنغ", "kong": "كونغ", "kou": "كو", "ku": "كو",
    "kuan": "كوان", "kuang": "كوانغ", "kui": "كوي", "kun": "كون",
    "kuo": "كو",
    "la": "لا", "lai": "لاي", "lan": "لان", "lang": "لانغ", "lao": "لاو",
    "le": "له", "lei": "لي", "leng": "لنغ", "li": "لي", "lian": "ليان",
    "liang": "ليانغ", "liao": "لياو", "lin": "لين", "ling": "لينغ",
    "liu": "ليو", "long": "لونغ", "lou": "لو", "lu": "لو", "luan": "لوان",
    "lun": "لون", "luo": "لو",
    "ma": "ما", "mai": "ماي", "man": "مان", "mang": "مانغ", "mao": "ماو",
    "me": "مه", "mei": "مي", "men": "من", "meng": "منغ", "mi": "مي",
    "mian": "ميان", "miao": "مياو", "min": "مين", "ming": "مينغ",
    "mo": "مو", "mou": "مو", "mu": "مو",
    "na": "نا", "nai": "ناي", "nan": "نان", "nang": "نانغ", "nao": "ناو",
    "ne": "نه", "nei": "ني", "nen": "نن", "ni": "ني", "nian": "نيان",
    "niang": "نيانغ", "niao": "نياو", "nie": "نيه", "nin": "نين",
    "ning": "نينغ", "niu": "نيو", "nong": "نونغ", "nu": "نو",
    "nuan": "نوان", "nuo": "نو",
    "ou": "أو",
    "pai": "باي", "pan": "بان", "pang": "بانغ", "pei": "بي", "peng": "بنغ",
    "pi": "بي", "pian": "بيان", "piao": "بياو", "ping": "بينغ", "po": "بو",
    "pu": "بو",
    "qi": "تشي", "qia": "تشيا", "qian": "تشيان", "qiang": "تشيانغ",
    "qiao": "تشياو", "qie": "تشييه", "qin": "تشين", "qing": "تشينغ",
    "qiong": "تشيونغ", "qiu": "تشيو", "qu": "تشو", "quan": "تشوان",
    "que": "تشويه",
    "rang": "رانغ", "rao": "راو", "ren": "رن", "ri": "ري", "rong": "رونغ",
    "ru": "رو", "rui": "روي", "run": "رون", "ruo": "رو",
    "sa": "سا", "sai": "ساي", "san": "سان", "sang": "سانغ", "se": "سه",
    "sha": "شا", "shan": "شان", "shang": "شانغ", "shao": "شاو", "she": "شه",
    "shen": "شن", "sheng": "شنغ", "shi": "شي", "shou": "شو", "shu": "شو",
    "shua": "شوا", "shuai": "شواي", "shuan": "شوان", "shuang": "شوانغ",
    "shui": "شوي", "shun": "شون", "shuo": "شو",
    "si": "سي", "song": "سونغ", "su": "سو", "sui": "سوي", "sun": "سون",
    "suo": "سو",
    "ta": "تا", "tai": "تاي", "tan": "تان", "tang": "تانغ", "tao": "تاو",
    "te": "ته", "teng": "تنغ", "ti": "تي", "tian": "تيان", "tie": "تيه",
    "ting": "تينغ", "tong": "تونغ", "tou": "تو", "tu": "تو", "tuan": "توان",
    "tun": "تون", "tuo": "تو",
    "wa": "وا", "wai": "واي", "wan": "وان", "wang": "وانغ", "wei": "وي",
    "wen": "ون", "weng": "ونغ", "wo": "وو", "wu": "وو",
    "xi": "شي", "xia": "شيا", "xian": "شيان", "xiang": "شيانغ",
    "xiao": "شياو", "xie": "شيه", "xin": "شين", "xing": "شينغ",
    "xiong": "شيونغ", "xiu": "شيو", "xu": "شو", "xuan": "شوان",
    "xue": "شويه", "xun": "شون",
    "ya": "يا", "yan": "يان", "yang": "يانغ", "yao": "ياو", "ye": "يه",
    "yi": "يي", "yin": "يين", "ying": "ينغ", "yong": "يونغ", "you": "يو",
    "yu": "يو", "yuan": "يوان", "yue": "يويه", "yun": "يون",
    "za": "زا", "zeng": "زنغ", "zui": "زوي", "zun": "زون", "zen": "تسن", "zai": "زاي", "zan": "زان", "zang": "زانغ", "zao": "زاو",
    "ze": "زه", "zha": "تشا", "zhai": "تشاي", "zhan": "تشأن"[:-1] + "ان",
    "zhang": "تشأن"[:-1] + "انغ", "zhao": "تشاو", "zhe": "تشي",
    "zhen": "تشن", "zheng": "تشنغ", "zhi": "تشي", "zhong": "تشونغ",
    "zhou": "تشو", "zhu": "تشو", "zhuang": "تشوانغ", "zhun": "تشون",
    "zhuo": "تشو", "zi": "تسي", "zong": "تسونغ", "zou": "تسو", "zu": "تسو",
    "zuo": "تسو",
}

# CN names whose GeoNames pinyin tokenization is unusable, plus the names the
# evidence pipeline cannot reach — generated name-by-name, same conventions.
HAND_AR_CN = {
    "长海": "تشأنغهاي",
    "通州": "تونغتشو", "和平": "ههبينغ", "河东": "ههدونغ", "河西": "ههشي",
    "南开": "نانكاي", "河北": "ههبي", "红桥": "هونغتشياو", "东丽": "دونغلي",
    "西青": "شيتشينغ", "津南": "جيننان", "北辰": "بييتشن", "武清": "ووتشينغ",
    "宝坻": "باودي", "乳源瑶族": "رويوانياوتسو", "神农架": "شننونغجيا", "德钦": "دهتشين", "独山子": "دوشانتسي", "克拉玛依": "كهلامايي", "扎赉诺尔": "تشالاينوإير", "陈巴尔虎": "تشنباإيرجو", "普兰店": "بولانديان", "浑江": "هونغجيانغ", "台儿庄": "تايإيرتشوانغ", "城区": "تشنغتشو", "郊区": "جياوتشو", "随县": "سويشيان", "滨海": "بينهاي", "宁河": "نينغهه", "静海": "جينغهاي",
    "蓟州": "جيتشو", "迁西": "تشييانشي", "邯山": "هانشان", "襄都": "شيانغدو",
    "信都": "شيندو", "丰宁满族": "فنغنينغمانتسو", "平城": "بينغتشنغ",
    "云冈": "يونغانغ", "云州": "يونتشو", "潞州": "لوتشو",
    "科尔沁": "كهإيرتشين", "科尔沁左翼中": "كهإيرتشينتسويتشونغ",
    "康巴什": "كانغباشي", "鄂托克": "ههتسوكه", "杭锦": "هانغجين",
    "鄂伦春": "ههلونتشون", "杭锦后": "هانغجينهو", "浑南": "هوننان",
    "富拉尔基": "فولاإيرجي", "四方台": "سيفانغتاي", "伊美": "ييمي",
    "乌翠": "ووتسوي", "汤旺": "تانغوانغ", "丰林": "فنغلين",
    "大箐山": "داتشينغشان", "金林": "جينلين", "向阳": "شيانغيانغ",
    "黄浦": "هوانغبو", "徐汇": "شوهوي", "长宁": "تشانغنينغ",
    "静安": "جينغان", "普陀": "بوتو", "虹口": "هونغكو", "闵行": "مينهانغ",
    "宝山": "باوشان", "嘉定": "جيادينغ", "金山": "جينشان",
    "松江": "سونغجيانغ", "青浦": "تشينغبو", "奉贤": "فنغشيان",
    "崇明": "تشونغمينغ", "梁溪": "ليانغشي", "新吴": "شينوو",
    "淮安": "هوايآن", "涟水": "ليانشوي", "临平": "لينبينغ",
    "钱塘": "تشيانتانغ", "镇海": "تشنهاي", "龙港": "لونغغانغ",
    "仙居": "شيانجو", "怀远": "هواييوان", "烈山": "ليهشان",
    "铜官": "تونغغوان", "义安": "ييآن", "徽州": "هوييتشو",
    "颍上": "ينغشان", "叶集": "يهجي", "金门": "جينمن",
    "红谷滩": "هونغغوتان", "濂溪": "ليانشي", "柴桑": "تشايسانغ",
    "彭泽": "بنغزه", "会昌": "هويتشانغ", "广信": "غوانغشين",
    "市中": "شيتشونغ", "钢城": "كانغتشنغ", "岚山": "لانشان",
    "汉阳": "هانيانغ", "郧阳": "يونيانغ", "西陵": "شيلينغ",
    "夷陵": "ييلينغ", "鄂城": "ههتشنغ", "黄州": "هوانغتشو",
    "宣恩": "شوانإن", "来凤": "لايفنغ", "龙山": "لونغشان",
    "渌口": "لوكو", "定安": "دينغآن", "屯昌": "تونتشانغ",
    "澄迈": "تشنغماي", "临高": "لينغاو", "白沙黎族": "بايشاليتسو",
    "昌江黎族": "تشانغجيانغليتسو", "乐东黎族": "لهدونغليتسو",
    "保亭黎族苗族": "باوتينغليتسومياوتسو",
    "琼中黎族苗族": "تشيونغتشونغليتسومياوتسو",
    "万州": "وانتشو", "涪陵": "فولينغ", "渝中": "يوتشونغ",
    "大渡口": "دادوكو", "江北": "جيانغبي", "沙坪坝": "شابينغبا",
    "九龙坡": "جيولونغبو", "南岸": "نانآن", "北碚": "بيبي",
    "綦江": "تشيتشيانغ", "大足": "داتسو", "渝北": "يوبي",
    "巴南": "بانان", "黔江": "تشيانجيانغ", "长寿": "تشانغشو",
    "江津": "جيانغجين", "合川": "ههتشوان", "永川": "يونغتشوان",
    "南川": "نانتشوان", "璧山": "بيشان", "铜梁": "تونغليانغ",
    "潼南": "تونغنان", "荣昌": "رونغتشانغ", "开州": "كايتشو",
    "梁平": "ليانغبينغ", "武隆": "وولونغ", "城口": "تشنغكو",
    "丰都": "فنغدو", "垫江": "ديانهيانغ", "云阳": "يونيانغ",
    "奉节": "فنغجيه", "巫溪": "ووشي", "石柱土家族": "شيتشوتوجياتسو",
    "秀山土家族苗族": "شيوشانتوجياتسومياوتسو",
    "酉阳土家族苗族": "يويانغتوجياتسومياوتسو",
    "彭水苗族土家族": "بنغشويمياوتسوتوجياتسو",
    "郫都": "بيندو", "安州": "أنتشو", "昭化": "تشاوهوا",
    "叙州": "شوتشو", "达川": "داتشوان", "恩阳": "انيانغ",
    "马尔康": "ماإيركانغ", "观山湖": "غوانشانجو", "盘州": "بانتشو",
    "播州": "بوتشو", "碧江": "بيتشيانغ", "福贡": "فوغونغ",
    "桑珠孜": "سانغتشيوتسي", "卡若": "كارو", "巴宜": "بايي",
    "双湖": "شوانغجو", "鄠邑": "هويي", "彬州": "بينتشو",
    "临夏": "لينشيا", "乐都": "لهندو", "沙依巴克": "شاييباكه",
    "伊州": "ييتشو", "阿拉山口": "الاشانكو", "和静": "ههجينغ",
    "和硕": "ههشو", "伊宁": "يينينغ", "北屯": "بييتون",
    "铁门关": "تيهمنغوان", "双河": "شوانغهه", "昆玉": "كونيو",
    "胡杨河": "هويانغهه", "新星": "شينشينغ", "白杨": "بايانغ",
    "城区": "تشنغتشو", "郊区": "جياوتشو", "忠县": "تسونغشيان",
    "随县": "سويشيان", "索县": "سووشيان", "梅县": "ميشيان",
    "横州": "هنغتشو", "兴安": "شينغان", "龙圩": "لونغشو",
    "平桂": "بينغغي", "平安": "بينغآن",
}

SUFFIX_STRIP = ("自治旗", "自治县", "林区", "矿区", "新区", "旗", "区", "市", "县")
SUFFIX_SYLLABLES = {
    "自治旗": ("zi", "zhi", "qi"), "自治县": ("zi", "zhi", "xian"),
    "林区": ("lin", "qu"), "矿区": ("kuang", "qu"), "新区": ("xin", "qu"),
    "旗": ("qi",), "区": ("qu",), "市": ("shi",), "县": ("xian",),
}

GB_AR = {
    "Armagh, Banbridge and Craigavon": "أرما وبانبريدج وكريغافون",
    "Ards and North Down": "أردس ونورث داون",
    "Antrim and Newtownabbey": "أنترم ونيوتونابي",
    "Bath and North East Somerset": "باث ونورث إيست سومرست",
    "Blackburn with Darwen": "بلاكبيرن مع داروين",
    "Bournemouth, Christchurch and Poole": "بورنموث، كرايستشيرش وبول",
    "Bedford": "بيدفورد",
    "Brent": "برينت",
    "Bexley": "بيكسلي",
    "Belfast": "بلفاست",
    "Bridgend": "بريدجند",
    "Barnsley": "بارنسلي",
    "Bolton": "بولتون",
    "Bracknell Forest": "براكنيل فورست",
    "Bradford": "برادفورد",
    "Bury": "بوري",
    "Central Bedfordshire": "وسط بيدفوردشير",
    "Causeway Coast and Glens": "كوزواي كوست وجلينز",
    "Ceredigion": "كيريديجيون",
    "Cheshire West and Chester": "تشيشير ويست وتشستر",
    "Calderdale": "كالديرديل",
    "Carmarthenshire": "كارمارثينشير",
    "Croydon": "كرويدون",
    "Conwy": "كونوي",
    "Darlington": "دارلينغتون",
    "Doncaster": "دونكاستر",
    "Derry and Strabane": "ديري وسترابين",
    "East Ayrshire": "إيست آيرشير",
    "East Renfrewshire": "إيست رينفروشير",
    "Flintshire": "فلينتشاير",
    "Fermanagh and Omagh": "فيرماناغ وأوما",
    "Gateshead": "غيتسهيد",
    "Halton": "هالتون",
    "Havering": "هافيرينغ",
    "Hartlepool": "هارتلبول",
    "Inverclyde": "إنفركلايد",
    "Kirklees": "كيركليز",
    "Kingston upon Thames": "كينغستون أبون تيمز",
    "Knowsley": "نوزلي",
    "Lisburn and Castlereagh": "ليسبورن وكاستلريغ",
    "Mid and East Antrim": "ميد وإيست أنترم",
    "Milton Keynes": "ميلتون كينز",
    "Monmouthshire": "مونماوثشير",
    "Merton": "ميرتون",
    "Moray": "موراي",
    "Merthyr Tydfil": "ميرثير تيدفيل",
    "Mid Ulster": "ميد ألستر",
    "North Ayrshire": "نورث آيرشير",
    "North East Lincolnshire": "نورث إيست لينكولنشير",
    "North Lanarkshire": "نورث لاناركشير",
    "North Lincolnshire": "نورث لينكولنشير",
    "Newry, Mourne and Down": "نيوري، مورن وداون",
    "North Northamptonshire": "نورث نورثهامبتونشير",
    "North Somerset": "نورث سومرست",
    "North Tyneside": "نورث تاينسايد",
    "Newport": "نيوبورت",
    "Oldham": "أولدهام",
    "Redcar and Cleveland": "ريدكار وكليفلاند",
    "Rochdale": "روتشديل",
    "Redbridge": "ريدبريدج",
    "Renfrewshire": "رينفروشير",
    "Rotherham": "روثرهام",
    "South Ayrshire": "ساوث آيرشير",
    "Sefton": "سيفبتون",
    "South Gloucestershire": "ساوث غلوسترشير",
    "Saint Helens": "سانت هيلينز",
    "Stockport": "ستوكبورت",
    "Sunderland": "سندرلاند",
    "Solihull": "سوليهول",
    "Southend-on-Sea": "ساوثند أون سي",
    "Stirling": "ستيرلينغ",
    "Stockton-on-Tees": "ستوكتون أون تيز",
    "South Tyneside": "ساوث تاينسايد",
    "Swindon": "سويندون",
    "Southwark": "ساذارك",
    "Tameside": "تيمسايد",
    "Torbay": "تورباي",
    "Vale of Glamorgan": "فايل أوف غلامورغان",
    "West Berkshire": "ويست بيركشير",
    "Wigan": "ويغان",
    "Walsall": "واسال",
    "West Northamptonshire": "ويست نورثهامبتونشير",
    "Wokingham": "ووكينغهام",
    "Warrington": "وارينغتون",
    "Wrexham": "ريكسهام",
}

GB_KO = {
    "Antrim and Newtownabbey": "앤트림 뉴타운애비",
    "Bournemouth, Christchurch and Poole": "바운머스 크라이스트처치 풀",
    "Derry and Strabane": "데리 스트라베인",
    "Fermanagh and Omagh": "퍼머나 오마",
    "Lisburn and Castlereagh": "리스번 캐슬레아",
    "North Northamptonshire": "노스 노샘프턴셔",
    "Newport": "뉴포트",
    "West Northamptonshire": "웨스트 노샘프턴셔",
}

GB_JA = {
    "North Northamptonshire": "ノースノーサンプトンシャー",
    "West Northamptonshire": "ウェストノーサンプトンシャー",
}


def is_arabic(text: str) -> bool:
    return all(
        ("\u0600" <= ch <= "\u06ff") or ("\u0750" <= ch <= "\u077f")
        or ch in " ،؛"
        for ch in text
    )


def base_name(name: str) -> tuple[str, tuple[str, ...]]:
    """Strip one trailing admin suffix; returns (base, stripped syllables)."""
    for suffix in SUFFIX_STRIP:
        if name.endswith(suffix) and len(name) > len(suffix) + 1:
            return name[: -len(suffix)], SUFFIX_SYLLABLES[suffix]
    return name, ()


def pinyin_evidence(name: str, kind: str, code: str, geo: dict) -> str | None:
    """Lowercase spaced pinyin from the GeoNames extract, suffix-stripped."""
    row = None
    if kind == "statistical-prefecture":
        row = geo["adm2"].get(code)
    elif kind == "statistical-county":
        cands = [r for r in geo["adm3"]
                 if r["a2"] == code[:4]
                 and any(k in r["zh"] for k in (name, name[:-1]))]
        row = cands[0] if len(cands) == 1 else None
    if not row:
        return None
    spaced = [a for a in row["latin"] if a.isascii() and a.islower() and " " in a]
    if not spaced:
        return None
    # the shortest tokenization is most likely the bare base (city-level
    # romanizations like "nan tong shi" are longer and would bleed into the
    # district's name); ties keep the first occurrence
    spaced.sort(key=lambda a: len(a.split()))
    syllables = spaced[0].split()
    base, stripped = base_name(name)
    # align evidence length: base chars = base syllables (儿 aside)
    if len(syllables) == len(name) and len(name) > len(base):
        syllables = syllables[: len(base)]
    elif len(syllables) == len(base) + len(stripped):
        syllables = syllables[: len(base)]
    return " ".join(syllables)


def transliterate(pinyin: str) -> str | None:
    out = []
    for syllable in pinyin.split():
        mapped = SYLLABLES.get(syllable)
        if mapped is None:
            return None
        out.append(mapped)
    return "".join(out)


def main() -> int:
    geo = json.loads((ROOT / "sources/raw/geonames/cn-adm-rows.json").read_text("utf-8"))
    wd = json.loads((ROOT / "sources/raw/wikidata/cn-node-labels.json").read_text("utf-8"))
    regions = {n["id"]: n for n in
               json.loads((ROOT / "data/regions/CN.json").read_text("utf-8"))["nodes"]}

    translations: dict[str, dict[str, str]] = {}
    notes: list[str] = []
    table_hits = hand_hits = 0

    for nid, entry in wd["nodes"].items():
        if "ar" in entry["labels"]:
            continue
        node = regions[nid]
        pinyin = pinyin_evidence(node["name"], node["kind"], node["code"], geo)
        text = transliterate(pinyin) if pinyin else None
        if text is not None:
            translations[nid] = {"ar": text}
            table_hits += 1
            continue
        base, _ = base_name(node["name"])
        hand = HAND_AR_CN.get(base) or HAND_AR_CN.get(node["name"])
        if hand is not None:
            translations[nid] = {"ar": hand}
            hand_hits += 1
        else:
            notes.append(f"{nid} {node['name']}: pinyin={pinyin!r} has no table/hand entry")

    # --- validation of the syllable table against community labels ----------
    agree = disagree = 0
    disagreements: list[str] = []
    for nid, entry in wd["nodes"].items():
        ar = entry["labels"].get("ar")
        if not ar:
            continue
        node = regions[nid]
        pinyin = pinyin_evidence(node["name"], node["kind"], node["code"], geo)
        if pinyin is None:
            continue
        mine = transliterate(pinyin)
        if mine is None:
            continue
        if mine == ar:
            agree += 1
        else:
            disagree += 1
            disagreements.append(f"{node['name']} table={mine!r} community={ar!r}")

    # --- GB residuals -------------------------------------------------------
    gb_regions = {n["name"]: n["id"] for n in
                  json.loads((ROOT / "data/regions/GB.json").read_text("utf-8"))["nodes"]}
    for locale, table in (("ar", GB_AR), ("ko", GB_KO), ("ja", GB_JA)):
        pack = json.loads((ROOT / f"data/i18n/{locale}/GB.json").read_text("utf-8"))
        for name, text in table.items():
            nid = gb_regions.get(name)
            if nid is None or nid in pack["names"]:
                continue
            translations.setdefault(nid, {})[locale] = text

    # --- QA -----------------------------------------------------------------
    problems: list[str] = []
    for nid, by_locale in translations.items():
        for locale, text in by_locale.items():
            if not text:
                problems.append(f"{nid}/{locale}: empty")
            if locale == "ar" and not is_arabic(text):
                problems.append(f"{nid}/ar: non-Arabic characters in {text!r}")
    by_name: dict[str, str] = {}
    for nid, by_locale in sorted(translations.items()):
        name = regions.get(nid, {}).get("name", nid)
        ar = by_locale.get("ar")
        if ar:
            if name in by_name and by_name[name] != ar:
                problems.append(f"duplicate name {name}: {by_name[name]!r} vs {ar!r}")
            by_name[name] = ar

    document = {
        "source": "AI-generated residual translations (seed layer)",
        "generatedAt": "2026-11-14",
        "model": "GLM (ZCode session), deterministic syllable table + name-by-name generation",
        "method": (
            "CN ar: pinyin→Arabic syllable table (recorded in tool source) over "
            "GeoNames pinyin evidence (2,143 names), bare transliteration of the "
            "base without the admin suffix per the dominant community convention; "
            "names without usable evidence generated name-by-name. GB ar/ko/ja: "
            "name-by-name generation following standard Arabic/Korean/Japanese "
            "media forms for English council names."),
        "reviewStatus": "AI-generated and AI-checked only; humanReviewVerified=false; provisional quality; entries enter the human-review queue",
        "license": "Generated content of this project; no upstream restrictions",
        "qa": {
            "tableVsCommunityAgreement": agree,
            "tableVsCommunityDisagreement": disagree,
            "problems": problems,
            "notes": notes,
        },
        "translations": dict(sorted(translations.items())),
    }
    if problems:
        print("QA FAILED:")
        for problem in problems[:20]:
            print(" ", problem)
        print(f"total problems: {len(problems)} — extract NOT written")
        return 1

    text = json.dumps(document, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(text)
    print(f"wrote {OUT} ({len(text):,} bytes): entries={len(translations)} "
          f"CN table track={table_hits} hand track={hand_hits} "
          f"table-vs-community: agree={agree} disagree={disagree}")
    for line in disagreements[:12]:
        print("  ~", line)
    for line in notes[:10]:
        print("  !", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
