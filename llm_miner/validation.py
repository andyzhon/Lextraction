"""Small deterministic checks applied before model measurements are stored."""

from copy import deepcopy


def normalize_measurements(data):
    """Keep nonnumeric records, but do not count blank quantities as measurements."""
    if isinstance(data, list):
        return [normalize_measurements(item) for item in data]
    if not isinstance(data, dict):
        return data
    record = deepcopy(data)
    for key, values in list(record.items()):
        if key in {"meta", "processes"} or not isinstance(values, list):
            continue
        kept = []
        for value in values:
            if (not isinstance(value, dict) or "value" not in value
                    or (value["value"] is not None and str(value["value"]).strip())):
                kept.append(value)
            elif value.get("condition"):
                record.setdefault("notes", []).append({
                    "property": key, "observation": value["condition"],
                    "reason": "No numeric value was reported"})
        if kept:
            record[key] = kept
        else:
            record.pop(key, None)
    # Explicit particle-size wording is not a measurement of crystallite size.
    crystal_sizes = record.get("crystal size", [])
    if isinstance(crystal_sizes, list):
        kept = []
        for value in crystal_sizes:
            if not isinstance(value, dict):
                kept.append(value)
                continue
            condition = str(value.get("condition", "")).lower()
            if "coating diameter" in condition or "coating particle" in condition:
                record.setdefault("coating particle size", []).append(value)
            elif "particle size" in condition or "particle diameter" in condition:
                record.setdefault("particle size", []).append(value)
            else:
                kept.append(value)
        if "crystal size" in record:
            if kept:
                record["crystal size"] = kept
            else:
                record.pop("crystal size")
    return record
