"""best-buds-chair v1 — woman + dog patio chair diorama."""

from bambu.cad.archetypes.seated_diorama import DEFAULT_PARAMS, build_seated_diorama

# PARAMS cite designs/v1/print_constraints.yaml and people.yaml.
PARAMS = {
    **DEFAULT_PARAMS,
    "base": {"x": 118.0, "y": 65.0, "z": 10.0, "corner_r": 9.0},
    "nameplate": {"text": "BEST BUDS", "size": 7.5, "proud": 1.6},
    "chair": {"cx": 8.0, "cy": 2.0, "seat_w": 36.0, "seat_d": 30.0},
    "woman": {"cx": 14.0, "cy": 4.0, "head_w": 20.0, "head_h": 21.0, "torso_w": 17.0, "torso_h": 14.0},
    "dog": {"cx": -6.0, "cy": 6.0, "head_r": 10.5},
}


def build_scene():
    return build_seated_diorama(PARAMS)


model = build_scene()
