@echo off
set PGDIR=%APPDATA%\postgresql
set PGFILE=%PGDIR%\pgpass.conf
set OUT=C:\Users\OWNER\Claude\Projects\GBC Project\pgpass_setup_result.txt
if not exist "%PGDIR%" mkdir "%PGDIR%"
if exist "%PGFILE%" (
  echo ALREADY_EXISTS: %PGFILE% > "%OUT%"
  echo (left untouched - not reading its contents) >> "%OUT%"
) else (
  > "%PGFILE%" echo wrds-pgdata.wharton.upenn.edu:9737:wrds:seanqin2028:REPLACE_WITH_YOUR_WRDS_PASSWORD
  echo CREATED_TEMPLATE: %PGFILE% >> "%OUT%"
)
echo --- folder listing --- >> "%OUT%"
dir "%PGDIR%" >> "%OUT%" 2>&1
type "%OUT%"
