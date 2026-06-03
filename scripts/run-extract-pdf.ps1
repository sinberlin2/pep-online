# Extract brands from competition PDF → characteristics.csv
# Run in PowerShell after: conda activate pep-online

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$pdf = Get-ChildItem -Path "brand\research\*.pdf" | Select-Object -First 1
if (-not $pdf) {
    Write-Error "No PDF in brand\research\. Add Drink_....pdf or competition-table.pdf"
}

Write-Host "Using PDF: $($pdf.Name)"
pip install -q pymupdf openai python-dotenv
python scripts/extract_competition_pdf.py --pdf $pdf.FullName --max-pages 3

Write-Host ""
Write-Host "Next:"
Write-Host "  python scripts/merge_brand_research.py"
Write-Host "  python -m agents.brand_run --positioning 2"
