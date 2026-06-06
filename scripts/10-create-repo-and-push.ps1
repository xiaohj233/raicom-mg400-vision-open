$ErrorActionPreference = "Stop"
if (Get-Variable PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue) {
    $Global:PSNativeCommandUseErrorActionPreference = $false
}

$RepoName = "raicom-mg400-vision-open"
$GithubUser = "xiaohj233"
$RemoteUrl = "git@github.com:${GithubUser}/${RepoName}.git"
$RepoFullName = "${GithubUser}/${RepoName}"

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

Write-Host "== raicom-mg400-vision-open: create repo and push =="
Write-Host "Repo: $RepoFullName"
Write-Host "Remote: $RemoteUrl"

if (-not (Test-Command git)) {
    Write-Error "未找到 git。请先安装 Git for Windows。"
    exit 1
}

if (-not (Test-Path ".git")) {
    Write-Host "初始化 git 仓库..."
    Invoke-CheckedNative git @("init")
} else {
    Write-Host "当前目录已有 .git，继续使用现有历史。"
}

Invoke-CheckedNative git @("add", "-A")
$Staged = Get-NativeText git @("diff", "--cached", "--name-only")
if ($Staged) {
    Write-Host "创建提交..."
    $commitCode = Invoke-QuietNative git @("commit", "-m", "Initial open-source release")
    if ($commitCode -ne 0) {
        Write-Host "提交失败或没有可提交内容，继续检查仓库状态。"
    }
} else {
    Write-Host "没有需要提交的暂存变更。"
}

Write-Host "切换默认分支为 main..."
Invoke-CheckedNative git @("branch", "-M", "main")

$repoExists = $false
if (Test-Command gh) {
    Write-Host "检测到 GitHub CLI，检查远程仓库..."
    $viewCode = Invoke-QuietNative gh @("repo", "view", $RepoFullName)
    if ($viewCode -eq 0) {
        $repoExists = $true
        Write-Host "GitHub 仓库已存在，跳过创建。"
    } else {
        Write-Host "GitHub 仓库不存在，尝试创建公开仓库..."
        $createCode = Invoke-QuietNative gh @("repo", "create", $RepoFullName, "--public", "--source", ".", "--remote", "origin")
        if ($createCode -eq 0) {
            $repoExists = $true
            Write-Host "GitHub 仓库创建完成。"
        } else {
            Write-Host "GitHub 仓库创建失败。可能原因：未登录 GitHub CLI、无权限、仓库名冲突。"
            Write-Host "请先执行：gh auth login"
            Write-Host "或手动在 GitHub 创建仓库后重新运行本脚本。"
        }
    }
} else {
    Write-Host "请先安装 GitHub CLI，或手动在 GitHub 创建仓库后再运行 push。"
}

$originUrl = Get-NativeText git @("remote", "get-url", "origin")
if ($originUrl) {
    Write-Host "设置 origin 为 SSH remote..."
    Invoke-CheckedNative git @("remote", "set-url", "origin", $RemoteUrl)
} else {
    Write-Host "添加 origin SSH remote..."
    Invoke-CheckedNative git @("remote", "add", "origin", $RemoteUrl)
}

Write-Host "推送 main 分支..."
Invoke-CheckedNative git @("push", "-u", "origin", "main")

Write-Host "完成。"
