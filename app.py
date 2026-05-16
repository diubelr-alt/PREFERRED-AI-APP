import io
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from ultralytics import YOLO

# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(page_title="AI Measure Asphalt", layout="wide")

st.title("AI Measure – A→B / B→C con Depth (in) y Tons")
st.caption("Cámara + YOLO + Visualización manual de colores. Sin weather. Versión final.")

# =========================
# CARGA MODELO YOLO
# =========================
@st.cache_resource
def load_model():
    try:
        model = YOLO("measure_model.pt")  # Debe estar en la misma carpeta
        return model
    except Exception as e:
        st.error(f"No se pudo cargar measure_model.pt: {e}")
        return None

model = load_model()

# =========================
# HELPERS
# =========================
def feet_to_feet_inches(feet_value: float):
    total_inches = round(feet_value * 12)
    ft = total_inches // 12
    inch = total_inches % 12
    return f"{int(ft)}' {int(inch)}\""

def distance_pixels(p1, p2):
    return float(np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2))

def hex_to_bgr(hex_color):
    hex_color = hex_color.lstrip('#')
    return (int(hex_color[4:6], 16), int(hex_color[2:4], 16), int(hex_color[0:2], 16))

# =========================
# CORE: MEDIR DESDE IMAGEN
# =========================
def measure_from_image(image_bytes: bytes, depth_in: float,
                       color_AB, color_BC, text_color, line_thickness):
    if model is None:
        return None, "Modelo YOLO no cargado."

    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    results = model(img)[0]

    tape_box = None
    markers = []

    for box in results.boxes:
        cls = int(box.cls[0])
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2

        if cls == 0:
            tape_box = (x1, y1, x2, y2)
        elif cls in [1, 2, 3]:
            markers.append((cx, cy, cls))

    if tape_box is None:
        return None, "No se detectó la cinta (clase 0)."

    if len(markers) < 3:
        return None, "No se detectaron A, B y C."

    tx1, ty1, tx2, ty2 = tape_box
    tape_pixels = abs(tx2 - tx1)
    if tape_pixels <= 0:
        return None, "Error en la detección de la cinta."

    pixels_per_foot = tape_pixels / 1.0

    A = next((m for m in markers if m[2] == 1), None)
    B = next((m for m in markers if m[2] == 2), None)
    C = next((m for m in markers if m[2] == 3), None)

    if A is None or B is None or C is None:
        return None, "Faltan marcadores A, B o C."

    Ax, Ay, _ = A
    Bx, By, _ = B
    Cx, Cy, _ = C

    px_len = distance_pixels((Ax, Ay), (Bx, By))
    px_wid = distance_pixels((Bx, By), (Cx, Cy))

    length_ft = px_len / pixels_per_foot
    width_ft = px_wid / pixels_per_foot

    draw_img = img.copy()

    # Convertir colores
    colAB = hex_to_bgr(color_AB)
    colBC = hex_to_bgr(color_BC)
    colTXT = hex_to_bgr(text_color)

    # Dibujar puntos
    for (x, y, cls) in [A, B, C]:
        cv2.circle(draw_img, (int(x), int(y)), 10, (0, 255, 255), -1)
        label = "A" if cls == 1 else "B" if cls == 2 else "C"
        cv2.putText(draw_img, label, (int(x)+5, int(y)-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # Líneas
    text_len = feet_to_feet_inches(length_ft)
    text_wid = feet_to_feet_inches(width_ft)

    midAB = (int((Ax + Bx) / 2), int((Ay + By) / 2))
    midBC = (int((Bx + Cx) / 2), int((By + Cy) / 2))

    cv2.line(draw_img, (int(Ax), int(Ay)), (int(Bx), int(By)), colAB, line_thickness)
    cv2.putText(draw_img, text_len, (midAB[0]+5, midAB[1]-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, colTXT, 3)

    cv2.line(draw_img, (int(Bx), int(By)), (int(Cx), int(Cy)), colBC, line_thickness)
    cv2.putText(draw_img, text_wid, (midBC[0]+5, midBC[1]-5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, colTXT, 3)

    draw_img_rgb = cv2.cvtColor(draw_img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(draw_img_rgb)
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)

    result = {
        "length_ft": round(length_ft, 2),
        "width_ft": round(width_ft, 2),
        "depth_in": round(depth_in, 2)
    }

    return (buf, result), None

# =========================
# UI PRINCIPAL
# =========================
st.subheader("Opciones de visualización manual")

color_AB = st.color_picker("Color línea A→B", "#00FF00")
color_BC = st.color_picker("Color línea B→C", "#00FFFF")
text_color = st.color_picker("Color del texto", "#FFFFFF")
line_thickness = st.slider("Grosor de línea", 2, 10, 4)

if st.button("Reset Colors"):
    color_AB = "#00FF00"
    color_BC = "#00FFFF"
    text_color = "#FFFFFF"

st.subheader("Modos extra")
modo = st.radio("Modo visual:", ["Normal", "High Contrast", "Night Vision"])

if modo == "High Contrast":
    color_AB = "#FFFFFF"
    color_BC = "#000000"
    text_color = "#FF0000"

elif modo == "Night Vision":
    color_AB = "#00FF00"
    color_BC = "#00FF00"
    text_color = "#00FF00"

col_left, col_right = st.columns([1, 1])

with col_left:
    depth_in = st.number_input("Depth (in)", min_value=0.0, max_value=24.0, value=3.0, step=0.25)

    img_file = st.camera_input("Tomar foto del tramo (con cinta + A/B/C visibles)")

    if img_file is not None:
        image_bytes = img_file.getvalue()
        with st.spinner("Procesando imagen..."):
            output, err = measure_from_image(
                image_bytes, depth_in,
                color_AB, color_BC, text_color, line_thickness
            )

        if err:
            st.error(err)
        else:
            buf, measures = output
            st.success("Medición completada.")
            st.write(f"**Length (ft):** {measures['length_ft']}")
            st.write(f"**Width (ft):** {measures['width_ft']}")
            st.write(f"**Depth (in):** {measures['depth_in']}")

            length_ft = measures["length_ft"]
            width_ft = measures["width_ft"]
            depth_ft = measures["depth_in"] / 12.0

            area_sqft = length_ft * width_ft
            volume_cuft = area_sqft * depth_ft
            tons = volume_cuft * 0.0725

            st.write(f"**Área (sq ft):** {round(area_sqft, 2)}")
            st.write(f"**Volumen (ft³):** {round(volume_cuft, 2)}")
            st.write(f"**Tons (aprox):** {round(tons, 2)}")

with col_right:
    st.subheader("Vista AI")
    if img_file is not None and not err:
        st.image(buf, caption="Medición AI", use_column_width=True)
