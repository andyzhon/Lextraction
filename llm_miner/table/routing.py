"""Conservative overrides for tables outside the original crystallography domain."""

import re
from bs4 import BeautifulSoup


def route_table(text, context=None):
    plain = BeautifulSoup(text, "html.parser").get_text(" ")
    plain = re.sub(r"\s+", " ", plain).lower()
    # Dissolved ions in electrolyte are a stability measurement, not solid composition.
    if (re.search(r"\b(?:dissolv\w*|leach\w*|dissolution)\b", plain)
            and re.search(r"\b(?:co|cobalt)\b", plain)
            and re.search(r"\b(?:ppm|electrolyte)\b", plain)):
        return "Property"
    parameters = ("rf power", "coating time", "chamber temperature",
                  "working pressure", "dezn flow rate", "bubble pressure")
    if (sum(item in plain for item in parameters) >= 2
            and ("process parameter" in plain or "coating conditions" in plain
                 or "coating conditions" in str(context or "").lower())):
        return "Synthesis condition"
    return None
