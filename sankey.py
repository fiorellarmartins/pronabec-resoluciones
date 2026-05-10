#!/usr/bin/env python3
"""
Sankey: Becarios → Classification → Subclass
Source: persons_final.csv (LLM-classified, deduplicated by DNI)
"""
import csv, plotly.graph_objects as go
from collections import defaultdict

CSV = "/Users/fiorellaramirez/Desktop/pronabec_datos/llm_classification/persons_final.csv"
OUT = "/Users/fiorellaramirez/Desktop/pronabec_datos/sankey_pronabec.html"

rows = list(csv.DictReader(open(CSV)))

FALLBACKS = {
    "cumplió":        "cumplimiento_directo",
    "devolución":     "pérdida_otros",
    "incumplimiento": "declaración",
    "aplazamiento":   "otros_motivos",
    "improcedente":   "otros",
    "nulidad":        "otros",
    "otro":           "admin",
}

# aggregate
beca_counts = defaultdict(int)
class_counts = defaultdict(lambda: defaultdict(int))
class_sub    = defaultdict(lambda: defaultdict(int))

for r in rows:
    beca = r["beca"]
    cls  = r["final_class"]
    sub  = r["final_subclass"] if r["final_subclass"] else FALLBACKS.get(cls, "")
    beca_counts[beca] += 1
    class_counts[beca][cls] += 1
    class_sub[cls][sub] += 1

bp_n     = beca_counts["beca_presidente"]
bb_n     = beca_counts["beca_bicentenario"]
total_n  = bp_n + bb_n

COLORS = {
    "entry":            "#4C72B0",
    "beca_presidente":  "#DD8452",
    "beca_bicentenario":"#55A868",
    "cumplió":          "#2CA02C",
    "acreditación":           "#74C476",
    "acreditación_parcial":   "#A1D99B",
    "cumplimiento_directo":   "#238B45",
    "motivos_académicos":     "#C5B0D5",
    "motivos_laborales":      "#9467BD",
    "motivos_salud":          "#DDA0DD",
    "otros_motivos":          "#B09AC7",
    "ampliación":             "#F7B6D2",
    "exoneración":            "#E377C2",
    "acreditación_denegada":  "#CE6DBD",
    "declaración":            "#9B0000",
    "recurso_improcedente":   "#D62728",
    "fundado_recurso":        "#BDBDBD",
    "sin_efecto":             "#7F7F7F",
    "devolución":       "#D62728",
    "incumplimiento":   "#8B0000",
    "aplazamiento":     "#9467BD",
    "improcedente":     "#E377C2",
    "nulidad":          "#7F7F7F",
    "otro":             "#BCBD22",
    "admisión":         "#AEC7E8",
    "viaje":            "#FFBB78",
    "modificación":     "#98DF8A",
    "renuncia":         "#FF9896",
    "excepción":        "#C5B0D5",
    "admin":            "#C49C94",
    "abandono":         "#FF6B6B",
    "bajo_rendimiento": "#FF9F43",
    "no_aceptación":    "#EE5A24",
    "pérdida_otros":    "#C0392B",
    "otros":            "#AAAAAA",
}

def rgba(hex_color, alpha=0.45):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

node_labels, node_colors, node_x = [], [], []

def add_node(label, color_key, x):
    node_labels.append(label)
    node_colors.append(COLORS.get(color_key, "#AAAAAA"))
    node_x.append(x)
    return len(node_labels) - 1

sources, targets, values, link_colors = [], [], [], []

def add_edge(src, tgt, val, color_key):
    if val <= 0: return
    sources.append(src); targets.append(tgt)
    values.append(val)
    link_colors.append(rgba(COLORS.get(color_key, "#AAAAAA")))

# ── Layer 0: entry ────────────────────────────────────────────────────────────
idx_entry = add_node(f"Beca Presidente / Bicentenario\n{total_n:,} personas únicas", "entry", 0.01)

# ── Layer 1: beca type ────────────────────────────────────────────────────────
idx_bp = add_node(f"Beca Presidente\n{bp_n:,}", "beca_presidente", 0.22)
idx_bb = add_node(f"Beca Bicentenario\n{bb_n:,}", "beca_bicentenario", 0.22)
add_edge(idx_entry, idx_bp, bp_n, "beca_presidente")
add_edge(idx_entry, idx_bb, bb_n, "beca_bicentenario")

# ── Layer 2: classifications ──────────────────────────────────────────────────
CLASS_LABEL = {
    "cumplió":        "Cumplió compromiso",
    "incumplimiento": "Incumplimiento",
    "aplazamiento":   "Aplazamiento",
    "improcedente":   "Improcedente",
    "nulidad":        "Nulidad",
    "devolución":     "Devolución",
    "otro":           "Otro",
}
CLASS_ORDER = ["cumplió","incumplimiento","aplazamiento","improcedente","nulidad","devolución","otro"]

combined_class = {
    c: class_counts["beca_presidente"].get(c,0) + class_counts["beca_bicentenario"].get(c,0)
    for c in CLASS_ORDER
}
target_classes = [(c, combined_class[c]) for c in CLASS_ORDER if combined_class.get(c,0) > 0]

class_nodes = {}
for cls, cnt in target_classes:
    class_nodes[cls] = add_node(f"{CLASS_LABEL[cls]}\n{cnt:,}", cls, 0.52)
    bp_cnt = class_counts["beca_presidente"].get(cls, 0)
    bb_cnt = class_counts["beca_bicentenario"].get(cls, 0)
    add_edge(idx_bp, class_nodes[cls], bp_cnt, cls)
    add_edge(idx_bb, class_nodes[cls], bb_cnt, cls)

# ── Layer 3: subclasses ───────────────────────────────────────────────────────
CUMPLIO_SUB_LABEL = {"acreditación":"Acreditación procedente",
                     "acreditación_parcial":"Acreditación parcial",
                     "cumplimiento_directo":"Cumplimiento directo"}
APLAZ_SUB_LABEL   = {"motivos_académicos":"Motivos académicos",
                     "motivos_laborales":"Motivos laborales",
                     "motivos_salud":"Motivos de salud",
                     "otros_motivos":"Otros motivos"}
IMPRPC_SUB_LABEL  = {"aplazamiento":"Aplazamiento denegado",
                     "ampliación":"Ampliación denegada",
                     "exoneración":"Exoneración denegada",
                     "acreditación":"Acreditación denegada",
                     "otros":"Otros"}
INCMPL_SUB_LABEL  = {"declaración":"Declaración de incumplimiento",
                     "recurso_improcedente":"Recurso improcedente"}
NULIDAD_SUB_LABEL = {"fundado_recurso":"Recurso fundado",
                     "sin_efecto":"Resolución sin efecto",
                     "otros":"Otros"}
DEV_SUB_LABEL     = {"abandono":"Abandono","bajo_rendimiento":"Bajo rendimiento",
                     "renuncia":"Renuncia voluntaria","no_aceptación":"No aceptó beca",
                     "pérdida_otros":"Pérdida/otros"}
OTRO_SUB_LABEL    = {"admisión":"Admisión","viaje":"Viaje / retorno",
                     "modificación":"Modificación","admin":"Admin / trámites",
                     "renuncia":"Renuncia","excepción":"Excepción"}

SUB_LABELS = {
    "cumplió":        CUMPLIO_SUB_LABEL,
    "aplazamiento":   APLAZ_SUB_LABEL,
    "improcedente":   IMPRPC_SUB_LABEL,
    "incumplimiento": INCMPL_SUB_LABEL,
    "nulidad":        NULIDAD_SUB_LABEL,
    "devolución":     DEV_SUB_LABEL,
    "otro":           OTRO_SUB_LABEL,
}

for parent_cls in CLASS_ORDER:
    if parent_cls not in class_nodes: continue
    sub_label = SUB_LABELS[parent_cls]
    subs = sorted(
        [(s, class_sub[parent_cls][s]) for s in sub_label if class_sub[parent_cls].get(s, 0) > 0],
        key=lambda x: -x[1]
    )
    if not subs: continue
    for sub, cnt in subs:
        key = f"sub_{parent_cls}_{sub}"
        idx = add_node(f"{sub_label[sub]}\n{cnt:,}", sub, 0.83)
        add_edge(class_nodes[parent_cls], idx, cnt, sub)

# ── figure ────────────────────────────────────────────────────────────────────
fig = go.Figure(go.Sankey(
    arrangement="snap",
    node=dict(
        pad=18,
        thickness=20,
        line=dict(color="#555", width=0.4),
        label=node_labels,
        color=node_colors,
        x=node_x,
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        color=link_colors,
    ),
))

fig.update_layout(
    title=dict(
        text=(f"PRONABEC — Beca Presidente y Bicentenario · Resultado por persona<br>"
              f"<sup>{total_n:,} personas únicas (deduplicado por DNI) · "
              f"clasificación LLM · {bp_n:,} Beca Presidente · {bb_n:,} Bicentenario</sup>"),
        font=dict(size=15),
    ),
    font=dict(size=11, family="Helvetica Neue, Arial"),
    width=1350,
    height=820,
    paper_bgcolor="white",
    margin=dict(l=20, r=20, t=80, b=20),
)

fig.write_html(OUT, include_plotlyjs="cdn")
print(f"Saved: {OUT}")
print(f"\nBeca Presidente ({bp_n}) + Bicentenario ({bb_n}) = {total_n}")
for c, n in target_classes:
    print(f"  {c}: {n}")
