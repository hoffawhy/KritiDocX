import re
import logging

logger = logging.getLogger("MyDocX_CssEngine")

class CssTokenizer:
    """
    LEXICAL ANALYZER (The string breaker)
    -------------------------------------
    Responsible for raw parsing of inline style attributes.
    Ensures safe splitting of properties even with complex nested syntax 
    (like data URIs or functional notation rgb(..)).
    """

    # -------------------------------------------------------------
    # 1. CORE REGEX PATTERNS (Preserving Robustness)
    # -------------------------------------------------------------
    
    # 1. Split Regex:
    # Splits by ';' ONLY if NOT inside parentheses (...).
    # Critical for: background-image: url('data:image/png;base64,...');
    # Logic: Lookahead ensures no closing ')' comes without opening '(' first after the match.
    _SAFE_SPLIT_PATTERN = re.compile(r';(?![^(]*\))')

    # 2. Cleanup: Remove Comments /* ... */
    _COMMENT_PATTERN = re.compile(r'/\*.*?\*/', re.DOTALL)

    @classmethod
    def parse_inline_styles(cls, style_str):
        """
        Input: "margin: 10px; color: red !important;  /* Comment */"
        Output: {'margin': '10px', 'color': 'red'}
        """
        if not style_str or not isinstance(style_str, str):
            return {}

        raw = style_str.strip()
        if not raw: return {}

        # A. Pre-Cleaning (Remove CSS Comments)
        clean_text = cls._COMMENT_PATTERN.sub('', raw)

        # B. Safe Splitting (Tokenization)
        declarations = cls._SAFE_SPLIT_PATTERN.split(clean_text)
        
        style_map = {}

        for decl in declarations:
            # Skip empty whitespace chunks
            if not decl.strip(): 
                continue
                
            # C. Property-Value Separation
            if ':' in decl:
                # Maxsplit=1 ensures "background: url(http://site:80/img)" doesn't break at http port
                prop, val = decl.split(':', 1)
                
                # D. Normalization (Sanitization)
                clean_prop = prop.strip().lower()
                clean_val = val.strip()

                # Handle '!important' removal (Word styling logic implies inline IS important)
                if '!' in clean_val:
                    clean_val = clean_val.split('!')[0].strip()

                if clean_prop and clean_val:
                    style_map[clean_prop] = clean_val

        return style_map