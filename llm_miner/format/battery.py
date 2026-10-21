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

    "average_discharge_voltage": (
        "Average discharge voltage at a specified cycle.",
        {
            "value": "", "unit": "",
            "cycles": "", "rate": "",
            "condition": ""
        },
        {"value": "3.5", "unit": "V", "cycles": "1"}
    ),

    "voltage_decay_rate": (
        "Reported voltage fading rate per cycle.",
        {
            "value": "", "unit": "",
            "cycles": "", "condition": ""
        },
        {"value": "4.5", "unit": "mV/cycle"}
    ),

    "cv_peak_separation": (
        "Potential separation between CV redox peaks.",
        {
            "value": "", "unit": "",
            "method": "", "condition": ""
        },
        {"value": "0.2", "unit": "V", "method": "CV"}
    ),

    "charge_transfer_resistance": (
        "Charge-transfer resistance measured by EIS.",
        {
            "value": "", "unit": "",
            "cycles": "", "method": "",
            "condition": ""
        },
        {"value": "80", "unit": "ohm", "method": "EIS"}
    ),

    "xrd_intensity_ratio": (
        "XRD peak intensity ratio with indexed peaks.",
        {
            "value": "", "unit": "",
            "peaks": "", "method": "",
            "condition": ""
        },
        {"value": "1.5", "unit": "",
         "peaks": "(003)/(104)"}
    ),

    "xps_binding_energy": (
        "XPS binding energy of a specified element and orbital.",
        {
            "value": "", "unit": "",
            "element": "", "orbital": "",
            "oxidation_state": "", "condition": ""
        },
        {"value": "855", "unit": "eV",
         "element": "Ni", "orbital": "2p3/2"}
    ),

    "eds_elemental_composition": (
        "EDS element abundance; distinguish mass and atomic percent.",
        {
            "value": "", "unit": "",
            "element": "", "basis": "",
            "condition": ""
        },
        {"value": "20", "unit": "%",
         "element": "Ni", "basis": "atomic"}
    ),

    "lattice_plane_spacing": (
        "Interplanar distance of an indexed lattice plane.",
        {
            "value": "", "unit": "",
            "hkl": "", "phase": "",
            "method": "", "condition": ""
        },
        {"value": "0.47", "unit": "nm",
         "hkl": "(003)", "method": "TEM"}
    )

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
