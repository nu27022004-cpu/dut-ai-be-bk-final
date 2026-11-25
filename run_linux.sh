#!/bin/bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "[1/3] Tạo môi trường ảo Python (.venv)..."
    python3 -m venv .venv
fi

source .venv/bin/activate

if ! python -c "import flask, sklearn, pandas, openpyxl, joblib" 2>/dev/null; then
    echo "[2/3] Cài đặt thư viện từ requirements.txt..."
    pip install -r requirements.txt
fi

if [ ! -f "models/intent_model.joblib" ]; then
    echo "[3/3] Huấn luyện mô hình AI V6 (5-Fold Stratified CV)..."
    python train.py
fi

echo "Khởi chạy DUT AI Student Assistant V6 tại http://127.0.0.1:5000"
python app.py
