@echo off
cd /d %~dp0

if not exist .venv (
    echo [1/3] Tao moi truong ao Python ^(.venv^)...
    py -m venv .venv
)

call .venv\Scripts\activate

python -c "import flask, sklearn, pandas, openpyxl, joblib" 2>nul
if errorlevel 1 (
    echo [2/3] Cai dat thu vien tu requirements.txt...
    pip install -r requirements.txt
)

if not exist models\intent_model.joblib (
    echo [3/3] Huan luyen mo hinh AI V6 ^(5-Fold Stratified CV^)...
    python train.py
)

echo Khoi chay DUT AI Student Assistant V6 tai http://127.0.0.1:5000
python app.py
pause
