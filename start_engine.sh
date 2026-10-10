#!/bin/bash
echo "🧹 Step 1: Sweeping zombie Python processes..."
pkill -9 -f "python auto_watcher.py" || true
pkill -9 -f "python repo_indexer.py" || true
sleep 1

echo "🗑️ Step 2: Wiping the locked Qdrant database..."
rm -rf qdrant_ledger_data

echo "🏗️ Step 3: Rebuilding the Global Context Graph..."
python repo_indexer.py

echo "🚀 Step 4: Igniting the Core Controller..."
python auto_watcher.py
