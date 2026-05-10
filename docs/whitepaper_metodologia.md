# clasificación automatizada de resoluciones jefaturales PRONABEC
## metodología

---

### contexto

el Programa Nacional de Becas y Crédito Educativo (PRONABEC) emite resoluciones jefaturales que documentan los resultados de los compromisos de servicio suscritos por becarios de la Beca Presidente de la República y la Beca Generación Bicentenario. estas resoluciones, publicadas en el portal de transparencia, constituyen la única fuente sistemática de información sobre el cumplimiento individual de los beneficiarios.

---

### universo de documentos

se procesaron 14,914 resoluciones jefaturales descargadas desde el portal de transparencia de PRONABEC, correspondientes a cuatro oficinas emisoras:

- **OBE / OBB** — Oficina de Becas en el Exterior / Oficina de Becas Bicentenario (2018–2024)
- **DIAB** — Dirección de Impacto y Acreditación de Becas (2024–2026)
- **OGT** — Oficina de Gestión de Talento (2019–2024)
- **OBPOST** — Oficina de Becas de Postgrado (2012–2017)

de ese universo, 907 documentos correspondían a la Beca Presidente de la República o la Beca Generación Bicentenario, que constituyen el objeto de análisis.

---

### filtrado y clasificación

cada documento fue asignado a una de siete clases según el acto resolutivo principal:

| clase | descripción |
|---|---|
| cumplió | declaración de cumplimiento del compromiso de servicio |
| devolución | orden de restitución de montos o pérdida de beca |
| incumplimiento | declaración formal de incumplimiento |
| aplazamiento | aprobación de postergación del compromiso |
| improcedente | rechazo de una solicitud |
| nulidad | anulación de una resolución anterior |
| otro | trámites administrativos (viajes, modificaciones, admisiones) |

la clasificación inicial fue realizada mediante expresiones regulares y luego validada documento por documento con un modelo de lenguaje (claude sonnet), que confirmó o corrigió la clase asignada, identificó al beneficiario y generó un resumen del acto resolutivo. la tasa de corrección global fue del 42%, con las mayores discrepancias en la clase "devolución".

---

### deduplicación por persona

varios beneficiarios aparecen en más de una resolución a lo largo del tiempo. para construir un padrón de resultados finales se deduplicaron los registros por DNI, conservando la resolución más reciente por persona. de los 907 documentos, 117 no contenían un DNI extraíble y fueron excluidos. los restantes correspondían a 644 personas únicas.

---

### resultados

| resultado | n | % |
|---|---|---|
| cumplió compromiso | 252 | 39.1% |
| otro (admin / viaje / modificación) | 258 | 40.1% |
| aplazamiento | 58 | 9.0% |
| devolución | 48 | 7.5% |
| improcedente | 13 | 2.0% |
| incumplimiento | 10 | 1.6% |
| nulidad | 5 | 0.8% |

la categoría "otro" agrupa principalmente autorizaciones de viaje (36%), rectificaciones de errores materiales (27%) y resoluciones de admisión (17%), que corresponden a trámites intermedios y no a resultados finales del compromiso.

---

*procesamiento realizado en mayo 2026 · fiorella ramirez*
