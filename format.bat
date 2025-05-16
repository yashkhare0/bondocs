@echo off
REM Script to set up formatting and run it on all files for Windows

echo Installing pre-commit hooks...
pre-commit install

echo Updating pre-commit hooks...
pre-commit autoupdate

echo Running Black and Ruff on all files...
black .
ruff --fix .

echo Running pre-commit on all files...
pre-commit run --all-files

echo Done! Your code is now formatted.
