"""
DOCUMENT CONSTANTS (The Physics & Rules Engine)
-----------------------------------------------
यह फ़ाइल OOXML (Open XML) के गणितीय और संरचनात्मक स्थिरांकों (Constants) को परिभाषित करती है।

Microsoft Word XML 4 अलग-अलग यूनिट सिस्टम का उपयोग करता है:
1. Twips (Twentyths of a Point): लेआउट, मार्जिन, इंडेंट के लिए।
2. EMUs (English Metric Units): इमेजेस, शेप्स, और ड्रॉइंग्स के लिए।
3. Half-Points (1/2 pt): फोंट साइज के लिए।
4. Eighth-Points (1/8 pt): बॉर्डर्स की मोटाई के लिए।

यह फ़ाइल उन सभी का केंद्रीकृत नियंत्रक (Central Controller) है।
"""
from docx.enum.text import WD_COLOR_INDEX


class DocConstants:
    
    # =========================================================================
    # 1. 📏 UNIT CONVERSION FACTORS (द यूनिवर्सल कन्वर्टर)
    # =========================================================================
    # DPI Assumption for PX conversion (Standard Web DPI)
    DEFAULT_DPI = 96 

    # --- EMUs (Used for Images/Shapes) ---
    # 1 Inch = 914,400 EMUs
    # (Chosen because it divides evenly by 360 degrees, mm, inches, and points)
    EMU_PER_INCH = 914400
    EMU_PER_CM   = 360000
    EMU_PER_MM   = 36000
    EMU_PER_POINT = 12700  # 914400 / 72
    EMU_PER_PIXEL = 9525   # 914400 / 96 (At 96 DPI)

    # --- TWIPS (Used for Layout/Margins) ---
    # 1 Inch = 1,440 Twips (1 Point = 20 Twips)
    TWIPS_PER_INCH = 1440
    TWIPS_PER_POINT = 20
    TWIPS_PER_CM = 567     # 1440 / 2.54 (approx)
    TWIPS_PER_MM = 57      # approx
    TWIPS_PER_PIXEL = 15   # 1440 / 96

    # --- SPECIALIZED UNITS ---
    # Borders: Defined in 1/8th of a point
    BORDER_UNITS_PER_POINT = 8  
    
    # Fonts: Defined in Half-Points (e.g., 24 = 12pt)
    FONT_UNITS_PER_POINT = 2

    # Percentage: Defined in 50th of a percent (e.g., 5000 = 100%)
    PCT_FULL_WIDTH = 5000


    # =========================================================================
    # 2. 📄 PAPER GEOMETRY (पेज का भूगोल)
    # =========================================================================
    # आयाम Twips में हैं (Layout Engine के लिए)
    
    # Format: (Width, Height) in Twips
    PAPER_SIZES = {
        'a4':     (11906, 16838),  # 8.27 x 11.69 inches
        'a3':     (16838, 23811),  # 11.69 x 16.54 inches
        'letter': (12240, 15840),  # 8.5 x 11 inches
        'legal':  (12240, 20160),  # 8.5 x 14 inches
        'tabloid':(15840, 24480),  # 11 x 17 inches
    }

    # Default Margins (Moderate) - In Twips
    DEFAULT_MARGINS = {
        'top': 1440,    # 1 inch
        'bottom': 1440, # 1 inch
        'left': 1440,   # 1 inch
        'right': 1440,  # 1 inch
        'gutter': 0
    }


    # =========================================================================
    # 3. 🕸️ XML NAMESPACES (Schema Map)
    # =========================================================================
    # Low-level XML manipulation के लिए आवश्यक URIs
    # इसका उपयोग lxml/python-docx को यह बताने के लिए किया जाता है कि टैग किस परिवार का है।
    
    NS = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main', # Core Word
        'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',    # Math (OMML)
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships', # Refs
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing', # Wrappers
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',         # Drawing Art
        'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',    # Pictures
        'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape', # Shapes
        'v': 'urn:schemas-microsoft-com:vml' # Legacy Vector Graphics
    }

    # =========================================================================
    # 4. 🧱 LAYOUT LIMITS & DEFAULTS
    # =========================================================================
    # Word के फिजिकल लिमिट्स (ताकि डॉक्यूमेंट क्रैश न हो)
    
    # 22 inches (Twips) - Max size logic allows usually
    MAX_PAGE_WIDTH_TWIPS = 31680 
    
    # Minimum valid column width
    MIN_COLUMN_WIDTH_TWIPS = 720  # 0.5 inch
    
    # Z-Index Base (Word separates floating items by large numbers)
    # Floating objects starts from this relativeHeight base to sit above text
    Z_INDEX_BASE = 251658240


    # =========================================================================
    # 5. 🔗 RELATIONSHIP TYPES (Linking Constants)
    # =========================================================================
    # Used for HyperlinkManager & Media
    
    REL_TYPE_HYPERLINK = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
    REL_TYPE_IMAGE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
    REL_TYPE_HEADER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/header"
    REL_TYPE_FOOTER = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer"

    # =========================================================================
    # 6. 🖼️ PLACEHOLDER ASSETS (Fallback Generation)
    # =========================================================================
    # If a dynamic image fails, these constants guide the Red Box generator
    
    ERROR_BOX_WIDTH_PX = 400
    ERROR_BOX_HEIGHT_PX = 150
    ERROR_FONT_SIZE = 20
    
    # =========================================================================
    # 7. 🎨 GLOBAL WEB COLORS (CSS Level 3 / W3C Standard)
    # =========================================================================
    # यह डिक्शनरी किसी भी HTML कलर नाम को पहचान लेगी
    WEB_COLORS = {
        "aliceblue": "F0F8FF", "antiquewhite": "FAEBD7", "aqua": "00FFFF", 
        "aquamarine": "7FFFD4", "azure": "F0FFFF", "beige": "F5F5DC", 
        "bisque": "FFE4C4", "black": "000000", "blanchedalmond": "FFEBCD", 
        "blue": "0000FF", "blueviolet": "8A2BE2", "brown": "A52A2A", 
        "burlywood": "DEB887", "cadetblue": "5F9EA0", "chartreuse": "7FFF00", 
        "chocolate": "D2691E", "coral": "FF7F50", "cornflowerblue": "6495ED", 
        "cornsilk": "FFF8DC", "crimson": "DC143C", "cyan": "00FFFF", 
        "darkblue": "00008B", "darkcyan": "008B8B", "darkgoldenrod": "B8860B", 
        "darkgray": "A9A9A9", "darkgreen": "006400", "darkkhaki": "BDB76B", 
        "darkmagenta": "8B008B", "darkolivegreen": "556B2F", "darkorange": "FF8C00", 
        "darkorchid": "9932CC", "darkred": "8B0000", "darksalmon": "E9967A", 
        "darkseagreen": "8FBC8F", "darkslateblue": "483D8B", "darkslategray": "2F4F4F", 
        "darkturquoise": "00CED1", "darkviolet": "9400D3", "deeppink": "FF1493", 
        "deepskyblue": "00BFFF", "dimgray": "696969", "dodgerblue": "1E90FF", 
        "firebrick": "B22222", "floralwhite": "FFFAF0", "forestgreen": "228B22", 
        "fuchsia": "FF00FF", "gainsboro": "DCDCDC", "ghostwhite": "F8F8FF", 
        "gold": "FFD700", "goldenrod": "DAA520", "gray": "808000", 
        "green": "008000", "greenyellow": "ADFF2F", "honeydew": "F0FFF0", 
        "hotpink": "FF69B4", "indianred": "CD5C5C", "indigo": "4B0082", 
        "ivory": "FFFFF0", "khaki": "F0E68C", "lavender": "E6E6FA", 
        "lavenderblush": "FFF0F5", "lawngreen": "7CFC00", "lemonchiffon": "FFFACD", 
        "lightblue": "ADD8E6", "lightcoral": "F08080", "lightcyan": "E0FFFF", 
        "lightgoldenrodyellow": "FAFAD2", "lightgray": "D3D3D3", "lightgreen": "90EE90", 
        "lightpink": "FFB6C1", "lightsalmon": "FFA07A", "lightseagreen": "20B2AA", 
        "lightskyblue": "87CEFA", "lightslategray": "778899", "lightsteelblue": "B0C4DE", 
        "lightyellow": "FFFFE0", "lime": "00FF00", "limegreen": "32CD32", 
        "linen": "FAF0E6", "magenta": "FF00FF", "maroon": "800000", 
        "mediumaquamarine": "66CDAA", "mediumblue": "0000CD", "mediumorchid": "BA55D3", 
        "mediumpurple": "9370DB", "mediumseagreen": "3CB371", "mediumslateblue": "7B68EE", 
        "mediumspringgreen": "00FA9A", "mediumturquoise": "48D1CC", 
        "mediumvioletred": "C71585", "midnightblue": "191970", "mintcream": "F5FFFA", 
        "mistyrose": "FFE4E1", "moccasin": "FFE4B5", "navajowhite": "FFDEAD", 
        "navy": "000080", "oldlace": "FDF5E6", "olive": "808000", 
        "olivedrab": "6B8E23", "orange": "FFA500", "orangered": "FF4500", 
        "orchid": "DA70D6", "palegoldenrod": "EEE8AA", "palegreen": "98FB98", 
        "paleturquoise": "AFEEEE", "palevioletred": "DB7093", "papayawhip": "FFEFD5", 
        "peachpuff": "FFDAB9", "peru": "CD853F", "pink": "FFC0CB", 
        "plum": "DDA0DD", "powderblue": "B0E0E6", "purple": "800080", 
        "red": "FF0000", "rosybrown": "BC8F8F", "royalblue": "4169E1", 
        "saddlebrown": "8B4513", "salmon": "FA8072", "sandybrown": "F4A460", 
        "seagreen": "2E8B57", "seashell": "FFF5EE", "sienna": "A0522D", 
        "silver": "C0C0C0", "skyblue": "87CEEB", "slateblue": "6A5ACD", 
        "slategray": "708090", "snow": "FFFAFA", "springgreen": "00FF7F", 
        "steelblue": "4682B4", "tan": "D2B48C", "teal": "008080", 
        "thistle": "D8BFD8", "tomato": "FF6347", "turquoise": "40E0D0", 
        "violet": "EE82EE", "wheat": "F5DEB3", "white": "FFFFFF", 
        "whitesmoke": "F5F5F5", "yellow": "FFFF00", "yellowgreen": "9ACD32"
    }

    
    # Hex codes to Highlighter Enum Mapping (For robustness)
    HEX_TO_HIGHLIGHT = {
        'FFFF00': WD_COLOR_INDEX.YELLOW,
        '00FF00': WD_COLOR_INDEX.BRIGHT_GREEN, # Standard Web Green (Lime)
        '00FFFF': WD_COLOR_INDEX.TURQUOISE,    # Cyan
        'FF00FF': WD_COLOR_INDEX.PINK,         # Magenta
        '0000FF': WD_COLOR_INDEX.BLUE,
        'FF0000': WD_COLOR_INDEX.RED,
        '000080': WD_COLOR_INDEX.DARK_BLUE,
        '008080': WD_COLOR_INDEX.TEAL,
        '808080': WD_COLOR_INDEX.GRAY_50,
        '000000': WD_COLOR_INDEX.BLACK
    }