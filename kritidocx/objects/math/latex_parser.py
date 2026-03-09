r"""
LATEX PARSER MODULE (The Math Sanitizer)
----------------------------------------
Responsibility:
Pre-processes raw LaTeX strings derived from HTML/Markdown before they hit the core XML Converter.

Why is this needed?
1. Cleanliness: HTML text often contains hidden Unicode chars (\xa0, \u200b) that break XML generators.
2. Structure: Standard 'pmatrix' renders poorly in Word (fixed brackets). We convert to expandable delimiters.
3. Syntax: Normalizes web-latex shorthand (\lt, \gt) to standard symbols.

Process Flow:
Raw String -> Unescape HTML -> Clean Invisible Chars -> Expand Matrices -> Normalize Operators -> Clean LaTeX.
"""

import re
import html
import logging

# Fallback logger
try:
    from kritidocx.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger("MyDocX_Math")

class LatexParser:
    r"""
    Static utility to normalize LaTeX strings for OOXML conversion.
    """

    # Dictionary mapping LaTeX environments to Expanded Delimiters
    # Key: (Environment Start, End) -> Value: (Left Delim, Right Delim)
    # Using specific bracket logic allows Word equations to 'Grow' with content.
    MATRIX_MAP = [
        (r'\begin{pmatrix}', r'\end{pmatrix}', r'\left(', r'\right)'),
        (r'\begin{bmatrix}', r'\end{bmatrix}', r'\left[', r'\right]'),
        (r'\begin{Bmatrix}', r'\end{Bmatrix}', r'\left\{', r'\right\}'),
        (r'\begin{vmatrix}', r'\end{vmatrix}', r'\left|', r'\right|'),
        (r'\begin{Vmatrix}', r'\end{Vmatrix}', r'\left\|', r'\right\|')
    ]


    # Pattern to find 'matrix' body inside the wrappers
    # Matches "\begin{type} CONTENT \end{type}"
    MATRIX_REGEX_TEMPLATE = r'({start})\s*([\s\S]*?)\s*({end})'

    @classmethod
    def normalize(cls, latex_str):
        """
        Master cleaning function.
        Input: Raw messy LaTeX (e.g., "$$ x &lt; y $$")
        Output: Clean math-ready LaTeX (e.g., "x < y")
        """
        if not latex_str:
            return ""

        clean = str(latex_str).strip()

        # -------------------------------------------------------------
        # STEP 1: DECODE HTML ENTITIES
        # -------------------------------------------------------------
        # Example: "x &lt; y" -> "x < y"
        clean = html.unescape(clean)

        # -------------------------------------------------------------
        # STEP 2: REMOVE INVISIBLE ARTIFACTS
        # -------------------------------------------------------------
        # The "Invisible Box" problem solver.
        replacements = {
            '\xa0': ' ',
            '\u200b': '',
            '\u200e': '',
            '\u200f': '',
            '\t': ' ', # Tabs to space
            
            # --- [NEW ADDITION START] ---
            # math_core.py से लिए गए अतिरिक्त कचरा कैरेक्टर्स
            '\u2061': '', # Function Apply
            '\u2062': '', # Invisible Times
            '\u2063': '', # Invisible Separator
            '\u2064': '', # Invisible Plus
            # --- [NEW ADDITION END] ---
        }
        for bad_char, replacement in replacements.items():
            clean = clean.replace(bad_char, replacement)

        # यह गलती से लिखे गए टेक्स्ट (जैसे "abc\u200b") को भी हटाएगा
        # यह सुनिश्चित करता है कि स्क्रीनशॉट जैसी समस्या दोबारा न हो
        literal_garbage = [r'\u200b', r'\u200B', r'\u200e', r'\u200E']
        for junk in literal_garbage:
            clean = clean.replace(junk, '')
            
        # Specific Handle for \xa0 (NBSP string literal) -> Space
        clean = clean.replace(r'\xa0', ' ').replace(r'\xA0', ' ')

        # -------------------------------------------------------------
        # STEP 3: OPERATOR NORMALIZATION
        # -------------------------------------------------------------
        # Web LaTeX often uses shortcuts that converters might miss
        ops_map = {
            r'\lt': '<',
            r'\gt': '>',
            r'\le': r'\leq',
            r'\ge': r'\geq',
            r'\,': ' ',
            r'\;': ' ',
            r'\:': ' '
        }

        for raw_op, norm_op in ops_map.items():
            # Replace full word matches only to avoid partials if necessary
            # For operators, simple replace is usually safe in math context
            clean = clean.replace(raw_op, norm_op)

        # -------------------------------------------------------------
        # STEP 4: MATRIX EXPANSION (The Visual Fix)
        # -------------------------------------------------------------
        clean = cls._fix_matrices(clean)


        
        return clean.strip()

    @classmethod
    def _fix_matrices(cls, latex_text):
        r"""
        [UPDATED from math_core]
        Replaces rigid matrix environments with dynamic fenced matrices.
        Input:  \begin{pmatrix} a & b \\ c & d \end{pmatrix}
        Output: \left(\begin{matrix} a & b \\ c & d \end{matrix}\right)
        
        This triggers Word's <m:d> (Delimiter) tag which auto-resizes.
        """
        if not latex_text or "matrix" not in latex_text:
            return latex_text

        processed_text = latex_text

        # 1. Parentheses (pmatrix) -> ( ... )
        processed_text = processed_text.replace(r'\begin{pmatrix}', r'\left(\begin{matrix}')
        processed_text = processed_text.replace(r'\end{pmatrix}', r'\end{matrix}\right)')

        # 2. Brackets (bmatrix) -> [ ... ]
        processed_text = processed_text.replace(r'\begin{bmatrix}', r'\left[\begin{matrix}')
        processed_text = processed_text.replace(r'\end{bmatrix}', r'\end{matrix}\right]')

        # 3. Pipes (vmatrix) -> | ... |
        processed_text = processed_text.replace(r'\begin{vmatrix}', r'\left|\begin{matrix}')
        processed_text = processed_text.replace(r'\end{vmatrix}', r'\end{matrix}\right|')
        
        # 4. Braces (Bmatrix) -> { ... }
        processed_text = processed_text.replace(r'\begin{Bmatrix}', r'\left\{\begin{matrix}')
        processed_text = processed_text.replace(r'\end{Bmatrix}', r'\end{matrix}\right\}')

        # 5. Double Pipes (Vmatrix) -> || ... ||
        processed_text = processed_text.replace(r'\begin{Vmatrix}', r'\left\|\begin{matrix}')
        processed_text = processed_text.replace(r'\end{Vmatrix}', r'\end{matrix}\right\|')

        return processed_text