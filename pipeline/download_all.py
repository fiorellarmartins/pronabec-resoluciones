#!/usr/bin/env python3
"""
Download all PRONABEC resolution PDFs from gob.pe across 20 collections.
Saves to: pdfs_all/{collection_id}/
Resumes from download_log.txt — skips slugs already processed.
Logs progress to: download_log.txt
"""
import re, time, os, threading
from urllib.parse import unquote
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

COLLECTIONS = {
    # OBPOST 2012-2017
    3173: "OBPOST_2012",
    3174: "OBPOST_2013",
    3175: "OBPOST_2014",
    3176: "OBPOST_2015",
    3177: "OBPOST_2016",
    3178: "OBPOST_2017",
    # OBE/OGT 2018-2021
    2857: "OBE_2018",
    2869: "OGT_2019",
    2868: "OGT_2020",
    2940: "OBB_2020",
    2362: "OGT_2021",
    # DIAB/OBB 2022-2026
    4899:  "OGT_2022",
    10425: "OBB_2022",
    14804: "OGT_2023",
    15400: "OBB_2023",
    29783: "OGT_2024",
    30615: "OBB_2024",
    37574: "DIAB_2024",
    59185: "DIAB_2025",
    90276: "DIAB_2026",
}

BASE_DIR  = "/Users/fiorellaramirez/Desktop/pronabec_datos/pdfs_all"
LOG_FILE  = "/Users/fiorellaramirez/Desktop/pronabec_datos/download_log.txt"
COLL_BASE = "https://www.gob.pe/institucion/pronabec/colecciones"
NORM_BASE = "https://www.gob.pe/institucion/pronabec/normas-legales"
HEADERS   = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
WORKERS   = 8

os.makedirs(BASE_DIR, exist_ok=True)

# ── load already-processed slugs from log ─────────────────────────────────────
done_slugs = set()
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2 and parts[1] != "slug":  # skip header
                done_slugs.add(parts[1])
print(f"Resuming: {len(done_slugs)} slugs already processed")

# ── shared session + log lock ──────────────────────────────────────────────────
session = requests.Session()
session.headers.update(HEADERS)
log_lock = threading.Lock()
stats = {"downloaded": 0, "skipped": 0, "failed": 0}
stats_lock = threading.Lock()

# Append header if log is new
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("collection\tslug\tstatus\tpath\n")

def log(collection, slug, status, path=""):
    with log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{collection}\t{slug}\t{status}\t{path}\n")

def fetch(url, retries=3, stream=False):
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=30, stream=stream)
            r.raise_for_status()
            return r
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(1.5)

def get_collection_slugs(cid):
    slugs = []
    sheet = 1
    while True:
        r = fetch(f"{COLL_BASE}/{cid}?sheet={sheet}")
        if not r:
            break
        html = r.text
        page_slugs = re.findall(r'/normas-legales/(\d+-[^\s"<>]+)', html)
        if not page_slugs:
            break
        slugs.extend(page_slugs)
        if f"sheet={sheet+1}" not in html:
            break
        sheet += 1
        time.sleep(0.2)
    return list(dict.fromkeys(slugs))

def get_pdf_url(slug):
    r = fetch(f"{NORM_BASE}/{slug}")
    if not r:
        return None
    urls = re.findall(
        r'https://cdn\.www\.gob\.pe/uploads/document/file/\d+/[^\s"<>?]+\.pdf[^\s"<>?]*',
        r.text
    )
    pdfs = [u for u in urls if 'preview_' not in u]
    return pdfs[0] if pdfs else None

def download_pdf(url, dest):
    r = fetch(url, stream=True)
    if not r:
        return False
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return True

def process_slug(slug, label, out_dir):
    pdf_url = get_pdf_url(slug)
    time.sleep(0.15)

    if not pdf_url:
        log(label, slug, "no_url")
        with stats_lock:
            stats["failed"] += 1
        return "failed"

    filename = unquote(pdf_url.split("/")[-1].split("?")[0])
    dest = os.path.join(out_dir, filename)

    if os.path.exists(dest):
        log(label, slug, "skipped", dest)
        with stats_lock:
            stats["skipped"] += 1
        return "skipped"

    ok = download_pdf(pdf_url, dest)
    time.sleep(0.15)

    if ok:
        log(label, slug, "downloaded", dest)
        with stats_lock:
            stats["downloaded"] += 1
        return "downloaded"
    else:
        log(label, slug, "failed", pdf_url)
        with stats_lock:
            stats["failed"] += 1
        return "failed"

# ── main ──────────────────────────────────────────────────────────────────────
for cid, label in COLLECTIONS.items():
    out_dir = os.path.join(BASE_DIR, label)
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Collection {cid} — {label}")
    all_slugs = get_collection_slugs(cid)
    pending   = [s for s in all_slugs if s not in done_slugs]
    print(f"  Slugs: {len(all_slugs)} total, {len(pending)} pending")

    if not pending:
        print(f"  Already complete, skipping.")
        continue

    done_in_coll = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(process_slug, slug, label, out_dir): slug for slug in pending}
        for i, fut in enumerate(as_completed(futures), 1):
            fut.result()
            done_in_coll += 1
            if done_in_coll % 50 == 0 or done_in_coll == len(pending):
                with stats_lock:
                    d, sk, f = stats["downloaded"], stats["skipped"], stats["failed"]
                print(f"  [{label}] {done_in_coll}/{len(pending)} — dl={d} skip={sk} fail={f}", flush=True)

    with stats_lock:
        print(f"  Done: {label} — dl={stats['downloaded']} skip={stats['skipped']} fail={stats['failed']}")

print(f"\n{'='*60}")
with stats_lock:
    print(f"FINAL: downloaded={stats['downloaded']}  skipped={stats['skipped']}  failed={stats['failed']}")
print(f"Folder: {BASE_DIR}")
