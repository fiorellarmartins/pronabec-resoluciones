# resoluciones jefaturales PRONABEC

análisis automatizado de resoluciones jefaturales de la Beca Presidente de la República y la Beca Generación Bicentenario.

## qué contiene este repositorio

descargué 14,914 resoluciones jefaturales publicadas en el portal de transparencia de PRONABEC, correspondientes a cuatro oficinas emisoras (OBE, OBB, DIAB, OGT, OBPOST) entre 2012 y 2026. de ese universo, identifiqué 907 documentos correspondientes a las dos becas objetivo y los clasifiqué usando un modelo de lenguaje (claude sonnet), obteniendo un padrón de 641 personas únicas con su resultado final.

## estructura

```
├── classify_with_claude.py     clasificación LLM en paralelo
├── sankey.py                   diagrama de flujo de resultados
├── cohort_chart.py             distribución por año de convocatoria
├── export_excel.py             exportación a Excel
├── parsed_results.csv          clasificación regex de los 14,914 documentos
├── pipeline/
│   ├── download_all.py         descarga de PDFs desde el portal PRONABEC
│   ├── run_ocr.py              conversión PDF → texto (OCR)
│   └── parse_txts.py           clasificación inicial por expresiones regulares
├── llm_classification/
│   ├── persons_final.csv       padrón final: 641 personas únicas
│   ├── results.csv             clasificación LLM de los 907 documentos
│   └── results.jsonl           ídem en formato JSONL
├── outputs/
│   ├── clasificacion_pronabec.xlsx
│   ├── sankey_pronabec.html
│   └── cohort_chart.html
└── docs/
    └── whitepaper_metodologia.md
```

## resultados

| resultado | personas | % |
|---|---|---|
| cumplió compromiso | 252 | 39.3% |
| otro (viaje / modificación / admin) | 257 | 40.1% |
| aplazamiento | 57 | 8.9% |
| devolución | 48 | 7.5% |
| improcedente | 12 | 1.9% |
| incumplimiento | 10 | 1.6% |
| nulidad | 5 | 0.8% |

los documentos fuente (PDFs y TXTs, ~15GB) no están incluidos en el repositorio.

---

# PRONABEC jefatural resolutions

automated analysis of jefatural resolutions from the Beca Presidente de la República and Beca Generación Bicentenario scholarship programs.

## what this repository contains

14,914 jefatural resolutions were downloaded from the PRONABEC transparency portal, covering four issuing offices (OBE, OBB, DIAB, OGT, OBPOST) between 2012 and 2026. of that universe, 907 documents were identified as belonging to the two target scholarship programs and classified using a language model (claude sonnet), producing a registry of 641 unique individuals with their final outcome.

## structure

```
├── classify_with_claude.py     parallel LLM classification
├── sankey.py                   results flow diagram
├── cohort_chart.py             distribution by cohort year
├── export_excel.py             Excel export
├── parsed_results.csv          regex classification of all 14,914 documents
├── pipeline/
│   ├── download_all.py         PDF download from PRONABEC portal
│   ├── run_ocr.py              PDF to text conversion (OCR)
│   └── parse_txts.py           initial regex-based classification
├── llm_classification/
│   ├── persons_final.csv       final registry: 641 unique individuals
│   ├── results.csv             LLM classification of 907 documents
│   └── results.jsonl           same in JSONL format
├── outputs/
│   ├── clasificacion_pronabec.xlsx
│   ├── sankey_pronabec.html
│   └── cohort_chart.html
└── docs/
    └── whitepaper_metodologia.md
```

## results

| outcome | individuals | % |
|---|---|---|
| fulfilled commitment | 252 | 39.3% |
| other (travel / modification / admin) | 257 | 40.1% |
| deferral | 57 | 8.9% |
| restitution | 48 | 7.5% |
| dismissed request | 12 | 1.9% |
| non-compliance | 10 | 1.6% |
| nullification | 5 | 0.8% |

source documents (PDFs and TXTs, ~15GB) are not included in this repository.
