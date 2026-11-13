// SPDX-License-Identifier: BSD-3-Clause
// Hand-curated illustrative fixtures. They are NOT the production dataset.

const locales = <String, String>{
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

const _keys = <String>[
  'heading', 'subtitle', 'countries', 'choose', 'search', 'confirm', 'back',
  'offline', 'online', 'cached', 'error', 'retry', 'empty', 'deepest', 'selected',
  'unsaved', 'preview', 'network', 'airplane', 'dark', 'fail', 'clear', 'loading',
  'language', 'cancel', 'discard', 'discardTitle', 'draft', 'sample', 'emptyHint',
];

const _words = <String, List<String>>{
  'zh-Hans': [
    '每个地方，都有你的语言。', '选择所在地，保留完整路径。', '国家与地区', '选择地区',
    '搜索名称或 ID', '确认选择', '返回上一级', '随包离线', '模拟在线', '已缓存',
    '暂时无法加载', '重试', '没有匹配的地区', '已到示例数据最深层级', '已确认的选择',
    '尚未确认', '交互原型 · 所有加载均为模拟；不发送网络请求', '体验控制', '模拟离线',
    '深色模式', '演示加载失败', '清除搜索', '正在加载地区…', '显示语言', '继续选择',
    '放弃修改', '放弃尚未确认的选择？', '当前路径', '示例数据', '试试其他名称或地区代码。',
  ],
  'zh-Hant': [
    '每個地方，都有你的語言。', '選擇所在地，保留完整路徑。', '國家與地區', '選擇地區',
    '搜尋名稱或 ID', '確認選擇', '返回上一級', '隨包離線', '模擬線上', '已快取',
    '暫時無法載入', '重試', '沒有符合的地區', '已到範例資料最深層級', '已確認的選擇',
    '尚未確認', '互動原型 · 所有載入均為模擬；不發送網路請求', '體驗控制', '模擬離線',
    '深色模式', '示範載入失敗', '清除搜尋', '正在載入地區…', '顯示語言', '繼續選擇',
    '放棄修改', '放棄尚未確認的選擇？', '目前路徑', '範例資料', '試試其他名稱或地區代碼。',
  ],
  'en': [
    'Every place. Your language.', 'Choose a place. Keep the complete path.',
    'Countries & regions', 'Choose a region', 'Search names or IDs', 'Confirm selection',
    'Go up one level', 'Bundled offline', 'Simulated online', 'Cached',
    'Unable to load right now', 'Retry', 'No matching regions', 'Deepest fixture level reached',
    'Confirmed selection', 'Unconfirmed', 'Interactive prototype · All loading is simulated; no network requests',
    'Experience controls', 'Simulate offline', 'Dark mode', 'Show load failure', 'Clear search',
    'Loading regions…', 'Display language', 'Keep choosing', 'Discard changes',
    'Discard your unconfirmed selection?', 'Current path', 'Sample data', 'Try another name or region code.',
  ],
  'ja': [
    'どの場所にも、あなたの言葉を。', '地域を選び、階層をそのまま保持。', '国と地域', '地域を選択',
    '名前・ID を検索', '選択を確定', '上の階層へ', 'オフライン同梱', 'オンラインを再現', 'キャッシュ済み',
    '読み込めませんでした', '再試行', '一致する地域がありません', 'サンプルの最下層です', '確定した選択',
    '未確定', '操作プロトタイプ · 読み込みはシミュレーションです。通信は行いません', '体験設定', 'オフラインを再現',
    'ダークモード', '読み込みエラーを表示', '検索をクリア', '地域を読み込み中…', '表示言語', '選択を続ける',
    '変更を破棄', '未確定の選択を破棄しますか？', '現在の階層', 'サンプルデータ', '別の名前や地域コードをお試しください。',
  ],
  'ko': [
    '모든 지역을, 나의 언어로.', '지역을 선택하고 전체 경로를 유지하세요.', '국가 및 지역', '지역 선택',
    '이름 또는 ID 검색', '선택 확인', '상위 단계로', '오프라인 포함', '온라인 시뮬레이션', '캐시됨',
    '지금 불러올 수 없습니다', '다시 시도', '일치하는 지역이 없습니다', '샘플의 마지막 단계입니다', '확인된 선택',
    '확인 전', '대화형 프로토타입 · 모든 로딩은 시뮬레이션이며 네트워크 요청이 없습니다', '체험 설정', '오프라인 시뮬레이션',
    '다크 모드', '로딩 실패 표시', '검색 지우기', '지역 로딩 중…', '표시 언어', '계속 선택',
    '변경 취소', '확인하지 않은 선택을 취소할까요?', '현재 경로', '샘플 데이터', '다른 이름이나 지역 코드를 입력하세요.',
  ],
  'ru': [
    'Любое место. На вашем языке.', 'Выберите место, сохраняя полный путь.', 'Страны и территории', 'Выберите регион',
    'Поиск по названию или ID', 'Подтвердить выбор', 'На уровень выше', 'В приложении', 'Имитация сети', 'В кэше',
    'Не удалось загрузить', 'Повторить', 'Ничего не найдено', 'Последний уровень примера', 'Подтверждённый выбор',
    'Не подтверждено', 'Интерактивный прототип · Загрузка имитируется; сетевых запросов нет', 'Настройки просмотра', 'Без сети',
    'Тёмная тема', 'Показать ошибку', 'Очистить поиск', 'Загрузка регионов…', 'Язык интерфейса', 'Продолжить выбор',
    'Отменить изменения', 'Отменить неподтверждённый выбор?', 'Текущий путь', 'Пример данных', 'Попробуйте другое название или код.',
  ],
  'de': [
    'Jeder Ort. Deine Sprache.', 'Wähle einen Ort mit vollständigem Pfad.', 'Länder und Gebiete', 'Region auswählen',
    'Namen oder IDs suchen', 'Auswahl bestätigen', 'Eine Ebene zurück', 'Offline enthalten', 'Netzsimulation', 'Im Cache',
    'Laden nicht möglich', 'Erneut versuchen', 'Keine Treffer', 'Tiefste Ebene der Beispieldaten', 'Bestätigte Auswahl',
    'Unbestätigt', 'Interaktiver Prototyp · Alle Ladevorgänge sind simuliert; keine Netzwerkanfragen', 'Ansicht einstellen', 'Offline simulieren',
    'Dunkles Design', 'Ladefehler zeigen', 'Suche löschen', 'Regionen werden geladen…', 'Anzeigesprache', 'Weiter auswählen',
    'Änderungen verwerfen', 'Unbestätigte Auswahl verwerfen?', 'Aktueller Pfad', 'Beispieldaten', 'Versuche einen anderen Namen oder Gebietscode.',
  ],
  'fr': [
    'Chaque lieu. Votre langue.', 'Choisissez un lieu et gardez le chemin complet.', 'Pays et territoires', 'Choisir une région',
    'Rechercher un nom ou un ID', 'Confirmer le choix', 'Niveau précédent', 'Inclus hors ligne', 'Réseau simulé', 'En cache',
    'Chargement impossible', 'Réessayer', 'Aucune région trouvée', 'Dernier niveau des données de démonstration', 'Choix confirmé',
    'Non confirmé', 'Prototype interactif · Chargement simulé ; aucune requête réseau', 'Réglages de démonstration', 'Simuler le mode hors ligne',
    'Mode sombre', 'Afficher une erreur', 'Effacer la recherche', 'Chargement des régions…', 'Langue d’affichage', 'Continuer',
    'Abandonner', 'Abandonner le choix non confirmé ?', 'Chemin actuel', 'Données de démonstration', 'Essayez un autre nom ou code de région.',
  ],
  'it': [
    'Ogni luogo. La tua lingua.', 'Scegli un luogo e conserva il percorso completo.', 'Paesi e territori', 'Scegli una regione',
    'Cerca nomi o ID', 'Conferma selezione', 'Torna al livello precedente', 'Incluso offline', 'Rete simulata', 'Nella cache',
    'Impossibile caricare', 'Riprova', 'Nessuna regione trovata', 'Ultimo livello dei dati di esempio', 'Selezione confermata',
    'Da confermare', 'Prototipo interattivo · Caricamenti simulati; nessuna richiesta di rete', 'Controlli della demo', 'Simula offline',
    'Tema scuro', 'Mostra errore', 'Cancella ricerca', 'Caricamento regioni…', 'Lingua visualizzata', 'Continua a scegliere',
    'Annulla modifiche', 'Annullare la selezione non confermata?', 'Percorso attuale', 'Dati di esempio', 'Prova un altro nome o codice di regione.',
  ],
  'ar': [
    'كل مكان، بلغتك.', 'اختر مكانًا واحتفظ بمساره الكامل.', 'الدول والمناطق', 'اختر المنطقة',
    'ابحث بالاسم أو المعرّف', 'تأكيد الاختيار', 'العودة مستوى واحدًا', 'متاح دون اتصال', 'محاكاة الاتصال', 'محفوظ مؤقتًا',
    'تعذّر التحميل الآن', 'إعادة المحاولة', 'لا توجد مناطق مطابقة', 'وصلت إلى آخر مستوى في بيانات المثال', 'الاختيار المؤكد',
    'غير مؤكد', 'نموذج تفاعلي · كل عمليات التحميل محاكاة؛ لا توجد طلبات شبكة', 'إعدادات العرض', 'محاكاة عدم الاتصال',
    'الوضع الداكن', 'عرض فشل التحميل', 'مسح البحث', 'جارٍ تحميل المناطق…', 'لغة العرض', 'متابعة الاختيار',
    'تجاهل التغييرات', 'هل تريد تجاهل الاختيار غير المؤكد؟', 'المسار الحالي', 'بيانات مثال', 'جرّب اسمًا أو رمز منطقة آخر.',
  ],
};

String label(String locale, String key) {
  final index = _keys.indexOf(key);
  return index < 0 ? key : (_words[locale] ?? _words['en']!)[index];
}

class DemoCountry {
  const DemoCountry(this.code, this.nativeName, this.names);
  final String code;
  final String nativeName;
  final List<String> names;
  String name(String locale) => names[locales.keys.toList().indexOf(locale)];
  String get rootId => 'cc:$code';
}

const countries = <DemoCountry>[
  DemoCountry('CN', '中国', ['中国', '中國', 'China', '中国', '중국', 'Китай', 'China', 'Chine', 'Cina', 'الصين']),
  DemoCountry('JP', '日本', ['日本', '日本', 'Japan', '日本', '일본', 'Япония', 'Japan', 'Japon', 'Giappone', 'اليابان']),
  DemoCountry('KR', '대한민국', ['韩国', '韓國', 'South Korea', '韓国', '대한민국', 'Республика Корея', 'Südkorea', 'Corée du Sud', 'Corea del Sud', 'كوريا الجنوبية']),
  DemoCountry('US', 'United States', ['美国', '美國', 'United States', 'アメリカ合衆国', '미국', 'США', 'Vereinigte Staaten', 'États-Unis', 'Stati Uniti', 'الولايات المتحدة']),
  DemoCountry('GB', 'United Kingdom', ['英国', '英國', 'United Kingdom', 'イギリス', '영국', 'Великобритания', 'Vereinigtes Königreich', 'Royaume-Uni', 'Regno Unito', 'المملكة المتحدة']),
  DemoCountry('DE', 'Deutschland', ['德国', '德國', 'Germany', 'ドイツ', '독일', 'Германия', 'Deutschland', 'Allemagne', 'Germania', 'ألمانيا']),
  DemoCountry('FR', 'France', ['法国', '法國', 'France', 'フランス', '프랑스', 'Франция', 'Frankreich', 'France', 'Francia', 'فرنسا']),
  DemoCountry('IT', 'Italia', ['意大利', '義大利', 'Italy', 'イタリア', '이탈리아', 'Италия', 'Italien', 'Italie', 'Italia', 'إيطاليا']),
  DemoCountry('RU', 'Россия', ['俄罗斯', '俄羅斯', 'Russia', 'ロシア', '러시아', 'Россия', 'Russland', 'Russie', 'Russia', 'روسيا']),
  DemoCountry('SA', 'السعودية', ['沙特阿拉伯', '沙烏地阿拉伯', 'Saudi Arabia', 'サウジアラビア', '사우디아라비아', 'Саудовская Аравия', 'Saudi-Arabien', 'Arabie saoudite', 'Arabia Saudita', 'المملكة العربية السعودية']),
];

class DemoNode {
  const DemoNode(this.id, this.parentId, this.countryCode, this.nativeName, this.names);
  final String id;
  final String parentId;
  final String countryCode;
  final String nativeName;
  final Map<String, String> names;
  String name(String locale) => names[locale] ?? nativeName;
}

const nodes = <DemoNode>[
  DemoNode('cn:44', 'cc:CN', 'CN', '广东省', {'en': 'Guangdong', 'zh-Hant': '廣東省', 'ja': '広東省'}),
  DemoNode('cn:4403', 'cn:44', 'CN', '深圳市', {'en': 'Shenzhen', 'zh-Hant': '深圳市'}),
  DemoNode('cn:440305', 'cn:4403', 'CN', '南山区', {'en': 'Nanshan District', 'zh-Hant': '南山區'}),
  DemoNode('cn:440304', 'cn:4403', 'CN', '福田区', {'en': 'Futian District', 'zh-Hant': '福田區'}),
  DemoNode('cn:4401', 'cn:44', 'CN', '广州市', {'en': 'Guangzhou', 'zh-Hant': '廣州市'}),
  DemoNode('cn:11', 'cc:CN', 'CN', '北京市', {'en': 'Beijing', 'ja': '北京市'}),
  DemoNode('cn:31', 'cc:CN', 'CN', '上海市', {'en': 'Shanghai', 'ja': '上海市'}),
  DemoNode('jp:13', 'cc:JP', 'JP', '東京都', {'zh-Hans': '东京都', 'en': 'Tokyo'}),
  DemoNode('jp:27', 'cc:JP', 'JP', '大阪府', {'en': 'Osaka'}),
  DemoNode('jp:26', 'cc:JP', 'JP', '京都府', {'en': 'Kyoto'}),
  DemoNode('kr:11', 'cc:KR', 'KR', '서울특별시', {'zh-Hans': '首尔特别市', 'en': 'Seoul'}),
  DemoNode('kr:26', 'cc:KR', 'KR', '부산광역시', {'zh-Hans': '釜山广域市', 'en': 'Busan'}),
  DemoNode('us:CA', 'cc:US', 'US', 'California', {'zh-Hans': '加利福尼亚州', 'zh-Hant': '加利福尼亞州'}),
  DemoNode('us:NY', 'cc:US', 'US', 'New York', {'zh-Hans': '纽约州', 'zh-Hant': '紐約州'}),
  DemoNode('us:WA', 'cc:US', 'US', 'Washington', {'zh-Hans': '华盛顿州', 'zh-Hant': '華盛頓州'}),
  DemoNode('gb:ENG', 'cc:GB', 'GB', 'England', {'zh-Hans': '英格兰', 'zh-Hant': '英格蘭'}),
  DemoNode('gb:SCT', 'cc:GB', 'GB', 'Scotland', {'zh-Hans': '苏格兰', 'zh-Hant': '蘇格蘭'}),
  DemoNode('de:BY', 'cc:DE', 'DE', 'Bayern', {'zh-Hans': '巴伐利亚州', 'en': 'Bavaria'}),
  DemoNode('de:BE', 'cc:DE', 'DE', 'Berlin', {'zh-Hans': '柏林'}),
  DemoNode('fr:IDF', 'cc:FR', 'FR', 'Île-de-France', {'zh-Hans': '法兰西岛大区', 'en': 'Île-de-France'}),
  DemoNode('fr:BRE', 'cc:FR', 'FR', 'Bretagne', {'zh-Hans': '布列塔尼大区', 'en': 'Brittany'}),
  DemoNode('it:25', 'cc:IT', 'IT', 'Lombardia', {'zh-Hans': '伦巴第大区', 'en': 'Lombardy'}),
  DemoNode('it:62', 'cc:IT', 'IT', 'Lazio', {'zh-Hans': '拉齐奥大区', 'en': 'Lazio'}),
  DemoNode('ru:MOW', 'cc:RU', 'RU', 'Москва', {'zh-Hans': '莫斯科', 'en': 'Moscow'}),
  DemoNode('ru:SPE', 'cc:RU', 'RU', 'Санкт-Петербург', {'zh-Hans': '圣彼得堡', 'en': 'Saint Petersburg'}),
  DemoNode('sa:01', 'cc:SA', 'SA', 'الرياض', {'zh-Hans': '利雅得省', 'en': 'Riyadh'}),
  DemoNode('sa:02', 'cc:SA', 'SA', 'مكة المكرمة', {'zh-Hans': '麦加省', 'en': 'Makkah'}),
];
