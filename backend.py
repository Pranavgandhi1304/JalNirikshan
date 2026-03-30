from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from datetime import datetime
import uvicorn
import pandas as pd
from PIL import Image
import io
import base64
import numpy as np
import cv2
from contextlib import contextmanager
import random
from typing import Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Jal Nirikshan - Eichhornia Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_NAME = 'jal_nirikshan.db'

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS reports 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      timestamp TEXT NOT NULL, 
                      lat REAL NOT NULL, 
                      lon REAL NOT NULL, 
                      coverage REAL NOT NULL, 
                      score REAL NOT NULL, 
                      lake TEXT NOT NULL, 
                      status TEXT NOT NULL,
                      user_email TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS teams 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      lake_name TEXT NOT NULL,
                      team_members TEXT NOT NULL,
                      team_size INTEGER NOT NULL,
                      health_score REAL,
                      assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        logger.info("✅ Database initialized")

# Team members pool
TEAM_MEMBERS = [
    "Ramesh Kumar", "Sita Devi", "Amit Sharma", "Priya Patel", "Vikram Singh",
    "Laxmi Bai", "Rajesh Gupta", "Meera Joshi", "Kiran Reddy", "Sunita Yadav",
    "Arun Mehra", "Neha Singh", "Deepak Verma", "Pooja Rani", "Sanjay Das",
    "Kavita Sharma", "Mohan Lal", "Anita Rao", "Vijay Kumar", "Ritu Devi"
]

def allocate_teams(lake_name: str, score: float) -> Dict:
    """LOWER score = MORE teams (Fixed logic)"""
    if score < 25:  # Critical - MAX teams
        team_size = random.randint(6, 10)
    elif score < 45:  # High
        team_size = random.randint(4, 7)
    elif score < 65:  # Moderate
        team_size = random.randint(2, 4)
    else:  # Healthy - MIN teams
        team_size = 1
    
    team = random.sample(TEAM_MEMBERS, team_size)
    team_str = ", ".join(team)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO teams (lake_name, team_members, team_size, health_score) VALUES (?, ?, ?, ?)",
            (lake_name, team_str, team_size, score)
        )
    
    return {"lake": lake_name, "team": team, "size": team_size}

def detect_eichhornia(image: Image.Image) -> Dict:
    """Eichhornia-specific detection with Green/Yellow precaution"""
    img_array = np.array(image.convert('RGB'))
    img_array = cv2.resize(img_array, (800, 600))
    
    # Enhance contrast
    lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    lab[:,:,0] = cv2.equalizeHist(lab[:,:,0].astype(np.uint8))
    img_array = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    
    # GREEN/YELLOW PRECAUTION - Eichhornia ONLY
    # Primary: Purple-green glossy leaves (H=110-135 ONLY)
    eich_primary = cv2.inRange(hsv, np.array([110, 70, 50]), np.array([135, 200, 180]))
    
    # Secondary: Mature Eichhornia stems (H=120-140)
    eich_secondary = cv2.inRange(hsv, np.array([120, 80, 60]), np.array([140, 220, 200]))
    
    # EXCLUDE algae greens (H=20-90) & yellows
    algae_mask = cv2.inRange(hsv, np.array([20, 50, 50]), np.array([90, 255, 255]))
    eich_mask = cv2.bitwise_or(eich_primary, eich_secondary)
    eich_mask = cv2.bitwise_and(eich_mask, cv2.bitwise_not(algae_mask))
    
    # Morphological operations
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    eich_mask = cv2.morphologyEx(eich_mask, cv2.MORPH_OPEN, kernel_open)
    eich_mask = cv2.morphologyEx(eich_mask, cv2.MORPH_CLOSE, kernel_close)
    
    # Size filter
    contours, _ = cv2.findContours(eich_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filtered_mask = np.zeros_like(eich_mask)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 800:
            perimeter = cv2.arcLength(cnt, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            if circularity > 0.25:
                cv2.fillPoly(filtered_mask, [cnt], 255)
    
    eich_mask = filtered_mask
    
    # Texture filter
    texture_mask = cv2.Laplacian(eich_mask.astype(np.uint8), cv2.CV_64F)
    texture_mask = (texture_mask > 60).astype(np.uint8) * 255
    eich_mask = cv2.bitwise_and(eich_mask, texture_mask)
    
    # Water body filter
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    water_mask = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=2)
    eich_mask = cv2.bitwise_and(eich_mask, cv2.bitwise_not(water_mask))
    
    # Coverage calculation
    water_pixels = np.sum(gray < 200)
    eich_pixels = np.sum(eich_mask > 0)
    coverage = (eich_pixels / max(water_pixels, 1)) * 100 if water_pixels > 0 else 0
    coverage = min(95, coverage)
    
    score = max(0, 92 - coverage * 1.25)
    status = 'Critical' if score < 25 else 'High' if score < 45 else 'Moderate' if score < 65 else 'Healthy'
    
    mask_colored = cv2.cvtColor(eich_mask.astype(np.uint8), cv2.COLOR_GRAY2RGB)
    mask_colored[eich_mask > 0] = [0, 255, 0]
    
    return {
        'eichhornia_coverage': round(coverage, 2),
        'health_score': round(score, 2),
        'status': status,
        'detection_confidence': round(min(coverage * 0.8, 95), 1),
        'mask_image': Image.fromarray(mask_colored)
    }

init_db()

@app.post("/reports/")
async def add_report(
    lat: float = Form(...),
    lon: float = Form(...),
    lake: str = Form(...),
    image_b64: str = Form(...),
    user_email: str = Form(None)
):
    try:
        logger.info(f"Processing report for {lake} at ({lat}, {lon})")
        image_data = base64.b64decode(image_b64.split(',')[1])
        image = Image.open(io.BytesIO(image_data)).convert('RGB')
        analysis = detect_eichhornia(image)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO reports 
                (timestamp, lat, lon, coverage, score, lake, status, user_email) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), lat, lon, analysis['eichhornia_coverage'],
                 analysis['health_score'], lake, analysis['status'], user_email)
            )
            report_id = cursor.lastrowid
        
        team_info = None
        if analysis['health_score'] < 70:
            team_info = allocate_teams(lake, analysis['health_score'])
        
        return {
            "status": "success",
            "report_id": report_id,
            "analysis": analysis,
            "team_allocated": team_info,
            "message": f"Eichhornia report processed for {lake}"
        }
    except Exception as e:
        logger.error(f"Report processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/")
async def get_reports(limit: int = 50):
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM reports ORDER BY timestamp DESC LIMIT ?", conn, params=(limit,))
    return df.to_dict('records') if not df.empty else []

@app.get("/reports/{lake_name}")
async def get_reports_by_lake(lake_name: str, limit: int = 20):
    with get_db_connection() as conn:
        df = pd.read_sql_query(
            "SELECT * FROM reports WHERE lake LIKE ? ORDER BY timestamp DESC LIMIT ?",
            conn, params=(f"%{lake_name}%", limit)
        )
    return df.to_dict('records') if not df.empty else []

@app.get("/teams/")
async def get_teams(limit: int = 20):
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM teams ORDER BY assigned_at DESC LIMIT ?", conn, params=(limit,))
    return df.to_dict('records') if not df.empty else []

@app.get("/stats/")
async def get_statistics():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        total_reports = cursor.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        avg_coverage = cursor.execute("SELECT AVG(coverage) FROM reports").fetchone()[0] or 0
        critical_lakes = cursor.execute("SELECT COUNT(DISTINCT lake) FROM reports WHERE score < 30").fetchone()[0]
        active_teams = cursor.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
        latest_report = cursor.execute("SELECT MAX(timestamp) FROM reports").fetchone()[0]
    
    return {
        "total_reports": total_reports,
        "average_coverage": round(avg_coverage, 2),
        "critical_lakes": critical_lakes,
        "active_teams": active_teams,
        "latest_report": latest_report,
        "system_status": "healthy"
    }

@app.get("/health")
async def health_check():
    with get_db_connection() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    logger.info("🚀 Starting Jal Nirikshan API")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
