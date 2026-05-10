#!/usr/bin/env python3
"""
Stacked bar: resolution class distribution by convocatoria year
Beca Presidente + Bicentenario only.
"""
import csv, re
from collections import defaultdict
import plotly.graph_objects as go

CSV = "/Users/fiorellaramirez/Desktop/pronabec_datos/llm_classification/persons_final.csv"
OUT = "/Users/fiorellaramirez/Desktop/pronabec_datos/cohort_chart.html"

VALID_YEARS = {str(y) for y in range(2010, 2026)}

rows = list(csv.DictReader(open(CSV)))
target = [r for r in rows if r["convocatoria"] in VALID_YEARS]

CLASS_ORDER = ["cumplió","devolución","incumplimiento","aplazamiento","improcedente","nulidad","otro"]
CLASS_LABEL = {
    "cumplió":        "Cumplió compromiso",
    "devolución":     "Devolución",
    "incumplimiento": "Incumplimiento",
    "aplazamiento":   "Aplazamiento",
    "improcedente":   "Improcedente",
    "nulidad":        "Nulidad",
    "otro":           "Otro",
}
COLORS = {
    "cumplió":        "#2CA02C",
    "devolución":     "#D62728",
    "incumplimiento": "#8B0000",
    "aplazamiento":   "#9467BD",
    "improcedente":   "#E377C2",
    "nulidad":        "#7F7F7F",
    "otro":           "#BCBD22",
}

# aggregate counts[year][class]
counts = defaultdict(lambda: defaultdict(int))
for r in target:
    counts[r["convocatoria"]][r["final_class"]] += 1

years = sorted(counts.keys())
year_totals = {y: sum(counts[y].values()) for y in years}

fig = go.Figure()

for cls in CLASS_ORDER:
    y_vals = [counts[yr][cls] for yr in years]
    pct    = [counts[yr][cls] / year_totals[yr] * 100 if year_totals[yr] else 0 for yr in years]
    fig.add_trace(go.Bar(
        name=CLASS_LABEL[cls],
        x=years,
        y=y_vals,
        marker_color=COLORS[cls],
        customdata=list(zip(pct, [year_totals[yr] for yr in years])),
        hovertemplate=(
            "<b>%{x}</b> — " + CLASS_LABEL[cls] + "<br>"
            "%{y} resoluciones (%{customdata[0]:.1f}% de %{customdata[1]})<extra></extra>"
        ),
    ))

fig.update_layout(
    barmode="stack",
    title=dict(
        text="PRONABEC — Resoluciones por Convocatoria<br>"
             "<sup>Beca Presidente de la República y Beca Generación Bicentenario · "
             f"{len(target):,} personas únicas · clasificación LLM · última resolución por DNI</sup>",
        font=dict(size=15),
    ),
    xaxis=dict(title="Año de convocatoria", tickmode="linear", dtick=1),
    yaxis=dict(title="Número de resoluciones"),
    legend=dict(traceorder="normal", title="Clasificación"),
    font=dict(size=12, family="Helvetica Neue, Arial"),
    width=1050,
    height=560,
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=60, r=20, t=90, b=60),
)
fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor="#EEEEEE")

fig_norm = go.Figure()
for cls in CLASS_ORDER:
    pct = [counts[yr][cls] / year_totals[yr] * 100 if year_totals[yr] else 0 for yr in years]
    fig_norm.add_trace(go.Bar(
        name=CLASS_LABEL[cls],
        x=years,
        y=pct,
        marker_color=COLORS[cls],
        customdata=[counts[yr][cls] for yr in years],
        hovertemplate=(
            "<b>%{x}</b> — " + CLASS_LABEL[cls] + "<br>"
            "%{y:.1f}% (%{customdata} resoluciones)<extra></extra>"
        ),
    ))

fig_norm.update_layout(
    barmode="stack",
    title=dict(
        text="PRONABEC — Composición por Convocatoria (normalizado)<br>"
             "<sup>Beca Presidente de la República y Beca Generación Bicentenario · "
             f"{len(target):,} personas únicas · clasificación LLM · última resolución por DNI</sup>",
        font=dict(size=15),
    ),
    xaxis=dict(title="Año de convocatoria", tickmode="linear", dtick=1),
    yaxis=dict(title="% de resoluciones", ticksuffix="%", range=[0, 100]),
    legend=dict(traceorder="normal", title="Clasificación"),
    font=dict(size=12, family="Helvetica Neue, Arial"),
    width=1050,
    height=560,
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=60, r=20, t=90, b=60),
)
fig_norm.update_xaxes(showgrid=False)
fig_norm.update_yaxes(showgrid=True, gridcolor="#EEEEEE")

# write both charts to one HTML
from plotly.subplots import make_subplots
import plotly.io as pio

html_abs  = fig.to_html(full_html=False, include_plotlyjs="cdn")
html_norm = fig_norm.to_html(full_html=False, include_plotlyjs=False)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("<html><head><meta charset='utf-8'></head><body>\n")
    f.write(html_abs + "\n<hr style='margin:32px 0'>\n" + html_norm)
    f.write("\n</body></html>")

print(f"Saved: {OUT}")
print(f"\nCohort totals:")
for yr in years:
    breakdown = "  ".join(f"{c}:{counts[yr][c]}" for c in CLASS_ORDER if counts[yr][c])
    print(f"  {yr}: {year_totals[yr]:3d}  |  {breakdown}")
print(f"\nDropped (missing/invalid year): {len(rows) - len(target) + sum(1 for r in rows if r['beca'] not in ('beca_presidente','beca_bicentenario'))}")
