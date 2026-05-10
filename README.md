# Resoluciones Jefaturales PRONABEC

Análisis automatizado de resoluciones jefaturales de la Beca Presidente de la República y la Beca Generación Bicentenario.

## Qué contiene este repositorio

Descargué 14,914 resoluciones jefaturales publicadas en el portal de transparencia de PRONABEC, correspondientes a cuatro oficinas emisoras (OBE, OBB, DIAB, OGT, OBPOST) entre 2012 y 2026. De ese universo, identifiqué 907 documentos correspondientes a las dos becas objetivo y los clasifiqué usando un modelo de lenguaje (Claude Sonnet), obteniendo un padrón de 641 personas únicas con su resultado final.

## Estructura

```
├── classify_with_claude.py     Clasificación LLM en paralelo
├── sankey.py                   Diagrama de flujo de resultados
├── cohort_chart.py             Distribución por año de convocatoria
├── export_excel.py             Exportación a Excel
├── parsed_results.csv          Clasificación regex de los 14,914 documentos
├── pipeline/
│   ├── download_all.py         Descarga de PDFs desde el portal PRONABEC
│   ├── run_ocr.py              Conversión PDF → texto (OCR)
│   └── parse_txts.py           Clasificación inicial por expresiones regulares
├── llm_classification/
│   ├── persons_final.csv       Padrón final: 641 personas únicas
│   ├── results.csv             Clasificación LLM de los 907 documentos
│   └── results.jsonl           Ídem en formato JSONL
├── outputs/
│   ├── clasificacion_pronabec.xlsx
│   ├── sankey_pronabec.html
│   └── cohort_chart.html
└── docs/
    └── whitepaper_metodologia.md
```

## Resultados

| Resultado | Personas | % |
|---|---|---|
| Cumplió compromiso | 252 | 39.3% |
| Otro (viaje / modificación / admin) | 257 | 40.1% |
| Aplazamiento | 57 | 8.9% |
| Devolución | 48 | 7.5% |
| Improcedente | 12 | 1.9% |
| Incumplimiento | 10 | 1.6% |
| Nulidad | 5 | 0.8% |

Los documentos fuente (PDFs y TXTs, ~15GB) no están incluidos en el repositorio. Están disponibles en OSF: [osf.io/74pjd](https://osf.io/74pjd)

---

# PRONABEC Jefatural Resolutions

Automated analysis of jefatural resolutions from the Beca Presidente de la República and Beca Generación Bicentenario scholarship programs.

## What This Repository Contains

14,914 jefatural resolutions were downloaded from the PRONABEC transparency portal, covering four issuing offices (OBE, OBB, DIAB, OGT, OBPOST) between 2012 and 2026. Of that universe, 907 documents were identified as belonging to the two target scholarship programs and classified using a language model (Claude Sonnet), producing a registry of 641 unique individuals with their final outcome.

## Structure

```
├── classify_with_claude.py     Parallel LLM classification
├── sankey.py                   Results flow diagram
├── cohort_chart.py             Distribution by cohort year
├── export_excel.py             Excel export
├── parsed_results.csv          Regex classification of all 14,914 documents
├── pipeline/
│   ├── download_all.py         PDF download from PRONABEC portal
│   ├── run_ocr.py              PDF to text conversion (OCR)
│   └── parse_txts.py           Initial regex-based classification
├── llm_classification/
│   ├── persons_final.csv       Final registry: 641 unique individuals
│   ├── results.csv             LLM classification of 907 documents
│   └── results.jsonl           Same in JSONL format
├── outputs/
│   ├── clasificacion_pronabec.xlsx
│   ├── sankey_pronabec.html
│   └── cohort_chart.html
└── docs/
    └── whitepaper_metodologia.md
```

## Results

| Outcome | Individuals | % |
|---|---|---|
| Fulfilled commitment | 252 | 39.3% |
| Other (travel / modification / admin) | 257 | 40.1% |
| Deferral | 57 | 8.9% |
| Restitution | 48 | 7.5% |
| Dismissed request | 12 | 1.9% |
| Non-compliance | 10 | 1.6% |
| Nullification | 5 | 0.8% |

Source documents (PDFs and TXTs, ~15GB) are not included in this repository. They are available on OSF: [osf.io/74pjd](https://osf.io/74pjd)
