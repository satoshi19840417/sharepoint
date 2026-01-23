# SharePoint List Creation Script - Inventory Management
# Version: 1.1.2 (Module Auto-Install Restored)
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
$ListName = "在庫管理"
$ListUrl = "InventoryManagement"
$Template = "GenericList"
$PnPClientId = "31359c7f-bd7e-475c-86db-fdb8c937548e"

# --- FUNCTION: TRY CONNECT ---
function Try-Connect {
    param($Method, $UseClientId = $false)
    
    Write-Host "Attempting login via [$Method]... " -NoNewline -ForegroundColor Yellow
    try {
        if ($Method -eq "Interactive") {
            # Try Interactive first - works best in external windows
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
        # Write-Warning "Login failed via $Method"
        # Write-Host $_.Exception.Message -ForegroundColor Red
        return $false
    }
}

# --- MAIN CONNECTION LOGIC ---
Clear-Host
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "SharePoint List Creation - Login" -ForegroundColor Cyan
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

# --- CREATE LIST ---
$List = Get-PnPList -Identity $ListName -ErrorAction SilentlyContinue

if ($List) {
    Write-Warning "List '$ListName' already exists. Skipping creation."
}
else {
    Write-Host "Creating list '$ListName'..." -ForegroundColor Cyan
    $List = New-PnPList -Title $ListName -Template $Template -Url $ListUrl
    Write-Host "List created." -ForegroundColor Green
}

# --- ADD FIELDS ---
Write-Host "Adding/Updating columns..." -ForegroundColor Cyan

# Helper function to add text field
function Add-TextField ($InternalName, $DisplayName, $Required = $false) {
    Write-Host "Processing field: $DisplayName ($InternalName)"
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type Text -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required = $true } | Out-Null
    }
}

# Helper function to add number field
function Add-NumberField ($InternalName, $DisplayName, $Required = $false) {
    Write-Host "Processing field: $DisplayName ($InternalName)"
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type Number -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required = $true } | Out-Null
    }
}

# Helper function to add date field
function Add-DateField ($InternalName, $DisplayName) {
    Write-Host "Processing field: $DisplayName ($InternalName)"
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type DateTime -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    Set-PnPField -List $ListName -Identity $InternalName -Values @{Format = "DateOnly" } | Out-Null
}

# 1. Title
Write-Host "Configuring 'Title' field..."
Set-PnPField -List $ListName -Identity "Title" -Values @{Title = "品名"; Required = $true } | Out-Null

# 2. Text Fields
Add-TextField -InternalName "Maker" -DisplayName "メーカー" -Required $true
Add-TextField -InternalName "MakerCode" -DisplayName "メーカーコード" -Required $true
Add-TextField -InternalName "BranchNumber" -DisplayName "枝番"
Add-TextField -InternalName "PackageType" -DisplayName "包装形状"
Add-TextField -InternalName "Vendor" -DisplayName "発注業者"
Add-TextField -InternalName "SourceOrderID" -DisplayName "発注ID"
Add-TextField -InternalName "Barcode" -DisplayName "バーコード"
Add-TextField -InternalName "LotNumber" -DisplayName "ロット番号"

# 3. Number/Currency Fields
Add-NumberField -InternalName "UnitsPerBox" -DisplayName "入数/箱"
Add-NumberField -InternalName "CurrentStock" -DisplayName "現在在庫数" -Required $true
Add-NumberField -InternalName "SafetyStock" -DisplayName "安全在庫数"

Write-Host "Processing field: 単価 (UnitPrice)"
Add-PnPField -List $ListName -DisplayName "単価" -InternalName "UnitPrice" -Type Currency -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null

# 4. Calculated Field
Write-Host "Processing field: 在庫金額 (InventoryValue)"
$Formula = "=[UnitPrice]*[CurrentStock]"
Add-PnPField -List $ListName -DisplayName "在庫金額" -InternalName "InventoryValue" -Type Calculated -Formula $Formula -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
Set-PnPField -List $ListName -Identity "InventoryValue" -Values @{OutputType = "Currency" } | Out-Null

# 5. User Field
Write-Host "Processing field: 発注者 (Orderer)"
Add-PnPField -List $ListName -DisplayName "発注者" -InternalName "Orderer" -Type User -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null

# 6. Date Fields
Add-DateField -InternalName "ExpiryDate" -DisplayName "使用期限"
Add-DateField -InternalName "DeliveryDate" -DisplayName "納品日"
Add-DateField -InternalName "InspectionDate" -DisplayName "受入検査日"
Add-DateField -InternalName "COA_Date" -DisplayName "COA入手日"

# 7. Choice Fields (Multi)
Write-Host "Processing field: 保管場所 (StorageLocation)"
$LocationFieldXml = "<Field Type='MultiChoice' DisplayName='保管場所' Name='StorageLocation' StaticName='StorageLocation' Group='Custom Columns' FillInChoice='TRUE'><CHOICES><CHOICE>204</CHOICE><CHOICE>101</CHOICE><CHOICE>未来</CHOICE><CHOICE>7F</CHOICE><CHOICE>動物舎</CHOICE></CHOICES></Field>"
Add-PnPFieldFromXml -List $ListName -FieldXml $LocationFieldXml -ErrorAction SilentlyContinue | Out-Null

Write-Host "Processing field: 保管温度 (StorageTemperature)"
$TempFieldXml = "<Field Type='MultiChoice' DisplayName='保管温度' Name='StorageTemperature' StaticName='StorageTemperature' Group='Custom Columns' FillInChoice='TRUE'><CHOICES><CHOICE>常温</CHOICE><CHOICE>4℃</CHOICE><CHOICE>-30℃</CHOICE><CHOICE>-80℃</CHOICE></CHOICES></Field>"
Add-PnPFieldFromXml -List $ListName -FieldXml $TempFieldXml -ErrorAction SilentlyContinue | Out-Null

# 8. Note Field
Write-Host "Processing field: 備考 (Notes)"
Add-PnPField -List $ListName -DisplayName "備考" -InternalName "Notes" -Type Note -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null

Write-Host ""
Write-Host "All done! Please check the list '$ListName' in your SharePoint site." -ForegroundColor Green
Write-Host "Press Enter to finish..."
Read-Host
