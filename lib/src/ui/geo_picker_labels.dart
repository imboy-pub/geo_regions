// SPDX-License-Identifier: BSD-3-Clause
/// Picker UI labels with ten-language defaults (P1-07).
///
/// The picker never invents copy and never references a host product
/// (GR/AT-15): every visible string comes from [GeoPickerLabels]. The
/// defaults below cover the ten primary locales used across the project
/// (CONSUMER_CONTRACT §3); hosts override per field for anything else.
///
/// The coverage wording is deliberate: an empty child list of an
/// `unknown`-coverage node is announced as "coverage unknown", never as
/// "reached the deepest level" — unknown coverage must not impersonate a
/// verified endpoint (AT-11, DEMO_UX).
library;

import '../names.dart' show kGeoLocaleAliases;

/// All user-facing strings the default picker UI can render.
class GeoPickerLabels {
  /// Creates a label set; every field is required so hosts see the full
  /// surface they must translate.
  const GeoPickerLabels({
    required this.searchHint,
    required this.confirm,
    required this.back,
    required this.retry,
    required this.discard,
    required this.discardTitle,
    required this.cancel,
    required this.clearSearch,
    required this.loading,
    required this.noResults,
    required this.noResultsHint,
    required this.coverageUnknown,
    required this.noChildRegions,
    required this.error,
    required this.bundled,
    required this.cached,
    required this.online,
    required this.draft,
    required this.unsaved,
    required this.countries,
    this.fallbackBadge,
    this.tentativeBadge,
  });

  /// Search field placeholder.
  final String searchHint;

  /// Primary confirmation action.
  final String confirm;

  /// One-level-up navigation action.
  final String back;

  /// Retry after a load or confirm failure.
  final String retry;

  /// Discard action button.
  final String discard;

  /// Discard confirmation dialog title.
  final String discardTitle;

  /// Keep the draft (dialog cancel).
  final String cancel;

  /// Search clear button tooltip.
  final String clearSearch;

  /// Live-region text while rows load.
  final String loading;

  /// Search produced no hits.
  final String noResults;

  /// Hint under [noResults].
  final String noResultsHint;

  /// Node coverage is `unknown`: the snapshot does not know whether finer
  /// regions exist. Never rendered as "deepest level reached".
  final String coverageUnknown;

  /// Declared coverage is complete and lists no children.
  final String noChildRegions;

  /// Load or confirm failure headline.
  final String error;

  /// Availability badge: resource ships with the app bundle.
  final String bundled;

  /// Availability badge: previously fetched and cached.
  final String cached;

  /// Availability badge: served remotely.
  final String online;

  /// Draft path heading.
  final String draft;

  /// Badge: draft differs from the last confirmed selection.
  final String unsaved;

  /// Breadcrumb root for the country screen (standalone picker).
  final String countries;

  /// Optional badge appended to labels served outside the requested
  /// locale's own chain (fallback). `null` disables the badge.
  final String? fallbackBadge;

  /// Optional badge appended to tentatively-reviewed names
  /// (`provisional`/`unconfirmed`, AT-14). `null` disables the badge.
  final String? tentativeBadge;

  /// Resolves [locale] to the built-in defaults (`zh-CN` maps to the
  /// `zh-Hans` column via the project alias table); falls back to English.
  static GeoPickerLabels forLocale(String locale) =>
      _defaults[locale] ??
      _defaults[kGeoLocaleAliases[locale]] ??
      _defaults['en']!;

  /// Returns a copy with the given strings replaced; hosts typically start
  /// from `GeoPickerLabels.forLocale(...)` and override a few fields.
  GeoPickerLabels copyWith({
    String? searchHint,
    String? confirm,
    String? back,
    String? retry,
    String? discard,
    String? discardTitle,
    String? cancel,
    String? clearSearch,
    String? loading,
    String? noResults,
    String? noResultsHint,
    String? coverageUnknown,
    String? noChildRegions,
    String? error,
    String? bundled,
    String? cached,
    String? online,
    String? draft,
    String? unsaved,
    String? countries,
    String? fallbackBadge,
    String? tentativeBadge,
  }) {
    return GeoPickerLabels(
      searchHint: searchHint ?? this.searchHint,
      confirm: confirm ?? this.confirm,
      back: back ?? this.back,
      retry: retry ?? this.retry,
      discard: discard ?? this.discard,
      discardTitle: discardTitle ?? this.discardTitle,
      cancel: cancel ?? this.cancel,
      clearSearch: clearSearch ?? this.clearSearch,
      loading: loading ?? this.loading,
      noResults: noResults ?? this.noResults,
      noResultsHint: noResultsHint ?? this.noResultsHint,
      coverageUnknown: coverageUnknown ?? this.coverageUnknown,
      noChildRegions: noChildRegions ?? this.noChildRegions,
      error: error ?? this.error,
      bundled: bundled ?? this.bundled,
      cached: cached ?? this.cached,
      online: online ?? this.online,
      draft: draft ?? this.draft,
      unsaved: unsaved ?? this.unsaved,
      countries: countries ?? this.countries,
    );
  }
}

const Map<String, GeoPickerLabels> _defaults = <String, GeoPickerLabels>{
  'zh-Hans': GeoPickerLabels(
    searchHint: '搜索名称或 ID',
    confirm: '确认选择',
    back: '返回上一级',
    retry: '重试',
    discard: '放弃修改',
    discardTitle: '放弃尚未确认的选择？',
    cancel: '继续选择',
    clearSearch: '清除搜索',
    loading: '正在加载地区…',
    noResults: '没有匹配的地区',
    noResultsHint: '试试其他名称或地区代码。',
    coverageUnknown: '数据范围未知',
    noChildRegions: '数据未包含下级地区',
    error: '暂时无法加载',
    bundled: '随包离线',
    cached: '已缓存',
    online: '在线',
    draft: '当前路径',
    unsaved: '尚未确认',
    countries: '国家与地区',
    fallbackBadge: '未翻译',
    tentativeBadge: '暂定',
  ),
  'zh-Hant': GeoPickerLabels(
    searchHint: '搜尋名稱或 ID',
    confirm: '確認選擇',
    back: '返回上一級',
    retry: '重試',
    discard: '放棄修改',
    discardTitle: '放棄尚未確認的選擇？',
    cancel: '繼續選擇',
    clearSearch: '清除搜尋',
    loading: '正在載入地區…',
    noResults: '沒有符合的地區',
    noResultsHint: '試試其他名稱或地區代碼。',
    coverageUnknown: '資料範圍未知',
    noChildRegions: '資料未包含下級地區',
    error: '暫時無法載入',
    bundled: '隨包離線',
    cached: '已快取',
    online: '線上',
    draft: '目前路徑',
    unsaved: '尚未確認',
    countries: '國家與地區',
    fallbackBadge: '未翻譯',
    tentativeBadge: '暫定',
  ),
  'en': GeoPickerLabels(
    searchHint: 'Search names or IDs',
    confirm: 'Confirm selection',
    back: 'Go up one level',
    retry: 'Retry',
    discard: 'Discard changes',
    discardTitle: 'Discard your unconfirmed selection?',
    cancel: 'Keep choosing',
    clearSearch: 'Clear search',
    loading: 'Loading regions…',
    noResults: 'No matching regions',
    noResultsHint: 'Try another name or region code.',
    coverageUnknown: 'Coverage of this level is unknown in this dataset',
    noChildRegions: 'This dataset includes no child regions here',
    error: 'Unable to load right now',
    bundled: 'Bundled offline',
    cached: 'Cached',
    online: 'Online',
    draft: 'Current path',
    unsaved: 'Unconfirmed',
    countries: 'Countries & regions',
    fallbackBadge: 'not translated',
    tentativeBadge: 'provisional',
  ),
  'ja': GeoPickerLabels(
    searchHint: '名前・ID を検索',
    confirm: '選択を確定',
    back: '上の階層へ',
    retry: '再試行',
    discard: '変更を破棄',
    discardTitle: '未確定の選択を破棄しますか？',
    cancel: '選択を続ける',
    clearSearch: '検索をクリア',
    loading: '地域を読み込み中…',
    noResults: '一致する地域がありません',
    noResultsHint: '別の名前や地域コードをお試しください。',
    coverageUnknown: 'この階層のデータ範囲は不明です',
    noChildRegions: 'このデータに下位地域は含まれていません',
    error: '読み込めませんでした',
    bundled: 'オフライン同梱',
    cached: 'キャッシュ済み',
    online: 'オンライン',
    draft: '現在の階層',
    unsaved: '未確定',
    countries: '国と地域',
    fallbackBadge: '未翻訳',
    tentativeBadge: '暫定',
  ),
  'ko': GeoPickerLabels(
    searchHint: '이름 또는 ID 검색',
    confirm: '선택 확인',
    back: '상위 단계로',
    retry: '다시 시도',
    discard: '변경 취소',
    discardTitle: '확인하지 않은 선택을 취소할까요?',
    cancel: '계속 선택',
    clearSearch: '검색 지우기',
    loading: '지역 로딩 중…',
    noResults: '일치하는 지역이 없습니다',
    noResultsHint: '다른 이름이나 지역 코드를 입력하세요.',
    coverageUnknown: '이 수준의 데이터 범위는 알 수 없습니다',
    noChildRegions: '이 데이터에 하위 지역이 없습니다',
    error: '지금 불러올 수 없습니다',
    bundled: '오프라인 포함',
    cached: '캐시됨',
    online: '온라인',
    draft: '현재 경로',
    unsaved: '확인 전',
    countries: '국가 및 지역',
    fallbackBadge: '번역 없음',
    tentativeBadge: '임시',
  ),
  'ru': GeoPickerLabels(
    searchHint: 'Поиск по названию или ID',
    confirm: 'Подтвердить выбор',
    back: 'На уровень выше',
    retry: 'Повторить',
    discard: 'Отменить изменения',
    discardTitle: 'Отменить неподтверждённый выбор?',
    cancel: 'Продолжить выбор',
    clearSearch: 'Очистить поиск',
    loading: 'Загрузка регионов…',
    noResults: 'Ничего не найдено',
    noResultsHint: 'Попробуйте другое название или код.',
    coverageUnknown: 'Объём данных этого уровня неизвестен',
    noChildRegions: 'В этих данных нет дочерних регионов',
    error: 'Не удалось загрузить',
    bundled: 'В приложении',
    cached: 'В кэше',
    online: 'Онлайн',
    draft: 'Текущий путь',
    unsaved: 'Не подтверждено',
    countries: 'Страны и территории',
    fallbackBadge: 'нет перевода',
    tentativeBadge: 'предварительно',
  ),
  'de': GeoPickerLabels(
    searchHint: 'Namen oder IDs suchen',
    confirm: 'Auswahl bestätigen',
    back: 'Eine Ebene zurück',
    retry: 'Erneut versuchen',
    discard: 'Änderungen verwerfen',
    discardTitle: 'Unbestätigte Auswahl verwerfen?',
    cancel: 'Weiter auswählen',
    clearSearch: 'Suche löschen',
    loading: 'Regionen werden geladen…',
    noResults: 'Keine Treffer',
    noResultsHint: 'Versuche einen anderen Namen oder Gebietscode.',
    coverageUnknown: 'Datenumfang dieser Ebene ist unbekannt',
    noChildRegions: 'Keine untergeordneten Gebiete in diesen Daten',
    error: 'Laden nicht möglich',
    bundled: 'Offline enthalten',
    cached: 'Im Cache',
    online: 'Online',
    draft: 'Aktueller Pfad',
    unsaved: 'Unbestätigt',
    countries: 'Länder und Gebiete',
    fallbackBadge: 'nicht übersetzt',
    tentativeBadge: 'vorläufig',
  ),
  'fr': GeoPickerLabels(
    searchHint: 'Rechercher un nom ou un ID',
    confirm: 'Confirmer le choix',
    back: 'Niveau précédent',
    retry: 'Réessayer',
    discard: 'Abandonner',
    discardTitle: 'Abandonner le choix non confirmé ?',
    cancel: 'Continuer',
    clearSearch: 'Effacer la recherche',
    loading: 'Chargement des régions…',
    noResults: 'Aucune région trouvée',
    noResultsHint: 'Essayez un autre nom ou code de région.',
    coverageUnknown: 'Étendue de données inconnue à ce niveau',
    noChildRegions: 'Aucune sous-région dans ces données',
    error: 'Chargement impossible',
    bundled: 'Inclus hors ligne',
    cached: 'En cache',
    online: 'En ligne',
    draft: 'Chemin actuel',
    unsaved: 'Non confirmé',
    countries: 'Pays et territoires',
    fallbackBadge: 'non traduit',
    tentativeBadge: 'provisoire',
  ),
  'it': GeoPickerLabels(
    searchHint: 'Cerca nomi o ID',
    confirm: 'Conferma selezione',
    back: 'Torna al livello precedente',
    retry: 'Riprova',
    discard: 'Annulla modifiche',
    discardTitle: 'Annullare la selezione non confermata?',
    cancel: 'Continua a scegliere',
    clearSearch: 'Cancella ricerca',
    loading: 'Caricamento regioni…',
    noResults: 'Nessuna regione trovata',
    noResultsHint: 'Prova un altro nome o codice di regione.',
    coverageUnknown: 'Copertura dati sconosciuta a questo livello',
    noChildRegions: 'Nessuna sottoregione in questi dati',
    error: 'Impossibile caricare',
    bundled: 'Incluso offline',
    cached: 'Nella cache',
    online: 'Online',
    draft: 'Percorso attuale',
    unsaved: 'Da confermare',
    countries: 'Paesi e territori',
    fallbackBadge: 'non tradotto',
    tentativeBadge: 'provvisorio',
  ),
  'ar': GeoPickerLabels(
    searchHint: 'ابحث بالاسم أو المعرّف',
    confirm: 'تأكيد الاختيار',
    back: 'العودة مستوى واحدًا',
    retry: 'إعادة المحاولة',
    discard: 'تجاهل التغييرات',
    discardTitle: 'هل تريد تجاهل الاختيار غير المؤكد؟',
    cancel: 'متابعة الاختيار',
    clearSearch: 'مسح البحث',
    loading: 'جارٍ تحميل المناطق…',
    noResults: 'لا توجد مناطق مطابقة',
    noResultsHint: 'جرّب اسمًا أو رمز منطقة آخر.',
    coverageUnknown: 'نطاق البيانات غير معروف عند هذا المستوى',
    noChildRegions: 'لا توجد مناطق فرعية في هذه البيانات',
    error: 'تعذّر التحميل الآن',
    bundled: 'متاح دون اتصال',
    cached: 'محفوظ مؤقتًا',
    online: 'متصل',
    draft: 'المسار الحالي',
    unsaved: 'غير مؤكد',
    countries: 'الدول والمناطق',
    fallbackBadge: 'غير مترجم',
    tentativeBadge: 'مبدئي',
  ),
};
