import os
import datetime
import requests
import json
from math import ceil

import streamlit as st

from modules.calculations import (
    calculate_area,
    calculate_volume,
    calculate_tons,
)
from modules.database import (
    init_db,
    save_project,
    get_projects,
    delete_project,
    restore_project,
)
from modules.vision import measure_from_image

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="PREFERRED MATERIAL INC – AI FIELD SUITE",
    layout="centered",
)

# Ensure DB exists
init_db()

# ----------------------------------------------------
# AUTH
# ----------------------------------------------------
VALID_USERS = {
    "preferred": {
        "password": "material123",
        "license_until": "2027-12-31",
    }
}

def check_login(user: str, pwd: str):
    data = VALID_USERS.get(user)
    if not data:
        return False, "User not found."

    if data["password"] != pwd:
        return False, "Invalid password."

    today = datetime.date.today()
    exp = datetime.datetime.strptime(data["license_until"], "%Y-%m-%d").date()
    if today > exp:
        return False, "Company license expired."

    return True, "OK"


if "auth" not in st.session_state:
    st.session_state.auth = False

# ----------------------------------------------------
# LOGIN UI
# ----------------------------------------------------
st.markdown(
    """
    <style>
    body { background-color: #111111; }
    .main { background-color: #111111; }
    .big-title {
        font-size: 40px; font-weight: 800; color: #00ff55;
        text-align: center; letter-spacing: 1px; font-style: italic;
    }
    .sub-title {
        text-align: center; color: #cccccc; font-size: 16px; font-style: italic;
    }
    .section-title {
        font-size: 22px; font-weight: 700; color: #00ff55;
        margin-top: 10px; font-style: italic;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='big-title'>PREFERRED MATERIAL INC – AI FIELD SUITE</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Asphalt Tonnage & Logistics Engine</div>", unsafe_allow_html=True)

login_image_path = os.path.join("assets", "photos", "login.jpg")
if os.path.exists(login_image_path):
    st.image(login_image_path, use_container_width=True)

st.markdown("### Login")

col_login1, col_login2 = st.columns(2)
with col_login1:
    user = st.text_input("User Name")
with col_login2:
    pwd = st.text_input("Password", type="password")

if st.button("LOGIN"):
    ok, msg = check_login(user, pwd)
    if ok:
        st.session_state.auth = True
        st.success("Access granted.")
    else:
        st.session_state.auth = False
        st.error(msg)

if not st.session_state.auth:
    st.stop()

st.markdown("---")

# ----------------------------------------------------
# SESSION STATE INIT
# ----------------------------------------------------
defaults = {
    "area": 0.0,
    "volume": 0.0,
    "base_tons": 0.0,
    "total_tons": 0.0,
    "ai_loads": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------------------------------
# WEATHER — GPS AUTOMÁTICO + FALLBACK
# ----------------------------------------------------
st.markdown("<div class='section-title'>🌦️ Weather Conditions</div>", unsafe_allow_html=True)

gps_js = """
<script>
navigator.geolocation.getCurrentPosition(
    function(pos) {
        const coords = {
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude
        };
        const query = new URLSearchParams(window.location.search);
        query.set("gps", JSON.stringify(coords));
        window.location.search = query.toString();
    },
    function(err) {
        const query = new URLSearchParams(window.location.search);
        query.set("gps_error", err.message);
        window.location.search = query.toString();
    }
);
</script>
"""

st.components.v1.html(gps_js, height=0)

gps_raw = st.query_params.get("gps", None)


lat = None
lon = None

if gps_raw:
    try:
        gps = json.loads(gps_raw)
        lat = gps["latitude"]
        lon = gps["longitude"]
    except:
        lat = None
        lon = None

if st.button("CHECK WEATHER"):

    if lat and lon:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&current_weather=true"
        )
        data = requests.get(url).json()
        w = data["current_weather"]
        temp_c = w["temperature"]
        temp_f = temp_c * 9 / 5 + 32

        colw1, colw2, colw3 = st.columns(3)
        with colw1:
            st.metric("Location", "GPS Position")
        with colw2:
            st.metric("Temperature (°F)", f"{temp_f:.1f}")
        with colw3:
            st.metric("Wind Speed", f"{w['windspeed']} mph")

        rain_codes = [51, 53, 55, 61, 63, 65, 80, 81, 82]
        if w["weathercode"] in rain_codes:
            st.error("⚠️ Rain approaching / raining in the area.")
        else:
            st.success("✅ No rain detected nearby.")

    else:
        st.warning("GPS unavailable. Enter your city manually.")
        city = st.text_input("City (e.g., Tampa, FL)")
        if city:
            geo = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
            ).json()

            if "results" in geo:
                lat = geo["results"][0]["latitude"]
                lon = geo["results"][0]["longitude"]

                url = (
                    "https://api.open-meteo.com/v1/forecast"
                    f"?latitude={lat}&longitude={lon}&current_weather=true"
                )
                data = requests.get(url).json()
                w = data["current_weather"]
                temp_c = w["temperature"]
                temp_f = temp_c * 9 / 5 + 32

                colw1, colw2, colw3 = st.columns(3)
                with colw1:
                    st.metric("Location", city)
                with colw2:
                    st.metric("Temperature (°F)", f"{temp_f:.1f}")
                with colw3:
                    st.metric("Wind Speed", f"{w['windspeed']} mph")

                rain_codes = [51, 53, 55, 61, 63, 65, 80, 81, 82]
                if w["weathercode"] in rain_codes:
                    st.error("⚠️ Rain approaching / raining in the area.")
                else:
                    st.success("✅ No rain detected nearby.")
            else:
                st.error("City not found.")

st.markdown("---")

# ----------------------------------------------------
# PROJECT MEASUREMENTS
# ----------------------------------------------------
st.markdown("<div class='section-title'>📏 Project Measurements</div>", unsafe_allow_html=True)

project_name = st.text_input("Project Name")

colA, colB, colC = st.columns(3)
with colA:
    length_ft = st.number_input("Length (ft)", min_value=0.0, value=0.0)
with colB:
    width_ft = st.number_input("Width (ft)", min_value=0.0, value=0.0)
with colC:
    depth_in = st.number_input("Depth (in)", min_value=0.0, value=0.0)

if st.button("RESET / CLEAR PROJECT"):
    for k in defaults.keys():
        st.session_state[k] = defaults[k]
    st.experimental_rerun()

st.markdown("---")

# ----------------------------------------------------
# TRUCK & MATERIAL SETTINGS
# ----------------------------------------------------
st.markdown("<div class='section-title'>🚚 Truck & Material Settings</div>", unsafe_allow_html=True)

colT1, colT2, colT3 = st.columns(3)
with colT1:
    truck_capacity = st.number_input("Truck Capacity (tons)", value=21.0, min_value=1.0)
with colT2:
    manual_trucks = st.number_input("Manual Trucks Planned", min_value=0, value=0)
with colT3:
    extra_tons = st.number_input("Extra Tons (correction)", min_value=0.0, value=0.0)

st.markdown("---")

# ----------------------------------------------------
# CALCULATE
# ----------------------------------------------------
if st.button("CALCULATE"):
    if project_name.strip() == "":
        st.error("Project Name is required.")
    elif length_ft <= 0 or width_ft <= 0 or depth_in <= 0:
        st.error("All dimensions must be greater than zero.")
    else:
        area = calculate_area(length_ft, width_ft)
        volume = calculate_volume(area, depth_in)
        base_tons = calculate_tons(volume)
        total_tons = base_tons + extra_tons
        ai_loads = ceil(total_tons / truck_capacity)

        st.session_state.area = area
        st.session_state.volume = volume
        st.session_state.base_tons = base_tons
        st.session_state.total_tons = total_tons
        st.session_state.ai_loads = ai_loads

        save_project(
            {
                "project_name": project_name,
                "length_ft": length_ft,
                "width_ft": width_ft,
                "depth_in": depth_in,
                "area_sqft": area,
                "volume_cuft": volume,
                "tons": total_tons,
            }
        )

        st.success("Calculation complete.")

# DISPLAY RESULTS
st.markdown("### 📊 Results")
colR1, colR2, colR3 = st.columns(3)
with colR1:
    st.metric("Area", f"{st.session_state.area:.2f} sq ft")
with colR2:
    st.metric("Volume", f"{st.session_state.volume:.2f} cu ft")
with colR3:
    st.metric("Base Tons", f"{st.session_state.base_tons:.2f}")

colR4, colR5, colR6 = st.columns(3)
with colR4:
    st.metric("Extra Tons", f"{extra_tons:.2f}")
with colR5:
    st.metric("Total Tons (AI)", f"{st.session_state.total_tons:.2f}")
with colR6:
    st.metric("AI Required Loads", st.session_state.ai_loads)

st.markdown("### 🧠 AI Decision Engine")
if manual_trucks > 0 and st.session_state.ai_loads > 0:
    diff = manual_trucks - st.session_state.ai_loads
    if diff > 0:
        st.error(f"Manual order has {diff} extra truck(s).")
    elif diff < 0:
        st.warning(f"Manual order is short by {abs(diff)} truck(s).")
    else:
        st.success("Manual order matches AI calculation.")
else:
    st.info("Enter manual truck count to compare AI vs Manual.")

# ----------------------------------------------------
# AI VISION MODE
# ----------------------------------------------------
st.markdown("---")
st.markdown("<div class='section-title'>🤖📷 AI VISION MODE</div>", unsafe_allow_html=True)

photo = st.camera_input("Capture project area")

if photo and project_name.strip() != "":
    st.success("Image captured.")
    image_bytes = photo.getvalue()
    ai_measures = measure_from_image(image_bytes, project_name)

    colV1, colV2, colV3 = st.columns(3)
    with colV1:
        st.number_input("AI Length (ft)", value=float(ai_measures["length_ft"]), disabled=True)
    with colV2:
        st.number_input("AI Width (ft)", value=float(ai_measures["width_ft"]), disabled=True)
    with colV3:
        st.number_input("AI Depth (in)", value=float(ai_measures["depth_in"]), disabled=True)

    if st.button("USE AI MEASUREMENTS"):
        st.info("AI measurements placeholder applied (currently zeros).")
else:
    if photo and project_name.strip() == "":
        st.warning("Set a Project Name before capturing AI Vision images.")

# ----------------------------------------------------
# PROJECT HISTORY
# ----------------------------------------------------
st.markdown("---")
st.markdown("<div class='section-title'>📂 Project History</div>", unsafe_allow_html=True)

projects = get_projects(active_only=True)

if not projects:
    st.info("No projects saved.")
else:
    for p in projects:
        pid, name, L, W, D, A, V, T, deleted, created_at = p
        colH1, colH2 = st.columns([4, 1])
        with colH1:
            st.write(f"🚧 **{name}** | TONS: **{T:.2f}** | L:{L} W:{W} D:{D} | {created_at}")
        with colH2:
            if st.button("🗑️ Delete", key=f"del_{pid}"):
                delete_project(pid)
                st.warning(f"Project '{name}' moved to Trash.")
                st.experimental_rerun()

# ----------------------------------------------------
# TRASH / RECOVERY
# ----------------------------------------------------
st.markdown("---")
st.markdown("<div class='section-title'>🗑️ Trash (Recover Projects)</div>", unsafe_allow_html=True)

trash = get_projects(active_only=False, deleted_only=True)

if not trash:
    st.info("Trash is empty.")
else:
    for p in trash:
        pid, name, L, W, D, A, V, T, deleted, created_at = p
        colTr1, colTr2 = st.columns([4, 1])
        with colTr1:
            st.write(f"🗂️ {name} | TONS: {T:.2f} | {created_at}")
        with colTr2:
            if st.button("♻️ Restore", key=f"restore_{pid}"):
                restore_project(pid)
                st.success(f"Project '{name}' restored.")
                st.experimental_rerun()

