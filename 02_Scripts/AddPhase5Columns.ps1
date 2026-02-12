# SharePoint Phase 5 Column Addition Script
# Version: 1.0.0
# Purpose: Add sending flow columns to 発注依頼_Requests_Test list
# Reference: 01_Documents/01_Phases/Phase5_送付フロー/Phase5_送付フロー計画書.md

$ErrorActionPreference = "Stop"

# --- CHECK PRE-REQUISITES ---
Write-Host "Checking for PnP.PowerShell module..." -ForegroundColor Gray
if (-not (Get-Module -ListAvailable -Name PnP.PowerShell)) {
    Write-Warning "PnP.PowerShell module not found. Attempting to install..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser -ErrorAction SilentlyContinue
        Install-Module -Name PnP.PowerShell -Scope CurrentUser -Force -AllowClobber -SkipPublisherCheck
        Write-Host "Module installed successfully." -ForegroundColor Green
    }
    catch {
        Write-Error "Failed to auto-install PnP.PowerShell."
        Write-Error $_.Exception.Message
        Write-Host "Please try running this command in PowerShell manually: Install-Module PnP.PowerShell -Scope CurrentUser" -ForegroundColor Yellow
        Read-Host "Press Enter to exit..."
        exit
    }
}

# Import the module explicitly
Write-Host "Importing PnP.PowerShell module..." -ForegroundColor Gray
Import-Module PnP.PowerShell -ErrorAction Stop


# --- CONFIGURATION ---
$SiteUrl = "https://cellgentech.sharepoint.com/sites/SP__Prototype"
$ListName = "発注依頼_Requests_Test"
$PnPClientId = "31359c7f-bd7e-475c-86db-fdb8c937548e"

# --- FUNCTION: TRY CONNECT ---
function Try-Connect {
    param($Method, $UseClientId = $false)

    Write-Host "Attempting login via [$Method]... " -NoNewline -ForegroundColor Yellow
    try {
        if ($Method -eq "Interactive") {
            Connect-PnPOnline -Url $SiteUrl -Interactive -ErrorAction Stop
        }
        elseif ($Method -eq "DeviceLogin_Default") {
            Write-Host "`n   (Look for code below)" -ForegroundColor Gray
            Connect-PnPOnline -Url $SiteUrl -DeviceLogin -ErrorAction Stop
        }
        elseif ($Method -eq "DeviceLogin_PnP") {
            Write-Host "`n   (Look for code below)" -ForegroundColor Gray
            Connect-PnPOnline -Url $SiteUrl -DeviceLogin -ClientId $PnPClientId -ErrorAction Stop
        }
        return $true
    }
    catch {
        Write-Host "FAILED" -ForegroundColor Red
        return $false
    }
}

# --- MAIN CONNECTION LOGIC ---
Clear-Host
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Phase 5: Add Sending Flow Columns" -ForegroundColor Cyan
Write-Host "Target: $ListName" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------"
Write-Host ""

$Connected = $false

# 1. Try Interactive (Best for external windows)
if (-not $Connected) {
    if (Try-Connect "Interactive") { $Connected = $true }
}

# 2. Try DeviceLogin (Default App)
if (-not $Connected) {
    Write-Host ""
    Write-Host "Falling back to Device Login..." -ForegroundColor Cyan
    Write-Host "To login: Open https://microsoft.com/devicelogin and enter the code shown below." -ForegroundColor White
    if (Try-Connect "DeviceLogin_Default") { $Connected = $true }
}

# 3. Try DeviceLogin (PnP App)
if (-not $Connected) {
    Write-Host ""
    Write-Host "Falling back to Device Login (PnP ID)..." -ForegroundColor Cyan
    Write-Host "To login: Open https://microsoft.com/devicelogin and enter the code shown below." -ForegroundColor White
    if (Try-Connect "DeviceLogin_PnP") { $Connected = $true }
}

if (-not $Connected) {
    Write-Error "All login methods failed. Aborting."
    Read-Host "Press Enter to exit..."
    exit
}

Write-Host ""
Write-Host "Connected successfully!" -ForegroundColor Green

# --- VERIFY LIST EXISTS ---
$List = Get-PnPList -Identity $ListName -ErrorAction SilentlyContinue

if (-not $List) {
    Write-Error "List '$ListName' not found. Aborting."
    Read-Host "Press Enter to exit..."
    exit
}

Write-Host "List '$ListName' found (ID: $($List.Id))." -ForegroundColor Green
Write-Host ""

# --- HELPER FUNCTIONS ---
function Add-TextField ($InternalName, $DisplayName, $Required = $false) {
    Write-Host "Processing field: $DisplayName ($InternalName)"
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type Text -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required = $true } | Out-Null
    }
}

function Add-NumberField ($InternalName, $DisplayName, $Required = $false) {
    Write-Host "Processing field: $DisplayName ($InternalName)"
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type Number -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required = $true } | Out-Null
    }
}

# --- ADD PHASE 5 COLUMNS ---
Write-Host "Adding Phase 5 columns..." -ForegroundColor Cyan
Write-Host ""

# 1. OrderID (発注ID) - Text, Required - Grouping key
Add-TextField -InternalName "OrderID" -DisplayName "発注ID" -Required $true

# 2. DeliveryAddress (納品先) - Text
Add-TextField -InternalName "DeliveryAddress" -DisplayName "納品先"

# 3. VendorID (業者ID) - Text
Add-TextField -InternalName "VendorID" -DisplayName "業者ID"

# 4. QuoteNumber (見積書番号) - Text
Add-TextField -InternalName "QuoteNumber" -DisplayName "見積書番号"

# 5. SortOrder (表示順) - Number
Add-NumberField -InternalName "SortOrder" -DisplayName "表示順"

# 6. SendStatus (送付ステータス) - Choice
Write-Host "Checking for existing SendStatus field..."
$ExistingSendStatus = Get-PnPField -List $ListName -Identity "SendStatus" -ErrorAction SilentlyContinue
if ($ExistingSendStatus) {
    Write-Warning "SendStatus already exists (Type: $($ExistingSendStatus.TypeAsString)). Skipping creation."
} else {
    Write-Host "Processing field: 送付ステータス (SendStatus)"
    $SendStatusXml = "<Field Type='Choice' DisplayName='送付ステータス' Name='SendStatus' StaticName='SendStatus' Group='Phase5'><Default>未送付</Default><CHOICES><CHOICE>未送付</CHOICE><CHOICE>送付中</CHOICE><CHOICE>送付済</CHOICE><CHOICE>エラー</CHOICE></CHOICES></Field>"
    Add-PnPFieldFromXml -List $ListName -FieldXml $SendStatusXml -ErrorAction SilentlyContinue | Out-Null
}

# 7. ErrorLog (エラーログ) - Note (multiline text)
Write-Host "Processing field: エラーログ (ErrorLog)"
Add-PnPField -List $ListName -DisplayName "エラーログ" -InternalName "ErrorLog" -Type Note -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null

# --- VERIFICATION ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Verifying all Phase 5 columns..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$RequiredFields = @("OrderID", "DeliveryAddress", "VendorID", "QuoteNumber", "SortOrder", "SendStatus", "ErrorLog")
$AllGood = $true

foreach ($FieldName in $RequiredFields) {
    $F = Get-PnPField -List $ListName -Identity $FieldName -ErrorAction SilentlyContinue
    if ($F) {
        Write-Host "  [OK] $FieldName ($($F.Title)) - $($F.TypeAsString)" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $FieldName" -ForegroundColor Red
        $AllGood = $false
    }
}

Write-Host ""
if ($AllGood) {
    Write-Host "All Phase 5 columns verified successfully!" -ForegroundColor Green
} else {
    Write-Warning "Some columns are missing. Please check the errors above."
}

Write-Host ""
Write-Host "Press Enter to finish..."
Read-Host
