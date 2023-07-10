@ECHO OFF


mkdir attachments
mkdir outputs
mkdir videos

cmd /k "python -m venv venv & .\venv\Scripts\activate & python.exe -m pip install --upgrade pip & pip install -r requirements.txt & python .\scripts\main.py"

PAUSE