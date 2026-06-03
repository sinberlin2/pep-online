Add-Type -AssemblyName System.Drawing

# Prefer poster in brand/marketing/; outputs go to brand/product/
$srcPath = Join-Path $PSScriptRoot "..\brand\marketing\pep-hero.png"
if (-not (Test-Path $srcPath)) {
  $srcPath = Join-Path $PSScriptRoot "..\images\pep-hero.png"
}
$srcPath = (Resolve-Path $srcPath).Path
$outDir = Join-Path $PSScriptRoot "..\brand\product"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outDir = (Resolve-Path $outDir).Path
$src = [System.Drawing.Bitmap]::FromFile($srcPath)
$pf = [System.Drawing.Imaging.PixelFormat]::Format32bppArgb

function Test-Cream([System.Drawing.Color]$c, [int]$tol = 40) {
  if ($c.A -lt 10) { return $true }
  if ($c.R -gt 228 -and $c.G -gt 210 -and $c.B -gt 188 -and ($c.R - $c.B) -lt 45) { return $true }
  return $false
}

function Export-Cutout($bitmap, $rect, $outName) {
  $crop = $bitmap.Clone($rect, $pf)
  $w = $rect.Width
  $h = $rect.Height
  $out = New-Object System.Drawing.Bitmap($w, $h, $pf)

  $srcData = $crop.LockBits(
    (New-Object System.Drawing.Rectangle 0, 0, $w, $h),
    [System.Drawing.Imaging.ImageLockMode]::ReadOnly,
    $pf
  )
  $dstData = $out.LockBits(
    (New-Object System.Drawing.Rectangle 0, 0, $w, $h),
    [System.Drawing.Imaging.ImageLockMode]::WriteOnly,
    $pf
  )

  $bytes = $w * $h * 4
  $buffer = New-Object byte[] $bytes
  [System.Runtime.InteropServices.Marshal]::Copy($srcData.Scan0, $buffer, 0, $bytes)

  for ($i = 0; $i -lt $bytes; $i += 4) {
    $b = $buffer[$i]
    $g = $buffer[$i + 1]
    $r = $buffer[$i + 2]
    $a = $buffer[$i + 3]
    $c = [System.Drawing.Color]::FromArgb($a, $r, $g, $b)
    if (Test-Cream $c) {
      $buffer[$i + 3] = 0
    }
  }

  [System.Runtime.InteropServices.Marshal]::Copy($buffer, 0, $dstData.Scan0, $bytes)
  $crop.UnlockBits($srcData)
  $out.UnlockBits($dstData)
  $crop.Dispose()

  $path = Join-Path $outDir $outName
  $out.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  $out.Dispose()
  Write-Host "Wrote $outName (${w}x${h})"
}

Export-Cutout $src ([System.Drawing.Rectangle]::new(218, 298, 215, 495)) "pep-can.png"
Export-Cutout $src ([System.Drawing.Rectangle]::new(438, 318, 175, 445)) "pep-glass.png"
Export-Cutout $src ([System.Drawing.Rectangle]::new(248, 718, 200, 115)) "pep-mango.png"

$src.Dispose()
Write-Host "Done."
