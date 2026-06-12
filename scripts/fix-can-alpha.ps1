# Remove light checkerboard squares only (ChatGPT fake transparency).
Add-Type -AssemblyName System.Drawing

$path = (Resolve-Path (Join-Path $PSScriptRoot "..\brand\product\pep-can.png")).Path
$src = [System.Drawing.Bitmap]::FromFile($path)
$pf = [System.Drawing.Imaging.PixelFormat]::Format32bppArgb
$img = New-Object System.Drawing.Bitmap($src.Width, $src.Height, $pf)
$g = [System.Drawing.Graphics]::FromImage($img)
$g.Clear([System.Drawing.Color]::Transparent)
$g.DrawImage($src, 0, 0, $src.Width, $src.Height)
$g.Dispose()
$src.Dispose()

function Test-LightCheckerboard([int]$r, [int]$g, [int]$b) {
  $max = [Math]::Max($r, [Math]::Max($g, $b))
  $min = [Math]::Min($r, [Math]::Min($g, $b))
  if (($max - $min) -gt 22) { return $false }
  return $max -ge 168
}

$rect = New-Object System.Drawing.Rectangle 0, 0, $img.Width, $img.Height
$data = $img.LockBits($rect, [System.Drawing.Imaging.ImageLockMode]::ReadWrite, $pf)
$bytes = $img.Width * $img.Height * 4
$buffer = New-Object byte[] $bytes
[System.Runtime.InteropServices.Marshal]::Copy($data.Scan0, $buffer, 0, $bytes)
$removed = 0

for ($i = 0; $i -lt $bytes; $i += 4) {
  $b = $buffer[$i]; $g = $buffer[$i + 1]; $r = $buffer[$i + 2]
  if (Test-LightCheckerboard $r $g $b) {
    $buffer[$i] = 0; $buffer[$i + 1] = 0; $buffer[$i + 2] = 0; $buffer[$i + 3] = 0
    $removed++
  }
}

[System.Runtime.InteropServices.Marshal]::Copy($buffer, 0, $data.Scan0, $bytes)
$img.UnlockBits($data)
$img.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
$img.Dispose()
Write-Host "Removed $removed light checkerboard pixels"
