@echo off
chcp 65001 > nul
title EVN LAM DONG - HE THONG TONG HOP BAO CAO THU NGAN HANG 2026
color 0B

echo ===============================================================================
echo        CONG TY DIEN LUC LAM DONG - PHONG TAI CHINH KE TOAN
echo   HE THONG QUAN LY VA TONG HOP BAO CAO THU TIEN DIEN QUA NGAN HANG ^& TCTG
echo ===============================================================================
echo.
echo [*] Dang kiem tra moi truong Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python! Vui long cai dat Python hoac lien he quan tri vien.
    pause
    exit /b
)

echo [*] Dang khoi dong may chu du lieu noi bo (Port 5678)...
start "" http://localhost:5678
python server.py

pause
