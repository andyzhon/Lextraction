SAMPLE_RULES = """
Sample and evidence rules:
- Keep bare material, coated material, electrode fabrication and material groups distinct.
- Use the meta fields in the supplied format. Record coating amount with its stated unit;
  use the same sample name across text and tables. Include loading in a coated sample name.
- For an unspecified coating loading, keep a generic coated-material record. Do not copy a
  generic statement to every loading or infer loading/time pairs from two separate lists.
- Keep substrate formula and coating formula separate. ZnO/LiCoO2 denotes a coating
  composite, not a single stoichiometric compound. Do not invent a sample id.
- Preserve <, <=, >, >= and approximate values; do not turn bounds into exact measurements.
- Include test conditions only when supported. Distinguish DSC onset, peak temperature,
  relative onset shift, TGA weight-loss/oxygen-release events and integrated peak-area ratios.
- Do not interpret particle diameter as crystallite size, coating thickness or XRD size.
- A general thermal event belongs to a material_group, not to every individual sample.
- Do not output quantitative property entries with missing values. Retain qualitative
  observations separately as notes. Never guess values from figures or repair OCR units.
- For each measurement provide evidence containing a verbatim supporting excerpt when
  the format includes that field. Never copy facts from examples to the input results.
"""
