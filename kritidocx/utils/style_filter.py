class StyleFilter:
    # वे प्रॉपर्टीज जो केवल कंटेनर (Div, UL, Table, P) पर लगनी चाहिए
    # और बच्चों (Children - Text) को विरासत में नहीं मिलनी चाहिए।
    
    BOX_PROPERTIES = [
        # --- 1. Visual Box Model (Borders) ---
        'border', 'border-top', 'border-bottom', 'border-left', 'border-right',
        'border-style', 'border-color', 'border-width',
        
        # --- 2. Dimensions & Positioning (Container Physics) ---
        'width', 'height', 
        'position', 'top', 'bottom', 'left', 'right', 'z-index', 
        'float', 'clear', 'rotation_deg', 'rotation_oa',
        
        # --- 3. [CRITICAL FIX] Backgrounds (शेडिंग लीक रोकें) ---
        # अगर ये फिल्टर नहीं हुए, तो अंदर का टेक्स्ट खुद को भी Highlight कर लेता है।
        'background', 'background-color', 'background-image',
        
        # --- 4. Layout Triggers ---
        'page-break-before', 'break-before', 'page-break-after', 'break-after',
        'page-break-inside', 'break-inside',
        'size', 
        'column-count', 'column-gap', 'column-rule',
        'display', 'align-items', 'justify-content' # Flex Props
    ]

    @classmethod
    def get_clean_child_context(cls, parent_context):
        """
        पेरेंट स्टाइल्स की एक कॉपी बनाता है और उसमें से Box-Level प्रॉपर्टीज हटा देता है।
        इससे बच्चे (Text Run) सिर्फ Font/Color इनहेरिट करते हैं, डिब्बा नहीं।
        """
        if not parent_context: return {}
        
        clean_context = parent_context.copy()
        
        # ब्लैकलिस्ट की हुई प्रॉपर्टीज हटा दें
        for prop in cls.BOX_PROPERTIES:
            # हम normal key और snake_case key (parsing variations) दोनों चेक करेंगे
            # e.g., 'background-color' और 'background_color'
            clean_context.pop(prop, None)
            clean_context.pop(prop.replace('-', '_'), None) 
            
        return clean_context