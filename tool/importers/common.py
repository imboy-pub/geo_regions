"""Shared adapter contract for the ten-country official completion (Phase 2).

Per docs/superpowers/specs/2026-11-16-ten-country-official-region-completion-design.md:
country adapters normalize official inputs into SourceNode rows, a CountryDraft
is validated for structural integrity (unique ids, parent chains, no
cross-country parents, abolished routing), and only then does build(root) merge
the draft into the seed. Fixtures under tests/fixtures/official/{cc}/ drive the
contract tests; nothing here reaches the network.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SourceNode:
    """One normalized row from an official snapshot (or a fixture row)."""
    official_code: str
    parent_code: str
    kind: str
    name: str
    name_locale: str
    name_quality: str
    children_status: str
    abolished: bool = False


@dataclass
class CountryDraft:
    """Active nodes + migration records for one country batch."""
    nodes: list            # SourceNode rows that are current administration
    migrations: list       # dicts: officialCode, reason, disposition
    country: str = ""

    @property
    def codes(self):
        return {n.official_code for n in self.nodes if not n.abolished}


def load_fixture_csv(path) -> list[SourceNode]:
    import csv
    rows: list[SourceNode] = []
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(SourceNode(
                official_code=r['official_code'],
                parent_code=r.get('parent_code', ''),
                kind=r['kind'],
                name=r['name'],
                name_locale=r['name_locale'],
                name_quality=r['name_quality'],
                children_status=r['children_status'],
                abolished=r.get('abolished', 'false').lower() == 'true',
            ))
    return rows


def validate_draft(draft: CountryDraft, identity=None, parent_identity=None) -> str | None:
    """Return None when the draft is structurally sound, else the error text.

    Checks per the design doc: duplicate official codes, missing parents,
    parent cycles, cross-country parents, and abolished rows never entering
    the active node set.

    identity(node) -> hashable overrides the duplicate/cycle key (default:
    the bare official_code). parent_identity(node) -> hashable overrides the
    parent lookup key (default: the bare parent_code). National registries
    that legally reuse the same number across tiers (INSEE region 01
    Guadeloupe vs department 01 Ain; ISTAT likewise) need tier-aware keys;
    the default keeps every pre-existing behaviour byte-identical.
    """
    active = [n for n in draft.nodes if not n.abolished]
    by_code = {}
    for n in active:
        key = identity(n) if identity else n.official_code
        if key in by_code:
            return f"duplicate official code: {key}"
        by_code[key] = n
    for n in active:
        pkey = parent_identity(n) if parent_identity else n.parent_code
        if pkey:
            selfkey = identity(n) if identity else n.official_code
            if pkey == selfkey:
                return f"parent cycle at {selfkey}"
            if pkey not in by_code:
                return f"missing parent {pkey} for {selfkey}"
    # cycle check beyond self-parent: walk up with a visit budget
    for n in active:
        seen = set()
        cur = n
        while True:
            selfkey = identity(cur) if identity else cur.official_code
            pkey = parent_identity(cur) if parent_identity else cur.parent_code
            if not pkey:
                break
            if selfkey in seen:
                return f"parent cycle at {selfkey}"
            seen.add(selfkey)
            nxt = by_code.get(pkey)
            if nxt is None:
                break
            cur = nxt
    for n in draft.nodes:
        if n.abolished:
            # must not appear as an active node row
            nkey = identity(n) if identity else n.official_code
            actives_with_code = [
                a for a in active
                if (identity(a) if identity else a.official_code) == nkey]
            if actives_with_code:
                return f"abolished code {nkey} also present as active"
    return None
