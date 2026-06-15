---
name: design
description: 定義新專案的目標、範圍與技術方向
agent: designer
argument-hint: 可選：提供初始需求、限制或偏好的技術方向。
---

# Design

## Overview

用於定義「專案是什麼」與「全專案大框架」，適合新專案或尚未建立 project brief / architecture baseline 的情境。若提供 `$ARGUMENTS`，將其視為初始需求、限制或偏好的技術方向。

## When to Use

- 新專案尚未有 `.project/memory/project.md`、project brief 或全專案大框架
- 使用者需要釐清產品目標、使用者、非目標與技術方向
- 需要先建立 project-level baseline，再交給 `planner` 做細部實作規劃

## When NOT to Use

- 既有 repo 需要掃描現況，改用 `analyze`
- 已有 project-level baseline，只需要功能、phase 或模組的細部實作方案，改用 `planner`
- 使用者要審查或修改既有 plan，改用 `validate-plan` 或 `planner`

## Inputs / Scope

- `$ARGUMENTS` 可包含需求摘要、目標使用者、限制條件、技術偏好或非目標
- 未指定時，先讀現有 Memory Bank，避免覆蓋已建立的 project definition
- 產出以 project-level brief + architecture baseline 為主；可描述模組邊界、資料流與 roadmap，但不拆 implementation task

## Escalation Boundary

- 若問題已進入具體架構方案、migration 或 rollout，停止並轉回 `planner`
- 若需求缺少必要產品決策，列出 open questions，不自行補成事實
- 不覆蓋既有 project brief，除非使用者明確要求更新專案定義

## 執行步驟

1. 先確認是否已有 `.project/memory/project.md` 或既有 project brief；若已存在，避免重複定義。
2. 蒐集專案目標、使用者、核心功能、非功能需求、風險與技術限制。
3. 釐清必做與可延後範圍，產出清楚的 scope 邊界與全專案大框架。
4. 將 project brief、系統大框架、核心模組、資料流與 phase roadmap 寫入 `project.md`，必要時同步更新 `tech-stack.md` 與 workspace memory。

## 產出要求

- 專案簡介
- 核心功能與非目標
- 技術棧方向
- 系統大框架、核心模組、資料流與部署輪廓
- 全專案 phase roadmap；Phase 1 只能是 roadmap 的第一段，不可取代整體 baseline
- 主要風險與未決問題

## 重要原則

- design 定義問題空間與全專案大框架，不直接拆 task 或細部 implementation plan
- 若需求其實是某個功能怎麼做，應轉交 `planner`
- 先找出不確定性，再決定是否需要更多提問

## Next Step

- 細部實作規劃、功能方案或 phase plan：交給 `planner`
- 已有既有專案需要掃描：交給 `analyze`
