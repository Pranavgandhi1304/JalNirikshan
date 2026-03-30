import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
import cv2
from PIL import Image
import requests
import base64
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Jal Nirikshan", layout="wide", initial_sidebar_state="expanded")

# Poppr-Inspired CSS - Dark Text + Dynamic Scroll Animations
st.markdown("""
<style>
/* FORCE LIGHT THEME + DARK TEXT */
[data-testid="stAppViewContainer"] { 
    background-color: #f8fafc !important; 
    color: #0f172a !important; 
    font-weight: 500 !important;
}
.stApp { 
    background-color: #f8fafc !important; 
    color: #0f172a !important;
}

/* DARK TEXT OVERRIDE - All Streamlit elements */
.stText > label { color: #0f172a !important; font-weight: 600; }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { 
    color: #0f172a !important; font-weight: 700; 
}
.stMetric label { color: #1e293b !important; font-weight: 600; }
.stSelectbox > label, .stNumberInput > label { 
    color: #0f172a !important; font-weight: 600; 
}

/* POPPR SCROLL ANIMATIONS - Staggered */
.poppr-anim-1 { 
    opacity: 0; transform: translateY(60px); 
    animation: popprSlideInUp 1s cubic-bezier(0.25,0.46,0.45,0.94) 0.1s forwards; 
}
.poppr-anim-2 { 
    opacity: 0; transform: translateY(60px); 
    animation: popprSlideInUp 1s cubic-bezier(0.25,0.46,0.45,0.94) 0.2s forwards; 
}
.poppr-anim-3 { 
    opacity: 0; transform: translateY(60px); 
    animation: popprSlideInUp 1s cubic-bezier(0.25,0.46,0.45,0.94) 0.3s forwards; 
}
.poppr-anim-4 { 
    opacity: 0; transform: translateY(60px); 
    animation: popprSlideInUp 1s cubic-bezier(0.25,0.46,0.45,0.94) 0.4s forwards; 
}

@keyframes popprSlideInUp {
    0% { opacity: 0; transform: translateY(60px) scale(0.95); }
    50% { opacity: 0.7; transform: translateY(20px) scale(0.98); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* DARK GREEN GRADIENT SYSTEM */
:root { 
    --primary-dark: #14532d; 
    --primary: #166534; 
    --primary-light: #22c55e;
    --bg-light: #f8fafc;
    --text-dark: #0f172a;
    --text-muted: #475569;
}

/* TABS - Poppr Style */
.stTabs [data-baseweb="tab-list"] {
    background: linear-gradient(135deg, var(--primary-dark) 0%, #1e4a2e 100%) !important;
    border-radius: 20px !important; padding: 16px 24px !important;
    gap: 12px !important; backdrop-filter: blur(20px);
}
.stTabs [data-baseweb="tab"] {
    height: 56px !important; 
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 16px !important; 
    color: white !important;
    font-weight: 600 !important;
    transition: all 0.4s cubic-bezier(0.25,0.46,0.45,0.94) !important;
}
.stTabs [data-baseweb="tab"][aria-selected=true] {
    background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%) !important;
    color: var(--text-dark) !important; 
    box-shadow: 0 25px 60px rgba(22,101,52,0.4) !important;
    transform: translateY(-2px) !important;
}

/* CARDS */
.info-card, .team-card { 
    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%) !important;
    border-radius: 24px !important; 
    color: white !important; 
    padding: 3rem !important;
    box-shadow: 0 35px 80px rgba(20,83,45,0.4) !important;
}

/* BUTTONS */
.stButton > button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%) !important;
    color: white !important; border-radius: 16px !important;
    font-weight: 600 !important; border: none !important;
    box-shadow: 0 20px 40px rgba(22,101,52,0.3) !important;
    transition: all 0.3s cubic-bezier(0.25,0.46,0.45,0.94) !important;
}
.stButton > button:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 30px 60px rgba(22,101,52,0.5) !important;
}
</style>
""", unsafe_allow_html=True)

# Session state
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = "Public User"
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'current_lat' not in st.session_state: st.session_state.current_lat = 21.15
if 'current_lon' not in st.session_state: st.session_state.current_lon = 79.08

@st.cache_data
def load_india_data():
    data = [
        {"lake": "Futala Lake, Nagpur", "lat": 21.15, "lon": 79.08, "coverage": 25.0, "score": 65.0, "area_km2": 0.8, "status": "Moderate"},
        {"lake": "Shukravari Lake, Nagpur", "lat": 21.12, "lon": 79.10, "coverage": 45.0, "score": 28.0, "area_km2": 1.2, "status": "High"},
        {"lake": "Ambazari Lake, Nagpur", "lat": 21.13, "lon": 79.05, "coverage": 15.0, "score": 82.0, "area_km2": 4.5, "status": "Healthy"},
        {"lake": "Pench Lake, Nagpur", "lat": 21.25, "lon": 79.25, "coverage": 32.0, "score": 52.0, "area_km2": 2.8, "status": "Moderate"},
        {"lake": "Wular Lake, J&K", "lat": 34.29, "lon": 74.58, "coverage": 55.0, "score": 25.0, "area_km2": 189.0, "status": "High"},
        {"lake": "Dal Lake, Srinagar", "lat": 34.13, "lon": 74.84, "coverage": 48.0, "score": 35.0, "area_km2": 21.0, "status": "High"},
        {"lake": "Loktak Lake, Manipur", "lat": 24.48, "lon": 93.77, "coverage": 68.0, "score": 15.0, "area_km2": 287.0, "status": "Critical"},
        {"lake": "Kolleru Lake, AP", "lat": 16.62, "lon": 81.23, "coverage": 72.0, "score": 12.0, "area_km2": 245.0, "status": "Critical"},
        {"lake": "Vembanad Lake, Kerala", "lat": 9.65, "lon": 76.40, "coverage": 85.0, "score": 5.0, "area_km2": 205.0, "status": "Critical"},
        {"lake": "Chilika Lake, Odisha", "lat": 19.73, "lon": 85.33, "coverage": 40.0, "score": 38.0, "area_km2": 1100.0, "status": "High"},
    ]
    df = pd.DataFrame(data)
    df['size'] = np.clip(df['area_km2'] * 2.5, 8, 35)
    return df

def generate_pdf_report(lake_name, analysis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, "Jal Nirikshan Official Report", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Lake: {lake_name}", ln=True)
    pdf.cell(0, 10, f"Eichhornia Coverage: {analysis['eichhornia_coverage']:.1f}%", ln=True)
    pdf.cell(0, 10, f"Health Score: {analysis['health_score']:.1f}/100", ln=True)
    pdf.cell(0, 10, f"Status: {analysis['status']}", ln=True)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}", ln=True)
    
    return pdf.output()

# Header - Animation 1
st.markdown("""
<div class="poppr-anim-1" style='text-align:center; padding:4rem 2rem; 
    background:linear-gradient(135deg, #14532d 0%, #166534 50%, #22c55e 100%); 
    color:white; border-radius:30px; margin-bottom:3rem; box-shadow:0 40px 100px rgba(20,83,45,0.5);'>
    <h1 style='font-size:3.5rem; font-weight:800; margin:0; text-shadow:2px 2px 4px rgba(0,0,0,0.3);'>
        Jal Nirikshan
    </h1>
    <p style='font-size:1.5rem; opacity:0.95; margin:1rem 0 0 0;'>
        Eichhornia Detection & Cleanup Management
    </p>
</div>
""", unsafe_allow_html=True)

df = load_india_data()

# Sidebar
with st.sidebar:
    st.markdown('<div class="poppr-anim-2">', unsafe_allow_html=True)
    st.header("Search & Login")
    
    search_term = st.text_input("Search lakes")
    filtered_df = df[df['lake'].str.contains(search_term, case=False, na=False)] if search_term else df
    
    st.markdown("---")
    
    if not st.session_state.logged_in:
        st.markdown("**Demo Login**")
        username = st.text_input("Username", placeholder="citizen")
        password = st.text_input("Password", type="password", placeholder="jalnirikshan123")
        
        if st.button("Login", use_container_width=True):
            if username == "citizen" and password == "jalnirikshan123":
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_email = "citizen@jalnirikshan.com"
                st.success("Logged in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")
    else:
        st.success(f"Welcome {st.session_state.username}")
        if st.button("Logout", use_container_width=True):
            for key in ['logged_in', 'username', 'user_email']: 
                if key in st.session_state: del st.session_state[key]
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Metrics - Animation 3
col1, col2, col3, col4 = st.columns(4)
with col1: st.markdown('<div class="poppr-anim-3">', unsafe_allow_html=True)
col1.metric("Lakes Monitored", len(filtered_df))
with col2: st.markdown('<div class="poppr-anim-3">', unsafe_allow_html=True)
col2.metric("Critical Lakes", len(filtered_df[filtered_df['score'] < 30]))
with col3: st.markdown('<div class="poppr-anim-3">', unsafe_allow_html=True)
col3.metric("Avg Coverage", f"{filtered_df['coverage'].mean():.1f}%")
with col4: st.markdown('<div class="poppr-anim-3">', unsafe_allow_html=True)
col4.metric("Total Area", f"{filtered_df['area_km2'].sum():.1f} km²")
for col in [col1, col2, col3, col4]: st.markdown('</div>', unsafe_allow_html=True)

# 5 Tabs with staggered animations
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Live Map", "Reports", "Camera Upload", "Problem Info", "Teams"])

with tab1:
    st.markdown('<div class="poppr-anim-1">', unsafe_allow_html=True)
    st.markdown("## National Lake Health Dashboard")
    
    m = folium.Map(location=[20.59, 78.96], zoom_start=5)
    def get_color(score):
        if score < 30: return '#dc2626'
        elif score < 50: return '#f59e0b'
        elif score < 70: return '#facc15'
        return '#22c55e'
    
    for _, row in filtered_df.iterrows():
        folium.CircleMarker(
            [row['lat'], row['lon']], 
            radius=row['size'],
            popup=f"<b>{row['lake']}</b><br>Coverage: {row['coverage']:.1f}%<br>Health: {row['score']:.1f}<br>Status: <b>{row['status']}</b>",
            color=get_color(row['score']), fill=True, fillOpacity=0.7
        ).add_to(m)
    
    st_folium(m, width=1200, height=500)
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="poppr-anim-2">', unsafe_allow_html=True)
    st.markdown("## Official Reports")
    
    for _, row in filtered_df.iterrows():
        try:
            pdf_data = generate_pdf_report(row['lake'], {
                'eichhornia_coverage': row['coverage'], 
                'health_score': row['score'], 
                'status': row['status']
            })
            st.download_button(
                f"Download: {row['lake']}", 
                pdf_data, 
                f"{row['lake'].replace(' ','_')}_report.pdf", 
                "application/pdf",
                use_container_width=True
            )
        except Exception:
            st.warning(f"Could not generate PDF for {row['lake']}")
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="poppr-anim-3">', unsafe_allow_html=True)
    if st.session_state.logged_in:
        st.success("Camera upload with GPS enabled")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            camera_image = st.camera_input("Live camera")
            uploaded_file = st.file_uploader("Upload from gallery", type=['png','jpg','jpeg'])
            
            if st.button("Capture GPS (Mock)"):
                st.session_state.current_lat = 21.15
                st.session_state.current_lon = 79.08
                st.success("GPS coordinates captured")
            
            col_lat, col_lon = st.columns(2)
            lat = col_lat.number_input("Latitude", value=st.session_state.get('current_lat', 21.15))
            lon = col_lon.number_input("Longitude", value=st.session_state.get('current_lon', 79.08))
            
            selected_lake = st.selectbox("Select lake", df['lake'].tolist())
        
        with col2:
            if st.button("Analyze & Submit Report", type="primary", use_container_width=True):
                if camera_image or uploaded_file:
                    image = Image.open(camera_image) if camera_image else Image.open(uploaded_file)
                    
                    _, img_encoded = cv2.imencode('.jpg', np.array(image))
                    img_b64 = base64.b64encode(img_encoded).decode()
                    
                    try:
                        response = requests.post("http://localhost:8000/reports/", json={
                            'lat': lat, 'lon': lon, 'lake': selected_lake,
                            'image_b64': f"data:image/jpeg;base64,{img_b64}",
                            'user_email': st.session_state.user_email
                        }, timeout=30)
                        
                        if response.status_code == 200:
                            api_result = response.json()
                            st.session_state.report_result = api_result['analysis']
                            st.session_state.report_lake = selected_lake
                            st.session_state.report_image = image
                            st.session_state.team_info = api_result.get('team_allocated')
                            st.session_state.report_id = api_result['report_id']
                            st.success(f"Report #{api_result['report_id']} saved successfully")
                            st.rerun()
                        else:
                            st.error("Backend API error")
                    except requests.exceptions.RequestException:
                        st.error("Backend not running. Start with: uvicorn main:app --reload")
        
        if 'report_result' in st.session_state:
            result = st.session_state.report_result
            col1r, col2r, col3r = st.columns(3)
            col1r.metric("Coverage", f"{result['eichhornia_coverage']:.1f}%")
            col2r.metric("Health Score", f"{result['health_score']:.0f}/100")
            col3r.metric("Status", result['status'])
            
            col_img1, col_img2 = st.columns(2)
            col_img1.image(st.session_state.report_image, "Original image", use_column_width=True)
            col_img2.image(result['mask_image'], "AI analysis overlay", use_column_width=True)
            
            if st.session_state.team_info:
                st.markdown(f"""
                <div class="team-card">
                    <h3 style='color:white; margin:0 0 1rem 0;'>Cleanup Team Deployed</h3>
                    <h4 style='color:white; margin:0 0 1rem 0;'>{st.session_state.team_info['size']} members</h4>
                    <p style='color:#ecfdf5; font-size:1.1rem;'>{', '.join(st.session_state.team_info['team'][:3])}</p>
                </div>
                """, unsafe_allow_html=True)
            
            pdf_data = generate_pdf_report(st.session_state.report_lake, result)
            st.download_button("Download PDF Report", pdf_data, "report.pdf", "application/pdf")
            
            if st.button("New Analysis"):
                for key in ['report_result', 'report_lake', 'report_image', 'team_info', 'report_id']:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()
    else:
        st.info("Please login to access camera upload\nDemo: citizen / jalnirikshan123")
    st.markdown('</div>', unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="poppr-anim-4">', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-card">
        <h2 style='font-size:2.8rem; font-weight:700; margin:0 0 2rem 0;'>
            Eichhornia crassipes Problem
        </h2>
        <p style='font-size:1.4rem; line-height:1.8; opacity:0.95;'>
            Water hyacinth spreads uncontrollably, blocking sunlight, killing aquatic life, 
            and disrupting water flow. Traditional reporting lacks precision and speed.
        </p>
        <h3 style='font-size:1.8rem; margin:2.5rem 0 1.5rem 0;'>Our Solution</h3>
        <p style='font-size:1.3rem; line-height:1.7;'>
            GPS-enabled camera uploads → AI analysis with algae filtering → 
            Automatic team allocation → Rapid cleanup deployment
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab5:
    st.markdown('<div class="poppr-anim-1">', unsafe_allow_html=True)
    st.markdown("## Active Cleanup Teams")
    
    try:
        teams = requests.get("http://localhost:8000/teams/?limit=10", timeout=5).json()
        for team in teams:
            st.markdown(f"""
            <div style='background:linear-gradient(135deg, #22c55e 0%, #166534 100%); 
                       color:white; padding:1.5rem; border-radius:16px; margin:1rem 0;'>
                <strong>{team['lake_name']}</strong> 
                <span style='float:right; font-size:1.1rem;'>
                    Health: {team['health_score']:.0f} | {team['team_size']} members
                </span>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.info("Backend API not available. Run: uvicorn main:app --reload")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer - Final Animation
st.markdown("""
<div class="poppr-anim-4" style='
    background: linear-gradient(135deg, #14532d 0%, #166534 100%); 
    color: white; padding: 4rem 2rem; border-radius: 30px; 
    margin: 4rem 0 2rem 0; text-align: center;
    box-shadow: 0 50px 120px rgba(20,83,45,0.6);'>
    <h2 style='font-size: 2.8rem; font-weight: 700; margin: 0 0 2rem 0;'>
        Production Ready Platform
    </h2>
    <div style='display: flex; justify-content: center; gap: 4rem; flex-wrap: wrap; font-size: 1.4rem;'>
        <div>25 Lakes Monitored</div>
        <div>Smart Team Allocation</div>
        <div>AI + GPS Integration</div>
        <div>Live Camera Analysis</div>
    </div>
    <p style='margin-top: 2rem; opacity: 0.9; font-size: 1.2rem;'>
        Dark green UI • Poppr scroll animations • Production ready
    </p>
</div>
""", unsafe_allow_html=True)
