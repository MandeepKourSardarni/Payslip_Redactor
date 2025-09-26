# 🧾 Universal Payslip Redactor

Batch-redacts **addresses** in payslip PDFs from one Excel/CSV.  
**White masks by default**, names/dates/IDs kept, OCR fallback, tidy merges, and a results workbook with **clickable links**.  


---

## ✨ Highlights

- 🎯 **Made for checks and audits** — helps confirm if a worker is on the supplier’s payroll and can flag subcontracting/third-party work.
- 🔐 **Hides personal info** — redacts address, DOB, “amount in words,” and net pay. **Keeps** name, dates, and emp_id.  
  Default mask is white; switch to black with `fill=(0,0,0)`.
- 📦 **Works in bulk** — handles **500–1000+** payslips in one go from a single Excel/CSV, cutting manual work for HR/Finance/Payroll.
- 🖥️ **Runs on your computer** — no uploads to any website or third party.
- ⚡ **Fast and scan-friendly** — OCR fallback for image-only PDFs.
- 🧼 **Clean masks** — safe merging that never covers the employee name.
- 📑 **Easy results** — redacted PDFs + an Excel file (`Payslips_redacted.xlsx`) with **clickable links**.
- 🧭 **Works with many templates** — robust across different payslip layouts; we’ve also redacted multiple **resume** templates successfully.


---

## 🚀 Quick Start

```bash
# Default: looks for Payslips.xlsx in the current folder
python payslip_universal_redactor.py

# Be chatty
python payslip_universal_redactor.py --verbose

# Pick a specific input & sheet
python payslip_universal_redactor.py --input MyRoster.xlsx --sheet "June"

# CSV input
python payslip_universal_redactor.py --input roster.csv

# Custom results workbook name
python payslip_universal_redactor.py --out MyRedactions.xlsx

# Skip writing the helper .ipynb
python payslip_universal_redactor.py --no-notebook
````

**Per-file output:** each PDF → `*_redacted.pdf` beside the original
**Summary output:** `Payslips_redacted.xlsx` → column `payslip_redacted_link` is made **clickable**

---

## 📥 Input Format (auto-detect)

Provide an **Excel (.xlsx)** or **CSV** with columns like:

* **Employee name**: `empname`, `emp_name`, `employee`, `employee_name`, `name`
* **Employee ID**: `empid`, `emp_id`, `employeeid`, `employee_id`, `id`
* **Payslip path/URL**: `payslip`, `payslip_link`, `payslip_path`, `file`, `pdf`
  (or any column that looks like a `.pdf` path/URL)

🗂️ **Relative** PDF paths resolve **relative to the spreadsheet file**.

---

## 🔒 What’s Redacted vs Kept

**Redacted (white):**

* Values to the **right** of labels: `Address`, `Amount in words`, `Net Pay in INR/USD/CAD`, `DOB`
* **Under-name** address fragments (ALL-CAPS shards, single letters like `N`, and digit lines)
* **Bottom-left** address clusters

**Kept (never masked):**

* **Employee name** (fuzzy ≥ 0.60)
* **Dates** (ISO, DMY, ranges, times, “Month YYYY”, `YYYYMMDD`, `YYYY MM DD`)
* **Employee ID** (direct/contained match)
* Pay dates near **PAYMENT DATE / PAY END DATE** labels

---

## 🎛️ Mask Color

* Default is **white**.
* To switch to **black**, change the `fill` passed to `redact_page` in `process_pdf`:

```python
# inside process_pdf(...)
n = redact_page(page, rects, fill=(0,0,0))  # ⬛ black masks
```

> The function accepts **RGB floats** in 0–1; `(1,1,1)` = white, `(0,0,0)` = black.

---

## ⚙️ Requirements

* Python **3.8+**
* Auto-installs: `pymupdf`, `pandas`, `openpyxl`, `pillow`, `pytesseract`
* Optional but recommended for scanned PDFs: **Tesseract** CLI on your system `PATH`

A small helper **Jupyter notebook** is written next to your input for convenience (disable with `--no-notebook`).

---

## 🧠 How It Works (brief)

1. Extract words (PyMuPDF); if none, rasterize and **OCR** with Tesseract.
2. **Protect** any text window that fuzzy-matches the employee **name** (never redact or merge across).
3. For each label (`Address`, etc.), **redact only the value** to its right on the **same line**.
4. Find address blocks **under the name** (consecutive address-ish lines) and **bottom-left** clusters; mask as **clean rectangles**.
5. **Keep** date-like tokens and the **emp_id**; redact other numeric tokens.
6. Apply **white** (or chosen color) masks with a small padding, save the redacted PDF.
7. Write a results workbook and make links **clickable**.

---

## 🧪 Notes & Troubleshooting

* **“PDF not found”** → Fix paths; remember relative paths are resolved **next to the spreadsheet**.
* **Name got masked** → Ensure a name column exists; fuzzy threshold is 0.60 and ignores single-letter initials.
* **Dates masked** → Most formats are recognized; placing **pay-date labels** near dates helps context.
* **Address leaks** → Under-name band & bottom-left clusters are broad; adding an explicit `Address:` label makes it deterministic.
* **Scanned PDFs** → Install Tesseract; quality improves around **300 DPI**.

**Exit codes:** `0` success · `2` input/read error · `3` results workbook write failure

---

## 🔧 Customize (optional)

* Add more labels in `ADDRESS_LABELS`, `AMOUNT_WORDS_LABELS`, etc.
* Extend street/unit vocab in `STREET_KEYWORDS`, `UNIT_KEYWORDS`.
* Tune all-caps detection via `RE_SHORT_UPPER`.
* Adjust name fuzzy threshold if your OCR is noisy.

---

## 🛡️ Privacy

Uses PyMuPDF `apply_redactions()` → content is **removed**, not merely hidden. All processing is **local**.

```
```
