@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1

set "NARO_ROOT=D:\NARO_LINKED_CLIENT_BASELINE\NARO_CP41_CORE_BASELINE_RESPONSIVE_UI"
if not exist "%NARO_ROOT%\_system\naro_updater.py" (
  set "NARO_ROOT=%~dp0"
)
if not exist "%NARO_ROOT%\_system\naro_updater.py" (
  echo لم يتم العثور على مجلد NARO الصحيح.
  echo ضع هذا الملف داخل مجلد NARO الرئيسي ثم شغله مرة اخرى.
  pause
  exit /b 2
)

set "REPAIR=%TEMP%\NARO_Link_Repair_G3.py"
set "URL=https://raw.githubusercontent.com/algifri1/lucent-muse-assets/naro-updates/naro/repair_g3.py?ts=%RANDOM%%RANDOM%"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -UseBasicParsing -Uri '%URL%' -OutFile '%REPAIR%'"
if errorlevel 1 (
  echo فشل تنزيل اداة اصلاح الربط.
  pause
  exit /b 3
)

where py.exe >nul 2>&1
if not errorlevel 1 (
  set "NARO_ROOT=%NARO_ROOT%"
  py -3 -X utf8 "%REPAIR%"
  set "RC=%ERRORLEVEL%"
  goto DONE
)

where python.exe >nul 2>&1
if not errorlevel 1 (
  set "NARO_ROOT=%NARO_ROOT%"
  python -X utf8 "%REPAIR%"
  set "RC=%ERRORLEVEL%"
  goto DONE
)

echo Python 3 غير موجود في PATH.
set "RC=4"

:DONE
echo.
if "%RC%"=="0" (
  echo SUCCESS - تم اصلاح الربط وتحديث NARO الى G3.
) else (
  echo لم يكتمل الاصلاح. النتيجة محفوظة داخل:
  echo %NARO_ROOT%\data\NARO_LINK_REPAIR_G3_RESULT.txt
)
pause
endlocal
exit /b %RC%
