#!/usr/bin/env python3
"""CLDR-only audit extensions for Geo Regions Protocol 1.0 (Python 3.10+).

This checks recorded source assertions, not legal administrative truth or human
review. It never downloads, rewrites data, or treats fallback as a translation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import geo_data as geo

CONTAINMENT = "sources/raw/cldr/subdivisionContainment.json"
METADATA = "audit/node_metadata.json"
REGISTRY = "audit/identity_registry.json"
SNAPSHOT_FILES = ("data/manifest.json", "sources/source-lock.json", "config/data_policy.json", METADATA, REGISTRY)
QUALITIES = frozenset(geo.PRODUCTION_SOURCE_QUALITIES)


def require(ok, message):
    geo.require(ok, "semantic-audit: " + message)


def read(root, path):
    return geo.load_json(geo.safe_resource(root, path))


def keyed(rows, label):
    require(isinstance(rows, list), label + " must be an array")
    result = {}
    for row in rows:
        require(isinstance(row, dict), label + " entry must be an object")
        key = row.get("id")
        geo.text_value(key, label + ".id")
        require(key not in result, f"duplicate ID in {label}: {key}")
        result[key] = row
    return result


def sidecar(root, path, dataset_id, field):
    obj = read(root, path)
    require(obj.get("schemaVersion") == 1, path + ": unsupported schemaVersion")
    require(obj.get("datasetId") == dataset_id, path + ": datasetId mismatch")
    return keyed(obj.get(field), path)


def snapshot_id(root):
    """Bind migration evidence to data, provenance, policy and identities."""
    hashes = {path: geo.sha256(geo.safe_resource(root, path)) for path in SNAPSHOT_FILES}
    return hashlib.sha256(geo.canonical(hashes)).hexdigest()


def canonical_tag(tag):
    geo.valid_locale(tag)
    parts = tag.split("-")
    return "-".join(part.lower() if i == 0 else
                    part.title() if len(part) == 4 and part.isalpha() else
                    part.upper() if len(part) == 2 and part.isalpha() else part.lower()
                    for i, part in enumerate(parts))


def explicit_script(tag):
    """Return an explicit BCP 47 script, never a private-use/extension value."""
    for part in canonical_tag(tag).split("-")[1:]:
        if len(part) == 1:
            break
        if len(part) == 4 and part.isalpha():
            return part.casefold()
    return None


def validate_alias(alias, target):
    source_script, target_script = explicit_script(alias), explicit_script(target)
    require(source_script is None or source_script == target_script,
            f"locale alias cannot change or discard an explicit script: {alias} -> {target}")


def validate_policy_aliases(policy):
    for alias, target in policy.get("localeAliases", {}).items():
        validate_alias(alias, target)


def resource_locale(requested, policy):
    """Explicit aliases first, then script-preserving RFC 4647 lookup."""
    tag = canonical_tag(requested)
    available = policy.get("locales", [])
    canonical = {value.casefold(): value for value in available}
    aliases = {key.casefold(): value for key, value in policy.get("localeAliases", {}).items()}
    if tag.casefold() in aliases:
        target = aliases[tag.casefold()]
        validate_alias(tag, target)
        return target
    parts = tag.split("-")
    script = explicit_script(tag)
    while parts:
        candidate = "-".join(parts).casefold()
        # Bare Chinese is ambiguous. Never infer a Chinese writing system.
        if parts[0].casefold() == "zh" and len(parts) == 1:
            break
        if candidate in canonical and (script is None or explicit_script(canonical[candidate]) == script):
            return canonical[candidate]
        prefix_matches = sorted(value for value in available if value.casefold().startswith(candidate + "-"))
        for match in prefix_matches:
            match_script = explicit_script(match)
            if script is None or script == match_script:
                return match
        parts.pop()
        if parts and len(parts[-1]) == 1:  # RFC 4647 extension singleton truncation
            parts.pop()
    return None


def name_context(root, country):
    policy = read(root, "config/data_policy.json")
    structure = read(root, f"data/regions/{country}.json")
    packs = {locale: read(root, f"data/i18n/{locale}/{country}.json")
             for locale in policy.get("locales", [])}
    return policy, structure, packs


def resolve_from(node, requested, policy, packs, default_locale="en"):
    """Resolve a display value without altering the sparse source name packs."""
    target = resource_locale(requested, policy)
    default = resource_locale(default_locale, policy)
    requested_tag = canonical_tag(requested)
    filtered = []
    for locale in dict.fromkeys(value for value in (target, default) if value is not None):
        pack = packs.get(locale, {})
        value = pack.get("names", {}).get(node["id"])
        quality = pack.get("coverage", {}).get("translationQualityById", {}).get(node["id"])
        if value is not None:
            geo.text_value(value, f"resolver {node['id']} {locale}")
            if quality in QUALITIES:
                fallback = locale != target
                return {"id": node["id"], "value": value, "requestedLocale": requested_tag,
                        "resourceLocale": target, "resolvedLocale": locale, "quality": quality,
                        "isFallback": fallback, "reason": "host-default" if fallback else "requested-resource",
                        "filteredLocales": filtered}
            filtered.append(locale)
    value, quality, locale = node.get("name"), node.get("nameQuality"), node.get("nameLocale")
    if isinstance(value, str) and value.strip() and quality in QUALITIES and isinstance(locale, str):
        geo.text_value(value, f"resolver {node['id']} default name")
        geo.valid_locale(locale)
        return {"id": node["id"], "value": value, "requestedLocale": requested_tag,
                "resourceLocale": target, "resolvedLocale": locale, "quality": quality,
                "isFallback": True, "reason": "qualified-default-name", "filteredLocales": filtered}
    return {"id": node["id"], "value": node["id"], "requestedLocale": requested_tag,
            "resourceLocale": target, "resolvedLocale": None, "quality": "identifier",
            "isFallback": True, "reason": "identifier-only", "filteredLocales": filtered}


def resolve_name(root, country, node_id, locale, default_locale="en"):
    policy, structure, packs = name_context(Path(root), country)
    nodes = keyed(structure["nodes"], country)
    require(node_id in nodes, "unknown requested node " + node_id)
    return resolve_from(nodes[node_id], locale, policy, packs, default_locale)


def inspect(root):
    root = Path(root).resolve()
    integrity = geo.validate(root)
    validate_policy_aliases(read(root, "config/data_policy.json"))
    dataset_id = integrity["datasetId"]
    metadata = sidecar(root, METADATA, dataset_id, "nodes")
    registry = sidecar(root, REGISTRY, dataset_id, "entries")
    source_lock = read(root, "sources/source-lock.json")
    source_refs = {entry["localPath"] for entry in source_lock["sources"]}
    for entry in source_lock["sources"]:
        require(entry["license"] == "Unicode-3.0", "CLDR-only profile forbids other source licenses")
        require(entry.get("repository") in ("https://github.com/unicode-org/cldr", "https://github.com/unicode-org/cldr-json"),
                "CLDR-only profile requires the recorded Unicode source repository")
    containment = read(root, CONTAINMENT)["supplemental"]["subdivisionContainment"]
    require(CONTAINMENT in source_refs, "containment source must be locked")
    catalog = read(root, "data/countries.json")
    structures = {row["code"]: read(root, f"data/regions/{row['code']}.json") for row in catalog["countries"]}
    nodes = {}
    for country, structure in structures.items():
        for node in structure["nodes"]:
            nodes[node["id"]] = (country, node)
    require(metadata.keys() == nodes.keys(), "metadata IDs must exactly match current nodes")
    active_keys = set()
    for node_id, entry in registry.items():
        require(entry.get("status") in ("active", "retired"), f"{node_id}: invalid registry status")
        require(entry.get("sourceNamespace") == "cldr", f"{node_id}: namespace must be cldr")
        for key in ("sourceKey", "countryCode", "firstSeenRelease"):
            geo.text_value(entry.get(key), f"registry {node_id}.{key}")
        if entry["status"] == "active":
            key = (entry["sourceNamespace"], entry["countryCode"], entry["sourceKey"])
            require(key not in active_keys, f"source key assigned to multiple active IDs: {key}")
            active_keys.add(key)
    require({key for key, entry in registry.items() if entry["status"] == "active"} == nodes.keys(),
            "active registry IDs must exactly match data; retired IDs cannot be active")
    max_depth = 0
    for node_id, (country, node) in nodes.items():
        row, identity = metadata[node_id], registry[node_id]
        for field in ("parentId", "kind", "code"):
            require(row.get(field) == node.get(field), f"{node_id}: metadata {field} mismatch")
        require(row.get("countryCode") == country, f"{node_id}: metadata country mismatch")
        require(row.get("sourceNamespace") == "cldr", f"{node_id}: metadata namespace mismatch")
        require(row.get("sourceKey") == identity["sourceKey"] and identity["countryCode"] == country,
                f"{node_id}: registry/source identity mismatch")
        refs = row.get("sourceRefs")
        require(isinstance(refs, list) and CONTAINMENT in refs and set(refs) <= source_refs,
                f"{node_id}: metadata source references are not locked")
        require("administrativeLevel" in row and "administrativeType" in row and
                row["administrativeLevel"] is None and row["administrativeType"] is None and
                row.get("levelStatus") == "source-hierarchy-only",
                f"{node_id}: legal administrative levels require a separately reviewed evidence contract")
        source_key = row["sourceKey"]
        if node["parentId"] is None:
            require(node_id == "cc:" + country and source_key == country and node["kind"] == "country" and node.get("code") == country,
                    f"{node_id}: invalid country identity")
        else:
            require(node["kind"] == "subdivision", f"{node_id}: non-root kind must be subdivision")
            require(source_key.startswith(country.lower()) and len(source_key) > 2,
                    f"{node_id}: invalid CLDR source key")
            require(node.get("code") == country + "-" + source_key[2:].upper(), f"{node_id}: code/source key mismatch")
            parent_key = metadata[node["parentId"]]["sourceKey"]
            require(source_key in containment.get(parent_key, {}).get("_contains", []),
                    f"{node_id}: parent edge absent from pinned CLDR containment")
        depth, current = 0, node
        while current["parentId"] is not None:
            depth += 1
            current = nodes[current["parentId"]][1]
        require(type(row.get("treeDepth")) is int and row["treeDepth"] == depth, f"{node_id}: incorrect treeDepth")
        max_depth = max(max_depth, depth)
    coverage = []
    for country, structure in structures.items():
        policy, _, packs = name_context(root, country)
        for locale, pack in packs.items():
            outcomes = [resolve_from(node, locale, policy, packs) for node in structure["nodes"]]
            qualities = pack.get("coverage", {}).get("translationQualityById", {})
            coverage.append({"country": country, "locale": locale, "nodes": len(outcomes),
                             "sourcePresent": len(pack["names"]),
                             "eligibleNames": sum(value in QUALITIES for value in qualities.values()),
                             "missingSourceNames": len(outcomes) - len(pack["names"]),
                             "fallbackCount": sum(row["isFallback"] for row in outcomes),
                             "identifierOnlyCount": sum(row["quality"] == "identifier" for row in outcomes)})
    return {"status": "pass", "profile": "CLDR-source-hierarchy-and-name-resolution",
            "datasetId": dataset_id, "nodes": len(nodes), "maxTreeDepth": max_depth,
            "snapshot": snapshot_id(root), "administrativeLevelsVerified": False,
            "historicalStability": "NOT_VERIFIED_BY_SINGLE_SNAPSHOT",
            "humanReviewVerified": False, "coverage": coverage}, nodes, registry


def check(root):
    return inspect(root)[0]


def verify_migrations(root, dataset_id, old_snapshot, new_snapshot, changes):
    if not changes:
        return 0
    document = read(root, "audit/migrations.json")
    require(document.get("schemaVersion") == 1 and document.get("datasetId") == dataset_id, "invalid migration document")
    require(document.get("fromSnapshot") == old_snapshot and document.get("toSnapshot") == new_snapshot,
            "migration snapshot bindings mismatch")
    events = document.get("events")
    require(isinstance(events, list), "migration events must be an array")
    expected = {geo.canonical(row) for row in changes}
    seen = set()
    for event in events:
        require(isinstance(event, dict), "migration event must be an object")
        signature = geo.canonical({key: event.get(key) for key in ("id", "change", "from", "to")})
        require(signature not in seen, "duplicate migration event")
        require(signature in expected, "migration event does not match an actual change")
        seen.add(signature)
        review = event.get("review", {})
        require(review.get("status") == "reviewed", "migration requires recorded review")
        geo.text_value(review.get("reviewer"), "migration reviewer")
        require(isinstance(review.get("reviewedAt"), str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", review["reviewedAt"]),
                "migration requires review date")
        evidence = geo.safe_resource(root, review.get("evidence"))
        require(evidence.stat().st_size > 0 and geo.sha256(evidence) == review.get("evidenceSha256"),
                "migration review evidence is empty or hash differs")
    require(seen == expected, "unreviewed breaking changes remain")
    return len(seen)


def stability(old_root, new_root):
    old_root, new_root = Path(old_root).resolve(), Path(new_root).resolve()
    old_report, old_nodes, old_registry = inspect(old_root)
    new_report, new_nodes, new_registry = inspect(new_root)
    dataset_id = old_report["datasetId"]
    require(dataset_id == new_report["datasetId"], "cross-dataset comparison requires a separate namespace migration")
    require(old_registry.keys() <= new_registry.keys(), "registry history cannot be removed")
    for node_id, before in old_registry.items():
        after = new_registry[node_id]
        for field in ("sourceNamespace", "sourceKey", "countryCode", "firstSeenRelease"):
            require(before[field] == after[field], f"{node_id}: immutable registry identity changed: {field}")
        require(before["status"] != "retired" or after["status"] == "retired", f"retired ID reused: {node_id}")
    added, removed = sorted(new_nodes.keys() - old_nodes.keys()), sorted(old_nodes.keys() - new_nodes.keys())
    changes = [{"id": node_id, "change": "removed", "from": "active", "to": "retired"} for node_id in removed]
    renamed, other = [], []
    for node_id in sorted(old_nodes.keys() & new_nodes.keys()):
        before, after = old_nodes[node_id][1], new_nodes[node_id][1]
        for field, label in (("parentId", "reparented"), ("kind", "kindChanged"), ("code", "codeChanged")):
            if before.get(field) != after.get(field):
                changes.append({"id": node_id, "change": label, "from": before.get(field), "to": after.get(field)})
        if before["name"] != after["name"]:
            renamed.append({"id": node_id, "from": before["name"], "to": after["name"]})
        for field in ("nameLocale", "nameQuality", "childrenStatus"):
            if before.get(field) != after.get(field):
                other.append({"id": node_id, "field": field, "from": before.get(field), "to": after.get(field)})
    # A newly minted ID may intentionally reuse a retired source code, but that
    # must also have explicit evidence. Never silently equate it with the old ID.
    old_source_ids = {}
    for node_id, entry in old_registry.items():
        key = (entry["sourceNamespace"], entry["countryCode"], entry["sourceKey"])
        old_source_ids.setdefault(key, []).append(node_id)
    reuses = []
    for node_id in added:
        row = new_registry[node_id]
        key = (row["sourceNamespace"], row["countryCode"], row["sourceKey"])
        if key in old_source_ids:
            reuses.append({"id": node_id, "previousIds": sorted(old_source_ids[key])})
    require(not reuses, "source code reused by a new ID: needs a separately reviewed identity-reuse contract " + json.dumps(reuses))
    reviewed = verify_migrations(new_root, dataset_id, old_report["snapshot"], new_report["snapshot"], changes)
    return {"status": "pass", "datasetId": dataset_id, "fromSnapshot": old_report["snapshot"],
            "toSnapshot": new_report["snapshot"], "added": added, "removed": removed,
            "policyChanged": read(old_root, "config/data_policy.json") != read(new_root, "config/data_policy.json"),
            "breakingChanges": changes, "renamed": renamed, "metadataChanges": other,
            "reviewedMigrationRecords": reviewed, "humanReviewVerified": False,
            "historicalStability": "SAME_SNAPSHOT_ONLY" if old_report["snapshot"] == new_report["snapshot"] else "PROVIDED_SNAPSHOTS_CHECKED",
            "sourceHistoryCompletenessVerified": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--report", type=Path)
    resolve_parser = sub.add_parser("resolve")
    resolve_parser.add_argument("--country", required=True)
    resolve_parser.add_argument("--id", required=True)
    resolve_parser.add_argument("--locale", required=True)
    resolve_parser.add_argument("--default-locale", default="en")
    stability_parser = sub.add_parser("stability")
    stability_parser.add_argument("--old-root", required=True, type=Path)
    stability_parser.add_argument("--new-root", required=True, type=Path)
    stability_parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            result = check(args.root)
        elif args.command == "resolve":
            check(args.root)
            result = resolve_name(args.root, args.country, args.id, args.locale, args.default_locale)
        else:
            result = stability(args.old_root, args.new_root)
        if getattr(args, "report", None):
            geo.write_json(args.report, result)
        print(json.dumps({key: value for key, value in result.items() if key != "coverage"}, ensure_ascii=False, indent=2))
        return 0
    except (geo.DataError, KeyError, TypeError, ValueError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
