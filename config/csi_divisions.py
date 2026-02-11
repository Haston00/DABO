"""
Full 16-division CSI MasterFormat breakout (AIA G702/G703 standard).

Each division maps to its sub-sections with scope descriptions used
for sheet classification, conflict rule scoping, and schedule activity
generation.
"""

CSI_DIVISIONS = {
    "01": {
        "name": "General Requirements",
        "sections": {
            "01 10 00": "Summary",
            "01 20 00": "Price & Payment Procedures",
            "01 30 00": "Administrative Requirements",
            "01 40 00": "Quality Requirements",
            "01 50 00": "Temporary Facilities & Controls",
            "01 60 00": "Product Requirements",
            "01 70 00": "Execution & Closeout",
            "01 80 00": "Performance Requirements",
        },
    },
    "02": {
        "name": "Existing Conditions / Site Construction",
        "sections": {
            "02 10 00": "Assessment",
            "02 20 00": "Environmental Assessment",
            "02 30 00": "Subsurface Investigation",
            "02 40 00": "Demolition",
            "02 50 00": "Site Remediation",
            "02 60 00": "Contaminated Site Material",
        },
    },
    "03": {
        "name": "Concrete",
        "sections": {
            "03 10 00": "Concrete Forming & Accessories",
            "03 20 00": "Concrete Reinforcing",
            "03 30 00": "Cast-in-Place Concrete",
            "03 35 00": "Concrete Finishing",
            "03 40 00": "Precast Concrete",
            "03 45 00": "Precast Structural Concrete",
            "03 50 00": "Cast Decks & Underlayment",
            "03 60 00": "Grouting",
        },
    },
    "04": {
        "name": "Masonry",
        "sections": {
            "04 20 00": "Unit Masonry",
            "04 22 00": "Concrete Unit Masonry",
            "04 40 00": "Stone Assemblies",
            "04 50 00": "Refractory Masonry",
            "04 70 00": "Manufactured Masonry",
        },
    },
    "05": {
        "name": "Metals / Structural Steel",
        "sections": {
            "05 10 00": "Structural Metal Framing",
            "05 12 00": "Structural Steel",
            "05 20 00": "Metal Joists",
            "05 30 00": "Metal Decking",
            "05 40 00": "Cold-Formed Metal Framing",
            "05 50 00": "Metal Fabrications",
            "05 51 00": "Metal Stairs",
            "05 52 00": "Metal Railings",
            "05 70 00": "Decorative Metal",
        },
    },
    "06": {
        "name": "Wood, Plastics & Composites",
        "sections": {
            "06 10 00": "Rough Carpentry",
            "06 11 00": "Wood Framing",
            "06 15 00": "Wood Decking",
            "06 17 00": "Shop-Fabricated Structural Wood",
            "06 20 00": "Finish Carpentry",
            "06 40 00": "Architectural Woodwork",
            "06 41 00": "Architectural Wood Casework",
            "06 60 00": "Plastic Fabrications",
        },
    },
    "07": {
        "name": "Thermal & Moisture Protection",
        "sections": {
            "07 10 00": "Dampproofing & Waterproofing",
            "07 20 00": "Thermal Protection",
            "07 25 00": "Weather Barriers",
            "07 30 00": "Steep Slope Roofing",
            "07 40 00": "Roofing & Siding Panels",
            "07 50 00": "Membrane Roofing",
            "07 60 00": "Flashing & Sheet Metal",
            "07 70 00": "Roof & Wall Specialties",
            "07 80 00": "Fire & Smoke Protection",
            "07 90 00": "Joint Sealants",
        },
    },
    "08": {
        "name": "Openings (Doors, Windows, Glazing)",
        "sections": {
            "08 10 00": "Doors & Frames",
            "08 11 00": "Metal Doors & Frames",
            "08 14 00": "Wood Doors",
            "08 30 00": "Specialty Doors & Frames",
            "08 40 00": "Entrances, Storefronts & Curtain Wall",
            "08 50 00": "Windows",
            "08 70 00": "Hardware",
            "08 80 00": "Glazing",
        },
    },
    "09": {
        "name": "Finishes",
        "sections": {
            "09 20 00": "Plaster & Gypsum Board",
            "09 22 00": "Metal Framing (Non-structural)",
            "09 30 00": "Tiling",
            "09 50 00": "Ceilings",
            "09 60 00": "Flooring",
            "09 65 00": "Resilient Flooring",
            "09 68 00": "Carpeting",
            "09 72 00": "Wall Coverings",
            "09 90 00": "Painting & Coating",
        },
    },
    "10": {
        "name": "Specialties",
        "sections": {
            "10 10 00": "Visual Display Surfaces",
            "10 14 00": "Signage",
            "10 20 00": "Interior Specialties",
            "10 21 00": "Compartments & Cubicles",
            "10 28 00": "Toilet, Bath & Laundry Accessories",
            "10 40 00": "Safety Specialties",
            "10 44 00": "Fire Protection Specialties",
            "10 50 00": "Storage Specialties",
            "10 70 00": "Exterior Specialties",
            "10 75 00": "Exterior Protection",
        },
    },
    "11": {
        "name": "Equipment",
        "sections": {
            "11 10 00": "Vehicle & Pedestrian Equipment",
            "11 13 00": "Loading Dock Equipment",
            "11 30 00": "Residential Equipment",
            "11 40 00": "Foodservice Equipment",
            "11 52 00": "Audio-Visual Equipment",
            "11 53 00": "Laboratory Equipment",
            "11 61 00": "Theater & Stage Equipment",
            "11 66 00": "Athletic Equipment",
            "11 70 00": "Healthcare Equipment",
            "11 82 00": "Solid Waste Handling",
        },
    },
    "12": {
        "name": "Furnishings",
        "sections": {
            "12 20 00": "Window Treatments",
            "12 30 00": "Casework",
            "12 35 00": "Specialty Casework",
            "12 36 00": "Countertops",
            "12 40 00": "Furnishings & Accessories",
            "12 48 00": "Rugs & Mats",
            "12 50 00": "Furniture",
            "12 93 00": "Site Furnishings",
        },
    },
    "13": {
        "name": "Special Construction",
        "sections": {
            "13 10 00": "Special Facility Components",
            "13 12 00": "Pre-Engineered Structures",
            "13 17 00": "Tubs & Pools",
            "13 20 00": "Special Purpose Rooms",
            "13 28 00": "Athletic & Recreational",
            "13 34 00": "Fabricated Structures",
            "13 48 00": "Seismic Protection",
            "13 49 00": "Radiation Protection",
        },
    },
    "14": {
        "name": "Conveying Equipment",
        "sections": {
            "14 10 00": "Dumbwaiters",
            "14 20 00": "Elevators",
            "14 21 00": "Electric Traction Elevators",
            "14 24 00": "Hydraulic Elevators",
            "14 30 00": "Escalators & Moving Walks",
            "14 40 00": "Lifts",
            "14 42 00": "Wheelchair Lifts",
            "14 91 00": "Facility Chutes",
        },
    },
    "15": {
        "name": "Mechanical (Plumbing, HVAC, Fire Protection)",
        "sections": {
            # Plumbing
            "15 05 00": "Common Work Results - Mechanical",
            "15 06 00": "Schedules",
            "22 05 00": "Common Work Results - Plumbing",
            "22 07 00": "Plumbing Insulation",
            "22 10 00": "Plumbing Piping",
            "22 11 00": "Facility Water Distribution",
            "22 13 00": "Facility Sanitary Sewage",
            "22 14 00": "Facility Storm Drainage",
            "22 30 00": "Plumbing Equipment",
            "22 40 00": "Plumbing Fixtures",
            "22 47 00": "Drinking Fountains & Coolers",
            "22 60 00": "Gas & Vacuum Systems",
            # HVAC
            "23 05 00": "Common Work Results - HVAC",
            "23 07 00": "HVAC Insulation",
            "23 09 00": "Instrumentation & Controls",
            "23 20 00": "HVAC Piping & Pumps",
            "23 21 00": "Hydronic Piping",
            "23 23 00": "Refrigerant Piping",
            "23 30 00": "HVAC Air Distribution",
            "23 34 00": "HVAC Fans",
            "23 36 00": "Air Terminal Units",
            "23 37 00": "Air Outlets & Inlets",
            "23 38 00": "Ventilation Hoods",
            "23 40 00": "HVAC Air Cleaning",
            "23 50 00": "Central Heating Equipment",
            "23 60 00": "Central Cooling Equipment",
            "23 64 00": "Packaged Water Chillers",
            "23 70 00": "Central HVAC Equipment",
            "23 73 00": "Indoor Central-Station AHUs",
            "23 74 00": "Packaged Outdoor HVAC Equipment",
            "23 81 00": "Decentralized HVAC Equipment",
            # Fire Protection
            "21 05 00": "Common Work Results - Fire Suppression",
            "21 10 00": "Water-Based Fire Suppression",
            "21 11 00": "Facility Fire-Suppression Water",
            "21 12 00": "Fire-Suppression Standpipes",
            "21 13 00": "Fire-Suppression Sprinkler Systems",
            "21 20 00": "Fire-Extinguishing Systems",
            "21 30 00": "Fire Pumps",
        },
    },
    "16": {
        "name": "Electrical",
        "sections": {
            # Power Distribution
            "26 05 00": "Common Work Results - Electrical",
            "26 05 19": "Low-Voltage Wire & Cable",
            "26 05 26": "Grounding & Bonding",
            "26 05 29": "Hangers & Supports",
            "26 05 33": "Raceways & Boxes",
            "26 05 53": "Identification",
            "26 08 00": "Commissioning",
            "26 09 13": "Power Monitoring",
            "26 09 23": "Lighting Control",
            "26 09 43": "Network Lighting Controls",
            "26 12 00": "Medium-Voltage Distribution",
            "26 22 00": "Low-Voltage Transformers",
            "26 24 13": "Switchboards",
            "26 24 16": "Panelboards",
            "26 24 19": "Motor Control Centers",
            "26 27 26": "Wiring Devices",
            "26 28 00": "Power Conditioning",
            "26 29 00": "Low-Voltage Controllers",
            "26 32 00": "Packaged Generator",
            "26 33 00": "Battery Equipment",
            "26 36 00": "Transfer Switches",
            "26 41 00": "Facility Lightning Protection",
            "26 43 00": "Surge Protective Devices",
            # Lighting
            "26 51 00": "Interior Lighting",
            "26 55 00": "Special Purpose Lighting",
            "26 56 00": "Exterior Lighting",
            # Communications
            "27 05 00": "Common Work Results - Communications",
            "27 05 28": "Pathways for Communications",
            "27 10 00": "Structured Cabling",
            "27 11 00": "Communications Equipment Room",
            "27 13 00": "Communications Backbone",
            "27 15 00": "Horizontal Cabling",
            "27 21 00": "Data Communications",
            "27 32 00": "Voice Communications",
            "27 41 00": "Audio-Video Systems",
            "27 51 00": "Distributed Audio-Video",
            # Electronic Safety & Security
            "28 05 00": "Common Work Results - Security",
            "28 10 00": "Access Control",
            "28 13 00": "Security Management",
            "28 16 00": "Intrusion Detection",
            "28 23 00": "Video Surveillance",
            "28 31 00": "Fire Detection & Alarm",
            "28 31 46": "Smoke Detection",
            "28 31 49": "Carbon Monoxide Detection",
            "28 31 74": "Mass Notification",
            "28 46 00": "Nurse Call",
        },
    },
}


def get_division(code: str) -> dict | None:
    """Look up a division by its 2-digit code."""
    return CSI_DIVISIONS.get(code)


def get_section_name(section_code: str) -> str | None:
    """Look up a section name by its full code (e.g., '03 30 00')."""
    for div in CSI_DIVISIONS.values():
        if section_code in div["sections"]:
            return div["sections"][section_code]
    return None


def find_division_for_section(section_code: str) -> str | None:
    """Return the 2-digit division code that contains a given section."""
    for div_code, div in CSI_DIVISIONS.items():
        if section_code in div["sections"]:
            return div_code
    return None
