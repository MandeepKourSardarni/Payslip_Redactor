import os, shutil, zipfile
from pathlib import Path
from uuid import uuid4
from subprocess import run, CalledProcessError
from flask import Flask, request, send_file, Response

# --- config ---
BASE = Path(__file__).parent.resolve()
RUNS = BASE / "runs"
RUNS.mkdir(exist_ok=True)
ALLOWED_XL = {".xlsx", ".xls", ".csv"}
ALLOWED_PDF = {".pdf"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GB

HTML = """<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Payslip Redactor</title>
<style>
 body{font:16px system-ui;margin:24px;max-width:720px}
 .card{padding:16px;border:1px solid #ddd;border-radius:12px}
 label{font-weight:600;display:block;margin-top:12px}
 input[type=file]{margin:6px 0}
 button{margin-top:16px;padding:10px 14px;border:0;border-radius:10px;background:#2563eb;color:#fff;font-weight:700;cursor:pointer}
 .tip{color:#666}
</style></head>
<body>
  <h1>Payslip Universal Redactor</h1>
  <p class="tip">Upload one Excel/CSV and one or more PDF payslips. You’ll receive a ZIP with redacted PDFs and a results spreadsheet.</p>
  <form class="card" action="/process" method="POST" enctype="multipart/form-data">
    <label for="excel">Excel/CSV</label>
    <input id="excel" name="excel" type="file" accept=".xlsx,.xls,.csv" required>
    <label for="pdfs">Payslip PDFs (multiple)</label>
    <input id="pdfs" name="pdfs" type="file" accept=".pdf" multiple>
    <button type="submit">Run Redactor</button>
  </form>
</body></html>"""

def _bad(msg: str) -> Response:
    return Response(f"<!doctype html><pre>{msg}</pre>", status=400, mimetype="text/html")

@app.get("/")
def index():
    return Response(HTML, mimetype="text/html")

@app.post("/process")
def process():
    excel = request.files.get("excel")
    if not excel or not excel.filename:
        return _bad("Missing Excel/CSV file.")

    if Path(excel.filename).suffix.lower() not in ALLOWED_XL:
        return _bad("Unsupported Excel/CSV type. Use .xlsx, .xls, or .csv.")

    pdfs = request.files.getlist("pdfs")
    for f in pdfs:
        if f and f.filename and Path(f.filename).suffix.lower() not in ALLOWED_PDF:
            return _bad(f"Unsupported file: {f.filename}")

    # Create a per-run folder; keep it simple & inspectable
    run_id = uuid4().hex[:10]
    work = RUNS / run_id
    work.mkdir(parents=True, exist_ok=True)

    # Save Excel and PDFs together so relative paths in the sheet work
    excel_path = work / Path(excel.filename).name
    excel.save(excel_path)
    for f in pdfs:
        if f and f.filename:
            (work / Path(f.filename).name).write_bytes(f.read())

    # Call your script as a subprocess (avoids import side-effects)
    cmd = [os.sys.executable, str((BASE / "payslip_universal_redactor.py").resolve()),
           "--input", excel_path.name, "--verbose"]
    rc = 0
    try:
        rc = run(cmd, cwd=work, check=False).returncode
    except CalledProcessError as e:
        rc = e.returncode or 1

    # Stage outputs into a tiny bundle folder
    stage = work / "_bundle"
    stage.mkdir(exist_ok=True)
    # copy redacted PDFs + results excel/csv
    for p in work.iterdir():
        if p.name.startswith("_bundle"): continue
        if p.suffix.lower() in {".pdf", ".xlsx", ".xls", ".csv"}:
            shutil.copy2(p, stage / p.name)

    (stage / "README.txt").write_text(
        "ZIP includes redacted PDFs (*_redacted.pdf) and Payslips_redacted.xlsx.\n"
        f"Exit code: {rc}\n"
    )

    # Make ZIP and return it
    zip_path = work.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in stage.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(stage))

    return send_file(zip_path, as_attachment=True,
                     download_name=f"redaction_results_{run_id}.zip",
                     mimetype="application/zip")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
