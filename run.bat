@ECHO OFF


mkdir attachments
mkdir outputs
mkdir videos

cmd /k ".\venv\Scripts\activate & python .\scripts\main.py"

PAUSE