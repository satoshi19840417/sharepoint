---
description: Generate professional and editable PowerPoint presentations using Markdown (Marp) and pptxgenjs.
---

# Presentation Generation Skill

Use this skill to create high-quality PowerPoint presentations. It supports two output formats:
1.  **Standard (Marp)**: High-quality rendering from Markdown, best for viewing.
2.  **Editable (pptxgenjs)**: Fully editable PowerPoint file generated via script, best for further customization.

## Prerequisites
- Node.js installed
- Dependencies: `pptxgenjs`, `@marp-team/marp-cli`

## Usage

### 1. Standard Presentation (Marp)
Use the provided Markdown template to create your slides.

**Template Location**: `templates/marp_template.md`

**Command**:
```bash
npx @marp-team/marp-cli@latest "path/to/your_slides.md" -o "path/to/output.pptx" --allow-local-files
```

### 2. Editable Presentation (Script)
Use the provided JavaScript template to generate a fully editable PPTX.

**Template Location**: `templates/script_template.js`

**Steps**:
1.  Copy `script_template.js` to your project script folder (e.g., `02_Scripts/my_presentation.js`).
2.  Modify the content in the script (look for `s1.addText`, `pres.addSlide`, etc.).
3.  Run the script:
    ```bash
    node 02_Scripts/my_presentation.js
    ```

## Customization
- **Logo**: The templates include logic for a company logo. Ensure the image path is correct in both the Markdown CSS and the JavaScript `addLogo` function.
- **Theme**: Modify the `theme` in Markdown or colors constants in the JavaScript file.
