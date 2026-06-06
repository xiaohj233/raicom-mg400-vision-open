$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue) {
    $Global:PSNativeCommandUseErrorActionPreference = $false
}

$RepoName = "raicom-mg400-vision-open"

function Test-Command($Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-QuietNative {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(Mandatory=$false)][string[]]$Arguments = @()
    )
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $FilePath @Arguments > $null 2> $null
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
}

function Invoke-CheckedNative {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(Mandatory=$false)][string[]]$Arguments = @()
    )
    & $FilePath @Arguments
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        throw "命令执行失败，退出码 ${code}: $FilePath $($Arguments -join ' ')"
    }
}

function Get-NativeText {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(Mandatory=$false)][string[]]$Arguments = @()
    )
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $text = & $FilePath @Arguments 2> $null
        if ($LASTEXITCODE -ne 0) { return $null }
        return $text
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
}

Write-Host "== raicom-mg400-vision-open: release version =="

if (-not (Test-Path "VERSION")) {
    Write-Error "找不到 VERSION 文件。"
    exit 1
}

$Version = (Get-Content "VERSION" -Raw).Trim()
if (-not $Version) {
    Write-Error "VERSION 为空。"
    exit 1
}
$Tag = "v$Version"
$ZipName = "$RepoName-v$Version.zip"
$ZipPath = Join-Path (Get-Location) $ZipName

if (-not (Test-Command git)) {
    Write-Error "未找到 git。请先安装 Git for Windows。"
    exit 1
}

if (-not (Test-Path ".git")) {
    Write-Error "当前目录不是 git 仓库。请先运行一键创建并上传仓库脚本。"
    exit 1
}

$Status = Get-NativeText git @("status", "--porcelain")
if ($Status) {
    Write-Host $Status
    Write-Error "工作区不干净。请先提交或清理变更后再发布。"
    exit 1
}

$TrackedFiles = Get-NativeText git @("ls-files")
$TrackedForbidden = @($TrackedFiles | Where-Object {
    ($_ -match '(^|/)\.venv/') -or
    ($_ -match '(^|/)__pycache__/') -or
    ($_ -match '(^|/)runs/') -or
    ($_ -match '(^|/)dataset/runs/') -or
    (($_ -match '^dataset/images/.+') -and ($_ -ne 'dataset/images/.gitkeep')) -or
    (($_ -match '^dataset/labels/.+') -and ($_ -ne 'dataset/labels/.gitkeep')) -or
    ($_ -match '^models/.+\.(pt|onnx|engine)$') -or
    ($_ -match '^images/.+\.(bmp|jpg|jpeg|png)$') -or
    ($_ -match '\.(iwcal|xml|whl|zip)$') -or
    ($_ -match '(^|/)dist/') -or
    ($_ -match '(^|/)build/')
})
if ($TrackedForbidden.Count -gt 0) {
    Write-Host $TrackedForbidden
    Write-Error "发现不应进入发布包的已跟踪文件。请先移除这些文件。"
    exit 1
}

Write-Host "生成发布 zip: $ZipName"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Invoke-CheckedNative git @("archive", "--format=zip", "--prefix=$RepoName-v$Version/", "--output=$ZipPath", "HEAD")

Write-Host "检查 tag: $Tag"
$tagCode = Invoke-QuietNative git @("rev-parse", "--verify", "$Tag^{tag}")
if ($tagCode -ne 0) {
    Invoke-CheckedNative git @("tag", "-a", $Tag, "-m", "Release $Tag")
} else {
    Write-Host "tag 已存在，跳过创建。"
}

Write-Host "推送 tag..."
Invoke-CheckedNative git @("push", "origin", $Tag)

if (Test-Command gh) {
    Write-Host "检测到 GitHub CLI，检查 GitHub Release..."
    $releaseCode = Invoke-QuietNative gh @("release", "view", $Tag)
    if ($releaseCode -eq 0) {
        Write-Host "Release 已存在，跳过创建。"
    } else {
        Write-Host "创建 GitHub Release..."
        Invoke-CheckedNative gh @("release", "create", $Tag, $ZipPath, "--title", $Tag, "--notes", "Open-source release $Tag")
    }
} else {
    Write-Host "未安装 GitHub CLI；已完成 tag 和 zip。请手动上传 $ZipName 到 GitHub Release。"
}

Write-Host "完成: $ZipPath"
