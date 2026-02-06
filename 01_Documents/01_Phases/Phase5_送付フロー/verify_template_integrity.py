
import os
import docx

base_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.abspath(os.path.join(base_dir, "../../02_Templates"))
template_path = os.path.join(templates_dir, "発注書テンプレート.docx")
output_path = os.path.join(base_dir, "TestOutput", "integrity_check.docx")

print(f"Opening: {template_path}")
try:
    doc = docx.Document(template_path)
    # Just save it immediately
    doc.save(output_path)
    print(f"Saved: {output_path}")
except Exception as e:
    print(f"Error: {e}")
