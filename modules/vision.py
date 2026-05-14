import os
from typing import Dict


def measure_from_image(image_bytes: bytes, project_name: str) -> Dict[str, float]:
    """
    Placeholder vision module.

    - Saves the image under data/projects as reference.
    - Returns zero measurements for now.
    - Later you can replace this with a real vision model.
    """
    os.makedirs(os.path.join("data", "projects"), exist_ok=True)
    safe_name = project_name.replace(" ", "_")
    img_path = os.path.join("data", "projects", f"{safe_name}_vision.jpg")

    with open(img_path, "wb") as f:
        f.write(image_bytes)

    # Placeholder values – replace with real AI logic later
    return {
        "length_ft": 0.0,
        "width_ft": 0.0,
        "depth_in": 0.0,
    }
