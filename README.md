# JalNirikshan

**JalNirikshan** is an open-source lake health monitoring tool focusing on **Eichhornia (water hyacinth) detection**, environment status, and community reporting.

## ✅ What’s included

- `backend.py`: FastAPI backend with:
  - `SQLite` dataset storage
  - image upload and classification (Eichhornia detection pipeline)
  - health endpoints and docs
- `dashboard.py`: Streamlit dashboard with:
  - interactive map view
  - report generation and export
  - team/member task management
  - camera image upload and visualization
- `JalNirikshan.py`: builtin integrity & dependency check
  - PDF generation
  - Unicode support
  - DB and OpenCV verification
- `requirements.txt`: Python dependency list
- `start.ps1`: Windows quick-start launcher

## 🧩 Features

- Eichhornia detection for lake health management
- easy REST API via FastAPI
- live dashboard UI via Streamlit
- one-command server plus UI launcher
- built-in tests and environment checks

## 🚀 Quick start (Windows)

```powershell
cd "C:\Users\LENOVO\Desktop\JalNirikshan\JalNirikshan"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## ▶️ Run services

### 1) Start backend

```powershell
python backend.py
```

Verify:
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

### 2) Start dashboard

```powershell
streamlit run dashboard.py
```

Open `http://localhost:8501`

### 3) Run local tests

```powershell
python JalNirikshan.py
```

## 🖱️ One-step start

```powershell
.\start.ps1
```

This will start both:
- backend: `uvicorn backend:app --reload --host 0.0.0.0 --port 8000`
- dashboard: `streamlit run dashboard.py`

## 🐛 Troubleshooting

If dependency errors appear:

```powershell
pip install fastapi uvicorn python-multipart pandas numpy pillow opencv-python
```

- On Python 3.13, some `opencv-python` binaries may be unavailable. Use Python 3.12 or 3.11.

## 🧪 Extend & contribute

1. fork this repository
2. create a feature branch
3. implement your data pipeline, detection model, or UI improvements
4. submit a PR with details & tests

---
