@echo off
echo Starting APIx FastAPI Backend and Dashboard...
echo ===================================================
echo Make sure you have installed requirements:
echo pip install fastapi uvicorn pandas
echo ===================================================
echo The dashboard will be available at: http://localhost:8000
echo ===================================================
python -m uvicorn scrapers.backend.main:app --reload --host 0.0.0.0 --port 8000
