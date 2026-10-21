"""Battery measurements shared by text and table extraction formatters."""

import json


PROPERTIES = { # 指导模型理解格式
    "particle_size": ("Particle diameter measured by microscopy or a particle-size analyser; not crystallite size.",
                      {"value": "", "unit": "", "method": "", "condition": ""},
                      {"value": "7", "unit": "µm", "method": "SEM"}),
    "coating_particle_size": ("Diameter of particles making up a surface coating; not coating thickness or substrate crystallite size.",
                              {"value": "", "unit": "", "component": "", "method": "", "condition": ""},
                              {"value": "15-25", "unit": "nm", "component": "Al2O3", "method": "SEM"}),
    "coating_amount": ("Measured coating loading; retain its mass/atomic fraction basis. Do not infer loading from time.",
                       {"value": "", "unit": "", "method": "", "condition": ""},
                       {"value": "0.2", "unit": "wt.%"}),
    "specific_capacity": ("Charge or discharge capacity per mass, together with rate, voltage range and cycle number.",
                          {"value": "", "unit": "", "kind": "", "cycles": "", "rate": "", "voltage_range": "", "temperature": "", "condition": ""},
                          {"value": "150", "unit": "mAh/g", "kind": "discharge", "cycles": "1", "rate": "1 C", "voltage_range": "3.0-4.4 V"}),
    "capacity_retention": ("Percentage of capacity remaining relative to a stated reference cycle; include cycle count and test conditions.",
                           {"value": "", "unit": "", "cycles": "", "reference_cycle": "", "rate": "", "voltage_range": "", "temperature": "", "condition": ""},
                           {"value": "70", "unit": "%", "cycles": "50", "reference_cycle": "1", "rate": "1 C", "voltage_range": "3.0-4.4 V"}),
    "cobalt_dissolution": ("Concentration of cobalt dissolved/leached into electrolyte; not elemental composition of the solid.",
                          {"value": "", "unit": "", "temperature": "", "time": "", "electrolyte": "", "sample_mass": "", "prior_cycles": "", "prior_rate": "", "method": "", "condition": ""},
                          {"value": "0.2", "unit": "ppm", "comparison": "<", "temperature": "60 °C", "time": "7 days", "method": "AAS"}),
    "thermal_onset_temperature": ("An explicitly reported absolute onset of a DSC/decomposition reaction, not a peak, relative shift, or general TGA loss event.",
                                  {"value": "", "unit": "", "method": "", "event": "", "heating_rate": "", "atmosphere": "", "charged_voltage": "", "hold_time": "", "condition": ""},
                                  {"value": "240", "unit": "°C", "method": "DSC", "event": "exothermic reaction onset"}),
    "thermal_onset_shift": ("Relative change in reaction onset compared to a named reference; never report it as an absolute temperature.",
                            {"value": "", "unit": "", "reference_sample": "", "direction": "", "method": "", "condition": ""},
                            {"value": "12", "unit": "°C", "comparison": ">=", "reference_sample": "bare LiCoO2", "direction": "higher", "method": "DSC"}),
    "heat_release": ("Absolute heat released in DSC, with reported units; not heat capacity or a relative peak-area ratio.",
                     {"value": "", "unit": "", "method": "", "heating_rate": "", "condition": ""},
                     {"value": "100", "unit": "J/g", "method": "DSC"}),
    "relative_heat_release": ("Ratio of DSC integrated peak area/heat to a named reference. Preserve inequalities and do not invent J/g.",
                              {"value": "", "unit": "", "reference_sample": "", "quantity": "", "method": "", "condition": ""},
                              {"value": "0.3", "comparison": "<", "unit": "ratio", "reference_sample": "bare LiCoO2", "quantity": "integrated peak area", "method": "DSC"}),
    "thermal_event": ("A reported TGA weight-loss/oxygen-release event. A general observation must stay with a material group and must not be assigned to every sample as an onset.",
                      {"value": "", "unit": "", "event": "", "method": "", "heating_rate": "", "atmosphere": "", "condition": ""},
                      {"value": "260", "unit": "°C", "is_approximate": True, "event": "oxygen release / major weight loss", "method": "TGA"}),
    "test_conditions": ("Electrochemical/DSC/TGA measurement setup, including shared conditions; not material synthesis.",
                        {"test_type": "", "cell_type": "", "rate": "", "voltage_range": "", "charged_voltage": "", "hold_time": "", "heating_rate": "", "atmosphere": "", "electrolyte": "", "condition": ""},
                        {"test_type": "TGA", "heating_rate": "10 °C/min", "atmosphere": "argon"}),

    "c_rate_reference": (
        "Reported basis of a 1C rate (e.g. 1C = 250 mAh/g). Do not infer it from a capacity measurement.",
        {"value": "", "unit": "", "definition": "", "condition": ""},
        {"value": "200", "unit": "mAh/g", "definition": "1C"},
    ),
    "average_discharge_voltage": (
        "Reported average discharge voltage at a specific cycle and rate, not voltage cutoff or a CV peak.",
        {"value": "", "unit": "", "cycles": "", "rate": "", "voltage_range": "", "condition": ""},
        {"value": "3.65", "unit": "V", "cycles": "1"},
    ),
    "voltage_drop": (
        "Reported drop in average discharge voltage between two cycles; never calculate a missing value or replace a reported value.",
        {"value": "", "unit": "", "initial_cycle": "", "final_cycle": "", "rate": "", "condition": ""},
        {"value": "0.3", "unit": "V", "initial_cycle": "1", "final_cycle": "100"},
    ),
    "voltage_decay_rate": (
        "Reported voltage decay per cycle (mV/cycle); distinguish it from total voltage drop. Never derive an unreported rate.",
        {"value": "", "unit": "", "initial_cycle": "", "final_cycle": "", "rate": "", "condition": ""},
        {"value": "4.2", "unit": "mV/cycle", "condition": "reported"},
    ),
    "cv_peak_separation": (
        "Peak-to-peak potential difference in cyclic voltammetry; not average discharge voltage or a voltage window.",
        {"value": "", "unit": "", "method": "", "scan_rate": "", "cycles": "", "condition": ""},
        {"value": "0.25", "unit": "V", "method": "CV"},
    ),
    "charge_transfer_resistance": (
        "Charge-transfer resistance (Rct) from EIS. Attach each value to its explicit cycling state; do not assume initial/after-cycle labels from arrow order alone.",
        {"value": "", "unit": "", "method": "", "cycles": "", "rate": "", "fitting_model": "", "condition": ""},
        {"value": "95", "unit": "ohm", "method": "EIS", "cycles": "100"},
    ),
    "lithium_diffusion_coefficient": (
        "Numerical Li-ion diffusion coefficient D_Li from GITT/PITT/EIS, only when a numerical value or range is explicitly given. Keep logarithm basis if log(D) is reported; do not invent values from qualitative trends.",
        {"value": "", "unit": "", "method": "", "quantity": "", "soc": "", "state": "", "condition": ""},
        {"value": "1e-11", "unit": "cm2/s", "method": "GITT", "quantity": "D_Li"},
    ),
    "rate_recovery_capacity": (
        "Discharge capacity measured after returning to a lower C-rate in a rate-capability experiment; record the preceding and returned rates.",
        {"value": "", "unit": "", "previous_rate": "", "recovered_rate": "", "cycles": "", "voltage_range": "", "condition": ""},
        {"value": "190", "unit": "mAh/g", "previous_rate": "2C", "recovered_rate": "0.1C"},
    ),
    "xrd_intensity_ratio": (
        "Ratio of XRD peak intensities I(hkl1)/I(hkl2); keep exact plane indices and comparison signs.",
        {"value": "", "unit": "", "numerator_hkl": "", "denominator_hkl": "", "method": "", "condition": ""},
        {"value": "1.6", "unit": "ratio", "numerator_hkl": "(003)", "denominator_hkl": "(104)", "method": "XRD"},
    ),
    "lattice_parameter": (
        "Unit-cell lattice parameter a, b or c, one axis per record, with units. Do not confuse crystallographic parameter with crystallite size.",
        {"value": "", "unit": "", "axis": "", "phase": "", "method": "", "condition": ""},
        {"value": "2.86", "unit": "Å", "axis": "a", "method": "XRD"},
    ),
    "lattice_parameter_ratio": (
        "Reported ratio of lattice parameters such as c/a; dimensionless, not an XRD peak intensity ratio.",
        {"value": "", "unit": "", "ratio": "", "phase": "", "method": "", "condition": ""},
        {"value": "4.99", "unit": "ratio", "ratio": "c/a", "method": "XRD"},
    ),
    "unit_cell_volume": (
        "Volume of the crystallographic unit cell; not particle volume, pore volume or unit-cell length.",
        {"value": "", "unit": "", "phase": "", "method": "", "condition": ""},
        {"value": "100", "unit": "Å3", "method": "XRD"},
    ),
    "lattice_plane_spacing": (
        "Interplanar spacing d(hkl) from TEM/HRTEM/XRD; record phase, plane and pre-/post-cycling state, if stated.",
        {"value": "", "unit": "", "hkl": "", "phase": "", "method": "", "cycles": "", "condition": ""},
        {"value": "0.47", "unit": "nm", "hkl": "(003)", "method": "HRTEM"},
    ),
    "eds_elemental_composition": (
        "EDS elemental abundance; record element and whether basis is mass or atomic percent. Separate two bases into distinct records; do not conflate them.",
        {"value": "", "unit": "", "element": "", "basis": "", "method": "", "condition": ""},
        {"value": "22.5", "unit": "%", "element": "Ni", "basis": "atomic", "method": "EDS"},
    ),
    "xps_binding_energy": (
        "XPS binding energy for a specific element and core level (e.g. Ni 2p3/2), with reported oxidation state only if supported.",
        {"value": "", "unit": "", "element": "", "orbital": "", "oxidation_state": "", "method": "", "condition": ""},
        {"value": "855.0", "unit": "eV", "element": "Ni", "orbital": "2p3/2", "method": "XPS"},
    ),
    "xps_spin_orbit_splitting": (
        "Reported spin-orbit separation of the two XPS core-level peaks; not an individual binding energy.",
        {"value": "", "unit": "", "element": "", "orbitals": "", "method": "", "condition": ""},
        {"value": "15", "unit": "eV", "element": "Co", "orbitals": "2p1/2 - 2p3/2", "method": "XPS"},
    ),
    "qualitative_performance_comparison": (
        "A nonnumeric, explicitly stated characterization or performance comparison. Preserve exact sample, comparator, technique, direction and verbatim evidence. Do not invent numerical diffusion, impedance or rate-capability values.",
        {"observation": "", "property": "", "reference_sample": "", "direction": "", "method": "", "condition": ""},
        {"observation": "The coated sample has lower polarization than the uncoated one", "property": "polarization", "reference_sample": "uncoated sample", "direction": "lower", "method": "CV"},
    ),

}


def register(formatter):
    """Register all resources together so a new property cannot be silently skipped."""
    for key, (description, fields, example_value) in PROPERTIES.items():
        label = key.replace("_", " ")
        fields = dict(fields, comparison="", is_approximate=None, evidence="")
        formatter.structured_data.data[key] = json.dumps({label: [fields]}, ensure_ascii=False)[1:-1]
        formatter.explanation.data[key] = description
        formatter.information.data[key] = (
            description + " Preserve comparisons (<, <=, >, >=), approximate values, "
            "and the exact sample loading. Fill evidence with a verbatim supporting sentence. "
            "Leave unreported fields empty; never infer graph values or repair OCR units by guessing.")
        record = {"meta": {"name": "0.2 wt.% Al2O3-coated LiCoO2", "chemical formula": "Al2O3/LiCoO2",
                           "role": "coated_material", "substrate formula": "LiCoO2",
                           "coating formula": "Al2O3", "coating amount": {"value": "0.2", "unit": "wt.%"}},
                  label: [example_value]}
        sentence = (f"For 0.2 wt.% Al2O3-coated LiCoO2, the reported {label} is "
                    + json.dumps(example_value, ensure_ascii=False) + ".")
        formatter.example_text.data[key] = "Paragraph: " + sentence + "\nJSON: " + json.dumps([record], ensure_ascii=False)
        formatter.example_table.data["battery_" + key] = {
            "contain": [label],
            "content": f"Input:\n| Sample | {label} |\n|---|---|\n| 0.2 wt.% Al2O3-coated LiCoO2 | {json.dumps(example_value, ensure_ascii=False)} |\nOutput: " + json.dumps([record], ensure_ascii=False),
            "output": json.dumps([record], ensure_ascii=False),
        }
