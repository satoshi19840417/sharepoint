# SharePoint List Creation Script - Receipt & Issue Records (Phase 7)
# Version: 1.0.0
# Created by: Antigravity

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
$TenantId = "cellgentech.onmicrosoft.com"
$InventoryListName = "在庫管理"
$ReceiptListName = "受入記録"
$IssueListName = "出庫記録"
$PnPClientId = "b84ae22e-26aa-4058-bd13-e61eb398a67d"

# --- MAIN CONNECTION LOGIC ---
Clear-Host
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "SharePoint List Creation - Receipt & Issue Records" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------"
Write-Host ""

# --- MAIN CONNECTION LOGIC ---
Clear-Host
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "SharePoint List Creation - Receipt & Issue Records" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------"
Write-Host ""

Write-Host "Connecting to SharePoint..." -ForegroundColor Cyan
Write-Host "Please follow the instructions below to log in." -ForegroundColor White
Write-Host ""

try {
    # Using Device Login with the registered Azure AD App
    Write-Host "1. Open https://microsoft.com/devicelogin in your browser" -ForegroundColor Yellow
    Write-Host "2. Enter the code that will appear below" -ForegroundColor Yellow
    Write-Host "3. Log in with your Microsoft 365 account" -ForegroundColor Yellow
    Write-Host ""
    
    Connect-PnPOnline -Url $SiteUrl -DeviceLogin -ClientId $PnPClientId -Tenant $TenantId -ErrorAction Stop
    Write-Host "Connected successfully!" -ForegroundColor Green
}
catch {
    Write-Error "Login failed."
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit
}

Write-Host ""
Write-Host "Connected successfully!" -ForegroundColor Green

# --- VERIFY INVENTORY LIST EXISTS ---
Write-Host ""
Write-Host "Verifying '在庫管理' list exists..." -ForegroundColor Cyan
$InventoryList = Get-PnPList -Identity $InventoryListName -ErrorAction SilentlyContinue

if (-not $InventoryList) {
    Write-Error "ERROR: '在庫管理' list not found. Please create it first (Phase 6)."
    Read-Host "Press Enter to exit..."
    exit
}
Write-Host "✓ '在庫管理' list found." -ForegroundColor Green

# --- CREATE RECEIPT LIST ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating '受入記録' list..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$ReceiptList = Get-PnPList -Identity $ReceiptListName -ErrorAction SilentlyContinue

if ($ReceiptList) {
    Write-Warning "List '$ReceiptListName' already exists. Skipping creation."
}
else {
    Write-Host "Creating list '$ReceiptListName'..." -ForegroundColor Yellow
    $ReceiptList = New-PnPList -Title $ReceiptListName -Template GenericList -Url "ReceiptRecords"
    Write-Host "✓ List created." -ForegroundColor Green
}

# --- ADD FIELDS TO RECEIPT LIST ---
Write-Host ""
Write-Host "Adding columns to '受入記録' list..." -ForegroundColor Cyan

# Helper functions
function Add-TextField ($ListName, $InternalName, $DisplayName, $Required = $false) {
    Write-Host "  • $DisplayName ($InternalName)" -ForegroundColor Gray
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type Text -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required = $true } | Out-Null
    }
}

function Add-NumberField ($ListName, $InternalName, $DisplayName, $Required = $false) {
    Write-Host "  • $DisplayName ($InternalName)" -ForegroundColor Gray
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type Number -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required = $true } | Out-Null
    }
}

function Add-DateField ($ListName, $InternalName, $DisplayName, $Required = $false) {
    Write-Host "  • $DisplayName ($InternalName)" -ForegroundColor Gray
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type DateTime -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    Set-PnPField -List $ListName -Identity $InternalName -Values @{Format = "DateOnly" } | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required = $true } | Out-Null
    }
}

function Add-UserField ($ListName, $InternalName, $DisplayName, $Required = $false) {
    Write-Host "  • $DisplayName ($InternalName)" -ForegroundColor Gray
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type User -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required = $true } | Out-Null
    }
}

# Configure Title field
Write-Host "  • 品名 (Title)" -ForegroundColor Gray
Set-PnPField -List $ReceiptListName -Identity "Title" -Values @{Title = "品名"; Required = $true } | Out-Null

# Receipt Date
Add-DateField -ListName $ReceiptListName -InternalName "ReceiveDate" -DisplayName "受入日" -Required $true

# Lookup to Inventory List
Write-Host "  • 在庫品目 (InventoryItem) - Lookup" -ForegroundColor Gray
$LookupFieldXml = "<Field Type='Lookup' DisplayName='在庫品目' Name='InventoryItem' StaticName='InventoryItem' List='$($InventoryList.Id)' ShowField='Title' Required='TRUE' />"
Add-PnPFieldFromXml -List $ReceiptListName -FieldXml $LookupFieldXml -ErrorAction SilentlyContinue | Out-Null

# Other text fields
Add-TextField -ListName $ReceiptListName -InternalName "Maker" -DisplayName "メーカー" -Required $true
Add-TextField -ListName $ReceiptListName -InternalName "LotNumber" -DisplayName "ロット番号" -Required $true

# Quantity
Add-NumberField -ListName $ReceiptListName -InternalName "Quantity" -DisplayName "数量" -Required $true

# Expiry Date
Add-DateField -ListName $ReceiptListName -InternalName "ExpiryDate" -DisplayName "使用期限"

# Inspection Result (Choice)
Write-Host "  • 検査結果 (InspectionResult) - Choice" -ForegroundColor Gray
$InspectionChoiceXml = "<Field Type='Choice' DisplayName='検査結果' Name='InspectionResult' StaticName='InspectionResult' Required='TRUE'><CHOICES><CHOICE>合格</CHOICE><CHOICE>不合格</CHOICE><CHOICE>保留</CHOICE></CHOICES><Default>合格</Default></Field>"
Add-PnPFieldFromXml -List $ReceiptListName -FieldXml $InspectionChoiceXml -ErrorAction SilentlyContinue | Out-Null

# Person
Add-UserField -ListName $ReceiptListName -InternalName "Person" -DisplayName "担当者" -Required $true

# Notes
Write-Host "  • 備考 (Notes)" -ForegroundColor Gray
Add-PnPField -List $ReceiptListName -DisplayName "備考" -InternalName "Notes" -Type Note -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null

Write-Host "✓ All columns added to '受入記録' list." -ForegroundColor Green

# --- CREATE ISSUE LIST ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Creating '出庫記録' list..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$IssueList = Get-PnPList -Identity $IssueListName -ErrorAction SilentlyContinue

if ($IssueList) {
    Write-Warning "List '$IssueListName' already exists. Skipping creation."
}
else {
    Write-Host "Creating list '$IssueListName'..." -ForegroundColor Yellow
    $IssueList = New-PnPList -Title $IssueListName -Template GenericList -Url "IssueRecords"
    Write-Host "✓ List created." -ForegroundColor Green
}

# --- ADD FIELDS TO ISSUE LIST ---
Write-Host ""
Write-Host "Adding columns to '出庫記録' list..." -ForegroundColor Cyan

# Configure Title field
Write-Host "  • 品名 (Title)" -ForegroundColor Gray
Set-PnPField -List $IssueListName -Identity "Title" -Values @{Title = "品名"; Required = $true } | Out-Null

# Issue Date
Add-DateField -ListName $IssueListName -InternalName "IssueDate" -DisplayName "出庫日" -Required $true

# Lookup to Inventory List
Write-Host "  • 在庫品目 (InventoryItem) - Lookup" -ForegroundColor Gray
$LookupFieldXml2 = "<Field Type='Lookup' DisplayName='在庫品目' Name='InventoryItem' StaticName='InventoryItem' List='$($InventoryList.Id)' ShowField='Title' Required='TRUE' />"
Add-PnPFieldFromXml -List $IssueListName -FieldXml $LookupFieldXml2 -ErrorAction SilentlyContinue | Out-Null

# Lot Number
Add-TextField -ListName $IssueListName -InternalName "LotNumber" -DisplayName "ロット番号" -Required $true

# Quantity
Add-NumberField -ListName $IssueListName -InternalName "Quantity" -DisplayName "数量" -Required $true

# Purpose (Choice)
Write-Host "  • 用途 (Purpose) - Choice" -ForegroundColor Gray
$PurposeChoiceXml = "<Field Type='Choice' DisplayName='用途' Name='Purpose' StaticName='Purpose' Required='TRUE'><CHOICES><CHOICE>製造</CHOICE><CHOICE>試験</CHOICE><CHOICE>検査</CHOICE><CHOICE>研究開発</CHOICE><CHOICE>サンプル提供</CHOICE><CHOICE>廃棄</CHOICE><CHOICE>その他</CHOICE></CHOICES></Field>"
Add-PnPFieldFromXml -List $IssueListName -FieldXml $PurposeChoiceXml -ErrorAction SilentlyContinue | Out-Null

# User
Add-UserField -ListName $IssueListName -InternalName "User" -DisplayName "使用者" -Required $true

# Test Number
Add-TextField -ListName $IssueListName -InternalName "TestNumber" -DisplayName "試験番号"

# Notes
Write-Host "  • 備考 (Notes)" -ForegroundColor Gray
Add-PnPField -List $IssueListName -DisplayName "備考" -InternalName "Notes" -Type Note -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null

Write-Host "✓ All columns added to '出庫記録' list." -ForegroundColor Green

# --- COMPLETION ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ ALL DONE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Created lists:" -ForegroundColor White
Write-Host "  1. 受入記録 (Receipt Records)" -ForegroundColor Cyan
Write-Host "  2. 出庫記録 (Issue Records)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Please check your SharePoint site:" -ForegroundColor White
Write-Host "  $SiteUrl" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Enter to finish..."
Read-Host
