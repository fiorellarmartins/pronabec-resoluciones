#!/usr/bin/env python3
"""
OCR runner — truly incremental.
Rasterizer thread + tesseract pool run concurrently.
Future callbacks write each TXT the moment its last page finishes.
Safe to re-run: skips existing TXTs.
"""
import os, subprocess, glob, csv, time, threading, queue
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

BASE_DIR  = "/Users/fiorellaramirez/Desktop/pronabec_datos/pdfs_all"
TXT_DIR   = "/Users/fiorellaramirez/Desktop/pronabec_datos/txts_all"
OCR_CHECK = "/Users/fiorellaramirez/Desktop/pronabec_datos/ocr_check.csv"
STAGE_DIR = "/tmp/pronabec_ocr_stage"
TESS_WORKERS = 8

os.makedirs(TXT_DIR, exist_ok=True)
os.makedirs(STAGE_DIR, exist_ok=True)

text_ok = set()
if os.path.exists(OCR_CHECK):
    with open(OCR_CHECK, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["needs_ocr"] == "0":
                text_ok.add(row["path"])

def txt_path(pdf_path):
    rel  = os.path.relpath(pdf_path, BASE_DIR)
    base = rel.replace(".pdf.pdf", "").replace(".pdf", "")
    return os.path.join(TXT_DIR, base + ".txt")

def pdf_stage_dir(pdf_path):
    rel  = os.path.relpath(pdf_path, BASE_DIR)
    stem = rel.replace(".pdf.pdf","").replace(".pdf","").replace("/","_").replace(" ","_")
    return os.path.join(STAGE_DIR, stem)

def pdftoppm_pdf(pdf_path):
    stage = pdf_stage_dir(pdf_path)
    pages = sorted(glob.glob(os.path.join(stage, "*.png")))
    if pages:
        return pages
    os.makedirs(stage, exist_ok=True)
    subprocess.run(
        ["pdftoppm", "-r", "300", "-png", pdf_path, os.path.join(stage, "page")],
        capture_output=True, timeout=120
    )
    return sorted(glob.glob(os.path.join(stage, "*.png")))

def tesseract_page(img_path):
    r = subprocess.run(
        ["tesseract", img_path, "stdout", "-l", "spa", "--psm", "1"],
        capture_output=True, timeout=90
    )
    return r.stdout.decode("utf-8", errors="ignore")


if __name__ == "__main__":
    all_pdfs = sorted(glob.glob(os.path.join(BASE_DIR, "**", "*.pdf"), recursive=True))
    pending  = [p for p in all_pdfs
                if not (os.path.exists(txt_path(p)) and os.path.getsize(txt_path(p)) > 0)]

    text_pend = [p for p in pending if p in text_ok]
    ocr_pend  = [p for p in pending if p not in text_ok]

    print(f"Total PDFs    : {len(all_pdfs)}")
    print(f"Already done  : {len(all_pdfs) - len(pending)}")
    print(f"Text-based    : {len(text_pend)}")
    print(f"OCR needed    : {len(ocr_pend)}", flush=True)

    if text_pend:
        print(f"\nExtracting {len(text_pend)} text-based PDFs...")
        for p in text_pend:
            out = txt_path(p)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            subprocess.run(["pdftotext", "-layout", p, out], capture_output=True, timeout=60)
        print("Text extraction done.", flush=True)

    if not ocr_pend:
        print("No OCR work remaining.")
        raise SystemExit(0)

    print(f"\nPipeline: {len(ocr_pend)} PDFs, {TESS_WORKERS} tesseract workers", flush=True)

    # Shared state (all protected by results_lock)
    results_lock   = threading.Lock()
    page_results   = defaultdict(dict)   # pdf -> {idx: text}
    pdf_page_counts = {}                 # pdf -> total pages
    pdfs_written   = [0]
    pages_done     = [0]
    pages_total    = [0]
    start          = time.time()

    def maybe_write(pdf):
        """Called under results_lock. Writes TXT if all pages collected."""
        expected = pdf_page_counts.get(pdf)
        if expected is None or len(page_results[pdf]) < expected:
            return
        out = txt_path(pdf)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        texts = [page_results[pdf].get(i, "") for i in range(expected)]
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(texts))
        del page_results[pdf]
        pdfs_written[0] += 1
        elapsed = time.time() - start
        rate    = pages_done[0] / elapsed if elapsed > 0 else 0
        rem     = (pages_total[0] - pages_done[0]) / rate if rate > 0 else 0
        print(f"  wrote {pdfs_written[0]:4d} TXTs  |  "
              f"pages {pages_done[0]}/{pages_total[0]}  |  ~{rem/60:.0f}m left", flush=True)

    def make_callback(pdf, idx):
        def cb(future):
            try:
                text = future.result()
            except Exception:
                text = ""
            with results_lock:
                page_results[pdf][idx] = text
                pages_done[0] += 1
                maybe_write(pdf)
        return cb

    pool = ProcessPoolExecutor(max_workers=TESS_WORKERS)

    def rasterize_all():
        sem  = threading.Semaphore(4)
        lock = threading.Lock()
        done = [0]

        def do_one(pdf):
            try:
                pages = pdftoppm_pdf(pdf)
            except Exception as e:
                print(f"  skip (error): {os.path.basename(pdf)} — {e}", flush=True)
                pages = []
            try:
                with results_lock:
                    pdf_page_counts[pdf] = len(pages)
                    pages_total[0] += len(pages)
                    if len(pages) == 0:
                        pdfs_written[0] += 1
                for idx, img in enumerate(pages):
                    f = pool.submit(tesseract_page, img)
                    f.add_done_callback(make_callback(pdf, idx))
                with lock:
                    done[0] += 1
                    if done[0] % 100 == 0 or done[0] == len(ocr_pend):
                        print(f"  rasterized {done[0]}/{len(ocr_pend)} PDFs  "
                              f"({pages_total[0]} pages queued)", flush=True)
            finally:
                sem.release()

        threads = []
        for pdf in ocr_pend:
            sem.acquire()
            t = threading.Thread(target=do_one, args=(pdf,), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    rast_thread = threading.Thread(target=rasterize_all, daemon=False)
    rast_thread.start()
    rast_thread.join()

    # Wait for all tesseract jobs to complete
    pool.shutdown(wait=True)

    import shutil
    shutil.rmtree(STAGE_DIR, ignore_errors=True)

    print(f"\nDone. {pdfs_written[0]} PDFs written, {pages_total[0]} pages, "
          f"{(time.time()-start)/60:.1f}m total")
