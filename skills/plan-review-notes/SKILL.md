---
name: plan-review-notes
description: Create/update markdown指摘まとめ files for phase planning documents; trigger when plan doc review feedback must be captured in the standard format.
---

# Plan Review Notes

Use when reviewing Phase計画書 and the user wants指摘をMarkdownにまとめる。

## Workflow
- Identify the target plan file path and its last updated date.
- Collect findings ordered by severity with short rationale.
- Create or update `<Phase番号>_タイトル_指摘まとめ.md` in the same folder.
- Include sections: ヘッダー(日付, 対象ファイル名+最終更新日)、指摘事項(番号付き・簡潔)、推奨対応。
- Preserve existing content; append new dated batches instead of overwriting.
- Reference the source file path with backticks; save UTF-8.

## References
- See `references/review-rules.md` for the shared review rules and naming pattern.
