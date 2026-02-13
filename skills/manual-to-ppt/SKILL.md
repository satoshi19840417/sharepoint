---
name: manual-to-ppt
description: Convert Excel manuals (text + embedded images) into CellGenTech-styled PowerPoint slides.
---

# Manual to PPT Skill

## Overview

This skill converts an Excel operation manual into a PowerPoint file.

Official entrypoint:

```bash
python skills/manual-to-ppt/main.py <excel_path>
```

## CLI Usage

### Simple mode

```bash
python skills/manual-to-ppt/main.py 05_mail/相見積操作マニュアル.xlsx
```

### Interactive mode

```bash
python skills/manual-to-ppt/main.py --interactive
```

### Optional arguments

- `--output <pptx>`: explicit output file path
- `--output-dir <dir>`: output directory (filename becomes `<excel_stem>.pptx`)
- `--logo <path>`: explicit logo path
- `--config <json>`: config JSON path
- `--interactive`: prompt for missing values

## Config File

Use `config/config_template.json` as a base and pass it with `--config`.

Precedence:

- `output_path`: `--output` > `--output-dir` > `config.default_output_dir` > Excel directory
- `logo_path`: `--logo` > `config.logo_path` > auto-detection > none
- `color_scheme`: `config.color_scheme` > internal default

## Legacy Compatibility

Legacy paths are still maintained:

- CLI: `python 05_mail/scripts/convert_manual_to_ppt.py`
- Import: `from convert_manual_to_ppt import convert_excel_to_ppt`

These are compatibility paths. New usage should call `skills/manual-to-ppt/main.py`.

## Troubleshooting

- `ERROR: Excel file not found`: check input path.
- `ERROR: Invalid config JSON`: fix JSON syntax.
- `ERROR: Cannot use --output and --output-dir together`: use one of them.
- `ModuleNotFoundError` from legacy scripts: ensure repository structure keeps `skills/manual-to-ppt` and `05_mail/scripts`.

