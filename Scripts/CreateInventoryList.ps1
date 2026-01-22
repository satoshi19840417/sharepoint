# SharePoint List Creation Script - Inventory Management
# Version: 1.0.0
# Created by: Antigravity

# --- CONFIGURATION ---
$ListName = "在庫管理"
$ListUrl = "InventoryManagement" # URL suffix
$Template = "GenericList"

# --- CONNECT ---
Write-Host "Connecting to SharePoint Online..." -ForegroundColor Cyan
$SiteUrl = Read-Host "Please enter your SharePoint Site URL (e.g., https://yourtenant.sharepoint.com/sites/yoursite)"

try {
    Connect-PnPOnline -Url $SiteUrl -Interactive
    Write-Host "Connected successfully!" -ForegroundColor Green
}
catch {
    Write-Error "Failed to connect to SharePoint. Please check your URL and credentials."
    exit
}

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
function Add-TextField ($InternalName, $DisplayName, $Required=$false) {
    Write-Host "Processing field: $DisplayName ($InternalName)"
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type Text -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required=$true} | Out-Null
    }
}

# Helper function to add number field
function Add-NumberField ($InternalName, $DisplayName, $Required=$false) {
    Write-Host "Processing field: $DisplayName ($InternalName)"
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type Number -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    if ($Required) {
        Set-PnPField -List $ListName -Identity $InternalName -Values @{Required=$true} | Out-Null
    }
}

# Helper function to add date field
function Add-DateField ($InternalName, $DisplayName) {
    Write-Host "Processing field: $DisplayName ($InternalName)"
    Add-PnPField -List $ListName -DisplayName $DisplayName -InternalName $InternalName -Type DateTime -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
    Set-PnPField -List $ListName -Identity $InternalName -Values @{Format="DateOnly"} | Out-Null
}

# 1. Title (Default field, just rename/configure)
Write-Host "Configuring 'Title' field..."
Set-PnPField -List $ListName -Identity "Title" -Values @{Title="品名"; Required=$true} | Out-Null

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

# 4. Calculated Field: InventoryValue
Write-Host "Processing field: 在庫金額 (InventoryValue)"
# Note: Formula uses Internal Names.
$Formula = "=[UnitPrice]*[CurrentStock]"
Add-PnPField -List $ListName -DisplayName "在庫金額" -InternalName "InventoryValue" -Type Calculated -Formula $Formula -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
Set-PnPField -List $ListName -Identity "InventoryValue" -Values @{OutputType="Currency"} | Out-Null

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
$LocationChoices = @("204", "101", "未来", "7F", "動物舎")
Add-PnPField -List $ListName -DisplayName "保管場所" -InternalName "StorageLocation" -Type Choice -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null
Set-PnPField -List $ListName -Identity "StorageLocation" -Values @{FillInChoice=$true; Choices=$LocationChoices} | Out-Null
# Set Multi-Select via XML update if needed, but standard Set-PnPField might not handle Multi flag easily for existing fields without explicit type param during creation or XML schema update.
# For simplicity in PnP, we often recreate or use Add-PnPField -Type MultiChoice if supported, or use XML.
# Let's try creating as MultiChoice directly if possible, otherwise we update schema.
# PnP PowerShell 'MultiChoice' type support validation:
# Re-adding as specific schema XML is safer for Multi-Choice.
$LocationFieldXml = "<Field Type='MultiChoice' DisplayName='保管場所' Name='StorageLocation' StaticName='StorageLocation' Group='Custom Columns' FillInChoice='TRUE'><CHOICES><CHOICE>204</CHOICE><CHOICE>101</CHOICE><CHOICE>未来</CHOICE><CHOICE>7F</CHOICE><CHOICE>動物舎</CHOICE></CHOICES></Field>"
Add-PnPFieldFromXml -List $ListName -FieldXml $LocationFieldXml -ErrorAction SilentlyContinue | Out-Null


Write-Host "Processing field: 保管温度 (StorageTemperature)"
$TempFieldXml = "<Field Type='MultiChoice' DisplayName='保管温度' Name='StorageTemperature' StaticName='StorageTemperature' Group='Custom Columns' FillInChoice='TRUE'><CHOICES><CHOICE>常温</CHOICE><CHOICE>4℃</CHOICE><CHOICE>-30℃</CHOICE><CHOICE>-80℃</CHOICE></CHOICES></Field>"
Add-PnPFieldFromXml -List $ListName -FieldXml $TempFieldXml -ErrorAction SilentlyContinue | Out-Null


# 8. Note Field
Write-Host "Processing field: 備考 (Notes)"
Add-PnPField -List $ListName -DisplayName "備考" -InternalName "Notes" -Type Note -AddToDefaultView -ErrorAction SilentlyContinue | Out-Null


Write-Host "All done! Please check the list '$ListName' in your SharePoint site." -ForegroundColor Green
