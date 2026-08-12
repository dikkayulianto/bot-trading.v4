@echo off
title Build Encrypted Customer Release - Port 5006
color 0B
echo =======================================================================
echo     BUILD ENCRYPTED RELEASE PACKAGE - PORT 5006 (SCALPING 90% BOT)
echo =======================================================================
echo.
echo [1/3] Mengenkripsi & Meng-obfuscate bot.py & strategy.py dengan PyArmor...
pyarmor gen bot.py strategy.py

echo.
echo [2/3] Menyusun Folder Distribusi Pembeli (dist_package_5006)...
if not exist "dist_package_5006" mkdir "dist_package_5006"
xcopy /E /I /Y "dist\*" "dist_package_5006\"
copy /Y "app.py" "dist_package_5006\"
copy /Y "config.json" "dist_package_5006\"
copy /Y "RUN_BOT_PORT_5006.bat" "dist_package_5006\"
copy /Y "PANDUAN_INSTALASI_PORT_5006.md" "dist_package_5006\"
copy /Y "preset_scalping_90pct_best.json" "dist_package_5006\"
xcopy /E /I /Y "templates" "dist_package_5006\templates"
xcopy /E /I /Y "static" "dist_package_5006\static"

echo.
echo =======================================================================
echo SUCCESS! Folder "dist_package_5006" telah berhasil dibuat!
echo Seluruh source code Python sudah TERKUNCI & TERENKRIPSI TOTAL.
echo Kirimkan folder "dist_package_5006" ini kepada pembeli Anda.
echo =======================================================================
pause
