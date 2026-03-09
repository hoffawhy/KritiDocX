"""
THEME CONFIGURATION (The Visual Design System)
----------------------------------------------
यह फाइल पूरे डॉक्यूमेंट का "लुक और फील" (Look & Feel) नियंत्रित करती है।
इसे 'Data Driven Design' के सिद्धांत पर बनाया गया है।

मुख्य विशेषताएँ:
1. Multi-Script Typography: हिंदी (Mangal) और अंग्रेजी (Calibri) के लिए अलग फोंट।
2. Semantic Color Palette: 'Red' की जगह 'Error' या 'Brand' जैसे नामों का उपयोग।
3. Border Translation: CSS स्टाइल्स को Word XML में मैप करना।
4. Component Styling: टेबल्स, लिस्ट और फॉर्म्स के लिए डिफॉल्ट सेटिंग्स।
"""

class ThemeConfig:
    # =========================================================================
    # 1. 🔤 TYPOGRAPHY (फोंट्स और लिपि)
    # =========================================================================
    
    # 1.1 मुख्य फोंट (Primary/ASCII Fonts)
    # अंग्रेजी टेक्स्ट के लिए
    FONTS_ASCII = {
        'body': 'Calibri',             # सामान्य पाठ
        'heading': 'Calibri Light',    # शीर्षक (H1-H6)
        'code': 'Courier New',         # कोड ब्लॉक
        'quote': 'Georgia',            # कोट्स
        'title': 'Arial Black',        # कवर पेज टाइटल
    }

    # 1.2 जटिल लिपि फोंट (Complex Script Fonts - CS)
    # हिंदी, मराठी, चेकबॉक्स और सिम्बल्स के लिए यह सबसे महत्वपूर्ण है
    FONTS_COMPLEX = {
        'hindi': 'Mangal',             # देवनागरी (Devanagari) के लिए मानक
        'forms': 'MS Gothic',          # ☑ ☐ चेकबॉक्स (Checkboxes) सही दिखाने के लिए अनिवार्य
        'symbol': 'Segoe UI Symbol',   # इमोजी और सिम्बल्स के लिए
        'asian': 'SimSun',             # चीनी/जापानी (CJK) सपोर्ट के लिए
        'arabic': 'Traditional Arabic'
    }

    # 1.3 फोंट साइज (Points में)
    # 1 Point = 1/72 Inch
    FONT_SIZES = {
        'body': 11,
        'title': 28,
        'subtitle': 16,
        'h1': 24,
        'h2': 18,
        'h3': 14,
        'h4': 12,
        'h5': 11,  # Bold assumed usually
        'h6': 10,
        'code': 9.5,
        'table_content': 10,
        'table_header': 10,
        'footnote': 9,
    }

    # =========================================================================
    # 2. 🎨 COLOR PALETTE (रंग संयोजन)
    # =========================================================================
    
    # 2.1 बेस कलर मैप (Base Colors)
    # साधारण HTML नामों को प्रोफेशनल Hex कोड्स में मैप करना
    COLOR_MAP = {
        # Basics
        'black': '000000',
        'white': 'FFFFFF',
        'transparent': 'auto',

        # Corporate Standards (Darker tones look better on prints)
        'red': 'C00000',        # Dark Professional Red
        'green': '006100',      # Excel-style Dark Green
        'blue': '2F5496',       # Word Standard Deep Blue
        'yellow': 'FFC000',     # Amber (Readable Yellow)
        
        # Grays
        'gray': '7F7F7F',
        'dark_gray': '595959',
        'light_gray': 'F2F2F2',
        
        # Accents
        'orange': 'ED7D31',
        'purple': '7030A0',
        'teal': '4472C4',
    }

    # 2.2 सिमेंटिक कलर्स (Semantic/Functional Colors)
    # लॉजिक में इनका उपयोग करें ताकि भविष्य में पूरी थीम बदलना आसान हो
    THEME_COLORS = {
        # Branding
        'brand_primary': '2E74B5',    # मेन टाइटल कलर
        'brand_secondary': '1F4D78',  # सब-टाइटल कलर
        
        # Alerts / Messages
        'success_bg': 'C6EFCE',       # Light Green BG
        'success_text': '006100',     # Dark Green Text
        
        'warning_bg': 'FFEB9C',       # Light Yellow BG
        'warning_text': '9C5700',     # Dark Yellow Text
        
        'error_bg': 'FFC7CE',         # Light Red BG
        'error_text': '9C0006',       # Dark Red Text
        
        # Components
        'table_border': 'BFBFBF',     # स्टैंडर्ड ग्रे बॉर्डर
        'table_header_bg': '4472C4',  # टेबल हेडर नीला
        'table_header_text': 'FFFFFF',# टेबल हेडर सफेद
        'code_bg': 'F4F4F4',          # कोड ब्लॉक ग्रे बैकग्राउंड
        'hyperlink': '0563C1',        # लिंक का नीला रंग
    }

    # =========================================================================
    # 3. 🛡️ BORDERS & STYLES (बॉर्डर और डिज़ाइन)
    # =========================================================================
    
    # CSS बॉर्डर स्टाइल्स को Word OOXML values में मैप करना
    # (Key = CSS, Value = Word XML Attribute)

    BORDER_STYLE_MAP = {
        # --- Standard CSS ---
        'solid':    'single',
        'dotted':   'dot',
        'dashed':   'dash',
        'double':   'double',
        'groove':   'threeDEngrave',  # Closest 3D effect
        'ridge':    'threeDEmboss',   # Closest 3D effect
        'inset':    'inset',
        'outset':   'outset',
        'hidden':   'nil',
        'none':     'nil',
        '0':        'nil',
        
        # --- Advanced / Custom Keyword Support ---
        # यूजर इन कीवर्ड्स का इस्तेमाल CSS में कर सकता है
        # e.g., border: 2px wavy red;
        
        'wavy':         'wave',           # लहरदार लाइन
        'wave':         'wave',           
        'double-wavy':  'doubleWave',     # दोहरी लहर
        'dash-dot':     'dashDot',        # - . - . -
        'dot-dash':     'dashDot',        # Synonym
        'dot-dot-dash': 'dashDotDot',     # . . - . . -
        
        # --- Word Exclusive (Pro) ---
        'thick-thin':   'thickThinSmallGap',
        'thin-thick':   'thinThickSmallGap',
        'triple':       'triple',         # तीन लाइनें
        'thick': 'thick',
        'hidden': 'nil'
    }


    # =========================================================================
    # 4. 🔗 TAG MAPPING (HTML -> Word Styles)
    # =========================================================================
    # HTML टैग्स को Word के Native Styles से जोड़ना।
    # यह सुनिश्चित करता है कि TOC (Index) में हेडर्स सही से दिखें।
    
    TAG_TO_STYLE_ID = {
        'p': 'Normal',
        'div': 'Normal',
        'span': 'Default Paragraph Font',
        'h1': 'Heading 1',
        'h2': 'Heading 2',
        'h3': 'Heading 3',
        'h4': 'Heading 4',
        'h5': 'Heading 5',
        'h6': 'Heading 6',
        'blockquote': 'Quote',      # Word का Quote Style
        'cite': 'Quote Char',
        'code': 'HTML Code',        # हम Custom Style 'HTML Code' बनाएंगे
        'pre': 'HTML Preformatted', 
        'li': 'List Paragraph',
        'caption': 'Caption'        # इमेजेस के नीचे कैप्शन
    }

    # =========================================================================
    # 5. 📐 LAYOUT DEFAULTS (Spacing & Structure)
    # =========================================================================
    
    # पैराग्राफ और लाइनों के बीच की दूरी
    PARAGRAPH_SPACING = {
        'line_height_rule': 'multiple', # 'multiple' or 'exactly'
        'line_height':1.15,            # 1.15x spacing
        'space_after': 10,              # 10pt (पैराग्राफ के बाद)
        'space_before': 0               # 0pt (पैराग्राफ से पहले)
    }

    # टेबल डिफ़ॉल्ट सेटिंग्स
    TABLE_DEFAULTS = {
        'width_pct': 100,         # 100% Page Width (5000 units)
        'style': 'Table Grid',    # डिफॉल्ट ग्रिड
        'alignment': 'center',    # टेबल को पेज के बीच में रखें
        'cell_padding_left': 108, # Twips (0.075 inch approx)
        'cell_padding_right': 108,
        'border_color': 'auto',
        'border_sz': 4,    # 1/2 pt
    }

    # =========================================================================
    # 6. 🔷 FORM & SYMBOLS (फॉर्म्स और प्रतीक)
    # =========================================================================
    # चेकबॉक्स और बुलेट्स के लिए यूनिकोड कैरेक्टर्स
    SYMBOLS = {
        # Checkboxes (Forms)
        'checkbox_checked': '\u2611',   # ☑
        'checkbox_unchecked': '\u2610', # ☐
        
        # Bullets (Lists)
        'bullet_solid': '●',            # Level 1
        'bullet_hollow': 'o',           # Level 2
        'bullet_square': '▪',           # Level 3
        'arrow': '➤',
        'tick': '✓'
    }
    
    # =========================================================================
    # 7. ⚓ LAYOUT DEFAULTS (Positioning Rules)
    # =========================================================================
    # यदि HTML में 'origin' नहीं दिया गया है, तो डिफ़ॉल्ट क्या मानें?
    POSITIONING_DEFAULTS = {
        # यदि पिक्सल में वैल्यू दी गई है (left: 50px, top: 10px) -> कागज का कोना (0,0)
        'coordinates': 'page', 
        
        # यदि एलाइनमेंट दिया गया है (right: 0, bottom: 0) -> मार्जिन (ताकि प्रिंट न कटे)
        'alignment': 'margin',
        
        # यदि संदर्भ टेक्स्ट पैराग्राफ का है (जैसे float, या relative)
        'rel_anchor': 'paragraph'
    }
