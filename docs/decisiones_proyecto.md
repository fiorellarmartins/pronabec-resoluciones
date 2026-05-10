# PRONABEC — Decisiones del Proyecto

**Fecha de inicio:** 2026-05-08  
**Objetivo:** Construir un universo completo de resoluciones PRONABEC sobre el Compromiso de Servicio al Perú de becarios de **Beca Presidente de la República** y **Beca Generación del Bicentenario**.

---

## 1. Definición del universo

**Decisión:** Descargar todas las resoluciones de las 20 colecciones de gob.pe correspondientes a las oficinas de postgrado de PRONABEC, no solo las que mencionan "compromiso".

**Por qué:** La búsqueda por palabra clave en gob.pe solo devuelve snippets de ~220 caracteres. Esos snippets capturan bien las resoluciones de `cumplió` (la acción aparece en la primera oración), pero pierden las de `devolución` e `incumplimiento` (la palabra clave aparece más adelante en el documento). Para tener un universo completo es necesario el texto completo de cada PDF.

**Alternativa descartada:** Filtrar por keyword "compromiso" en el buscador de gob.pe → cubre 7,011 docs pero deja fuera una parte desconocida del universo real.

---

## 2. Alcance de colecciones

**Decisión:** Descargar únicamente las 20 colecciones de las oficinas de postgrado (OBPOST, OBE, OGT, OBB, DIAB). No descargar otras colecciones de PRONABEC.

**Por qué:** Las becas objetivo (Beca Presidente, Beca Bicentenario) son programas de postgrado. Las otras colecciones de PRONABEC corresponden a programas de pregrado (Beca 18, Beca Permanencia, Beca Docente) que son fuera del alcance.

| Años | Oficina | Col IDs | Docs |
|------|---------|---------|------|
| 2012-2017 | OBPOST — Oficina de Becas Postgrado | 3173-3178 | 1,222 |
| 2018 | OBE/OGB — Oficina de Gestión de Becas | 2857 | 4,924 |
| 2019-2022 | OGT — Oficina de Gestión del Talento | 2869, 2868, 2362, 4899 | 1,472 |
| 2020-2022 | OBB — Oficina de Bienestar del Beneficiario | 2940, 10425 | 613 |
| 2023 | OGT + OBB | 14804, 15400 | 2,525 |
| 2024-2026 | OGT + OBB + DIAB | 29783, 30615, 37574, 59185, 90276 | 4,182 |
| **TOTAL** | | | **14,938** |

---

## 3. Método de descarga

**Decisión:** Descargar vía páginas de colección de gob.pe, no vía buscador.

**Por qué:** El buscador de gob.pe usa lógica OR (no AND), no permite filtrar por colección, y solo devuelve snippets. Las páginas de colección listan todos los documentos de forma ordenada y completa.

**Pipeline:**
1. Paginar `/colecciones/{cid}?sheet=N` → extraer slugs de normas
2. Fetch `/normas-legales/{slug}` → extraer URL CDN del PDF
3. Descargar PDF de `cdn.www.gob.pe/uploads/document/file/{id}/{filename}`

**Script:** `download_all.py`  
**Output:** `pdfs_all/{LABEL}/` (ej. `pdfs_all/OBPOST_2014/`)  
**Progreso incremental:** Saltea archivos ya descargados.

---

## 4. Detección de PDFs que necesitan OCR

**Decisión:** Clasificar cada PDF como "tiene texto" vs "necesita OCR" antes de procesar, usando `pdftotext`. Umbral: menos de 100 caracteres extraídos → necesita OCR.

**Por qué:** Ejecutar Tesseract en PDFs que ya tienen texto embebido es innecesario y lento. Sin embargo, en la práctica, >99% de los PDFs PRONABEC son documentos escaneados (text=0 chars). Solo 1 de los primeros 876 PDFs descargados era texto-digital.

**Observación:** Los PDFs de 2012-2014 son todos escaneados. Los de colecciones más recientes (DIAB 2022-2026) podrían tener más PDFs digitales — por verificar.

**Script:** `check_ocr_needed.py`  
**Output:** `ocr_check.csv`

---

## 5. OCR

**Decisión:** Usar Tesseract 5.5 con idioma español (`-l spa --psm 1`), convirtiendo primero a imágenes PNG a 300 DPI con `pdftoppm`.

**Por qué:** `pdftotext` retorna vacío en PDFs escaneados. Tesseract con español da buena calidad en documentos administrativos peruanos.

**Script:** `run_ocr.py`  
**Workers:** 4 procesos en paralelo  
**Output:** `txts_all/{LABEL}/` (misma estructura que `pdfs_all/`)  
**Progreso incremental:** Saltea archivos que ya tienen `.txt`.

---

## 6. Filtro por programa

**Decisión:** Para el análisis de Compromiso de Servicio, filtrar solo los documentos que mencionan "Beca Presidente" en el texto completo.

**Por qué:** Las colecciones OBPOST incluyen múltiples programas: Beca Haya de la Torre (2012), Beca Presidente (desde 2013), Beca Docente, y otros. Solo Beca Presidente y Beca Bicentenario son el objeto de estudio.

**Hallazgo:** "Beca Presidente" aparece por primera vez en documentos de 2013 (3 de 44 docs de OBPOST_2013). En 2012 no aparece ninguno — los 20 docs son de otros programas.

---

## 7. Clasificación por regex (primera pasada)

**Decisión:** Aplicar clasificación regex antes de usar Claude API, para cubrir los casos formulaicos a costo cero.

**Por qué:** Las resoluciones usan lenguaje muy estandarizado. Los casos claros (cumplió, devolución, nulidad, etc.) se pueden detectar con patrones simples. Usar la API de Claude solo para los casos ambiguos o `otro`.

**Clases:**

| Clase | Criterio |
|---|---|
| `cumplió` | "ha CUMPLIDO su Compromiso de Servicio" |
| `incumplimiento` | "ha INCUMPLIDO su Compromiso de Servicio" |
| `devolución` | "DEVOLVER...beca/monto", "reintegro", "PÉRDIDA DE LA BECA" |
| `nulidad` | "DECLARAR LA NULIDAD", "nulo y sin efecto" |
| `aplazamiento` | "APROBAR EL APLAZAMIENTO del Compromiso" |
| `improcedente` | "DECLARAR IMPROCEDENTE" |
| `otro` | ningún patrón anterior coincide |

La detección se aplica primero sobre la sección "SE RESUELVE" y luego sobre el texto completo como fallback.

**Script:** `parse_txts.py`  
**Output:** `parsed_results.csv`

---

## 8. Clasificación previa (519 documentos)

Antes de este pipeline, se clasificaron manualmente 519 documentos (subconjunto filtrado por "compromiso" en el buscador original) usando agentes Claude en 26 batches.

**Resultados:**
| Clase | N |
|---|---|
| otro | 304 |
| cumplió | 122 |
| nulidad | 35 |
| devolución | 32 |
| aplazamiento | 14 |
| improcedente | 12 |

Estos 519 docs están en `txt/` y `resultados/`. El Excel consolidado está en `pronabec_compromiso_clasificacion.xlsx`.

**Nota:** La clasificación anterior usaba `devolución` donde el pipeline nuevo usa `devolución` también, pero la definición de `incumplimiento` era `nulidad` en el esquema anterior. Se alinearon los nombres en el pipeline nuevo.

---

## Estado al 2026-05-08

| Etapa | Estado | Progreso |
|---|---|---|
| Descarga PDFs | En curso | ~1,952 / 14,938 |
| OCR | En curso (batch 2) | ~436 TXTs |
| Regex parsing | Ejecutado sobre TXTs disponibles | 395 parseados |
| Beca Presidente (regex) | Parcial | 140 docs |
| Claude API classification | Pendiente | — |

---

## Archivos clave

| Archivo | Descripción |
|---|---|
| `download_all.py` | Descarga PDFs de las 20 colecciones |
| `check_ocr_needed.py` | Clasifica PDFs como texto vs escaneado |
| `run_ocr.py` | Ejecuta Tesseract sobre PDFs escaneados |
| `parse_txts.py` | Clasificación regex de los TXTs |
| `universo_colecciones.md` | Mapa completo de colecciones y conteos |
| `ocr_check.csv` | Resultado del check texto vs OCR por PDF |
| `parsed_results.csv` | Clasificaciones regex actuales |
| `snippets_compromiso.csv` | Snippets de 7,011 docs con "compromiso" (gob.pe) |
| `pronabec_compromiso_clasificacion.xlsx` | Excel de los 519 docs clasificados manualmente |
| `pdfs_all/` | PDFs descargados por colección |
| `txts_all/` | TXTs OCR'd por colección |
