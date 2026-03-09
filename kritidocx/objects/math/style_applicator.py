"""
MATH STYLE APPLICATOR (The Color Fixer)
---------------------------------------
Responsibility:
Injects Visual Styles (Color, Font) into OMML elements.

Problem: 
MS Word resets Math equations to "Auto" (Black) color, ignoring parent styles.
Fonts like 'Calibri' generally don't apply to Math (forced to 'Cambria Math').

Solution:
Iterates through every <m:r> (Math Run) tag in the equation and forces 
<w:color> inside its properties.
"""

import logging
from kritidocx.basics.color_manager import ColorManager
from kritidocx.basics.font_handler import FontHandler
from kritidocx.xml_factory.xml_builder import XmlBuilder
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

logger = logging.getLogger("MyDocX_Math")

class StyleApplicator:
    """
    Applies CSS-derived styles to raw OMML elements.
    """

    # Namespaces required for XPath queries
    NS = {
        'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    }

    @classmethod
    def apply_style(cls, omml_element, style_data):
        """
        [FIXED]: Now Propagates Colors AND Underlines into the Equation.
        """
        if not style_data: return

        # --- 1. PREPARE COLORS ---
        target_hex = ColorManager.get_hex(style_data.get('color'))
        clean_hex = target_hex.replace('#', '') if target_hex else None
        
        # --- 2. PREPARE UNDERLINE (New addition for wavy red line) ---
        u_raw = style_data.get('text-decoration') or style_data.get('underline')
        u_style = None
        u_color = None
        
        if u_raw:
            u_str = str(u_raw).lower()
            if 'underline' in u_str or u_str == 'true':
                # Identify Style (wavy -> wave)
                if 'wavy' in u_str or 'wave' in u_str: u_style = 'wave'
                elif 'double' in u_str: u_style = 'double'
                else: u_style = 'single'
                
                # Extract Color from string if possible (e.g., 'red' or hex)
                # If no specific underline color, fallback to general color
                for word in u_str.split():
                    if word not in ['underline', 'wavy', 'none', 'double']:
                        found = ColorManager.get_hex(word)
                        if found: u_color = found.replace('#', '')

        # --- 3. TRAVERSAL & INJECTION ---
        # Find all Math Runs (<m:r>) and Properties (naryPr etc)
        targets = omml_element.xpath('.//m:r | .//m:ctrlPr', namespaces=cls.NS)

        for target in targets:
            # Prop-container resolution
            if target.tag.endswith('r'):
                # <m:r> uses <m:rPr>
                container = target.find(qn('m:rPr'))
                if container is None:
                    container = OxmlElement('m:rPr')
                    target.insert(0, container)
            else:
                # <m:ctrlPr> is already a container
                container = target

            # Ensure w:rPr inside math-property exists
            w_rPr = container.find(qn('w:rPr'))
            if w_rPr is None:
                w_rPr = OxmlElement('w:rPr')
                container.insert(0, w_rPr)

            # A. Inject Color
            if clean_hex:
                col_tag = w_rPr.find(qn('w:color')) or OxmlElement('w:color')
                col_tag.set(qn('w:val'), clean_hex)
                if col_tag not in w_rPr: w_rPr.append(col_tag)

            # B. [NEW]: Inject Underline Structure
            if u_style:
                u_tag = w_rPr.find(qn('w:u')) or OxmlElement('w:u')
                u_tag.set(qn('w:val'), u_style)
                if u_color:
                    u_tag.set(qn('w:color'), u_color)
                elif clean_hex: # If no explicit underline color, use text color
                    u_tag.set(qn('w:color'), clean_hex)
                    
                if u_tag not in w_rPr: w_rPr.append(u_tag)

        # -----------------------------------------------------------
        # PHASE 1: STANDARD TEXT RUNS (<m:r>)
        # (Variables a, b, x, y and Numbers)
        # -----------------------------------------------------------
        math_runs = omml_element.xpath('.//m:r', namespaces=cls.NS)
        for r in math_runs:
            # <m:rPr> को ढूँढो या बनाओ
            m_rPr = r.find(qn('m:rPr'))
            if m_rPr is None:
                m_rPr = OxmlElement('m:rPr')
                r.insert(0, m_rPr)
            
            # Helper से कलर इंजेक्ट करें
            cls._inject_color_xml(m_rPr, clean_hex)

        # -----------------------------------------------------------
        # PHASE 2: COMPLEX OPERATORS (Integrals, Roots, Fractions)
        # We must find parent Properties (*Pr) and inject m:ctrlPr
        # -----------------------------------------------------------
        
        # List of Structural Properties that control symbol appearance
        structure_paths = [
            './/m:naryPr',  # Integrals/Sums
            './/m:radPr',   # Roots
            './/m:fPr',     # Fractions (Bar line)
            './/m:dPr',     # Brackets/Delimiters
            './/m:accPr',   # Accents
            './/m:barPr',   # Overbars
            './/m:boxPr'    # Boxes
        ]
        
        combined_xpath = " | ".join(structure_paths)
        
        for prop_element in omml_element.xpath(combined_xpath, namespaces=cls.NS):
            # Inside the Property tag, look for m:ctrlPr (Control Properties)
            # ctrlPr governs the appearance of the operator/symbol itself
            ctrlPr = prop_element.find(qn('m:ctrlPr'))
            
            if ctrlPr is None:
                ctrlPr = OxmlElement('m:ctrlPr')
                # Schema Order: ctrlPr usually goes early
                prop_element.insert(0, ctrlPr)
            
            # Helper से कलर इंजेक्ट करें
            cls._inject_color_xml(ctrlPr, clean_hex)

        # (Optional Debug Log)
        logger.debug(f"Math Styler: Applied Aggressive Color {clean_hex}")
        
            
    @staticmethod
    def _inject_color_xml(parent_node, hex_color):
        """
        [NEW HELPER] Injects <w:rPr><w:color w:val="..."/></w:rPr> 
        into any OMML property container (m:rPr or m:ctrlPr).
        """
        if parent_node is None or not hex_color: return

        # 1. Ensure w:rPr exists (Wrapper for Word Props)
        w_rPr = parent_node.find(qn('w:rPr'))
        if w_rPr is None:
            w_rPr = OxmlElement('w:rPr')
            # Insert at beginning to be safe with schema order
            parent_node.insert(0, w_rPr)
        
        # 2. Ensure w:color exists
        color_node = w_rPr.find(qn('w:color'))
        if color_node is None:
            color_node = OxmlElement('w:color')
            w_rPr.append(color_node)
        
        # 3. Set HEX Value
        color_node.set(qn('w:val'), hex_color)