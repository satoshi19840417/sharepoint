
import os
import copy
import math
import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from datetime import datetime
import openpyxl
from openpyxl.utils import range_boundaries

# --- Configuration ---
base_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.abspath(os.path.join(base_dir, "../../02_Templates"))
word_template_path = os.path.join(templates_dir, "発注書テンプレート.docx")
excel_template_path = os.path.join(templates_dir, "請書テンプレート.xlsx")
output_dir = os.path.join(base_dir, "TestOutput")
word_output_path = os.path.join(output_dir, "発注書_検証用_MultiItem.docx")
excel_output_path = os.path.join(output_dir, "請書_検証用_MultiItem.xlsx")

# --- Dummy Data ---
DUMMY_DATA = {
    "Title": "検体解析業務委託",
    "OrderID": "PO-20260204-001",
    "Date": datetime.now().strftime("%Y/%m/%d"),
    "VendorName": "テストサプライヤー株式会社",
    "VendorAddress": "東京都港区芝浦3-1-1", # Assuming mapping
    "DeliveryDate": "2026/03/31",
    "DeliveryAddress": "千葉県千葉市中央区亥鼻1-8-15\n千葉大亥鼻イノベーションプラザ208",
    "RequestorName": "千賀 聡志", # For <<Orderer>>
    # Totals will be calculated
}

ITEMS = [
    {"ItemName": "DNA抽出キット", "Quantity": 2, "Unit": "箱", "UnitPrice": 50000},
    {"ItemName": "NGS解析サービス", "Quantity": 1, "Unit": "式", "UnitPrice": 900000},
    {"ItemName": "サンプル輸送費", "Quantity": 1, "Unit": "回", "UnitPrice": 15000},
    # Add more to test paging
    {"ItemName": "試薬A", "Quantity": 5, "Unit": "本", "UnitPrice": 2000},
    {"ItemName": "試薬B", "Quantity": 10, "Unit": "本", "UnitPrice": 1500},
]

# --- Helper Functions (Word) ---

def set_sdt_text(sdt, text):
    content = sdt.find(qn('w:sdtContent'))
    if content is None: return
    # Remove existing
    for child in list(content):
        content.remove(child)
    # Add new content respecting inline vs block SDT
    parent = sdt.getparent()
    if parent is not None and parent.tag == qn('w:p'):
        # Inline SDT: content must be runs, not paragraphs
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.text = str(text)
        r.append(t)
        content.append(r)
    else:
        # Block SDT: content should be paragraphs
        p = OxmlElement('w:p')
        r = OxmlElement('w:r')
        t = OxmlElement('w:t')
        t.text = str(text)
        r.append(t)
        p.append(r)
        content.append(p)

def populate_word_sdts(doc, data):
    for sdt in doc.element.body.iter(qn('w:sdt')):
        sdtPr = sdt.find(qn('w:sdtPr'))
        if sdtPr is None: continue
        tag = sdtPr.find(qn('w:tag'))
        if tag is None: continue
        
        val = tag.get(qn('w:val'))
        if val in data:
            set_sdt_text(sdt, data[val])

def find_item_table(doc):
    for table in doc.tables:
        # Check first row logic
        if len(table.rows) > 0:
            header_cells = table.rows[0].cells
            for cell in header_cells:
                text = cell.text.strip()
                if "ItemName" in text or "品名" in text:
                    return table
    return None

# Helper to fill and FLATTEN SDT in a specific element
# Flattening means: remove w:sdt wrapper, keep content (w:p or w:r).
# This prevents ID duplication and corruption in cloned rows.
def flatten_row_sdts(row_element, data):
    # Iterate over all SDTs in the row
    # We must collect them first because we are modifying the tree
    sdts = list(row_element.iter(qn('w:sdt')))
    
    for sdt in sdts:
        sdtPr = sdt.find(qn('w:sdtPr'))
        tag_val = None
        if sdtPr is not None:
            tag = sdtPr.find(qn('w:tag'))
            if tag is not None:
                tag_val = tag.get(qn('w:val'))
        
        # Determine replacement text
        text_to_set = None
        if tag_val and tag_val in data:
            text_to_set = data[tag_val]
        
        # If we have data, we set it. If not, we keep original text (or empty?). 
        # But we MUST flatten to avoid ID issues.
        
        content = sdt.find(qn('w:sdtContent'))
        if content is None: continue
        
        # If we need to set text, we replace the content's text run
        if text_to_set is not None:
            # Simple approach: remove all children of content, add new run
            for child in list(content):
                content.remove(child)
            
            # Helper to create run
            # Check context: are we in a paragraph? or block level?
            # sdtContent can contain paragraphs (if block sdt) or runs (if inline sdt)
            parent = sdt.getparent()
            
            # If parent is w:p, sdt is inline -> content should contain w:r
            # If parent is w:tc, sdt is block -> content should contain w:p
            
            if parent.tag == qn('w:p'):
                r = OxmlElement('w:r')
                t = OxmlElement('w:t')
                t.text = str(text_to_set)
                r.append(t)
                content.append(r)
            else:
                p = OxmlElement('w:p')
                r = OxmlElement('w:r')
                t = OxmlElement('w:t')
                t.text = str(text_to_set)
                r.append(t)
                p.append(r)
                content.append(p)
                
        # FLATTEN: Move children of sdtContent to sdt's parent, then remove sdt
        parent = sdt.getparent()
        index = list(parent).index(sdt)
        
        for child in list(content):
            parent.insert(index, child)
            index += 1
            
        parent.remove(sdt)

def process_word_template(doc, data, items):
    # 1. Scalar Fields
    populate_word_sdts(doc, data)
    
    # 2. <<Orderer>> Replacement
    orderer_key = "<<Orderer>>"
    for p in doc.paragraphs:
        if orderer_key in p.text:
            p.text = p.text.replace(orderer_key, data.get("RequestorName", ""))
    
    # 3. Tables (Items)
    table = find_item_table(doc)
    if table:
        print("  Found Item Table.")
        if len(table.rows) < 2:
            print("  Error: Table has no template row")
            return
            
        template_row = table.rows[1]
        subtotal = 0
        
        for item in items:
            # Calculate Data
            qty = item["Quantity"]
            price = item["UnitPrice"]
            amount = qty * price
            subtotal += amount
            
            # Clone Row
            new_row_element = copy.deepcopy(template_row._element)
            
            row_data = {
                "ItemName": str(item["ItemName"]),
                "Quantity": str(qty),
                "Unit": str(item["Unit"]),
                "UnitPrice": f"{price:,}",
                "Amount": f"{amount:,}"
            }
            
            # CRITICAL FIX: Flatten SDTs in the cloned row
            flatten_row_sdts(new_row_element, row_data)
            
            table._element.append(new_row_element)
        
        # Remove template row
        table._element.remove(template_row._element)
        
        # 4. Footer Totals
        tax = math.floor(subtotal * 0.10)
        total = subtotal + tax
        
        totals_data = {
            "SubTotal": f"¥{subtotal:,}",
            "Tax": f"¥{tax:,}",
            "Total": f"¥{total:,}"
        }
        populate_word_sdts(doc, totals_data)
    else:
        print("  WARNING: Item table not found in Word.")
                            


# --- Helper Functions (Excel) ---

def copy_row_style(ws, src_row_idx, dest_row_idx):
    src_row = ws[src_row_idx]
    dest_row = ws[dest_row_idx]
    
    for i, cell in enumerate(src_row):
        new_cell = dest_row[i]
        new_cell.font = copy.copy(cell.font)
        new_cell.border = copy.copy(cell.border)
        new_cell.fill = copy.copy(cell.fill)
        new_cell.number_format = cell.number_format
        new_cell.protection = copy.copy(cell.protection)
        new_cell.alignment = copy.copy(cell.alignment)

def process_excel_template(wb, data, items):
    ws = wb.active
    
    # 1. Header Data (Simple cell mapping assumption for demo)
    # Adjust coordinates as per actual template if known. 
    # For now, we assume named ranges or explicit cells? 
    # Plan says "Row 10...". 
    
    # 2. Items
    start_row = 10
    
    # Calculate Totals
    subtotal = 0
    
    # We insert rows in reverse or just handle shifting.
    # To append, we insert rows before the last "Total" line or just overwrite empty pre-formatted rows?
    # Plan says: "10行目...をコピーして挿入" (Copy insert row 10).
    
    for i, item in enumerate(items):
        current_row = start_row + i
        
        # If it's not the first item, we might need to insert a row to push down footer?
        # Or if the template has only 1 row, we insert N-1 rows.
        if i > 0:
            ws.insert_rows(current_row)
            copy_row_style(ws, start_row, current_row) # Copy from first data row
            
        # Set Values
        qty = item["Quantity"]
        price = item["UnitPrice"]
        amount = qty * price
        subtotal += amount
        
        # Column mapping (Arbitrary/Standard Assumption)
        # A=No, B=ItemName, C=Qty, D=Unit, E=Price, F=Amount
        ws.cell(row=current_row, column=1).value = i + 1
        ws.cell(row=current_row, column=2).value = item["ItemName"]
        ws.cell(row=current_row, column=3).value = qty
        ws.cell(row=current_row, column=4).value = item["Unit"]
        ws.cell(row=current_row, column=5).value = price
        ws.cell(row=current_row, column=6).value = amount 
    
    # Totals (Assume they are below the list. If we inserted rows, they pushed down.)
    # We might need to find where they are or assume fixed offset if no rows were inserted (but we did).
    
    pass

# --- Main ---

def main():
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # --- Process Word ---
    print(f"Processing Word Template: {word_template_path}")
    if os.path.exists(word_template_path):
        doc = docx.Document(word_template_path)
        process_word_template(doc, DUMMY_DATA, ITEMS)
        doc.save(word_output_path)
        print(f"  Saved Word to: {word_output_path}")
    else:
        print("  Word template not found.")

    # --- Process Excel ---
    print(f"Processing Excel Template: {excel_template_path}")
    if os.path.exists(excel_template_path):
        wb = openpyxl.load_workbook(excel_template_path)
        process_excel_template(wb, DUMMY_DATA, ITEMS)
        wb.save(excel_output_path)
        print(f"  Saved Excel to: {excel_output_path}")
    else:
        print("  Excel template not found.")

if __name__ == "__main__":
    main()
