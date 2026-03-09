"""
from kritidocx.utils.logger import logger
DRAWING XML FACTORY (The Graphics Architect)
--------------------------------------------
Responsibility:
Generates XML for Floating Objects (Images, Textboxes, Shapes).
Handles the complex DrawingML namespace (a:, wp:, wps:, pic:).

Core Concept:
In Word, everything floating is wrapped in an <wp:anchor>.
Inside Anchor, we have:
1. Coordinates (positionH, positionV)
2. Dimensions (extent)
3. Graphic Content (a:graphic)

Strict Schema Rules:
Elements MUST follow 'ANCHOR_ORDER' defined in base.py.
"""

from docx.oxml.ns import qn, nsmap

from kritidocx.config.settings import AppConfig
from kritidocx.utils import logger
from .base import XmlBase

# Ensure 'wps' (Word Processing Shapes) namespace is registered
if 'wps' not in nsmap:
    nsmap['wps'] = 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape'

class DrawingXml(XmlBase):
  
   
   # [NEW FROM ENGINE]: Word Schema requires rigid order inside <wp:anchor>
    ANCHOR_CHILD_ORDER = [
        'simplePos',
        'positionH',
        'positionV',
        'extent',
        'effectExtent',
        'wrapNone', 'wrapSquare', 'wrapTight', 'wrapThrough', 'wrapTopAndBottom',
        'docPr',
        'cNvGraphicFramePr',
        'graphic',
        'relativeHeight' # Important to be handled via attributes, but listing logic helpers
    ]
    
    # Global Z-Index Counter prevents overlapping collisions
    _z_base_counter = 0 
    # Counter for generating unique Shape IDs automatically if not provided
    _shape_id_counter = 1024

    @classmethod
    def _get_next_shape_id(cls):
        cls._shape_id_counter += 1
        return cls._shape_id_counter

    @classmethod
    def _get_safe_relative_height(cls, user_z_index=0):
        """
        [ENGINE CORE]: Calculates unique non-colliding Layer ID.
        Formula: Base + (Z-Index * 1000) + Counter
        """
        cls._z_base_counter += 1
        WORD_Z_BASE = 251658240  # Word Internal Base
        unique_layer_id = WORD_Z_BASE + (user_z_index * 1000) + cls._z_base_counter
        return str(int(unique_layer_id))

    @staticmethod
    def _enforce_sorting(anchor_element):
        """
        [ENGINE CORE]: Re-orders children to match ECMA strict requirement.
        Relies on XmlBase.sort_element_children
        """
        # DrawingXml inherited from XmlBase, so we can use cls methods or parent
        DrawingXml.sort_element_children(anchor_element, DrawingXml.ANCHOR_CHILD_ORDER)

    @staticmethod
    def _create_pos_axis(axis_tag, rel_from, value, mode='absolute'):
        """
        Creates <wp:positionH/V>.
        mode: 'absolute' (using posOffset) OR 'align' (using align tag)
        """
        pos = XmlBase.create_element(axis_tag)
        XmlBase.create_attribute(pos, 'relativeFrom', rel_from)
        
        if mode == 'align':
            # Case: <wp:align>right</wp:align>
            align_node = XmlBase.create_element('wp:align')
            align_node.text = str(value)
            pos.append(align_node)
        else:
            # Case: <wp:posOffset>14400</wp:posOffset>
            offset_node = XmlBase.create_element('wp:posOffset')
            offset_node.text = str(value)
            pos.append(offset_node)
            
        return pos

    # =========================================================================
    # 1. ⚓ THE ANCHOR BUILDER (Root Wrapper)
    # =========================================================================

    @classmethod
    def create_anchor(cls, pos_config):
        """
        Generates the container <wp:anchor> with layout settings.
        pos_config dictionary requirements:
        {
            'simple': bool, 
            'distL': int, 'distT': int... 
            'behind_doc': bool, 
            'locked': bool, 
            'layout_in_cell': bool,
            'z_index': int
        }
        """
        anchor = cls.create_element('wp:anchor')
        
        # 1. Standard Attributes
        cls.create_attribute(anchor, 'simplePos', '0')
        cls.create_attribute(anchor, 'relativeHeight', cls._calculate_rel_height(pos_config.get('z_index', 0)))
        cls.create_attribute(anchor, 'behindDoc', '1' if pos_config.get('behind_doc') else '0')
        cls.create_attribute(anchor, 'locked', '1' if pos_config.get('locked') else '0')
        cls.create_attribute(anchor, 'layoutInCell', '1' if pos_config.get('layout_in_cell', True) else '0')
        # --- [UPDATE START: Overlap Control] ---
        # फ्लोटिंग (wrap: square) के लिए यह '0' होना चाहिए, 
        # एब्सोल्यूट/ओवरले (draft stamp) के लिए '1'।
        # अगर config में allow_overlap 'False' है, तो इसे 0 सेट करें। डिफ़ॉल्ट True (1) है।
        can_overlap = "0" if pos_config.get('allow_overlap') is False else "1"
        cls.create_attribute(anchor, 'allowOverlap', can_overlap)
        # --- [UPDATE END] ---


        # Distance Attributes (Padding from text wrapping)
        for side in ['distT', 'distB', 'distL', 'distR']:
            cls.create_attribute(anchor, side, str(pos_config.get(side, 0)))

        return anchor

    @staticmethod
    def _calculate_rel_height(z_index):
        """Maps standard CSS Z-Index (1, 99) to Word Relative Height (High Ints)."""
        # Base constant from Word internals
        WORD_Z_BASE = 251658240 
        return str(WORD_Z_BASE + (z_index * 1000))

    # =========================================================================
    # 2. 📍 POSITIONING & SIZING
    # =========================================================================

    @classmethod
    def apply_geometry(cls, anchor_element, geom_data):
        """
        Fills the Anchor with coordinates and size.
        geom_data = {
            'pos_x': int, 'pos_y': int, 
            'align_h': 'right', 'align_v': 'top',
            'rel_h': 'column', 'rel_v': 'paragraph',
            'width_emu': int, 'height_emu': int
        }
        """
        # A. SimplePos Placeholder (Mandatory schema requirement)
        simple = cls.create_element('wp:simplePos')
        cls.create_attribute(simple, 'x', '0')
        cls.create_attribute(simple, 'y', '0')
        cls.upsert_child(anchor_element, simple, cls.ANCHOR_ORDER)

        # B. Horizontal Position
        h_val = geom_data.get('align_h')
        if h_val:
            posH = cls._create_pos_axis('wp:positionH', geom_data.get('rel_h', 'column'), h_val, mode='align')
        else:
            # Default to absolute offset
            posH = cls._create_pos_axis('wp:positionH', geom_data.get('rel_h', 'column'), geom_data.get('pos_x', 0), mode='absolute')
        cls.upsert_child(anchor_element, posH, cls.ANCHOR_ORDER)

        # C. Vertical Position
        v_val = geom_data.get('align_v')
        if v_val:
            posV = cls._create_pos_axis('wp:positionV', geom_data.get('rel_v', 'paragraph'), v_val, mode='align')
        else:
            posV = cls._create_pos_axis('wp:positionV', geom_data.get('rel_v', 'paragraph'), geom_data.get('pos_y', 0), mode='absolute')
        cls.upsert_child(anchor_element, posV, cls.ANCHOR_ORDER)

        # D. Extent (Size)
        extent = cls.create_element('wp:extent')
        cls.create_attribute(extent, 'cx', str(geom_data['width_emu']))
        cls.create_attribute(extent, 'cy', str(geom_data['height_emu']))
        cls.upsert_child(anchor_element, extent, cls.ANCHOR_ORDER)

        # E. EffectExtent (Margins around the drawing object - keep 0 usually)
        effect = cls.create_element('wp:effectExtent')
        for side in ['l', 't', 'r', 'b']: cls.create_attribute(effect, side, '0')
        cls.upsert_child(anchor_element, effect, cls.ANCHOR_ORDER)

    @classmethod
    def apply_wrapping(cls, anchor_element, wrap_type='square'):
        """
        Sets wrapping: square, tight, none (front/behind), topAndBottom.
        """
        # Determine Tag Name
        tag_map = {
            'square': 'wp:wrapSquare',
            'tight': 'wp:wrapTight',
            'none': 'wp:wrapNone',
            'through': 'wp:wrapThrough',
            'topAndBottom': 'wp:wrapTopAndBottom'
        }
        target_tag = tag_map.get(wrap_type, 'wp:wrapNone')
        
        wrap_node = cls.create_element(target_tag)
        
        if wrap_type == 'square':
            cls.create_attribute(wrap_node, 'wrapText', 'bothSides')
            
        cls.upsert_child(anchor_element, wrap_node, cls.ANCHOR_ORDER)

    # =========================================================================
    # 3. 🖼️ IMAGE INJECTION (The Graphic Frame)
    # =========================================================================

    @classmethod
    def create_image_graphic(cls, rId, name, width, height, border_props=None):
        """
        Creates Picture XML with proper 'Inset' Border Logic.
        """
        graphic = cls.create_element('a:graphic')
        graphicData = cls.create_element('a:graphicData')
        cls.create_attribute(graphicData, 'uri', "http://schemas.openxmlformats.org/drawingml/2006/picture")
        
        pic = cls.create_element('pic:pic')
        
        # 1. NV Props (Standard)
        nvPicPr = cls.create_element('pic:nvPicPr')
        cNvPr = cls.create_element('pic:cNvPr')
        cls.create_attribute(cNvPr, 'id', '0')
        cls.create_attribute(cNvPr, 'name', name)
        nvPicPr.append(cNvPr)
        nvPicPr.append(cls.create_element('pic:cNvPicPr'))
        pic.append(nvPicPr)
        
        # 2. BLIP Fill (Image Ref)
        blipFill = cls.create_element('pic:blipFill')
        blip = cls.create_element('a:blip')
        cls.create_attribute(blip, 'r:embed', rId)
        
        stretch = cls.create_element('a:stretch')
        stretch.append(cls.create_element('a:fillRect'))
        blipFill.append(blip); blipFill.append(stretch)
        pic.append(blipFill)
        
        # 3. SHAPE PROPERTIES
        spPr = cls.create_element('pic:spPr')
        
        # Transform (Size)
        xfrm = cls.create_element('a:xfrm')
        off = cls.create_element('a:off'); cls.create_attribute(off, 'x', '0'); cls.create_attribute(off, 'y', '0')
        ext = cls.create_element('a:ext'); cls.create_attribute(ext, 'cx', str(width)); cls.create_attribute(ext, 'cy', str(height))
        xfrm.append(off); xfrm.append(ext)
        spPr.append(xfrm)
        
        # Geometry
        prstGeom = cls.create_element('a:prstGeom'); cls.create_attribute(prstGeom, 'prst', 'rect')
        prstGeom.append(cls.create_element('a:avLst'))
        spPr.append(prstGeom)

        # ✅ [LOGGING SECTION FOR BORDER]
        if getattr(AppConfig, 'DEBUG_MEDIA', False):
            has_border = border_props and border_props.get('sz', 0) > 0
            logger.debug(f"   ✏️ [DrawingXml] Constructing Graphic. Border Active? {has_border}")

        if border_props and border_props.get('sz', 0) > 0:
            # 🟢 [DETAILS LOG]
            if getattr(AppConfig, 'DEBUG_MEDIA', False):
                w_val = int(border_props['sz'] * 1587.5)
                c_val = border_props.get('color')
                logger.debug(f"      ➤ Injecting <a:ln>: w={w_val}, color={c_val}, align='in'")

            ln = cls.create_element('a:ln')
            cls.create_attribute(ln, 'w', str(int(border_props['sz'] * 1587.5)))

            
            # ✅ [SOLUTION]: FORCE BORDER INSIDE (Inset)
            # यह बॉर्डर को इमेज के एरिया से बाहर निकलने से रोकेगा।
            cls.create_attribute(ln, 'algn', 'in') 
            
            # ✅ [EXTRA SAFETY]: Smooth Corners
            # तीखे कोने कभी-कभी बाहर निकल जाते हैं, उन्हें 'Round' करें।
            cls.create_attribute(ln, 'cap', 'flat')
            cls.create_attribute(ln, 'cmpd', 'sng') # Default Single Line logic anchor

            # Special style handling
            if border_props.get('val') == 'double':
                cls.create_attribute(ln, 'cmpd', 'dbl') # Double Line

            # Color
            solidFill = cls.create_element('a:solidFill')
            srgbClr = cls.create_element('a:srgbClr')
            clean_hex = border_props.get('color', '000000').replace('#', '')
            cls.create_attribute(srgbClr, 'val', clean_hex if clean_hex != 'auto' else '000000')
            solidFill.append(srgbClr)
            ln.append(solidFill)
            
            # Dash style if needed (dotted/dashed)
            # (Optional logic here if dash style needed later)

            spPr.append(ln)

        pic.append(spPr)
        graphicData.append(pic)
        graphic.append(graphicData)
        return graphic

    # =========================================================================
    # 4. 🔲 SHAPE / TEXTBOX INJECTION (WSP - Word Processing Shape)
    # =========================================================================

    @classmethod
    def create_textbox_graphic(cls, dims, style):
        """
        Creates <a:graphic> structure for a Floating Textbox.
        Uses the complex 'wps' namespace.
        
        Improvements:
        - Robust styling: Handles both Nested Dicts (from ShapeFactory) and Flat keys.
        - Correct Padding: Apply margins dynamically.
        - Rotation support: Correctly applies transform rotation.
        """
        graphic = cls.create_element('a:graphic')
        graphicData = cls.create_element('a:graphicData')
        cls.create_attribute(graphicData, 'uri', "http://schemas.microsoft.com/office/word/2010/wordprocessingShape")
        
        wsp = cls.create_element('wps:wsp')
        
        # -----------------------------------------------
        # A. Identity (Unique ID generation)
        # -----------------------------------------------
        cNvPr = cls.create_element('wps:cNvPr')
        unique_id = cls._get_next_shape_id()
        cls.create_attribute(cNvPr, 'id', str(unique_id))
        cls.create_attribute(cNvPr, 'name', f"Textbox {unique_id}")
        wsp.append(cNvPr)
        
        cNvSpPr = cls.create_element('wps:cNvSpPr')
        cls.create_attribute(cNvSpPr, 'txBox', '1') # This identifies it as a Textbox
        wsp.append(cNvSpPr)
        
        # -----------------------------------------------
        # B. Visual Properties (Colors, Lines, Transform)
        # -----------------------------------------------
        spPr = cls.create_element('wps:spPr')
        
        # 1. Transform (Size + Rotation)
        xfrm = cls.create_element('a:xfrm')
        
        # Rotation logic
        rot = style.get('rotation', 0)
        if rot != 0:
            cls.create_attribute(xfrm, 'rot', str(rot))
            
        off = cls.create_element('a:off')
        cls.create_attribute(off, 'x', '0')
        cls.create_attribute(off, 'y', '0')
        
        ext = cls.create_element('a:ext')
        cls.create_attribute(ext, 'cx', str(dims.get('width_emu', 0)))
        cls.create_attribute(ext, 'cy', str(dims.get('height_emu', 0)))
        
        xfrm.append(off)
        xfrm.append(ext)
        spPr.append(xfrm)
        
        # 2. Geometry (Rectangle default)
        prstGeom = cls.create_element('a:prstGeom')
        cls.create_attribute(prstGeom, 'prst', style.get('geom', 'rect'))
        prstGeom.append(cls.create_element('a:avLst'))
        spPr.append(prstGeom)
        
        # --- [NEW SHADOW INJECTION] ---
        shadow_cfg = style.get('shadow')
        if shadow_cfg:
            # 3D Effects Container (Must respect schema order before SolidFill?)
            # Actually DrawingML allows effectsLst after prstGeom and before/after fill depending on nesting.
            # Safe Place: Inside effectLst at end of spPr often works best or check Order.
            # Schema Order for spPr: xfrm, prstGeom, [fills], [ln], [effectLst], ...
            
            # तो इसे हम Ln (Line/Border) के बाद लगाएंगे (नीचे कोड देखें)
            pass 

        
        
        # 3. Background Fill Logic (Nested vs Flat support)
        # Priority: style['fill'] dict > style['fill_color'] string
        fill_data = style.get('fill') # Dictionary form
        fill_color_flat = style.get('fill_color') # Legacy string form
        
        if fill_data and isinstance(fill_data, dict):
            # Complex logic from ShapeFactory
            if fill_data.get('type') == 'solid':
                fill = cls.create_element('a:solidFill')
                rgb = cls.create_element('a:srgbClr')
                cls.create_attribute(rgb, 'val', fill_data.get('color', 'FFFFFF').replace('#', ''))
                fill.append(rgb)
                spPr.append(fill)
            else:
                spPr.append(cls.create_element('a:noFill')) # Transparent
        
        elif fill_color_flat:
            # Simple Logic (Backward Compatibility)
            fill = cls.create_element('a:solidFill')
            rgb = cls.create_element('a:srgbClr')
            cls.create_attribute(rgb, 'val', fill_color_flat.replace('#', ''))
            fill.append(rgb)
            spPr.append(fill)
        else:
            spPr.append(cls.create_element('a:noFill')) # Default to Transparent if nothing found

        # 4. Borders / Outline Logic
        # Priority: style['outline'] dict > style['stroke_color'] string
        ln_data = style.get('outline')
        stroke_flat = style.get('stroke_color')
        
        ln_tag = None
        
        if ln_data and isinstance(ln_data, dict):
            # --- Advanced Border Handling ---
            # XML Rule: <a:ln> tag must be omitted if no line, or <a:noFill> inside if forcing hidden
            width = ln_data.get('w', 0)
            ln_type = ln_data.get('type', 'solid')
            
            if ln_type == 'solid' and width > 0:
                ln_tag = cls.create_element('a:ln')
                cls.create_attribute(ln_tag, 'w', str(width))
                
                sFill = cls.create_element('a:solidFill')
                sRgb = cls.create_element('a:srgbClr')
                cls.create_attribute(sRgb, 'val', ln_data.get('color', '000000').replace('#', ''))
                sFill.append(sRgb)
                ln_tag.append(sFill)
                
                # Dash Handling (Solid/Dot/Dash)
                dash = ln_data.get('dash')
                if dash and dash != 'solid':
                    prstDash = cls.create_element('a:prstDash')
                    cls.create_attribute(prstDash, 'val', dash)
                    ln_tag.append(prstDash)

        elif stroke_flat:
            # --- Simple Border Handling ---
            ln_tag = cls.create_element('a:ln')
            w = style.get('stroke_weight', 9525) # Default ~0.75pt
            cls.create_attribute(ln_tag, 'w', str(w))
            
            sFill = cls.create_element('a:solidFill')
            sRgb = cls.create_element('a:srgbClr')
            cls.create_attribute(sRgb, 'val', stroke_flat.replace('#', ''))
            sFill.append(sRgb)
            ln_tag.append(sFill)
            
            # Simple Dash check
            if style.get('dash_style') and style.get('dash_style') != 'solid':
                prstDash = cls.create_element('a:prstDash')
                cls.create_attribute(prstDash, 'val', style['dash_style'])
                ln_tag.append(prstDash)

        # Append Line Tag if created
        if ln_tag is not None:
            spPr.append(ln_tag)
           
           
           
            
        if shadow_cfg:
            effectLst = cls.create_element('a:effectLst')
            
            # Create <a:outerShdw>
            outerShdw = cls.create_element('a:outerShdw')
            cls.create_attribute(outerShdw, 'blurRad', str(shadow_cfg['blurRad']))
            cls.create_attribute(outerShdw, 'dist', str(shadow_cfg['dist']))
            cls.create_attribute(outerShdw, 'dir', str(shadow_cfg['dir']))
            cls.create_attribute(outerShdw, 'algn', 'ctr') # Alignment Center relative to shape
            
            # Color
            sRgb = cls.create_element('a:srgbClr')
            cls.create_attribute(sRgb, 'val', shadow_cfg['color'])
            
            # Opacity/Alpha (Optional: 60%)
            alpha = cls.create_element('a:alpha')
            cls.create_attribute(alpha, 'val', '60000') # 60% approx
            sRgb.append(alpha)
            
            outerShdw.append(sRgb)
            effectLst.append(outerShdw)
            
            spPr.append(effectLst)  # [APPEND HERE]

        wsp.append(spPr)

        
        # -----------------------------------------------
        # C. Body Properties (Padding & Internal Wrap)
        # -----------------------------------------------
        bodyPr = cls.create_element('wps:bodyPr')
        
        # Padding Defaults (EMUs) ~0.1 inch if missing
        pad_data = style.get('padding', {})
        padding_map = {
            'lIns': pad_data.get('lIns', '91440'), 
            'tIns': pad_data.get('tIns', '45720'), 
            'rIns': pad_data.get('rIns', '91440'), 
            'bIns': pad_data.get('bIns', '45720')
        }
        
        for attr, val in padding_map.items():
            cls.create_attribute(bodyPr, attr, str(val))
            
        # Ensure text wraps properly inside the box shape
        cls.create_attribute(bodyPr, 'wrap', 'square') 
        # Prevent auto-overflow if shape size is strict
        cls.create_attribute(bodyPr, 'anchorCtr', '0')
        
        wsp.append(bodyPr)
        
        # -----------------------------------------------
        # D. Content Container (Where text actually lives)
        # -----------------------------------------------
        txbx = cls.create_element('wps:txbx')
        txbxContent = cls.create_element('w:txbxContent')
        txbx.append(txbxContent)
        wsp.append(txbx)
        
        graphicData.append(wsp)
        graphic.append(graphicData)
        
        return graphic, txbxContent
    
    
    @classmethod
    def create_textbox_structure(cls, unique_id, cx, cy, fill_color=None, border_color=None, dash_style='solid', fit_to_text=True, rotation=0, shadow_config=None):

        """
        [REVERSE ENGINEERED FIX]
        Based on valid MS Word 2016+ Schema structure.
        """
        # 1. Main Graphic Frame
        graphic = cls.create_element('a:graphic')
        graphicData = cls.create_element('a:graphicData')
        cls.create_attribute(graphicData, 'uri', "http://schemas.microsoft.com/office/word/2010/wordprocessingShape")
        
        # 2. Shape Container (WSP)
        wsp = cls.create_element('wps:wsp')
        # -------------------------------------------------------------
        # ✅ [CRITICAL FIX START]: MISSING INTERNAL IDENTITY
        # -------------------------------------------------------------
        # Rule: Every wps:wsp MUST start with wps:cNvPr
        cNvPr = cls.create_element('wps:cNvPr')
        
        # Shape का ID (एंकर के ID से अलग होना चाहिए, लेकिन हम उसी रेंज का उपयोग कर रहे हैं)
        # बेहतर सुरक्षा के लिए हम इसमें थोड़ा बदलाव कर देते हैं (e.g., id + 10000)
        # लेकिन सिंपल unique_id भी अक्सर काम करता है। हम एक सेफ 'integer' आईडी देंगे।
        safe_shape_id = str(int(unique_id) + 5000) 
        
        cls.create_attribute(cNvPr, 'id', safe_shape_id)
        cls.create_attribute(cNvPr, 'name', f"TextBox_{unique_id}")
        
        wsp.append(cNvPr)

        
        
        # A. Non-Visual Shape Properties (Removed explicit cNvPr inside to match source)
        cNvSpPr = cls.create_element('wps:cNvSpPr')
        cls.create_attribute(cNvSpPr, 'txBox', '1')
        wsp.append(cNvSpPr)
        
        # B. Visual Properties
        spPr = cls.create_element('wps:spPr')
        
        # --- [NEW] TRANSFORM (Position & Size inside Shape) ---
        xfrm = cls.create_element('a:xfrm')
        # यदि रोटेशन (60000 यूनिट्स में) मौजूद है, तो उसे XML में लगाएं
        if rotation and int(rotation) != 0:
            cls.create_attribute(xfrm, 'rot', str(rotation))

        off = cls.create_element('a:off')
        cls.create_attribute(off, 'x', "0")
        cls.create_attribute(off, 'y', "0")
        
        ext = cls.create_element('a:ext')
        # cx/cy Must be passed as Strings
        cls.create_attribute(ext, 'cx', str(cx))
        cls.create_attribute(ext, 'cy', str(cy))
        
        xfrm.append(off)
        xfrm.append(ext)
        spPr.append(xfrm)
        # ------------------------------------------------------

        # Geometry
        prstGeom = cls.create_element('a:prstGeom')
        cls.create_attribute(prstGeom, 'prst', 'rect')
        prstGeom.append(cls.create_element('a:avLst'))
        spPr.append(prstGeom)

        # Fill Color
        if fill_color:
            solidFill = cls.create_element('a:solidFill')
            srgb = cls.create_element('a:srgbClr')
            cls.create_attribute(srgb, 'val', fill_color.replace("#","").upper())
            solidFill.append(srgb)
            spPr.append(solidFill)
        else:
            # Transparent fill fallback
            spPr.append(cls.create_element('a:noFill'))

        # Border (Line) Logic with Dash Support
        ln = cls.create_element('a:ln')
        # चौड़ाई थोड़ी बढ़ा रहे हैं (9525 EMUs ~ 0.75pt -> 12700 ~ 1pt) ताकि Dash साफ दिखे
        cls.create_attribute(ln, 'w', "12700") 
        
        if border_color:
            # Color
            lnFill = cls.create_element('a:solidFill')
            lnRgb = cls.create_element('a:srgbClr')
            cls.create_attribute(lnRgb, 'val', border_color.replace("#","").upper())
            lnFill.append(lnRgb)
            ln.append(lnFill)
            
            # 🟢 [FIX: DASH STYLES]
            # Word PrstDash Values: 'solid', 'dash', 'dot', 'sysDash', 'sysDot', etc.
            valid_dashes = {'dashed': 'dash', 'dotted': 'sysDot', 'solid': 'solid', 'double': 'solid'}
            # HTML (dashed) -> Word (dash) mapping
            word_dash_val = valid_dashes.get(dash_style, 'solid')
            
            if word_dash_val != 'solid':
                prstDash = cls.create_element('a:prstDash')
                cls.create_attribute(prstDash, 'val', word_dash_val)
                ln.append(prstDash)
        else:
            # No Border
            ln.append(cls.create_element('a:noFill'))
            
        spPr.append(ln)
        
        # ----------------------------------------------------
        # 🔥 ADDED: SHADOW LOGIC (यहाँ जोड़ें, wsp append से पहले)
        # ----------------------------------------------------
        if shadow_config:
            effectLst = cls.create_element('a:effectLst')
            
            # Outer Shadow Tag
            shdw = cls.create_element('a:outerShdw')
            cls.create_attribute(shdw, 'blurRad', str(shadow_config['blurRad']))
            cls.create_attribute(shdw, 'dist', str(shadow_config['dist']))
            cls.create_attribute(shdw, 'dir', str(shadow_config['dir']))
            cls.create_attribute(shdw, 'algn', 'ctr') # Center alignment works well
            cls.create_attribute(shdw, 'rotWithShape', '0') # Don't rotate shadow with box

            # Color
            sRgb = cls.create_element('a:srgbClr')
            clean_col = str(shadow_config.get('color', '000000')).replace("#","").upper()
            cls.create_attribute(sRgb, 'val', clean_col)
            
            # Transparency (Word Default Shadow is often 50-60% alpha)
            # 60,000 units roughly equals visible but subtle.
            alpha = cls.create_element('a:alpha')
            cls.create_attribute(alpha, 'val', '60000') 
            sRgb.append(alpha)
            
            shdw.append(sRgb)
            effectLst.append(shdw)
            spPr.append(effectLst)
        # ----------------------------------------------------

        wsp.append(spPr)

        # C. Text Box Content Container
        txbx = cls.create_element('wps:txbx')
        txbxContent = cls.create_element('w:txbxContent')
        txbx.append(txbxContent)
        wsp.append(txbx)

        # ========================================================
        # D. Body Properties (PROPERTIES CONFLICT FIX)
        # ========================================================
        bodyPr = cls.create_element('wps:bodyPr')
        
        # बेस एट्रिब्यूट्स (जो हमेशा रहेंगे)
        attrs = {
            'rot': "0", 'spcFirstLastPara': "0", 
            'vert': "horz", 'wrap': "square", 
            'lIns': "91440", 'tIns': "45720", 'rIns': "91440", 'bIns': "45720",
            'numCol': "1", 'spcCol': "0", 'anchor': "t", 'anchorCtr': "0", 'compatLnSpc': "1"
        }

        # [CRITICAL LOGIC] : Overflow vs AutoFit
        if fit_to_text:
            # अगर AutoFit है, तो Overflow attributes न लगाएं (Crash से बचने के लिए)
            pass 
        else:
            # अगर Fixed Size (noAutoFit) है, तो Overflow allow करें
            attrs['vertOverflow'] = "overflow"
            attrs['horzOverflow'] = "overflow"

        # Apply Attributes
        for k, v in attrs.items():
            cls.create_attribute(bodyPr, k, v)

        # Mandatory Preset Text Warp (Same as before)
        prstTxWarp = cls.create_element('a:prstTxWarp')
        cls.create_attribute(prstTxWarp, 'prst', 'textNoShape')
        prstTxWarp.append(cls.create_element('a:avLst'))
        bodyPr.append(prstTxWarp)
        
        # AutoFit Logic tag append (Same as before)
        if fit_to_text:
            bodyPr.append(cls.create_element('a:spAutoFit'))
        else:
            bodyPr.append(cls.create_element('a:noAutofit'))


        wsp.append(bodyPr)
        
        graphicData.append(wsp)
        graphic.append(graphicData)

        return graphic, txbxContent
    
    
    @classmethod
    def create_absolute_anchor(cls, graphic_element, extent_info, coords, unique_id,force_wrap=False):
        """
        [STEP 2 LAYOUT] 
        Creates an Absolute Positioned Anchor (CSS: position: absolute/fixed).
        Accepts raw EMUs for X/Y coordinates.
        """
        # 1. Create Base Anchor
        anchor = cls.create_element('wp:anchor')
        
        # Default flags
        cls.create_attribute(anchor, 'simplePos', "0")
        cls.create_attribute(anchor, 'locked', "0")
        cls.create_attribute(anchor, 'layoutInCell', "1")
        
        # [NEW FIX]: Allow overlap control based on config
        # फ्लोटिंग रैपिंग के लिए ओवरलैप बंद होना चाहिए (0), 
        # एब्सोल्यूट/ओवरले इमेजेस के लिए यह चालू होना चाहिए (1)
        can_overlap = "1" if coords.get('allow_overlap', True) else "0"
        cls.create_attribute(anchor, 'allowOverlap', can_overlap)
        
        # Z-INDEX LOGIC
        # Negative z-index means behindDoc=1
        is_behind = "1" if coords.get('z_index', 0) < 0 else "0"
        cls.create_attribute(anchor, 'behindDoc', is_behind)
        
        # RelativeHeight (Standard "bring to front" layering int)
        # Shift CSS z-index (e.g. 99) to Word relativeHeight base
        z_val = coords.get('z_index', 0)
        rel_h = cls._get_safe_relative_height(z_val)
        cls.create_attribute(anchor, 'relativeHeight', rel_h)

        # [CRITICAL FIX]: Trust the Engine!
        # PositioningEngine ने पहले ही बहुत मेहनत करके 'rel_h' और 'rel_v' 
        # (जैसे 'page', 'margin') तय कर दिए हैं। 
        # राइटर को उन्हें override नहीं करना चाहिए, बल्कि उन्हें ही use करना चाहिए।
        
        # 'column' और 'paragraph' सुरक्षित डिफ़ॉल्ट हैं
        h_base = coords.get('rel_h', 'column') 
        v_base = coords.get('rel_v', 'paragraph')
        
        # SimplePos (Place-holder)
        simplePos = cls.create_element('wp:simplePos')
        cls.create_attribute(simplePos, 'x', "0"); cls.create_attribute(simplePos, 'y', "0")
        anchor.append(simplePos)

        # X (Horizontal) Position - [UPDATED FIX]
        # Check alignment first, then fallback to absolute offset
        h_val = coords.get('align_h')
        if h_val:
            posH = cls._create_pos_axis('wp:positionH', h_base, h_val, mode='align')
        else:
            x_off = coords.get('pos_x', 0)
            posH = cls._create_pos_axis('wp:positionH', h_base, x_off, mode='absolute')
        anchor.append(posH)

        # Y (Vertical) Position - [UPDATED FIX]
        v_val = coords.get('align_v')
        if v_val:
            posV = cls._create_pos_axis('wp:positionV', v_base, v_val, mode='align')
        else:
            y_off = coords.get('pos_y', 0)
            posV = cls._create_pos_axis('wp:positionV', v_base, y_off, mode='absolute')
        anchor.append(posV)


        # Extent (Size) - Uses Pre-calculated EMUs
        ext = cls.create_element('wp:extent')
        cls.create_attribute(ext, 'cx', str(coords.get('width', 1000)))
        cls.create_attribute(ext, 'cy', str(coords.get('height', 1000)))
        anchor.append(ext)

        # Mandatory Effect Extent (Zero margins)
        effExt = cls.create_element('wp:effectExtent')
        for s in ['l', 't', 'r', 'b']: cls.create_attribute(effExt, s, "0")
        anchor.append(effExt)

        # Wrap None (Absolute divs usually sit on top)
        # z_index चेक करें (हमने इसे ऊपर 'z_val' या coords से निकाला होगा)
        z_val = coords.get('z_index', 0)

        # [CRITICAL FIX: CSS LAYOUT EMULATION]
        # HTML/CSS में, Absolute/Fixed/Transformed एलिमेंट्स डॉक्यूमेंट फ्लो से बाहर होते हैं।
        # वे टेक्स्ट को धक्का (Reflow) नहीं देते, वे बस ओवरलैप करते हैं।
        # Word का 'wrapSquare' टेक्स्ट को तोड़ देता है (जैसा कि इमेज में 'Mission...Abstract' के साथ हुआ)।
        # इसलिए, हम डिफ़ॉल्ट रूप से 'wrapNone' (In Front of / Behind Text) का उपयोग करेंगे।
        
        # पुराना z-index check केवल लेयरिंग (Layering) के लिए ठीक है, रैपिंग के लिए नहीं।
        
        # [UPDATED LOGIC] Switch based on input parameter
        if force_wrap:
             # Case A: Wrap Square (Text को धक्का देगा)
             wrapSq = cls.create_element('wp:wrapSquare')
             cls.create_attribute(wrapSq, 'wrapText', "bothSides")
             anchor.append(wrapSq)
        else:
             # Case B: Wrap None (Overlay/Transparent) - Default
             anchor.append(cls.create_element('wp:wrapNone'))


        # Doc Props
        docPr = cls.create_element('wp:docPr')
        cls.create_attribute(docPr, 'id', str(unique_id))
        cls.create_attribute(docPr, 'name', f"Shape_{unique_id}")
        anchor.append(docPr)

        # Locks
        cNv = cls.create_element('wp:cNvGraphicFramePr')
        anchor.append(cNv)

        # Content
        anchor.append(graphic_element)

        # Schema Enforcement (Using existing sorter)
        cls._enforce_sorting(anchor)

        return anchor