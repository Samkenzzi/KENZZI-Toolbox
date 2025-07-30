import math
import streamlit as st
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from itertools import permutations, product

# --- Constants ---
MAX_SIDE_MM = 600
PALLET_LENGTH_MM = 1219  # 48 inches
PALLET_WIDTH_MM = 1016   # 40 inches
PALLET_HEIGHT_MM = 1800
PALLET_BASE_HEIGHT_MM = 148
USABLE_HEIGHT_MM = PALLET_HEIGHT_MM - PALLET_BASE_HEIGHT_MM

# --- Material Options (thickness in mm) ---
MATERIAL_THICKNESS = {
    "B Flute (3 mm)": 3,
    "C Flute (4 mm)": 4,
    "E Flute (1.5 mm)": 1.5,
    "Double Wall (7 mm)": 7,
    "Custom": None
}

# --- Unit Conversion Functions ---
def mm_to_in(mm): return mm / 25.4

def in_to_mm(inch): return inch * 25.4

def kg_to_lb(kg): return kg * 2.20462

def lb_to_kg(lb): return lb / 2.20462

# --- Input Handler ---
def convert_inputs(length, width, height, weight, unit_system):
    if unit_system == "imperial":
        length = in_to_mm(length)
        width = in_to_mm(width)
        height = in_to_mm(height)
        weight = lb_to_kg(weight)
    return length, width, height, weight

# --- Configurable Stacking Function ---
def calculate_dimensions(config, dims):
    x, y, z = config
    return dims[0]*x, dims[1]*y, dims[2]*z

# --- Pallet Calculation ---
def pallet_fit(outer_L, outer_W, outer_H):
    per_layer = int(PALLET_LENGTH_MM // outer_L) * int(PALLET_WIDTH_MM // outer_W)
    layers = USABLE_HEIGHT_MM / outer_H
    return per_layer, int(layers), per_layer * int(layers)

# --- Visualization Functions ---
def draw_box(ax, origin, size, color='lightblue'):
    x, y, z = origin
    dx, dy, dz = size
    vertices = np.array([
        [x, y, z], [x+dx, y, z], [x+dx, y+dy, z], [x, y+dy, z],
        [x, y, z+dz], [x+dx, y, z+dz], [x+dx, y+dy, z+dz], [x, y+dy, z+dz]
    ])
    faces = [[vertices[j] for j in [0,1,2,3]],
             [vertices[j] for j in [4,5,6,7]],
             [vertices[j] for j in [0,1,5,4]],
             [vertices[j] for j in [2,3,7,6]],
             [vertices[j] for j in [1,2,6,5]],
             [vertices[j] for j in [4,7,3,0]]]
    box = Poly3DCollection(faces, facecolors=color, linewidths=0.5, edgecolors='gray', alpha=0.7)
    ax.add_collection3d(box)

def plot_stacking(config, unit_size, title):
    x_units, y_units, z_units = config
    L, W, H = unit_size
    fig = plt.figure(figsize=(6, 5))
    ax = fig.add_subplot(111, projection='3d')
    for i in range(x_units):
        for j in range(y_units):
            for k in range(z_units):
                origin = (i*L, j*W, k*H)
                draw_box(ax, origin, (L, W, H))
    ax.set_title(title)
    ax.set_xlabel('L')
    ax.set_ylabel('W')
    ax.set_zlabel('H')
    ax.set_box_aspect([x_units*L, y_units*W, z_units*H])
    return fig

# --- Streamlit Form Interface ---
st.title("📦 Packaging & Palletization Calculator")
with st.form("packaging_form"):
    unit_system = st.radio("Unit System", ["metric (mm, kg)", "imperial (in, lb)"])
    unit_system = "metric" if "metric" in unit_system else "imperial"

    st.markdown("### Product Unit Dimensions")
    length = st.number_input("Length (mm/in)", min_value=0.0, format="%.2f")
    width = st.number_input("Width (mm/in)", min_value=0.0, format="%.2f")
    height = st.number_input("Height (mm/in)", min_value=0.0, format="%.2f")
    weight = st.number_input("Weight (kg/lb)", min_value=0.0, format="%.3f")

    st.markdown("### Packaging Configuration")
    units_per_inner = st.number_input("Units per Inner Case", min_value=1, step=1)
    inners_per_outer = st.number_input("Inners per Outer Case", min_value=1, step=1)

    possible_inner_configs = [cfg for cfg in product(range(1, units_per_inner+1), repeat=3)
                              if cfg[0]*cfg[1]*cfg[2] == units_per_inner]
    possible_outer_configs = [cfg for cfg in product(range(1, inners_per_outer+1), repeat=3)
                              if cfg[0]*cfg[1]*cfg[2] == inners_per_outer]

    st.markdown("### Inner Configuration (L x W x H)")
    inner_config = st.selectbox("Select stacking of units in Inner Case", possible_inner_configs)

    st.markdown("### Outer Configuration (L x W x H)")
    outer_config = st.selectbox("Select stacking of inners in Outer Case", possible_outer_configs)

    st.markdown("### Inner Case Material Thickness")
    inner_type = st.selectbox("Inner Case Material", list(MATERIAL_THICKNESS.keys()), key="inner")
    inner_thickness = MATERIAL_THICKNESS[inner_type] if MATERIAL_THICKNESS[inner_type] is not None else st.number_input("Custom Inner Thickness (mm)", min_value=0.0, format="%.2f", key="inner_custom")

    st.markdown("### Outer Case Material Thickness")
    outer_type = st.selectbox("Outer Case Material", list(MATERIAL_THICKNESS.keys()), key="outer")
    outer_thickness = MATERIAL_THICKNESS[outer_type] if MATERIAL_THICKNESS[outer_type] is not None else st.number_input("Custom Outer Thickness (mm)", min_value=0.0, format="%.2f", key="outer_custom")

    submit = st.form_submit_button("Calculate")

if submit:
    try:
        length, width, height, weight = convert_inputs(length, width, height, weight, unit_system)
        inner_L, inner_W, inner_H = calculate_dimensions(inner_config, (length, width, height))
        inner_dims = (inner_L + 2*inner_thickness, inner_W + 2*inner_thickness, inner_H + 2*inner_thickness)
        outer_L, outer_W, outer_H = calculate_dimensions(outer_config, inner_dims)
        outer_dims = (outer_L + 2*outer_thickness, outer_W + 2*outer_thickness, outer_H + 2*outer_thickness)

        inner_weight = weight * units_per_inner
        outer_weight = inner_weight * inners_per_outer

        per_layer, layers, total_cartons = pallet_fit(*outer_dims)
        total_units_per_pallet = total_cartons * units_per_inner * inners_per_outer

        st.success("✅ Calculation completed.")

        st.markdown("---")
        st.header("📏 Summary of Dimensions and Weights")

        st.subheader("Inner Case")
        st.write(f"Dimensions: {inner_dims} mm / {[round(mm_to_in(v), 2) for v in inner_dims]} in")
        st.write(f"Weight: {inner_weight:.2f} kg / {kg_to_lb(inner_weight):.2f} lb")

        st.subheader("Outer Case")
        st.write(f"Dimensions: {outer_dims} mm / {[round(mm_to_in(v), 2) for v in outer_dims]} in")
        st.write(f"Weight: {outer_weight:.2f} kg / {kg_to_lb(outer_weight):.2f} lb")

        st.subheader("Palletization")
        st.write({"cartons_per_layer": per_layer, "layers": layers, "total_cartons": total_cartons, "total_units": total_units_per_pallet})

        st.subheader("Stacking Configuration")
        st.write({"inner_config": inner_config, "outer_config": outer_config})

        st.pyplot(plot_stacking(inner_config, (length, width, height), "Unit → Inner Case"))
        st.pyplot(plot_stacking(outer_config, inner_dims, "Inner → Outer Case"))

    except ValueError as e:
        st.error(str(e))
