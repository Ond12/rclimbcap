REM

set original_dir=%CD%
set venv_root_dir=venvclimbcap

cd %venv_root_dir%

call Scripts\activate.bat

python ..\python_ui\testUI.pyw

call Scripts\deactivate.bat

cd %original_dir%
exit /B 0