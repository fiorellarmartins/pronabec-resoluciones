#!/usr/bin/env python3
"""
Validates regex classifications for Beca Presidente / Bicentenario documents
using Claude Code (claude -p) in parallel.

Output: llm_classification/results.jsonl  (one JSON object per line)
        llm_classification/results.csv    (final merged table)

Safe to re-run: skips already-processed filenames.
"""
import csv, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

CSV_IN   = "/Users/fiorellaramirez/Desktop/pronabec_datos/parsed_results.csv"
OUT_DIR  = "/Users/fiorellaramirez/Desktop/pronabec_datos/llm_classification"
JSONL    = os.path.join(OUT_DIR, "results.jsonl")
CSV_OUT  = os.path.join(OUT_DIR, "results.csv")
WORKERS  = 8

CLASSES    = ["cumplió","devolución","incumplimiento","aplazamiento","improcedente","nulidad","otro"]
SUBCLASSES = {
    "cumplió":        ["acreditación","acreditación_parcial","cumplimiento_directo"],
    "devolución":     ["abandono","bajo_rendimiento","renuncia","no_aceptación","pérdida_otros"],
    "incumplimiento": ["declaración","recurso_improcedente"],
    "aplazamiento":   ["motivos_académicos","motivos_laborales","motivos_salud","otros_motivos"],
    "improcedente":   ["aplazamiento","ampliación","exoneración","acreditación","otros"],
    "nulidad":        ["fundado_recurso","sin_efecto","otros"],
    "otro":           ["admisión","viaje","renuncia","modificación","excepción","admin"],
}

PROMPT_TEMPLATE = """You are analyzing a Peruvian government resolution from PRONABEC (scholarship program).

The regex classifier labeled this document as:
  class:    {regex_class}
  subclass: {regex_subclass}

Valid classes:    cumplió | devolución | incumplimiento | aplazamiento | improcedente | nulidad | otro
Valid subclasses per class:
  cumplió        → acreditación | acreditación_parcial | cumplimiento_directo
  devolución     → abandono | bajo_rendimiento | renuncia | no_aceptación | pérdida_otros
  incumplimiento → declaración | recurso_improcedente
  aplazamiento   → motivos_académicos | motivos_laborales | motivos_salud | otros_motivos
  improcedente   → aplazamiento | ampliación | exoneración | acreditación | otros
  nulidad        → fundado_recurso | sin_efecto | otros
  otro           → admisión | viaje | renuncia | modificación | excepción | admin

Document text:
---
{text}
---

Reply with ONLY a valid JSON object, no markdown, no explanation:
{{
  "validated": true or false,
  "llm_class": "<class>",
  "llm_subclass": "<subclass or empty string>",
  "person": "<full name of the person this resolution concerns, or empty string>",
  "summary": "<1-2 sentences: what this resolution does and why>",
  "note": "<discrepancy or observation if validated is false, else empty string>"
}}"""

def extract_text(path: str, max_chars: int = 2500) -> str:
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return ""
    # prefer SE RESUELVE section + preamble
    m = re.search(r"(SE\s+RESUELVE.*?)(?:Regístrese|Comuníquese|$)", text, re.IGNORECASE | re.DOTALL)
    if m:
        section = m.group(1)[:1500]
        preamble = text[:500]
        combined = preamble + "\n...\n" + section
    else:
        combined = text
    return combined[:max_chars]

def call_claude(row: dict) -> dict:
    text   = extract_text(row["path"])
    prompt = PROMPT_TEMPLATE.format(
        regex_class=row["class"],
        regex_subclass=row["subclass"] or "(none)",
        text=text,
    )
    try:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, timeout=120
        )
        raw = result.stdout.strip()
        # strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "validated": None,
            "llm_class": "",
            "llm_subclass": "",
            "person": "",
            "summary": "",
            "note": f"parse_error: {raw[:200]}",
        }
    except Exception as e:
        parsed = {
            "validated": None,
            "llm_class": "",
            "llm_subclass": "",
            "person": "",
            "summary": "",
            "note": f"error: {e}",
        }

    return {
        "filename":       row["filename"],
        "path":           row["path"],
        "beca":           row["beca"],
        "convocatoria":   row["convocatoria"],
        "dni":            row["dni"],
        "regex_class":    row["class"],
        "regex_subclass": row["subclass"],
        **parsed,
    }

def load_done() -> set:
    if not os.path.exists(JSONL):
        return set()
    done = set()
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            try:
                done.add(json.loads(line)["filename"])
            except Exception:
                pass
    return done

def main():
    rows = list(csv.DictReader(open(CSV_IN)))
    target = [r for r in rows if r["beca"] in ("beca_presidente","beca_bicentenario")]
    done   = load_done()
    pending = [r for r in target if r["filename"] not in done]

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if limit:
        pending = pending[:limit]

    print(f"Target docs:    {len(target)}")
    print(f"Already done:   {len(done)}")
    print(f"To process:     {len(pending)}{f'  (capped at {limit})' if limit else ''}")
    if not pending:
        print("Nothing to do.")
        build_csv()
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    out_fh = open(JSONL, "a", encoding="utf-8")
    errors = 0
    done_count = len(done)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(call_claude, r): r for r in pending}
        for fut in as_completed(futures):
            done_count += 1
            try:
                rec = fut.result()
                out_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out_fh.flush()
                status = "OK " if rec["validated"] else ("DIFF" if rec["validated"] is False else "ERR ")
                print(f"  [{done_count:4d}/{len(target)}] {status}  {rec['filename'][:60]}")
            except Exception as e:
                errors += 1
                print(f"  [{done_count:4d}/{len(target)}] FAIL  {e}", file=sys.stderr)

    out_fh.close()
    print(f"\nDone. Errors: {errors}")
    build_csv()

def build_csv():
    if not os.path.exists(JSONL):
        return
    records = []
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except Exception:
                pass

    if not records:
        return

    fields = ["filename","beca","convocatoria","dni",
              "regex_class","regex_subclass",
              "validated","llm_class","llm_subclass",
              "person","summary","note","path"]

    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)

    total      = len(records)
    validated  = sum(1 for r in records if r.get("validated") is True)
    disagreed  = sum(1 for r in records if r.get("validated") is False)
    errors     = sum(1 for r in records if r.get("validated") is None)

    print(f"\nResults CSV: {CSV_OUT}")
    print(f"  Total:      {total}")
    print(f"  Validated:  {validated} ({validated/total*100:.0f}%)")
    print(f"  Disagreed:  {disagreed} ({disagreed/total*100:.0f}%)")
    print(f"  Errors:     {errors}")

if __name__ == "__main__":
    main()
