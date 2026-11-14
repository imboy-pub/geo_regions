// SPDX-License-Identifier: BSD-3-Clause
import 'package:flutter_test/flutter_test.dart';
import 'package:geo_regions/geo_regions.dart';

import 'test_data.dart';

late GeoRegionStructure _cn;
late GeoRegionStructure _jp;
late GeoLocalePack _zhHansCn;
late GeoLocalePack _zhHantCn;
late GeoLocalePack _jaJp;

void main() {
  setUpAll(() {
    _cn = loadStructure('CN');
    _jp = loadStructure('JP');
    _zhHansCn = loadLocalePack('zh-Hans', _cn);
    _zhHantCn = loadLocalePack('zh-Hant', _cn);
    _jaJp = loadLocalePack('ja', _jp);
  });
  aliasTableGroup();
  candidateChainGroup();
  qualityPolicyGroup();
  scriptSeparationGroup();
  resolverGuardsGroup();
  qualityFallbackGroup();
  defaultLocaleGroup();
  idFallbackGroup();
  catalogNameGroup();
}

void aliasTableGroup() {
  group('locale alias table', () {
    test('explicit aliases match CONSUMER_CONTRACT §3', () {
      expect(kGeoLocaleAliases['zh-CN'], 'zh-Hans');
      expect(kGeoLocaleAliases['zh-SG'], 'zh-Hans');
      expect(kGeoLocaleAliases['zh-TW'], 'zh-Hant');
      expect(kGeoLocaleAliases['zh-HK'], 'zh-Hant');
      expect(kGeoLocaleAliases['zh-Hant'], 'zh-Hant');
      expect(kGeoLocaleAliases['en-US'], 'en');
      expect(kGeoLocaleAliases['ja-JP'], 'ja');
      expect(kGeoLocaleAliases['ko-KR'], 'ko');
      expect(kGeoLocaleAliases['ru-RU'], 'ru');
      expect(kGeoLocaleAliases['de-DE'], 'de');
      expect(kGeoLocaleAliases['fr-FR'], 'fr');
      expect(kGeoLocaleAliases['it-IT'], 'it');
      expect(kGeoLocaleAliases['ar-SA'], 'ar');
      // The Dart table must stay in lockstep with config/data_policy.json
      // localeAliases (12 protocol entries + the zh-Hant identity entry).
      expect(kGeoLocaleAliases.length, 13);
    });
  });
}

void candidateChainGroup() {
  group('locale candidate chains', () {
    test('script subtags are never truncated away', () {
      expect(geoLocaleCandidates('zh-Hans'), <String>['zh-Hans']);
      expect(geoLocaleCandidates('zh-Hant'), <String>['zh-Hant']);
      expect(geoLocaleCandidates('zh'), <String>['zh']);
    });

    test('region subtags truncate, aliases apply first', () {
      expect(geoLocaleCandidates('zh-CN'), <String>['zh-CN', 'zh-Hans', 'zh']);
      expect(geoLocaleCandidates('zh-TW'), <String>['zh-TW', 'zh-Hant', 'zh']);
      expect(geoLocaleCandidates('zh-HK'), <String>['zh-HK', 'zh-Hant', 'zh']);
      expect(geoLocaleCandidates('zh-SG'), <String>['zh-SG', 'zh-Hans', 'zh']);
      expect(geoLocaleCandidates('en-US'), <String>['en-US', 'en']);
      expect(geoLocaleCandidates('pt-BR'), <String>['pt-BR', 'pt']);
      expect(geoLocaleCandidates('zh-Hans-CN'), <String>[
        'zh-Hans-CN',
        'zh-Hans',
      ]);
    });
  });
}

void qualityPolicyGroup() {
  group('quality policy', () {
    test('accepted values pass; provisional, unconfirmed and unknown fail '
        'closed', () {
      for (final quality in kGeoAcceptedNameQualities) {
        expect(geoIsQualityAccepted(quality), isTrue, reason: quality);
      }
      expect(geoIsQualityAccepted('provisional'), isFalse);
      expect(geoIsQualityAccepted('unconfirmed'), isFalse);
      expect(geoIsQualityAccepted('machine-candidate'), isFalse);
      expect(geoIsQualityAccepted(null), isFalse);
      expect(geoIsQualityAccepted(''), isFalse);
      expect(
        geoIsQualityAccepted('provisional', optInProvisional: true),
        isTrue,
      );
      expect(
        geoIsQualityAccepted('unconfirmed', optInProvisional: true),
        isTrue,
      );
      // Opting in never unlocks unknown values.
      expect(
        geoIsQualityAccepted('who-knows', optInProvisional: true),
        isFalse,
      );
      expect(geoIsQualityAccepted(null, optInProvisional: true), isFalse);
    });
  });
}

void scriptSeparationGroup() {
  group('script separation (real data)', () {
    test('zh-CN resolves via the explicit alias to a non-fallback name', () {
      final resolver = GeoNameResolver(
        packs: <String, GeoLocalePack>{'zh-Hans': _zhHansCn},
      );
      final name = resolver.resolve(_cn.nodes.first, 'zh-CN');
      expect(name.text, '中国');
      expect(name.resolvedLocale, 'zh-Hans');
      expect(name.quality, 'cldr-json-qualified');
      expect(name.isFallback, isFalse);
      expect(name.source, GeoNameSource.translation);
    });

    test('bare zh never silently lands on zh-Hans', () {
      final resolver = GeoNameResolver(
        packs: <String, GeoLocalePack>{'zh-Hans': _zhHansCn},
      );
      final name = resolver.resolve(_cn.nodes.first, 'zh');
      expect(name.text, isNot('中国'));
      // Falls to the node default name ("China", cldr-json-qualified).
      expect(name.text, 'China');
      expect(name.isFallback, isTrue);
      expect(name.source, GeoNameSource.defaultName);
      expect(name.resolvedLocale, 'en');
    });

    test('zh-Hans and zh-Hant stay separate', () {
      final resolver = GeoNameResolver(
        packs: <String, GeoLocalePack>{
          'zh-Hans': _zhHansCn,
          'zh-Hant': _zhHantCn,
        },
      );
      final simplified = resolver.resolve(_cn.nodes.first, 'zh-CN');
      final traditional = resolver.resolve(_cn.nodes.first, 'zh-Hant');
      expect(simplified.text, '中国');
      expect(traditional.text, '中國');
      expect(traditional.resolvedLocale, 'zh-Hant');
    });

    test('zh-TW and zh-HK reach the zh-Hant pack through the alias table', () {
      // Regression: these protocol aliases were missing from the Dart table,
      // so zh-HK/zh-TW requests degraded to bare zh and lost the traditional
      // pack while the Python reference resolved them.
      final resolver = GeoNameResolver(
        packs: <String, GeoLocalePack>{'zh-Hant': _zhHantCn},
      );
      for (final requested in const <String>['zh-TW', 'zh-HK']) {
        final name = resolver.resolve(_cn.nodes.first, requested);
        expect(name.text, '中國', reason: requested);
        expect(name.resolvedLocale, 'zh-Hant', reason: requested);
        expect(name.isFallback, isFalse, reason: requested);
        expect(name.source, GeoNameSource.translation, reason: requested);
      }
    });

    test('zh-SG reaches the zh-Hans pack through the alias table', () {
      final resolver = GeoNameResolver(
        packs: <String, GeoLocalePack>{'zh-Hans': _zhHansCn},
      );
      final name = resolver.resolve(_cn.nodes.first, 'zh-SG');
      expect(name.text, '中国');
      expect(name.resolvedLocale, 'zh-Hans');
      expect(name.isFallback, isFalse);
    });
  });
}

void resolverGuardsGroup() {
  group('resolver construction', () {
    test('resolver guards against mixed countries', () {
      expect(
        () => GeoNameResolver(
          packs: <String, GeoLocalePack>{'zh-Hans': _zhHansCn, 'ja': _jaJp},
        ),
        throwsArgumentError,
      );
    });
  });
}

void qualityFallbackGroup() {
  group('quality-gated fallbacks (real data)', () {
    test('provisional translations are rejected by default (Tokyo in ja)', () {
      final resolver = GeoNameResolver(
        packs: <String, GeoLocalePack>{'ja': _jaJp},
      );
      final tokyo = _jp.nodes.firstWhere(
        (node) => node.id == 'iso3166-2:JP-13',
      );
      final name = resolver.resolve(tokyo, 'ja');
      // ja pack translation is provisional; the eligible default name
      // "Tokyo" (approved-in-source) is served as a labeled fallback.
      expect(name.text, 'Tokyo');
      expect(name.isFallback, isTrue);
      expect(name.source, GeoNameSource.defaultName);
      expect(name.quality, 'approved-in-source');

      final optedIn = GeoNameResolver(
        packs: <String, GeoLocalePack>{'ja': _jaJp},
        optInProvisional: true,
      );
      final provisional = optedIn.resolve(tokyo, 'ja');
      expect(provisional.text, '東京都');
      expect(provisional.quality, 'provisional');
      expect(provisional.isFallback, isFalse);
    });

    test('missing translations stay missing (deep CN node in en)', () {
      final enCn = loadLocalePack('en', _cn);
      final resolver = GeoNameResolver(
        packs: <String, GeoLocalePack>{'en': enCn},
      );
      // cn-stat:340176 (合肥高新技术产业开发区) has no GeoNames row either, so
      // the en pack keeps the node honestly missing.
      final zone = _cn.nodes.firstWhere(
        (node) => node.id == 'cn-stat:340176',
      );
      expect(enCn.names.containsKey(zone.id), isFalse);
      final name = resolver.resolve(zone, 'en-US');
      // en pack exists but lacks the node; default name is source-native
      // zh-Hans and passes the same quality policy.
      expect(name.text, '合肥高新技术产业开发区');
      expect(name.source, GeoNameSource.defaultName);
      expect(name.isFallback, isTrue);
      expect(name.resolvedLocale, 'zh-Hans');
      expect(name.quality, 'source-native');
    });

    test('GeoNames en overlay: provisional name serves only with opt-in', () {
      final enCn = loadLocalePack('en', _cn);
      final strict = GeoNameResolver(
        packs: <String, GeoLocalePack>{'en': enCn},
      );
      final optedIn = GeoNameResolver(
        packs: <String, GeoLocalePack>{'en': enCn},
        optInProvisional: true,
      );
      final nanshan = _cn.nodes.firstWhere(
        (node) => node.id == 'cn-stat:440305',
      );
      // The machine-matched GeoNames romanization is in the pack marked
      // provisional; the default profile filters it and the labeled native
      // fallback is served instead.
      expect(enCn.names['cn-stat:440305'], 'Nanshan');
      final filtered = strict.resolve(nanshan, 'en-US');
      expect(filtered.text, '南山区');
      expect(filtered.source, GeoNameSource.defaultName);
      expect(filtered.isFallback, isTrue);

      final served = optedIn.resolve(nanshan, 'en-US');
      expect(served.text, 'Nanshan');
      expect(served.quality, 'provisional');
      expect(served.source, GeoNameSource.translation);
      expect(served.isFallback, isFalse);
      expect(served.isTentative, isTrue);
    });
  });
}

void defaultLocaleGroup() {
  group('default locale stage', () {
    test('serves a labeled fallback translation', () {
      final resolver = GeoNameResolver(
        packs: <String, GeoLocalePack>{'zh-Hans': _zhHansCn},
        defaultLocale: 'zh-Hans',
      );
      final name = resolver.resolve(_cn.nodes.first, 'fr');
      expect(name.text, '中国');
      expect(name.source, GeoNameSource.defaultLocaleTranslation);
      expect(name.isFallback, isTrue);
      expect(name.resolvedLocale, 'zh-Hans');
    });
  });
}

GeoRegionNode _provisionalNode(String id, String quality) => GeoRegionNode(
  id: id,
  parentId: 'cc:XX',
  kind: 'subdivision',
  name: 'Maybe Wrong',
  childrenStatus: GeoChildrenStatus.unknown,
  nameLocale: 'en',
  nameQuality: quality,
);

void idFallbackGroup() {
  group('ID fallback (fail closed)', () {
    test('no acceptable name yields a stable-ID fallback result', () {
      final node = _provisionalNode('x:1', 'provisional');
      final resolver = GeoNameResolver();
      final name = resolver.resolve(node, 'zh-CN');
      expect(name.text, isNull);
      expect(name.isFallback, isTrue);
      expect(name.source, GeoNameSource.idFallback);
      expect(name.resolvedLocale, isNull);
      expect(name.quality, isNull);
      expect(name.nodeId, 'x:1');
      expect(name.requestedLocale, 'zh-CN');

      final optedIn = GeoNameResolver(optInProvisional: true);
      expect(optedIn.resolve(node, 'zh-CN').text, 'Maybe Wrong');
    });

    test('missing default-name quality fails closed', () {
      final node = GeoRegionNode(
        id: 'x:2',
        parentId: 'cc:XX',
        kind: 'subdivision',
        name: 'Unnamed',
        childrenStatus: GeoChildrenStatus.unknown,
      );
      expect(GeoNameResolver().resolve(node, 'en').text, isNull);
    });

    test('unknown quality labels fail closed even with provisional opt-in', () {
      final node = _provisionalNode('x:3', 'machine-candidate');
      expect(
        GeoNameResolver(optInProvisional: true).resolve(node, 'en').text,
        isNull,
      );
    });
  });
}

void catalogNameGroup() {
  group('catalog name resolution', () {
    test('zh-Hant and zh-Hans serve separate scripts; zh falls back', () {
      final catalog = loadCountryCatalog();
      final entry = catalog.entryFor('CN')!;
      final resolver = GeoNameResolver(
        catalogPacks: <String, GeoCatalogNames>{
          'zh-Hans': loadCatalogNames('zh-Hans'),
          'zh-Hant': loadCatalogNames('zh-Hant'),
        },
      );
      expect(resolver.resolveCatalogName(entry, 'zh-Hant').text, '中國');
      expect(resolver.resolveCatalogName(entry, 'zh-CN').text, '中国');
      // Bare zh has no pack: falls back to the catalog default name.
      final bare = resolver.resolveCatalogName(entry, 'zh');
      expect(bare.text, 'China');
      expect(bare.isFallback, isTrue);
      expect(bare.source, GeoNameSource.defaultName);
    });
  });
}
