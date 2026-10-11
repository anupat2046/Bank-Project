# Exports a .pptx to PDF with Microsoft PowerPoint, keeping real (searchable) text.
#   powershell -ExecutionPolicy Bypass -File export_pdf.ps1 <deck.pptx> [out.pdf]
param([Parameter(Mandatory = $true)][string]$Deck, [string]$Pdf)
$Deck = (Resolve-Path $Deck).Path
if (-not $Pdf) { $Pdf = [IO.Path]::ChangeExtension($Deck, ".pdf") }
$Pdf = [IO.Path]::GetFullPath($Pdf)
$app = New-Object -ComObject PowerPoint.Application
try {
    $p = $app.Presentations.Open($Deck, $true, $false, $false)  # read-only, no window
    $p.SaveAs($Pdf, 32)  # ppSaveAsPDF
    $p.Close()
    Write-Output "wrote $Pdf"
} finally {
    $app.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
