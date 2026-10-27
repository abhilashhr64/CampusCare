# CampusCare AI - 1-Click Native Android APK Builder
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       Building CampusCare AI Android APK Package         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot
$FrontendDir = "$WorkspaceRoot\frontend"
$AndroidDir = "$FrontendDir\android"
$JavaHome = "C:\Users\madha\.jdks\jbr-21.0.11"
$AndroidHome = "C:\Users\madha\AppData\Local\Android\Sdk"

# 1. Build Static Mobile Assets
Write-Host "`n[1/4] Generating Next.js Static Mobile Bundle..." -ForegroundColor Yellow
Push-Location $FrontendDir
$env:BUILD_TARGET = "mobile"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build Next.js mobile bundle!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# 2. Sync Web Assets with Capacitor
Write-Host "`n[2/4] Syncing Assets into Native Android Container..." -ForegroundColor Yellow
npx cap sync android
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to sync Capacitor assets!" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

# 3. Assemble Android APK via Gradle
Write-Host "`n[3/4] Compiling Native Android APK with Gradle (Java 21)..." -ForegroundColor Yellow
Push-Location $AndroidDir
$env:JAVA_HOME = $JavaHome
$env:ANDROID_HOME = $AndroidHome
$env:PATH = "$JavaHome\bin;$env:PATH"

.\gradlew.bat assembleDebug
if ($LASTEXITCODE -ne 0) {
    Write-Host "Gradle build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}
Pop-Location

# 4. Copy to Root
$SourceApk = "$AndroidDir\app\build\outputs\apk\debug\app-debug.apk"
$DestApk = "$WorkspaceRoot\CampusCare-AI.apk"
Copy-Item $SourceApk -Destination $DestApk -Force

$ApkInfo = Get-Item $DestApk
$SizeMB = [math]::Round($ApkInfo.Length / 1MB, 2)

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "       CampusCare AI Android APK Built Successfully!      " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host " - APK Path : $DestApk" -ForegroundColor White
Write-Host " - Size     : $SizeMB MB ($($ApkInfo.Length) bytes)" -ForegroundColor White
Write-Host " - Target   : Android 7.0 (API 24) to Android 16 (API 36)" -ForegroundColor White
Write-Host "==========================================================`n" -ForegroundColor Green
