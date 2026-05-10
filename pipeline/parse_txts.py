#!/usr/bin/env python3
"""
Regex-based classifier for PRONABEC resolution TXTs.
Extracts classification, person, DNI, convocatoria from each TXT.
Output: parsed_results.csv
"""
import os, re, csv, glob

TXT_DIR = "/Users/fiorellaramirez/Desktop/pronabec_datos/txts_all"
OUT_CSV = "/Users/fiorellaramirez/Desktop/pronabec_datos/parsed_results.csv"

# ── classification signal patterns (checked in order, first match wins) ───────
SIGNALS = [
    # cumplió — must declare compliance, not merely mention it in passing
    ("cumplió", re.compile(
        r"(?:ha\s+)?CUMPLIDO\s+(?:con\s+)?(?:su\s+)?[Cc]ompromiso\s+de\s+[Ss]ervicio"
        r"|DECLARAR\s+(?:el\s+)?CUMPLIMIENTO"
        r"|DECLARAR\s+PROCEDENTE\s+(?:la\s+)?solicitud\s+de\s+acreditaci[oó]n"
        r"|DECLARAR\s+PROCEDENTE\s+EN\s+PARTE\s+(?:la\s+)?solicitud\s+de\s+acreditaci[oó]n",
        re.IGNORECASE)),

    # incumplimiento
    ("incumplimiento", re.compile(
        r"(?:ha\s+)?INCUMPLIDO\s+(?:con\s+)?(?:su\s+)?[Cc]ompromiso\s+de\s+[Ss]ervicio"
        r"|INCUMPLIMIENTO\s+del\s+Compromiso\s+de\s+Servicio"
        r"|DECLARAR\s+(?:el\s+)?INCUMPLIMIENTO",
        re.IGNORECASE)),

    # devolución
    ("devolución", re.compile(
        r"DEVOLVER\b.*(?:beca|monto|S/\s*\d)"
        r"|reintegro\s+(?:de\s+)?(?:los\s+)?(?:montos?|fondos?|beneficios?)"
        r"|PÉRDIDA\s+DE\s+(?:LA\s+)?BECA"
        r"|pérdida\s+de\s+(?:la\s+)?beca",
        re.IGNORECASE)),

    # nulidad
    ("nulidad", re.compile(
        r"DECLARAR\s+(?:LA\s+)?NULIDAD"
        r"|nulo\s+y\s+sin\s+efecto"
        r"|sin\s+efecto\s+(?:la\s+)?(?:Resolución|RJ)",
        re.IGNORECASE)),

    # aplazamiento
    ("aplazamiento", re.compile(
        r"APROBAR\s+(?:EL\s+)?APLAZAMIENTO"
        r"|aplazar\s+(?:el\s+)?Compromiso\s+de\s+Servicio"
        r"|APLAZAMIENTO\s+del\s+Compromiso",
        re.IGNORECASE)),

    # improcedente
    ("improcedente", re.compile(
        r"DECLARAR\s+IMPROCEDENTE"
        r"|declarar\s+improcedente"
        r"|IMPROCEDENTE\s+(?:la\s+)?solicitud",
        re.IGNORECASE)),
]

# ── extraction helpers ─────────────────────────────────────────────────────────
RE_DNI = re.compile(r"DNI\s*[N°nº\.]*\s*(\d{8})\b")
RE_DNI2 = re.compile(r"\b(\d{8})\b")  # fallback bare 8-digit number

RE_PERSON = re.compile(
    r"(?:señor(?:ita)?|señora|sr\.|sra\.|don|doña)\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{5,60}?)(?=,|\s+identificad|\s+con\s+DNI|\s*\n)",
    re.IGNORECASE
)
RE_PERSON2 = re.compile(
    r"(?:al\s+(?:estudiante|becario|egresado)|del\s+(?:señor|señora))\s+([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\s]{5,60}?)(?=,|\s+identificad|\s+con\s+DNI|\s*\n)",
    re.IGNORECASE
)

RE_CONV = re.compile(
    r"[Cc]onvocatoria\s+(\d{4})"
    r"|[Bb]eca\s+Presidente.*?[Cc]onvocatoria\s+(\d{4})"
    r"|[Cc]onvocatoria\s+\d{4}-(\d{4})",
    re.IGNORECASE
)

def extract_resuelve(text):
    """Return the SE RESUELVE section if present, else full text."""
    m = re.search(r"SE\s+RESUELVE\s*:?(.*?)(?:Regístrese|Regístr[eé]se|Comuníquese|$)",
                  text, re.IGNORECASE | re.DOTALL)
    return m.group(1) if m else text

def classify(text):
    section = extract_resuelve(text)
    # check signals against resuelve section first, then full text
    for label, pattern in SIGNALS:
        if pattern.search(section) or pattern.search(text):
            return label
    return "otro"

def extract_dni(text):
    m = RE_DNI.search(text)
    if m:
        return m.group(1)
    # fallback: first 8-digit number near a name keyword
    candidates = RE_DNI2.findall(text)
    return candidates[0] if candidates else ""

def extract_person(text):
    for pat in (RE_PERSON, RE_PERSON2):
        m = pat.search(text)
        if m:
            name = m.group(1).strip()
            # clean up OCR artifacts
            name = re.sub(r"\s{2,}", " ", name)
            if len(name) > 8:
                return name.upper()
    return ""

def extract_convocatoria(text):
    m = RE_CONV.search(text)
    if m:
        return next(g for g in m.groups() if g)
    return ""

OTRO_PATTERNS = [
    ("admisión",    re.compile(r"APROBAR\s+(?:la\s+)?(?:lista|relación)\s+de\s+(?:\w+\s+){0,4}beneficiarios"
                               r"|DECLARAR\s+(?:como\s+)?beneficiario", re.IGNORECASE)),
    ("viaje",       re.compile(r"AUTORIZAR\s+(?:el\s+)?(?:viaje|permiso\s+de\s+viaje|retorno)", re.IGNORECASE)),
    ("renuncia",    re.compile(r"ACEPTAR\s+(?:la\s+)?(?:solicitud\s+de\s+)?renuncia"
                               r"|renuncia\s+(?:voluntaria\s+)?a\s+la\s+beca", re.IGNORECASE)),
    ("modificación",re.compile(r"MODIFICAR\s+(?:el\s+)?(?:periodo|plazo|cronograma|monto)"
                               r"|APROBAR\s+(?:la\s+)?(?:modificación|actualización|anexo)", re.IGNORECASE)),
    ("excepción",   re.compile(r"AUTORIZAR\s+excepcionalmente"
                               r"|EXONERAR\s+(?:al\s+)?becario", re.IGNORECASE)),
]

def classify_otro(text):
    section = extract_resuelve(text)
    for label, pat in OTRO_PATTERNS:
        if pat.search(section) or pat.search(text):
            return label
    return "admin"

DEV_PATTERNS = [
    ("abandono",        re.compile(r"abandono\s+de\s+estudios|abandon[oó]\s+(?:los\s+)?estudios", re.IGNORECASE)),
    ("bajo_rendimiento",re.compile(r"bajo\s+rendimiento|desaprobó|desaprobar\s+(?:los\s+)?cursos|rendimiento\s+académico\s+insuficiente", re.IGNORECASE)),
    ("renuncia",        re.compile(r"renuncia\s+(?:voluntaria\s+)?a\s+la\s+beca|solicitud\s+de\s+renuncia", re.IGNORECASE)),
    ("no_aceptación",   re.compile(r"no\s+acept[oó]\s+(?:la\s+)?beca|no\s+aceptación\s+de\s+la\s+beca", re.IGNORECASE)),
]

def classify_devolucion(text):
    for label, pat in DEV_PATTERNS:
        if pat.search(text):
            return label
    return "pérdida_otros"

APLAZ_PATTERNS = [
    ("motivos_académicos", re.compile(r"motivos?\s+académicos?|razones?\s+académicas?", re.IGNORECASE)),
    ("motivos_laborales",  re.compile(r"motivos?\s+(?:laborales?|profesionales?|trabajo)", re.IGNORECASE)),
    ("motivos_salud",      re.compile(r"motivos?\s+(?:de\s+)?salud|razones?\s+de\s+salud", re.IGNORECASE)),
]

def classify_aplazamiento(text):
    section = extract_resuelve(text)
    for label, pat in APLAZ_PATTERNS:
        if pat.search(section) or pat.search(text):
            return label
    return "otros_motivos"

IMPRPC_PATTERNS = [
    ("aplazamiento",  re.compile(r"solicitud\s+(?:del?\s+)?aplazamiento", re.IGNORECASE)),
    ("ampliación",    re.compile(r"ampliaci[oó]n\s+(?:de\s+)?(?:permanencia|duraci[oó]n|plazo|beca)", re.IGNORECASE)),
    ("exoneración",   re.compile(r"exoneraci[oó]n|exonerada?", re.IGNORECASE)),
    ("acreditación",  re.compile(r"acreditaci[oó]n", re.IGNORECASE)),
]

def classify_improcedente(text):
    section = extract_resuelve(text)
    for label, pat in IMPRPC_PATTERNS:
        if pat.search(section) or pat.search(text):
            return label
    return "otros"

INCMPL_PATTERNS = [
    ("recurso_improcedente", re.compile(r"IMPROCEDENTE.*[Rr]ecurso|[Rr]ecurso.*IMPROCEDENTE", re.IGNORECASE)),
]

def classify_incumplimiento(text):
    section = extract_resuelve(text)
    for label, pat in INCMPL_PATTERNS:
        if pat.search(section) or pat.search(text):
            return label
    return "declaración"

NULIDAD_PATTERNS = [
    ("fundado_recurso", re.compile(r"DECLARAR\s+FUNDADO|fundado.*recurso|recurso.*fundado", re.IGNORECASE)),
    ("sin_efecto",      re.compile(r"sin\s+efecto\s+(?:la\s+)?(?:Resolución|RJ)|dejar\s+sin\s+efecto", re.IGNORECASE)),
]

def classify_nulidad(text):
    section = extract_resuelve(text)
    for label, pat in NULIDAD_PATTERNS:
        if pat.search(section) or pat.search(text):
            return label
    return "otros"

CUMPLIO_PATTERNS = [
    ("acreditación_parcial", re.compile(
        r"DECLARAR\s+PROCEDENTE\s+EN\s+PARTE\s+(?:la\s+)?solicitud\s+de\s+acreditaci[oó]n", re.IGNORECASE)),
    ("acreditación", re.compile(
        r"DECLARAR\s+PROCEDENTE\s+(?:la\s+)?solicitud\s+de\s+acreditaci[oó]n", re.IGNORECASE)),
]

def classify_cumplio(text):
    section = extract_resuelve(text)
    for label, pat in CUMPLIO_PATTERNS:
        if pat.search(section) or pat.search(text):
            return label
    return "cumplimiento_directo"

def detect_beca(text):
    t = text.lower()
    has_p = "beca presidente" in t
    has_b = "beca bicentenario" in t or "beca generaci" in t and "bicentenario" in t
    if has_p and has_b:
        return "beca_presidente"  # presidente takes priority
    if has_p:
        return "beca_presidente"
    if has_b:
        return "beca_bicentenario"
    return "otro_programa"

def extract_quote(text, label):
    """Pull the most relevant sentence for the classification."""
    sentences = re.split(r"(?<=[.;])\s+", text)
    keywords = {
        "cumplió":        ["CUMPLIDO", "Compromiso de Servicio"],
        "incumplimiento": ["INCUMPLIDO", "incumplimiento"],
        "devolución":     ["DEVOLVER", "reintegro", "pérdida"],
        "nulidad":        ["NULIDAD", "nulo", "sin efecto"],
        "aplazamiento":   ["APLAZAMIENTO", "aplazar"],
        "improcedente":   ["IMPROCEDENTE", "improcedente"],
        "otro":           [],
    }
    kws = keywords.get(label, [])
    for sent in sentences:
        if any(kw.lower() in sent.lower() for kw in kws):
            return sent.strip()[:300]
    return ""

# ── main ──────────────────────────────────────────────────────────────────────
all_txts = sorted(glob.glob(os.path.join(TXT_DIR, "**", "*.txt"), recursive=True))
print(f"TXTs to parse: {len(all_txts)}")

from collections import Counter
counts = Counter()

with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "collection", "filename", "class", "subclass", "beca", "person", "dni", "convocatoria", "quote", "path"
    ])
    writer.writeheader()

    for path in all_txts:
        parts   = path.replace(TXT_DIR + "/", "").split("/")
        collection = parts[0]
        filename   = parts[-1]

        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue

        label    = classify(text)
        subclass = (classify_otro(text)          if label == "otro"
               else classify_devolucion(text)     if label == "devolución"
               else classify_cumplio(text)        if label == "cumplió"
               else classify_aplazamiento(text)   if label == "aplazamiento"
               else classify_improcedente(text)   if label == "improcedente"
               else classify_incumplimiento(text) if label == "incumplimiento"
               else classify_nulidad(text)        if label == "nulidad"
               else "")
        beca     = detect_beca(text)
        counts[label] += 1

        writer.writerow({
            "collection":   collection,
            "filename":     filename,
            "class":        label,
            "subclass":     subclass,
            "beca":         beca,
            "person":       extract_person(text),
            "dni":          extract_dni(text),
            "convocatoria": extract_convocatoria(text),
            "quote":        extract_quote(text, label),
            "path":         path,
        })

print(f"\nResults:")
for label, n in counts.most_common():
    print(f"  {label:20s} {n:5d}")
print(f"\nTotal: {sum(counts.values())}")
print(f"Saved: {OUT_CSV}")
