## Summary
<!-- 一兩句話:這個 PR 做什麼、解決什麼問題 -->

## Context
<!-- 為什麼要做。附相關的 GitHub Issue 或 Notion 任務連結 -->

## Changes
<!-- 主要改動,條列即可 -->
-

## Design decisions
<!-- 為什麼這樣設計;考慮過哪些替代方案、為什麼沒選 -->
-

## Risks and rollback
<!-- 可能出什麼問題;出問題時怎麼回復(例如 revert 這個 PR) -->
-

## Security
<!-- 沒碰到的項目寫「無」,不要刪掉 -->
- 資料 / key / 外部呼叫:
- 新增 dependency:<!-- 無,或列出套件與版本;hash 是否已鎖定 -->
- 不可信輸入(prompt injection、畸形資料)時的行為:<!-- 對應哪個 test -->
- 已知限制,上線前還要補什麼:
- 最壞情況:

## Test plan
<!-- 怎麼驗證;驗收標準至少一條資安項目 -->
- [ ]
- [ ] 資安:

## Open questions
<!-- 需要負責人決定的事:寫「這點需要再討論」並 @bing-kuo。沒有就寫「無」 -->
- 無

## Checklist
- [ ] CI 綠燈(`test`)
- [ ] secret scan 通過(`secret-scan`、pre-commit gitleaks)
- [ ] 文件已更新(README、docstring)
