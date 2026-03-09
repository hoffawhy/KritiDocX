"""
OMML ENGINE (The LaTeX to Word XML Converter)
---------------------------------------------
Responsibility:
Converts Clean LaTeX string -> MathML -> Word OMML (Office Math Markup Language).

Pipeline:
1. LaTeX String -> MathML XML (via 'latex2mathml' library).
2. MathML XML -> OMML XML (via 'lxml' XSLT Transformation).
3. OMML Post-Processing -> Cleaning glitches (Empty boxes, Ghost text).
4. OxmlElement creation -> Returns python-docx object.

Dependency:
- latex2mathml: Python lib for LaTeX parsing.
- lxml: High-performance XML toolkit.
- MML2OMML.XSL: The stylesheet provided by Microsoft (Located in assets).
"""
import importlib.resources as pkg_resources
import os
import logging
from kritidocx.config.settings import AppConfig
from kritidocx.xml_factory.xml_builder import XmlBuilder
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# External Libraries Check
try:
    from latex2mathml.converter import convert as latex_to_mml
    from lxml import etree
    DEPENDENCIES_INSTALLED = True
except ImportError:
    # यह लाइन जरुरी है ताकि Unit Test को 'latex_to_mml' नाम मिल सके, 
    # भले ही लाइब्रेरी इनस्टॉल न हो।
    latex_to_mml = None  
    etree = None
    DEPENDENCIES_INSTALLED = False

logger = logging.getLogger("MyDocX_Math")

class OmmlEngine:
    """
    Stateful engine to handle XSLT Loading and Transformation.
    """

    # Singleton instance for XSLT transformer to avoid re-parsing per equation
    _xslt_transformer = None
    _is_ready = False

    def __init__(self):
        """Initializes and loads XSLT if not already loaded."""
        if not DEPENDENCIES_INSTALLED:
            logger.error("Missing Libraries: 'latex2mathml' or 'lxml'. Math will fallback to text.")
            return

        if not OmmlEngine._xslt_transformer:
            self._load_xslt_resources()

    def _load_xslt_resources(self):
        """Loads the MML2OMML.XSL stylesheet using importlib."""
        try:
            # यह तरीका 'kritidocx.assets.templates' पैकेज से फाइल को सुरक्षित रूप से उठाता है
            # चाहे लाइब्रेरी zip फाइल के रूप में ही क्यों न हो।
            import kritidocx.assets.templates as template_pkg
            
            with pkg_resources.path(template_pkg, "MML2OMML.XSL") as xsl_path:
                if not os.path.exists(xsl_path):
                    OmmlEngine._is_ready = False
                    return
                
                xslt_doc = etree.parse(str(xsl_path))
                OmmlEngine._xslt_transformer = etree.XSLT(xslt_doc)
                OmmlEngine._is_ready = True
        except Exception as e:
            logger.error(f"Failed to load XSLT via importlib: {e}")
            OmmlEngine._is_ready = False

    # =========================================================================
    # 🔄 CORE CONVERSION LOGIC
    # =========================================================================

    def _patch_mathml_tree(self, mml_tree):
        """
        [NEW FEATURE from math_core]
        Pre-process MathML XML before XSLT transformation.
        Fixes Matrix Brackets: Converts <mrow>(<mtable>)</mrow> into <mfenced>
        so Word renders expandable brackets correctly.
        """
        if mml_tree is None: return mml_tree
        
        # MathML Namespace
        ns = {'m': 'http://www.w3.org/1998/Math/MathML'}
        
        # Find all <mrow> tags that contain a Table (<mtable>)
        rows_with_table = mml_tree.xpath('.//m:mrow[m:mtable]', namespaces=ns)
        
        for row in rows_with_table:
            children = list(row)
            # We need at least 3 elements: (LeftBracket + Table + RightBracket)
            if len(children) < 3: continue 

            first = children[0]
            last = children[-1]
            # Content between brackets (usually just the mtable)
            middle = children[1:-1] 

            # Check if first and last children are Operators (<mo>) -> Brackets
            if first.tag.endswith('mo') and last.tag.endswith('mo'):
                l_char = first.text.strip() if first.text else ""
                r_char = last.text.strip() if last.text else ""

                # Valid Matrix Brackets check
                valid_brackets = ['(', ')', '[', ']', '{', '}', '|', '‖']
                if l_char in valid_brackets and r_char in valid_brackets:
                    
                    # 1. Create new <mfenced> tag (Native MathML Fenced element)
                    # Note: We use the full namespace to match lxml requirements
                    fenced = etree.Element(f"{{http://www.w3.org/1998/Math/MathML}}mfenced")
                    fenced.set('open', l_char)
                    fenced.set('close', r_char)
                    
                    # 2. Move the middle content (Table) inside the Fenced tag
                    for item in middle:
                        fenced.append(item)
                    
                    # 3. Replace the old <mrow> with the new <mfenced> in the tree
                    parent = row.getparent()
                    if parent is not None:
                        idx = parent.index(row)
                        parent.insert(idx, fenced)
                        parent.remove(row)
                        
        return mml_tree

    def convert_to_omml(self, latex_str):
        """
        Input: "E=mc^2"
        Output: python-docx OxmlElement (<m:oMath>...</m:oMath>)
        """
        if not OmmlEngine._is_ready or not latex_str:
            return None


        try:
            # [CRITICAL FIX: INPUT TYPE DETECTION]
            # यदि इनपुट पहले से ही XML (<math...>) है, तो LaTeX कन्वर्जन को बाईपास करें।
            # अन्यथा लाइब्रेरी उसे '&lt;math...' में बदलकर खराब कर देगी।
            
            clean_input = latex_str.strip()
            
            if clean_input.startswith('<') and 'math' in clean_input.lower():
                # Case A: Raw MathML Input
                mml_str = clean_input
            else:
                # Case B: LaTeX Input
                mml_str = latex_to_mml(clean_input)
            
            # --- Namespace Injection (Legacy Check) ---
            # (यह कोड वैसा ही रहेगा जैसा पहले था, बस इसे नए 'mml_str' पर लागू करें)
            if 'xmlns' not in mml_str:
                mml_str = mml_str.replace('<math', '<math xmlns="http://www.w3.org/1998/Math/MathML"', 1)

            # 3. String -> LXML Tree
            mml_tree = etree.fromstring(mml_str)

            # Apply the Matrix Patch before XSLT
            self._patch_mathml_tree(mml_tree)


            # 4. Transform (MathML -> OMML)
            omml_tree = OmmlEngine._xslt_transformer(mml_tree)
            
            # 5. Serialization & Post-Processing
            # Convert lxml object to string to pass to python-docx
            omml_string = str(omml_tree)
            
            # Remove XML Declaration <?xml...?> if present
            if '<?xml' in omml_string:
                omml_string = omml_string.split('?>', 1)[-1].strip()

            # 6. Parse into Docx Element
            from docx.oxml import parse_xml
            element = parse_xml(omml_string)

            # 7. Final Polish (Remove glitches)
            self._clean_omml_artifacts(element)

            return element

        except Exception as e:
            logger.error(f"OMML Conversion Failed for '{latex_str[:15]}...': {e}")
            return None

    # =========================================================================
    # 🧹 ARTIFACT CLEANER (The Bug Fixer)
    # =========================================================================

    def _clean_omml_artifacts(self, math_element):
        """
        [UPGRADED from math_core]
        Deep Surgery to resolve 'Dotted Box' issues and Matrix Spacing.
        Strategy:
        1. Sanitize Text (Remove invisible unicode junk).
        2. Prune Dead Branches (Empty runs).
        3. Fix Integrals (Hide empty limits, fill empty bases).
        4. Collapse Empty Sub/Superscripts.
        5. Expand Matrices (Fix row spacing).
        """
        if math_element is None: return
        
        # Local Namespace definition for XPath
        ns = {
            'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }

        # --- PASS 1: TEXT SANITIZATION ---
        # Characters causing visible blocks or layout shifts
        garbage_chars = ['\u2061', '\u2062', '\u2063', '\u2064', '\u200B', '⬚', '□', '▒', '\u2591']
        
        for t_node in math_element.xpath('.//m:t', namespaces=ns):
            text = t_node.text or ""
            original_len = len(text)
            for g in garbage_chars:
                text = text.replace(g, "")
            
            # Don't strip completely, math might need spaces, but remove junk-only nodes
            if not text.strip(): text = "" 

            if len(text) != original_len:
                t_node.text = text

        # --- PASS 2: DEAD BRANCH PRUNING ---
        runs_to_delete = []
        for r_node in math_element.xpath('.//m:r', namespaces=ns):
            # Check for empty text nodes inside run
            t_nodes = r_node.xpath('./m:t', namespaces=ns)
            is_empty_text = True
            if t_nodes and any(t.text for t in t_nodes): 
                is_empty_text = False
            
            # Check for non-text objects (pictures/styles)
            has_other = bool(r_node.xpath('./w:drawing | ./m:rPr', namespaces=ns))
            
            if is_empty_text and not has_other:
                runs_to_delete.append(r_node)

        for node in runs_to_delete:
            if node.getparent() is not None: node.getparent().remove(node)

        # --- PASS 3: INTEGRAL & SUMMATION BOX KILLER ---
        nary_nodes = math_element.xpath('.//m:nary', namespaces=ns)
        for nary in nary_nodes:
            naryPr = nary.find(qn('m:naryPr'))
            if naryPr is None:
                naryPr = OxmlElement('m:naryPr')
                nary.insert(0, naryPr)

            # Hide Empty Limits (Sub/Sup)
            sub = nary.find(qn('m:sub'))
            sup = nary.find(qn('m:sup'))
            
            if not self._has_visible_text(sub):
                self._set_hide_tag(naryPr, 'm:subHide')
            if not self._has_visible_text(sup):
                self._set_hide_tag(naryPr, 'm:supHide')
                
            # FILL THE VOID: If base (m:e) is empty, inject Space to kill the Box
            e_node = nary.find(qn('m:e'))
            if e_node is not None:
                e_content = "".join(e_node.itertext()).strip()
                if not e_content:
                    r_dummy = OxmlElement('m:r')
                    t_dummy = OxmlElement('m:t')
                    t_dummy.text = " " # Neutral space
                    r_dummy.append(t_dummy)
                    e_node.append(r_dummy)

        # --- PASS 4: STRUCTURAL COLLAPSE (Empty Sub/Superscripts) ---
        # Fixes: "x_" showing a dotted box for subscript
        for tag_name in ['m:sSub', 'm:sSup']:
            for node in math_element.xpath(f'.//{tag_name}', namespaces=ns):
                # Check the argument (sub or sup part)
                arg_tag = 'm:sub' if 'Sub' in tag_name else 'm:sup'
                arg_node = node.find(qn(arg_tag))
                
                if arg_node is not None and not "".join(arg_node.itertext()).strip():
                    # Empty argument! Collapse structure.
                    # Move base content (<m:e>) to parent and remove wrapper.
                    e_part = node.find(qn('m:e'))
                    if e_part is not None:
                        parent = node.getparent()
                        idx = parent.index(node)
                        for child in list(e_part): 
                            parent.insert(idx, child)
                            idx += 1
                        parent.remove(node)

        # --- PASS 5: SPARSE VERTICAL EXPANSION (Matrix Fix) ---
        for m_node in math_element.xpath('.//m:m', namespaces=ns):
            mPr = m_node.find(qn('m:mPr'))
            if mPr is None:
                mPr = OxmlElement('m:mPr')
                m_node.insert(0, mPr)

            # Increase Spacing & Set Rule to 1 (Multiple) -> Allows content to breathe
            for tag in ['rowSpacing', 'colSpacing']:
                node = mPr.find(qn(f'm:{tag}'))
                if node is None:
                    node = OxmlElement(f'm:{tag}')
                    mPr.append(node)
                node.set(qn('m:val'), '3') # Wider gap

            rSpRule = mPr.find(qn('m:rowSpacingRule'))
            if rSpRule is None:
                rSpRule = OxmlElement('m:rowSpacingRule')
                mPr.append(rSpRule)
            rSpRule.set(qn('m:val'), '1') # Critical for fractions in matrix

            # Force Bracket Growth (Stretch)
            parent_d = m_node.xpath('ancestor::m:d[1]', namespaces=ns)
            if parent_d:
                dPr = parent_d[0].find(qn('m:dPr'))
                if dPr is not None:
                    grow = dPr.find(qn('m:grow')) or OxmlElement('m:grow')
                    grow.set(qn('m:val'), 'on')
                    if grow not in dPr: dPr.append(grow)

            # Sync Column Center Alignment
            self._sync_matrix_mcs_internal(m_node, mPr, ns)
            
            
    def _patch_nary_properties(self, nary_node, ns):
        """Ensures Integrals look clean without placeholder boxes."""
        # 1. Get or Create Properties (<m:naryPr>)
        naryPr = nary_node.find(f"{{{ns['m']}}}naryPr")
        if naryPr is None:
            # Ideally use XmlBuilder logic, but we are inside Oxml object logic here
            from docx.oxml import OxmlElement
            naryPr = OxmlElement('m:naryPr')
            nary_node.insert(0, naryPr)

        # 2. Check Subscript (Bottom Limit)
        sub = nary_node.find(f"{{{ns['m']}}}sub")
        if not self._has_visible_text(sub):
            # Hide it
            self._set_hide_tag(naryPr, 'm:subHide')

        # 3. Check Superscript (Top Limit)
        sup = nary_node.find(f"{{{ns['m']}}}sup")
        if not self._has_visible_text(sup):
            # Hide it
            self._set_hide_tag(naryPr, 'm:supHide')

    def _has_visible_text(self, node):
        """Recursively checks if a node contains real text."""
        if node is None: return False
        return bool("".join(node.itertext()).strip())

    def _set_hide_tag(self, prop_container, tag_name):
        """Sets <m:subHide w:val="on"/> safely."""
        
        tag = prop_container.find(qn(tag_name))
        if tag is None:
            tag = OxmlElement(tag_name)
            tag.set(qn('m:val'), 'on')
            prop_container.append(tag)
        else:
            tag.set(qn('m:val'), 'on')
            
    def _sync_matrix_mcs_internal(self, m_node, mPr, ns):
        """
        [HELPER] Rebuilds Matrix Column Properties (m:mcs) to force Center Alignment.
        """
        # 1. Remove old definitions
        old_mcs = mPr.find(qn('m:mcs'))
        if old_mcs is not None:
            mPr.remove(old_mcs)

        # 2. Count columns from first row
        rows = m_node.xpath('./m:mr', namespaces=ns)
        max_cols = 0
        if rows:
            max_cols = len(rows[0].xpath('./m:e', namespaces=ns))

        # 3. Create new centered definitions
        if max_cols > 0:
            mcs = OxmlElement('m:mcs')
            for _ in range(max_cols):
                mc = OxmlElement('m:mc')
                mcPr = OxmlElement('m:mcPr')
                mcJc = OxmlElement('m:mcJc')
                mcJc.set(qn('m:val'), 'center')
                mcPr.append(mcJc)
                mc.append(mcPr)
                mcs.append(mc)
            mPr.append(mcs)       