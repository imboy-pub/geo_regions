// SPDX-License-Identifier: BSD-3-Clause
// Demo chrome copy: display-language names, web deep-link locales and the
// ten-language word table for the demo's own headings and controls. Region
// copy lives in the SDK's GeoPickerLabels; this file is demo-only chrome.
library;

// The demo chrome uses the SDK's own material library on purpose (one
// coherent widget set with the SDK picker; see lib/main.dart).
// ignore_for_file: deprecated_member_use

import 'package:flutter/material.dart';

/// Maps the demo language keys to the BCP 47 locales used for framework copy.
const Map<String, Locale> demoLocaleTags = <String, Locale>{
  'zh-Hans': Locale.fromSubtags(
    languageCode: 'zh',
    scriptCode: 'Hans',
    countryCode: 'CN',
  ),
  'zh-Hant': Locale.fromSubtags(
    languageCode: 'zh',
    scriptCode: 'Hant',
    countryCode: 'TW',
  ),
  'en': Locale('en', 'US'),
  'ja': Locale('ja', 'JP'),
  'ko': Locale('ko', 'KR'),
  'ru': Locale('ru', 'RU'),
  'de': Locale('de', 'DE'),
  'fr': Locale('fr', 'FR'),
  'it': Locale('it', 'IT'),
  'ar': Locale('ar', 'SA'),
};

/// Display names of the demo languages (demo chrome, not data).
const Map<String, String> demoLanguageNames = <String, String>{
  'zh-Hans': '简体中文',
  'zh-Hant': '繁體中文',
  'en': 'English',
  'ja': '日本語',
  'ko': '한국어',
  'ru': 'Русский',
  'de': 'Deutsch',
  'fr': 'Français',
  'it': 'Italiano',
  'ar': 'العربية',
};

const List<String> _demoKeys = <String>[
  'heading',
  'subtitle',
  'countries',
  'airplane',
  'fail',
  'dark',
  'language',
  'preview',
  'selected',
  'dataset',
];

const Map<String, List<String>> _demoWords = <String, List<String>>{
  'zh-Hans': <String>[
    '每个地方，都有你的语言。',
    '选择所在地，保留完整路径。',
    '国家与地区',
    '模拟离线',
    '演示加载失败',
    '深色模式',
    '显示语言',
    '演示 · 离线子集与模拟 CDN；加载走完整校验链，不发送真实网络请求',
    '已确认的选择',
    '数据集',
  ],
  'zh-Hant': <String>[
    '每個地方，都有你的語言。',
    '選擇所在地，保留完整路徑。',
    '國家與地區',
    '模擬離線',
    '示範載入失敗',
    '深色模式',
    '顯示語言',
    '示範 · 離線子集與模擬 CDN；載入走完整校驗鏈，不發送真實網路請求',
    '已確認的選擇',
    '資料集',
  ],
  'en': <String>[
    'Every place. Your language.',
    'Choose a place. Keep the complete path.',
    'Countries & regions',
    'Simulate offline',
    'Show load failure',
    'Dark mode',
    'Display language',
    'Demo · offline subset and simulated CDN; loads run the full verification chain, no real network requests',
    'Confirmed selection',
    'Dataset',
  ],
  'ja': <String>[
    'どの場所にも、あなたの言葉を。',
    '地域を選び、階層をそのまま保持。',
    '国と地域',
    'オフラインを再現',
    '読み込みエラーを表示',
    'ダークモード',
    '表示言語',
    'デモ · オフライン同梱と擬似 CDN。読み込みは検証チェーン全体を通ります',
    '確定した選択',
    'データセット',
  ],
  'ko': <String>[
    '모든 지역을, 나의 언어로.',
    '지역을 선택하고 전체 경로를 유지하세요.',
    '국가 및 지역',
    '오프라인 시뮬레이션',
    '로딩 실패 표시',
    '다크 모드',
    '표시 언어',
    '데모 · 오프라인 하위 집합과 시뮬레이션 CDN. 로딩은 전체 검증 체인을 통과합니다',
    '확인된 선택',
    '데이터세트',
  ],
  'ru': <String>[
    'Любое место. На вашем языке.',
    'Выберите место, сохраняя полный путь.',
    'Страны и территории',
    'Без сети',
    'Показать ошибку',
    'Тёмная тема',
    'Язык интерфейса',
    'Демо · офлайн-подмножество и имитация CDN; загрузка идёт через полную проверку целостности',
    'Подтверждённый выбор',
    'Набор данных',
  ],
  'de': <String>[
    'Jeder Ort. Deine Sprache.',
    'Wähle einen Ort mit vollständigem Pfad.',
    'Länder und Gebiete',
    'Offline simulieren',
    'Ladefehler zeigen',
    'Dunkles Design',
    'Anzeigesprache',
    'Demo · Offline-Teilmenge und simulierte CDN; Laden durchläuft die komplette Prüfkette',
    'Bestätigte Auswahl',
    'Datensatz',
  ],
  'fr': <String>[
    'Chaque lieu. Votre langue.',
    'Choisissez un lieu et gardez le chemin complet.',
    'Pays et territoires',
    'Simuler le mode hors ligne',
    'Afficher une erreur',
    'Mode sombre',
    'Langue d’affichage',
    'Démo · sous-ensemble hors ligne et CDN simulé ; le chargement suit toute la chaîne de vérification',
    'Choix confirmé',
    'Jeu de données',
  ],
  'it': <String>[
    'Ogni luogo. La tua lingua.',
    'Scegli un luogo e conserva il percorso completo.',
    'Paesi e territori',
    'Simula offline',
    'Mostra errore',
    'Tema scuro',
    'Lingua visualizzata',
    'Demo · sottoinsieme offline e CDN simulato; il caricamento segue l’intera catena di verifica',
    'Selezione confermata',
    'Set di dati',
  ],
  'ar': <String>[
    'كل مكان، بلغتك.',
    'اختر مكانًا واحتفظ بمساره الكامل.',
    'الدول والمناطق',
    'محاكاة عدم الاتصال',
    'عرض فشل التحميل',
    'الوضع الداكن',
    'لغة العرض',
    'عرض توضيحي · مجموعة فرعية دون اتصال وشبكة توصيل محاكاة؛ يمرّ التحميل بسلسلة التحقق كاملة',
    'الاختيار المؤكد',
    'مجموعة البيانات',
  ],
};

String demoWord(String locale, String key) {
  final index = _demoKeys.indexOf(key);
  if (index < 0) {
    return key;
  }
  return (_demoWords[locale] ?? _demoWords['en']!)[index];
}
