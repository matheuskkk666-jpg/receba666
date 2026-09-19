#!/usr/bin/env python3
"""Offline, deterministic import tooling for authorized local content."""
import argparse
import hashlib
import json
from pathlib import Path

LANGS = ("pt_BR", "en")


def read_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fingerprint(texts):
    """Hashes an exact ordered list, including source-block boundaries."""
    return hashlib.sha256(json.dumps(texts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_blocks(path): return read_json(path)["blocks"]

def joined_source_text(source, source_ids):
    text = source[source_ids[0]]["text"]
    for source_id in source_ids[1:]:
        text += source[source_id].get("join_prefix", "\n\n") + source[source_id]["text"]
    return text


def index_blocks(blocks):
    index, errors = {}, []
    for block in blocks:
        source_id = block.get("source_id")
        if not source_id: errors.append("empty source_id")
        elif source_id in index: errors.append("duplicate source_id: " + source_id)
        else: index[source_id] = block
    return index, errors


def normalize_txt(source, output, language, source_alias, chapter_source_id):
    raw = Path(source).read_text(encoding="utf-8")
    paragraphs = [part.strip("\n") for part in raw.replace("\r\n", "\n").split("\n\n") if part.strip("\n")]
    blocks = [{"source_id": f"{chapter_source_id}.b{number:04d}", "chapter_source_id": chapter_source_id,
               "kind": "review_required", "speaker": None, "text": text, "source_language": language,
               "source_provenance": source_alias, "review_notes": "Semantic kind/speaker require editorial review."}
              for number, text in enumerate(paragraphs, 1)]
    write_json(output, {"version": 1, "blocks": blocks})
    return {"blocks": len(blocks)}


def load_sources(args):
    sources, errors = {}, []
    for language in LANGS:
        sources[language], duplicates = index_blocks(load_blocks(getattr(args, language)))
        errors.extend(f"{language} {error}" for error in duplicates)
    return sources, errors


def validate_alignment(alignment, sources):
    errors, mapped, missing, unit_ids = [], {language: set() for language in LANGS}, [], set()
    for unit in alignment.get("units", []):
        unit_id = unit.get("unit_id")
        if not unit_id or not unit.get("chapter_id"): errors.append("unit missing unit_id/chapter_id")
        if unit_id in unit_ids: errors.append("duplicate unit_id: " + str(unit_id))
        unit_ids.add(unit_id)
        for language in LANGS:
            source_ids = unit.get(language, [])
            if not source_ids:
                missing.append({"unit_id": unit_id, "language": language})
                continue
            for source_id in source_ids:
                if source_id not in sources[language]: errors.append(f"unknown {language} source block: {source_id}")
                elif source_id in mapped[language]: errors.append(f"duplicate {language} source block: {source_id}")
                mapped[language].add(source_id)
    retired = set(alignment.get("retired_units", []))
    if len(retired) != len(alignment.get("retired_units", [])): errors.append("duplicate retired unit declaration")
    if unit_ids & retired: errors.append("active unit also declared retired")
    unmapped = {language: sorted(set(sources[language]) - mapped[language]) for language in LANGS}
    return errors, unmapped, missing, unit_ids, retired


def load_ledger(path):
    ledger = read_json(path) if Path(path).exists() else {"version": 2, "units": {}, "retired_units": {}}
    ledger.setdefault("units", {}); ledger.setdefault("retired_units", {}); ledger["version"] = 2
    return ledger


def owners_for(ledger):
    owners = {}
    for bucket in ("units", "retired_units"):
        for unit_id, entry in ledger[bucket].items():
            if entry.get("narrative_id"): owners[entry["narrative_id"]] = unit_id
    return owners


def next_narrative_id(chapter_id, reserved):
    """Allocate above the largest reserved namespace value; never fill holes."""
    prefix = f"pipeline.{chapter_id}."
    values = [int(item[len(prefix):]) for item in reserved if item.startswith(prefix) and len(item[len(prefix):]) == 4 and item[len(prefix):].isdigit()]
    return f"{prefix}{max(values, default=0) + 1:04d}"


def package_for(rows, report):
    chapters, fragments = {}, {"narrative": [], "translations": {language: [] for language in LANGS}}
    for unit, narrative_id, _ in rows:
        chapter = chapters.setdefault(unit["chapter_id"], {"id": unit["chapter_id"], "narrative_ids": [], "scene_hints": []})
        chapter["narrative_ids"].append(narrative_id)
        if unit.get("scene_hint") and unit["scene_hint"] not in chapter["scene_hints"]: chapter["scene_hints"].append(unit["scene_hint"])
    for chapter_id, chapter in chapters.items():
        chapter["first_narrative_id"], chapter["last_narrative_id"] = chapter["narrative_ids"][0], chapter["narrative_ids"][-1]
        fragments["narrative"].append(f"narrative/{chapter_id}.json")
        for language in LANGS: fragments["translations"][language].append(f"translations/{language}/{chapter_id}.json")
    return {"version": 1, "runtime_ready": not report["blockers"], "fragments": fragments,
            "narrative_order": [narrative_id for _, narrative_id, _ in rows], "chapters": list(chapters.values()),
            "review_required": report["review_required"], "missing_translations": report["missing_translations"],
            "conflicts": report["conflicts"], "files_to_integrate": ["content manifest fragments and canonical narrative order", "editorial scene definitions for listed scene_hints", "localized chapter metadata for every listed chapter"]}


def import_content(args):
    sources, source_errors = load_sources(args); alignment = read_json(args.alignment)
    errors, unmapped, missing, active_ids, retirements = validate_alignment(alignment, sources)
    errors = source_errors + errors; ledger = load_ledger(args.ledger)
    removed = sorted(set(ledger["units"]) - active_ids); undeclared = sorted(set(removed) - retirements)
    errors.extend("removed unit requires retirement: " + item for item in undeclared)
    errors.extend("unknown unit retirement: " + item for item in sorted(retirements - set(ledger["units"]) - set(ledger["retired_units"])))
    conflicts, rows, new, preserved, owners = [], [], [], [], owners_for(ledger)
    for unit in alignment.get("units", []):
        unit_id = unit.get("unit_id")
        if any(item["unit_id"] == unit_id for item in missing): continue
        texts = {language: [sources[language][source_id]["text"] for source_id in unit[language]] for language in LANGS}
        fingerprints = {language: fingerprint(texts[language]) for language in LANGS}
        prior, explicit = ledger["units"].get(unit_id), unit.get("narrative_id")
        if unit_id in ledger["retired_units"]: conflicts.append("retired unit reused: " + unit_id); continue
        if prior and prior.get("fingerprints") != fingerprints: conflicts.append("fingerprint conflict: " + unit_id); continue
        narrative_id = prior["narrative_id"] if prior else explicit or next_narrative_id(unit["chapter_id"], owners)
        owner = owners.get(narrative_id)
        if owner and owner != unit_id: conflicts.append(f"narrative_id collision: {narrative_id} ({owner}, {unit_id})"); continue
        if prior and explicit and explicit != narrative_id: conflicts.append("narrative_id changed: " + unit_id); continue
        owners[narrative_id] = unit_id; rows.append((unit, narrative_id, fingerprints))
        (preserved if prior else new).append({"unit_id": unit_id, "narrative_id": narrative_id})
    review_required = [{"unit_id": unit["unit_id"], "reason": "editorial metadata or scene hint pending"} for unit, _, _ in rows if unit.get("kind") == "review_required" or not unit.get("scene_hint") or unit.get("status") not in (None, "source_exact")]
    coverage = {language: {"source_blocks": len(sources[language]), "mapped_blocks": len(sources[language]) - len(unmapped[language]), "unmapped_blocks": len(unmapped[language])} for language in LANGS}
    blockers = errors + conflicts + [f"missing translation: {item['unit_id']} ({item['language']})" for item in missing] + [f"unmapped {language}: {source_id}" for language in LANGS for source_id in unmapped[language]]
    removals = ([{"unit_id": unit_id, "status": "retired"} for unit_id in sorted(retirements)] +
                [{"unit_id": unit_id, "status": "pending_review"} for unit_id in undeclared])
    report = {"coverage": coverage, "new_units": new, "preserved_units": preserved, "removed_or_retired_units": removals, "conflicts": conflicts, "unmapped": unmapped, "missing_translations": missing, "review_required": review_required, "blockers": blockers}
    package = package_for(rows, report)
    if blockers:
        if not args.dry_run:
            write_json(Path(args.output) / "review_report.json", report); write_json(Path(args.output) / "content_package.json", package)
        return report, False
    if args.dry_run: return report, True
    for unit_id in retirements:
        if unit_id in ledger["units"]:
            ledger["retired_units"][unit_id] = ledger["units"].pop(unit_id)
    by_chapter = {}
    for unit, narrative_id, fingerprints in rows:
        chapter = by_chapter.setdefault(unit["chapter_id"], {"narrative": [], "pt_BR": [], "en": []})
        chapter["narrative"].append({"id": narrative_id, "scene": unit.get("scene_hint", "review_required"), "kind": unit.get("kind", "narration"), "provenance": "source_exact", "status": unit.get("status", "source_exact"), "source_unit": unit["unit_id"]})
        for language in LANGS: chapter[language].append({"id": narrative_id, "speaker": unit.get("speaker_hint", "") or "", "text": joined_source_text(sources[language], unit[language]), "source_blocks": unit[language], "status": unit.get("status", "source_exact")})
        ledger["units"][unit["unit_id"]] = {"narrative_id": narrative_id, "fingerprints": fingerprints, "chapter_id": unit["chapter_id"]}
    output = Path(args.output)
    for chapter_id, payload in by_chapter.items():
        write_json(output / "narrative" / f"{chapter_id}.json", payload["narrative"])
        for language in LANGS: write_json(output / "translations" / language / f"{chapter_id}.json", payload[language])
    write_json(args.ledger, ledger); write_json(output / "report.json", report); write_json(output / "content_package.json", package)
    return report, True


def main():
    parser = argparse.ArgumentParser(); commands = parser.add_subparsers(dest="cmd", required=True)
    normalized = commands.add_parser("normalize"); normalized.add_argument("source"); normalized.add_argument("output"); normalized.add_argument("--language", required=True, choices=LANGS); normalized.add_argument("--source-alias", required=True); normalized.add_argument("--chapter-source-id", required=True)
    for command in (commands.add_parser("import"), commands.add_parser("validate")):
        command.add_argument("--pt_BR", required=True); command.add_argument("--en", required=True); command.add_argument("--alignment", required=True)
    imported = commands.choices["import"]; imported.add_argument("--ledger", required=True); imported.add_argument("--output", required=True); imported.add_argument("--dry-run", action="store_true")
    displayed = commands.add_parser("report"); displayed.add_argument("path")
    args = parser.parse_args()
    if args.cmd == "normalize": print(json.dumps(normalize_txt(args.source, args.output, args.language, args.source_alias, args.chapter_source_id), ensure_ascii=False)); return 0
    if args.cmd == "validate":
        sources, source_errors = load_sources(args); errors, unmapped, missing, _, _ = validate_alignment(read_json(args.alignment), sources)
        result = {"errors": source_errors + errors, "unmapped": unmapped, "missing_translations": missing}; print(json.dumps(result, ensure_ascii=False, indent=2)); return int(bool(result["errors"] or missing or any(unmapped.values())))
    if args.cmd == "report": print(Path(args.path).read_text(encoding="utf-8")); return 0
    report, success = import_content(args); print(json.dumps(report, ensure_ascii=False, indent=2)); return int(not success)


if __name__ == "__main__": raise SystemExit(main())
