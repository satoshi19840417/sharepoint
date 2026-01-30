---
description: 作業終了時の引継ぎとGitHubプッシュ
---

# 作業終了時の引継ぎ手順

作業終了時に以下の手順を実行して、成果物をプロジェクトに保存しGitHubにプッシュする。

## 手順

### 1. 成果物の移動

作業中に作成した以下のファイルを、プロジェクトの適切なフォルダにコピーする：

- `implementation_plan.md` → `Documents/01_Phases/[Phase名]/[Phase名]_[作業名]計画.md`
- `task.md` → `Documents/01_Phases/[Phase名]/[Phase名]_[作業名]タスク.md`
- `walkthrough.md` → `Documents/01_Phases/[Phase名]/[Phase名]_[作業名]引継ぎ.md`

```powershell
# 例: Phase5テンプレート作成の場合
Copy-Item "$env:USERPROFILE\.gemini\antigravity\brain\[conversation-id]\implementation_plan.md" "Documents\01_Phases\Phase5_送付フロー\Phase5_テンプレート作成計画.md"
Copy-Item "$env:USERPROFILE\.gemini\antigravity\brain\[conversation-id]\task.md" "Documents\01_Phases\Phase5_送付フロー\Phase5_テンプレート作成タスク.md"
Copy-Item "$env:USERPROFILE\.gemini\antigravity\brain\[conversation-id]\walkthrough.md" "Documents\01_Phases\Phase5_送付フロー\Phase5_テンプレート作成引継ぎ.md"
```

### 2. Gitステージング

// turbo
```powershell
git add -A
```

### 3. コミット

```powershell
git commit -m "[Phase名] 作業内容の要約"
```

例: `git commit -m "[Phase5] テンプレート作成計画策定・タスク管理表作成"`

### 4. GitHubプッシュ

// turbo
```powershell
git push origin master
```

## 注意事項

- `.gitignore` に含まれるファイル（Work/, Archive/, 一時ファイル等）はコミットされない
- 成果物は必ずプロジェクト内のDocumentsフォルダに移動してからコミットすること
- コミットメッセージにはPhase名と作業内容を含めること
