@echo off
title Tat Tu Dong Cap Nhat Tin Tuc
echo =======================================================
echo   DANG TAT TINH NANG TU DONG CAP NHAT TIN TUC...
echo =======================================================
echo.
schtasks /delete /tn "CapNhatTinTucBaoMoi" /f
echo.
echo =======================================================
echo   DA TAT THANH CONG! WEBSITE SE KHONG TU DONG CAP NHAT.
echo =======================================================
pause
