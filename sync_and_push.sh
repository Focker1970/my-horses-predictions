#!/bin/bash
# 予測データを public/ にコピーし、GitHub に push するスクリプト
# 使い方: bash public/sync_and_push.sh

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PUBLIC_DIR="$PROJECT_DIR/public"

# 予測JSONをコピー
cp "$PROJECT_DIR/data/predictions/"*.json "$PUBLIC_DIR/data/predictions/" 2>/dev/null || true

# 戦略分析CSVをコピー
mkdir -p "$PUBLIC_DIR/data/strategy"
cp "$PROJECT_DIR/data/strategy/filter_results.csv" "$PUBLIC_DIR/data/strategy/" 2>/dev/null || true
cp "$PROJECT_DIR/data/strategy/race_analysis.csv" "$PUBLIC_DIR/data/strategy/" 2>/dev/null || true

# git push
cd "$PUBLIC_DIR"
git add -A
git commit -m "予測データ更新 $(date '+%Y-%m-%d %H:%M')" || { echo "変更なし"; exit 0; }
git push
echo "push 完了"
