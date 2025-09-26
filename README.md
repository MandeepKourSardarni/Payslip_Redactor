# Payslip Universal Redactor

**White-mask redaction for PDFs driven by an Excel/CSV roster — keeps names, keeps pay dates & emp IDs, and surgically wipes addresses**

---

## What this tool does

Give it a spreadsheet of employees and links to their payslip PDFs. For each PDF it will:

* **Redact in white** (not black boxes), permanently removing content from the file.
* **Never redact the employee’s name** (fuzzy matched at ≥60% to survive OCR glitches, spacing, or initials).
* **Preserve dates and emp IDs** (so audits still make sense).
* **Only mask values to the right of specific labels**:
  `Address`, `Amount in words`, `Net Pay in {INR|USD|CAD}`, `DOB` — the label text stays visible; the **value** is masked.
* **Catch free-form address blocks** you didn’t label, in two places:

  * **Directly under the name** (a smart band that scoops up short all-caps fragments and lone letters like “E ST”, “N”).
  * **Bottom-left stubs** (common tear-off areas) using a small cluster heuristic.
* **Safely merge rectangles** without ever crossing a detected name box.
* **Return a results spreadsheet** with **clickable links** to each redacted PDF.

Everything runs locally. If a page has no extractable text, it will **fall back to Tesseract OCR** (if installed).

---

## Why it’s hard — and how this script solves it

* **Names are sticky**: Fuzzy matching (≥0.60) guards against unwanted name redaction across fonts/kerning/ocr noise.
* **Addresses are sneaky**: Payslips often split addresses into tiny, all-caps shards. The **“under name” band** + **“bottom-left cluster”** logic treats short caps lines (“SHERBOURNE”, “N”) and digit-bearing snippets as address-ish and merges them into one clean mask.
* **Labels keep context**: We **leave labels visible** and only wipe the **values** to their right on the same line.
* **Dates & emp_id remain readable**: Regex + context windows keep pay dates intact and prevent emp_id from being wiped.

---

## Input & output at a glance

* **Input file**: `Payslips.xlsx` (default) or any `.xlsx`/`.csv` you specify.
  The script auto-detects likely columns:

  * Employee ID: any of `empid, emp_id, employeeid, employee_id, id`
  * Employee name: any of `empname, emp_name, employee, employee_name, name`
  * Payslip path/URL: any of `payslip, payslip_link, payslip_path, file, pdf …`
    (or any column that looks like a PDF path/URL)
* **Per-row input**: local path or relative path to a PDF (relative is resolved next to the spreadsheet).
* **Per-row output**: a sibling file named `*_redacted.pdf`.
* **Summary output**: `Payslips_redacted.xlsx` with a `payslip_redacted_link` column made **clickable**.

---

## Quick start

```bash
# Minimal: uses Payslips.xlsx in the current folder
python payslip_universal_redactor.py

# Verbose logging
python payslip_universal_redactor.py --verbose

# Pick a specific sheet
python payslip_universal_redactor.py --input MyRoster.xlsx --sheet "June"

# CSV input
python payslip_universal_redactor.py --input roster.csv

# Custom output filename for the results workbook
python payslip_universal_redactor.py --out MyRedactions.xlsx

# Skip writing the helper notebook
python payslip_universal_redactor.py --no-notebook
```

**Tip:** Relative PDF paths in your spreadsheet are resolved relative to the spreadsheet’s location.

---

## How the redaction pipeline works (high level)

1. **Extract words** from the page; if none are found and Tesseract exists, render and OCR.
2. **Protect names**: find all windows of tokens that fuzzy-match the normalized employee name (≥60%); mark these rectangles as **protected**.
3. **Label→Value masks**: for each label in
   `Address`, `Amount in words`, `Net Pay in INR/USD/CAD`, `DOB`,
   redact only the tokens **to the right on the same line**.
4. **Address blocks**:

   * **Under the name**: define a narrow band directly beneath the name’s union box; collect consecutive address-ish lines (short all-caps, digits, street/unit words) and mask as **one tidy rectangle**.
   * **Bottom-left area**: cluster adjacent lines and mark a cluster as address if it contains strong signals or multiple weak all-caps snippets; redact the cluster union.
5. **Numbers**: redact numeric tokens **except** if they look like **dates** (including ranges, times, “Month 2024”, “20250630”, “2025 06 30”) or match/contain the **emp_id**, or appear near **PAYMENT DATE / PAY END DATE**.
6. **Safety merge** rectangles without crossing any protected name box.
7. **Apply white masks** (with a small padding) and write the redacted PDF.

---

## Requirements

* Python 3.8+
* The script auto-installs these Python packages if missing:
  `pymupdf`, `pandas`, `openpyxl`, `pillow`, `pytesseract`
* **Optional** (for image-only PDFs):
  **Tesseract** CLI on your system `PATH` (`pytesseract` is the Python glue).
  Without it, image-only pages won’t OCR and may not redact correctly.

---

## Exit codes

* `0` – success
* `2` – input reading / validation error (missing file, unsupported type, etc.)
* `3` – failed to write the results workbook

---

## Troubleshooting

* **“PDF not found” in results**
  Ensure the spreadsheet’s PDF paths are correct. Relative paths are resolved next to the spreadsheet file.
* **Name isn’t preserved**
  Make sure the spreadsheet has a name column; the script warns if it can’t detect one. The fuzzy match ignores 1-letter initials; unusual scripts/fonts may need cleaner OCR.
* **Dates got masked**
  Add “Payment Date” or “Pay End Date” labels near the dates in the PDF template if possible; the script already keeps many formats, but context helps.
* **Address fragments still showing**
  The under-name band and bottom-left cluster are broad, but if your template puts address lines far from the name, make sure “Address:” labels exist — the label→value rule will catch them.
* **OCR quality**
  Install Tesseract and ensure PDFs are at least ~300 DPI when rasterized; noisy scans can hurt detection.

---

## Privacy & safety

* Redaction uses **PyMuPDF redaction annotations** with `apply_redactions()`, which **removes content** from the saved PDF (not just hides it).
* Processing is **local**; nothing is sent anywhere.

---

## Extending (if you ever need to)

* Add new labels to `ADDRESS_LABELS`, `AMOUNT_WORDS_LABELS`, etc.
* Adjust street/unit vocab in `STREET_KEYWORDS`, `UNIT_KEYWORDS`.
* Tweak the all-caps heuristic via `RE_SHORT_UPPER`.
* The name-match threshold (currently **0.60**) can be raised/lowered in `name_match_ratio`/`fuzzy_contains_name`.

---

