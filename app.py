import streamlit as st
import pandas as pd
import plotly.express as px
import db
import aurora
from datetime import datetime

# Initialize Database
db.init_db()

# --- Page Setup ---
st.set_page_config(
    page_title="Aurora 🌌 Space Weather Dashboard",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Theme Styling (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');
    
    /* Main body background & fonts */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif;
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Gradient title text */
    .title-gradient {
        background: linear-gradient(90deg, #a855f7, #6366f1, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 5px;
        font-family: 'Space Grotesk', sans-serif;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .title-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 25px;
        font-weight: 400;
    }
    
    /* Sidebar aesthetic adjustments */
    [data-testid="stSidebar"] {
        background-color: #0d1220 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Glassmorphism metrics card styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(20, 30, 55, 0.6), rgba(10, 15, 30, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 16px 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.35);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
    }
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        font-family: 'Space Grotesk', sans-serif;
        color: #f8fafc !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
    }
    
    /* Clean custom tabs */
    button[data-baseweb="tab"] {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        color: #94a3b8;
        border-bottom-width: 2px;
        transition: all 0.2s ease;
    }
    button[data-baseweb="tab"]:hover {
        color: #e2e8f0;
    }
    button[aria-selected="true"] {
        color: #6366f1 !important;
        border-color: #6366f1 !important;
    }
    
    /* High-end executive briefing panel */
    .briefing-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.07), rgba(168, 85, 247, 0.07));
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-left: 5px solid #6366f1;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(5px);
        margin-bottom: 25px;
    }
    
    .briefing-title {
        margin-top: 0;
        color: #a855f7;
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .briefing-text {
        font-size: 1.1rem;
        line-height: 1.65;
        color: #e2e8f0;
        margin-bottom: 0;
    }
    
    /* Custom severity display */
    .severity-card {
        background: linear-gradient(135deg, #101428, #180c2c);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100%;
        min-height: 160px;
    }
    
    .severity-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #a855f7;
        font-weight: bold;
        margin-bottom: 8px;
    }
    
    .severity-number {
        font-size: 3.8rem;
        font-weight: 800;
        color: #f43f5e;
        font-family: 'Space Grotesk', sans-serif;
        line-height: 1;
    }
    
    .severity-scale {
        font-size: 1.3rem;
        color: rgba(255, 255, 255, 0.35);
        font-weight: 400;
    }
    
    /* Status Badge styling */
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 50px;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        margin-top: 10px;
        border: 1px solid;
    }
    
    .status-badge-Quiet {
        background-color: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border-color: rgba(16, 185, 129, 0.25);
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.1);
    }
    .status-badge-Unsettled {
        background-color: rgba(245, 158, 11, 0.1);
        color: #f59e0b;
        border-color: rgba(245, 158, 11, 0.25);
        box-shadow: 0 0 15px rgba(245, 158, 11, 0.1);
    }
    .status-badge-Storm {
        background-color: rgba(249, 115, 22, 0.1);
        color: #f97316;
        border-color: rgba(249, 115, 22, 0.25);
        box-shadow: 0 0 15px rgba(249, 115, 22, 0.1);
    }
    .status-badge-Severe {
        background-color: rgba(239, 68, 68, 0.1);
        color: #ef4444;
        border-color: rgba(239, 68, 68, 0.25);
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.1);
    }
    
    /* Action button design override */
    div.stButton > button {
        background: linear-gradient(135deg, #6366f1, #a855f7) !important;
        color: white !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
        width: 100%;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        transform: translateY(-1.5px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
    }
    
    /* Clean custom horizontal dividers */
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, rgba(99, 102, 241, 0), rgba(99, 102, 241, 0.3) 50%, rgba(99, 102, 241, 0));
        margin: 25px 0;
    }
    
    /* Footer elements */
    .footer-text {
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
        margin-top: 40px;
        padding: 20px 0;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- Header Section ---
st.markdown('<div class="title-gradient">🌌 Aurora Space Weather</div>', unsafe_allow_html=True)
st.markdown('<div class="title-subtitle">NOAA Deep Space Telemetry & Gemini AI Analytical Cockpit</div>', unsafe_allow_html=True)

# --- Session State Setup ---
if 'selected_report_id' not in st.session_state:
    latest_id = db.get_latest_report_id()
    if latest_id:
        st.session_state.selected_report_id = latest_id
    else:
        st.session_state.selected_report_id = None

# --- Sidebar Controls ---
st.sidebar.markdown("### ⚡ Run Space Weather Report")
st.sidebar.markdown("Fetch real-time space weather data from NOAA and generate an executive Gemini AI briefing.")

days_to_pull = st.sidebar.slider(
    "Observation Window (Days)",
    min_value=1,
    max_value=7,
    value=3,
    help="Select the range of historical data to pull from NOAA for real-time telemetry."
)

if st.sidebar.button("Generate New Report"):
    with st.status("Connecting to NOAA SWPC endpoints...", expanded=True) as status_box:
        try:
            status_box.update(label="Downloading Planetary Kp Index data...", state="running")
            # Fetching happens within aurora.run()
            status_box.update(label="Retrieving Propagated Solar Wind readings...", state="running")
            # Fetching happens within aurora.run()
            status_box.update(label="Scanning GOES X-ray Flux & detecting Solar Flares...", state="running")
            # Fetching happens within aurora.run()
            status_box.update(label="Consulting Gemini-2.5-Flash space analyst...", state="running")
            
            # Run data pipeline
            new_id = aurora.run(days=days_to_pull)
            
            status_box.update(label="Report successfully written to database!", state="complete", expanded=False)
            st.sidebar.success(f"Report #{new_id} generated!")
            
            # Update session state to display the newly generated report
            st.session_state.selected_report_id = new_id
            st.rerun()
            
        except Exception as e:
            status_box.update(label="Error generating report", state="error", expanded=True)
            st.sidebar.error(f"Execution failed: {e}")

st.sidebar.markdown('<div style="height:15px"></div>', unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Historical Briefings")

all_reports = db.get_reports(limit=30)

if not all_reports:
    st.info("No space weather briefings found in local storage. Use the controls above to trigger your first real-time report analysis!")
    st.stop()

# Build dictionary for report selector
report_options = {r['id']: f"Report #{r['id']} ({r['created_at']} UTC)" for r in all_reports}
options_keys = list(report_options.keys())

# Determine current selectbox index based on session state
if st.session_state.selected_report_id in options_keys:
    default_index = options_keys.index(st.session_state.selected_report_id)
else:
    default_index = 0
    st.session_state.selected_report_id = options_keys[0]

def handle_report_selection():
    st.session_state.selected_report_id = st.session_state.temp_selected_report_id

selected_id = st.sidebar.selectbox(
    "Select Report to View",
    options=options_keys,
    format_func=lambda x: report_options[x],
    index=default_index,
    key="temp_selected_report_id",
    on_change=handle_report_selection
)

# --- Data Fetching for Selected Report ---
report = db.get_report(st.session_state.selected_report_id)

if not report:
    st.warning("Selected report could not be found. Re-syncing database...")
    st.session_state.selected_report_id = db.get_latest_report_id()
    st.rerun()

kp_data = db.get_report_kp(st.session_state.selected_report_id)
wind_data = db.get_report_wind(st.session_state.selected_report_id)
flares = db.get_report_flares(st.session_state.selected_report_id)

# --- Dashboard Layout ---

# 1. Executive Briefing Header Row
col_briefing, col_severity = st.columns([3, 1])

with col_briefing:
    st.markdown(f"""
    <div class="briefing-card">
        <div class="briefing-title">
            <span>🌌 AI Executive Space Weather Briefing</span>
        </div>
        <p class="briefing-text">{report['briefing']}</p>
    </div>
    """, unsafe_allow_html=True)

with col_severity:
    status_class = f"status-badge-{report['status']}"
    st.markdown(f"""
    <div class="severity-card">
        <div class="severity-label">Severity Index</div>
        <div class="severity-number">
            {int(report['severity_score'])}<span class="severity-scale">/10</span>
        </div>
        <div class="status-badge {status_class}">
            {report['status']} Status
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# 2. Key Telemetry Metrics Grid
st.subheader("📊 Key Telemetry Summary")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

# Calculate stats
kp_vals = [r['kp_index'] for r in kp_data if r['kp_index'] is not None]
wind_speeds = [r['speed'] for r in wind_data if r['speed'] is not None]

max_kp = max(kp_vals) if kp_vals else 0.0
avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0.0
max_wind = max(wind_speeds) if wind_speeds else 0.0

x_flares = sum(1 for f in flares if f['flare_class'] and f['flare_class'].startswith('X'))
m_flares = sum(1 for f in flares if f['flare_class'] and f['flare_class'].startswith('M'))
c_flares = sum(1 for f in flares if f['flare_class'] and f['flare_class'].startswith('C'))

# Render standard metrics with our glassmorphic CSS overrides
kpi1.metric(
    label="Max Kp Index", 
    value=f"{max_kp:.2f}",
    help="Geomagnetic activity index. Kp ≥ 5 indicates a geomagnetic storm."
)
kpi2.metric(
    label="Peak Solar Wind", 
    value=f"{max_wind:.0f} km/s" if max_wind > 0 else "0 km/s",
    delta=f"Avg: {avg_wind:.0f} km/s" if avg_wind > 0 else None,
    delta_color="normal",
    help="Speed of the solar plasma wind stream. Higher speeds hit Earth magnetosphere harder."
)
kpi3.metric(
    label="Major Solar Flares", 
    value=f"{x_flares + m_flares}",
    delta=f"{x_flares} X-class | {m_flares} M-class",
    delta_color="off",
    help="Total of high-energy X-class and M-class solar flares detected."
)
kpi4.metric(
    label="Total Flares Detected", 
    value=f"{len(flares)}",
    delta=f"{c_flares} C-class",
    delta_color="off",
    help="All detected solar flares exceeding the background C-class threshold (1e-6 W/m²)."
)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

# 3. Telemetry Visualizations & Reports Tabs
st.subheader("📈 Space Weather Visualizations")
tab_kp, tab_wind, tab_flares = st.tabs([
    "🌌 Planetary Kp Index", 
    "💨 Propagated Solar Wind", 
    "💥 Solar Flare Events"
])

# Plotly styling utility
def style_plotly_layout(fig, title, y_label):
    fig.update_layout(
        title={
            'text': title,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'family': 'Space Grotesk', 'size': 18, 'color': '#f8fafc'}
        },
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='#94a3b8',
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(
            gridcolor='rgba(255, 255, 255, 0.05)',
            linecolor='rgba(255, 255, 255, 0.1)',
            tickfont=dict(family='Outfit', size=11, color='#94a3b8')
        ),
        yaxis=dict(
            title=dict(
                text=y_label,
                font=dict(family='Space Grotesk', size=12, color='#94a3b8')
            ),
            gridcolor='rgba(255, 255, 255, 0.05)',
            linecolor='rgba(255, 255, 255, 0.1)',
            tickfont=dict(family='Outfit', size=11, color='#94a3b8')
        ),
        hoverlabel=dict(
            bgcolor='#0f172a',
            bordercolor='rgba(255, 255, 255, 0.1)',
            font_family='Outfit'
        )
    )

with tab_kp:
    if kp_data:
        df_kp = pd.DataFrame(kp_data)
        df_kp['time_tag'] = pd.to_datetime(df_kp['time_tag'])
        
        fig_kp = px.line(
            df_kp, 
            x='time_tag', 
            y='kp_index', 
            markers=True,
            color_discrete_sequence=['#a855f7']
        )
        
        # Color storm level band (Kp >= 5 is minor storm and above)
        fig_kp.add_hrect(
            y0=5, y1=9, 
            line_width=0, 
            fillcolor="#ef4444", 
            opacity=0.12, 
            annotation_text="Storm Warning threshold (Kp ≥ 5)", 
            annotation_position="top left",
            annotation_font_color="#ef4444",
            annotation_font_family="Space Grotesk"
        )
        
        style_plotly_layout(fig_kp, "Planetary K-Index Geomagnetic Telemetry", "Kp Index Value")
        fig_kp.update_yaxes(range=[0, 9.2])
        fig_kp.update_traces(
            line=dict(width=3), 
            marker=dict(size=8, symbol='circle', opacity=0.8)
        )
        
        st.plotly_chart(fig_kp, use_container_width=True)
    else:
        st.info("No geomagnetic Kp index readings stored for this briefing.")

with tab_wind:
    if wind_data:
        df_wind = pd.DataFrame(wind_data)
        df_wind['time_tag'] = pd.to_datetime(df_wind['time_tag'])
        
        fig_wind = px.line(
            df_wind, 
            x='time_tag', 
            y='speed',
            color_discrete_sequence=['#06b6d4']
        )
        
        style_plotly_layout(fig_wind, "NOAA Solar Wind Speed Telemetry", "Solar Wind Speed (km/s)")
        fig_wind.update_traces(line=dict(width=2.5))
        
        st.plotly_chart(fig_wind, use_container_width=True)
        
        # Additional Wind metrics (Density and Temp) inside an expander
        with st.expander("🔬 View Expanded Plasma Density & Temperature Telemetry"):
            col_d, col_t = st.columns(2)
            with col_d:
                fig_d = px.line(df_wind, x='time_tag', y='density', color_discrete_sequence=['#10b981'])
                style_plotly_layout(fig_d, "Solar Wind Plasma Density", "Proton Density (N/cm³)")
                st.plotly_chart(fig_d, use_container_width=True)
            with col_t:
                fig_t = px.line(df_wind, x='time_tag', y='temperature', color_discrete_sequence=['#ec4899'])
                style_plotly_layout(fig_t, "Solar Wind Temperature", "Ion Temperature (K)")
                st.plotly_chart(fig_t, use_container_width=True)
    else:
        st.info("No solar wind telemetry stored for this briefing.")

with tab_flares:
    if flares:
        st.markdown("### Detected Solar Flare Events")
        st.markdown("These high-energy solar emissions are detected from GOES satellite X-ray sensors. Significant flares (X & M-class) can trigger radio blackouts on Earth.")
        
        df_flares = pd.DataFrame(flares)
        
        # Prettify table representation
        df_disp = df_flares[['flare_class', 'begin_time', 'peak_time', 'end_time', 'max_flux']].copy()
        df_disp.columns = ['Flare Class', 'Begin Time (UTC)', 'Peak Time (UTC)', 'End Time (UTC)', 'Max Flux (W/m²)']
        
        # Display as elegant dataframe
        st.dataframe(
            df_disp.style.format({'Max Flux (W/m²)': '{:.2e}'}).set_properties(**{
                'background-color': '#0d1220',
                'color': '#f1f5f9',
                'border-color': 'rgba(255, 255, 255, 0.05)'
            }), 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No solar flare events exceeding the background C-class threshold were detected during this observational period.")

# --- Footer Section ---
st.markdown(f"""
<div class="footer-text">
    🌌 Aurora Dashboard | Observation Window: {report['days_requested']} Days | Generated: {report['created_at']} UTC | Telemetry via NOAA SWPC & Gemini AI
</div>
""", unsafe_allow_html=True)
