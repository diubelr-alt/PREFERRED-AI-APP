def calculate_area(length_ft: float, width_ft: float) -> float:
    """
    Calculate area in square feet.
    """
    return float(length_ft) * float(width_ft)


def calculate_volume(area_sqft: float, depth_in: float) -> float:
    """
    Calculate volume in cubic feet.
    depth_in is in inches, converted to feet.
    """
    depth_ft = float(depth_in) / 12.0
    return float(area_sqft) * depth_ft


def calculate_tons(volume_cuft: float, density: float = 13.79) -> float:
    """
    Convert volume (cubic feet) to tons using material density.
    Default density ~13.79 cu ft/ton for hot mix asphalt.
    """
    if density <= 0:
        raise ValueError("Density must be greater than zero.")
    return float(volume_cuft) / float(density)
