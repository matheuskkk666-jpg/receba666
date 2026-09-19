#!/usr/bin/env python3
"""Offline content-production pipeline. Uses only Python's standard library."""
import argparse, hashlib, json, sys
from pathlib import Path

LANGS = ("pt_BR", "en")

def read_json(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def write_json(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
def digest(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()
def load_blocks(path): return read_json(path)["blocks"]
def index_blocks(blocks): return {block["source_id"]: block for block in blocks}

def normalize_txt(source, output, language, source_alias, chapter_source_id):
    raw = Path(source).read_text(encoding="utf-8")
    # Newlines separating paragraphs are structure, not narrative text in a block.
    paragraphs = [part.strip("\n") for part in raw.replace("\r\n", "\n").split("\n\n") if part.strip("\n")]
    blocks = []
    for index, text in enumerate(paragraphs, 1):
        blocks.append({"source_id": f"{chapter_source_id}.b{index:04d}", "chapter_source_id": chapter_source_id,
          "kind": "review_required", "speaker": None, "text": text, "source_language": language,
          "source_provenance": source_alias, "review_notes": "Semantic kind/speaker require editorial review."})
    write_json(output, {"version": 1, "blocks": blocks})
    return {"blocks": len(blocks)}

def validate_alignment(alignment, sources):
    errors, mapped = [], {lang: set() for lang in LANGS}
    unit_ids = set()
    for unit in alignment.get("units", []):
        if not unit.get("unit_id") or not unit.get("chapter_id"): errors.append("unit missing unit_id/chapter_id")
        if unit.get("unit_id") in unit_ids: errors.append(f"duplicate unit_id: {unit.get('unit_id')}")
        unit_ids.add(unit.get("unit_id"))
        for lang in LANGS:
            ids = unit.get(lang, [])
            if not ids: errors.append(f"missing {lang} alignment: {unit.get('unit_id')}")
            for source_id in ids:
                if source_id not in sources[lang]: errors.append(f"unknown {lang} source block: {source_id}")
                elif source_id in mapped[lang]: errors.append(f"duplicate {lang} source block: {source_id}")
                mapped[lang].add(source_id)
    unmapped = {lang: sorted(set(sources[lang]) - mapped[lang]) for lang in LANGS}
    return errors, unmapped

def next_narrative_id(chapter_id, ledger_units, allocated):
    """Allocate only above existing IDs, so later inserts never renumber old text."""
    prefix = f"pipeline.{chapter_id}."
    known = set(allocated)
    known.update(unit.get("narrative_id") for unit in ledger_units.values())
    number = 1
    while f"{prefix}{number:04d}" in known:
        number += 1
    stable_id = f"{prefix}{number:04d}"
    allocated.add(stable_id)
    return stable_id

def import_content(args):
    sources = {lang: index_blocks(load_blocks(getattr(args, lang))) for lang in LANGS}
    alignment = read_json(args.alignment)
    errors, unmapped = validate_alignment(alignment, sources)
    ledger = read_json(args.ledger) if Path(args.ledger).exists() else {"version": 1, "units": {}}
    ledger.setdefault("units", {})
    conflicts, rows, allocated = [], [], set()
    for unit in alignment["units"]:
        fingerprints = {lang: digest("".join(sources[lang][sid]["text"] for sid in unit[lang])) for lang in LANGS}
        prior = ledger["units"].get(unit["unit_id"])
        if prior and prior["fingerprints"] != fingerprints:
            conflicts.append(unit["unit_id"]); continue
        stable_id = prior["narrative_id"] if prior else unit.get("narrative_id") or next_narrative_id(unit["chapter_id"], ledger["units"], allocated)
        allocated.add(stable_id)
        rows.append((unit, stable_id, fingerprints))
    coverage = {
        lang: {"source_blocks": len(sources[lang]), "mapped_blocks": len(sources[lang]) - len(unmapped[lang]), "unmapped_blocks": len(unmapped[lang])}
        for lang in LANGS
    }
    report = {"chapters": {}, "coverage": coverage, "narrative_ids": len(rows), "conflicts": conflicts, "unmapped": unmapped,
              "would_create": [stable_id for _, stable_id, _ in rows]}
    for unit, stable_id, fingerprints in rows:
        chapter = report["chapters"].setdefault(unit["chapter_id"], {lang: {"blocks": 0, "mapped": 0} for lang in LANGS})
        for lang in LANGS: chapter[lang]["blocks"] += len(unit[lang]); chapter[lang]["mapped"] += len(unit[lang])
    if errors or conflicts or any(unmapped.values()):
        report["errors"] = errors
        return report, False
    if args.dry_run: return report, True
    output = Path(args.output)
    by_chapter = {}
    for unit, stable_id, fingerprints in rows:
        chapter = by_chapter.setdefault(unit["chapter_id"], {"narrative": [], "pt_BR": [], "en": []})
        kind = unit.get("kind", "narration")
        chapter["narrative"].append({"id": stable_id, "scene": unit.get("scene_hint", "review_required"), "kind": kind,
          "provenance": "source_exact", "status": unit.get("status", "source_exact"), "source_unit": unit["unit_id"]})
        for lang in LANGS:
            # Paragraph boundaries are source structure and must survive a many-to-one alignment.
            text = "\n\n".join(sources[lang][sid]["text"] for sid in unit[lang])
            chapter[lang].append({"id": stable_id, "speaker": unit.get("speaker_hint", "") or "", "text": text,
              "source_blocks": unit[lang], "status": unit.get("status", "source_exact")})
        ledger["units"][unit["unit_id"]] = {"narrative_id": stable_id, "fingerprints": fingerprints, "chapter_id": unit["chapter_id"]}
    for chapter_id, payload in by_chapter.items():
        write_json(output / "narrative" / f"{chapter_id}.json", payload["narrative"])
        for lang in LANGS: write_json(output / "translations" / lang / f"{chapter_id}.json", payload[lang])
    write_json(args.ledger, ledger); write_json(output / "report.json", report)
    return report, True

def main():
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest="cmd", required=True)
    norm=sub.add_parser("normalize"); norm.add_argument("source"); norm.add_argument("output"); norm.add_argument("--language", required=True, choices=LANGS); norm.add_argument("--source-alias", required=True); norm.add_argument("--chapter-source-id", required=True)
    imp=sub.add_parser("import"); imp.add_argument("--pt_BR", required=True); imp.add_argument("--en", required=True); imp.add_argument("--alignment", required=True); imp.add_argument("--ledger", required=True); imp.add_argument("--output", required=True); imp.add_argument("--dry-run", action="store_true")
    val=sub.add_parser("validate"); val.add_argument("--pt_BR", required=True); val.add_argument("--en", required=True); val.add_argument("--alignment", required=True)
    rep=sub.add_parser("report"); rep.add_argument("path")
    a=parser.parse_args()
    if a.cmd == "normalize": result=normalize_txt(a.source,a.output,a.language,a.source_alias,a.chapter_source_id); print(json.dumps(result, ensure_ascii=False)); return 0
    if a.cmd == "validate":
        sources={l:index_blocks(load_blocks(getattr(a,l))) for l in LANGS}; errors,unmapped=validate_alignment(read_json(a.alignment),sources); print(json.dumps({"errors":errors,"unmapped":unmapped},ensure_ascii=False,indent=2)); return int(bool(errors or any(unmapped.values())))
    if a.cmd == "report": print(Path(a.path).read_text(encoding="utf-8")); return 0
    report,ok=import_content(a); print(json.dumps(report,ensure_ascii=False,indent=2)); return int(not ok)
if __name__ == "__main__": raise SystemExit(main())
