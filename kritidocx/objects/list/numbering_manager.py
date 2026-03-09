"""
from kritidocx.utils.logger import logger
NUMBERING MANAGER MODULE (The List Database Admin)
--------------------------------------------------
Responsibility:
Manages the internal 'word/numbering.xml' part of the OOXML package.

Word Numbering Architecture:
1. AbstractNum (<w:abstractNum>): A "Style Class". Defines how levels look (Symbols, Indents).
2. Num (<w:num>): An "Instance". Inherits an AbstractNum. Restarts counting from 1.

Key Features:
- Cache Mechanism: Reuses AbstractNums to minimize file bloat.
- Bridge Logic: Combines StyleFactory (Visuals) and IndentMath (Geometry).
- Safety: Auto-initializes numbering part if missing.
"""

import random
from kritidocx.config.settings import AppConfig
from kritidocx.utils import logger
from kritidocx.xml_factory.xml_builder import XmlBuilder
from .style_factory import StyleFactory
from .indent_math import IndentMath

class NumberingManager:
    """
    Controller for defining and instantiating lists.
    """

    def __init__(self, doc):
        """
        :param doc: python-docx Document object.
        """
        self.doc = doc
        self.numbering_part = None
        
        # Cache mapping style types to Abstract IDs
        # e.g., {'bullet': 100, 'decimal': 101}
        self._abstract_cache = {}

    def _ensure_access(self):
        """
        Lazy-loads the numbering part reference.
        Tries to access it safely.
        """
        if self.numbering_part:
            return self.numbering_part

        try:
            self.numbering_part = self.doc.part.numbering_part
        except AttributeError:
            # Fallback if accessed too early or structure issues
            # We assume python-docx handles part creation upon first access attempt usually
            pass
        return self.numbering_part

    def create_list_instance(self, style_type='decimal', css_overrides=None):
        """
        Primary API. Returns a unique 'numId' to use in a paragraph.
        
        Flow:
        1. Check if 'AbstractNum' for this style exists.
        2. If not, create and inject it using StyleFactory + IndentMath.
        3. Create a new 'Num' (Instance) pointing to that Abstract.
        4. Return the new Instance ID.
        """
        
        if getattr(AppConfig, 'DEBUG_LISTS', False):
            logger.debug(f"   ⚙️ [NumberingManager]: Requesting Instance for Type='{style_type}'")

        
        # Ensure we have access to XML root
        part = self._ensure_access()
        if not part:
            # If docx template is somehow broken/empty, minimal recovery or fail
            # (Normally standard template has numbering part)
            logger.warning("⚠️ Critical: Numbering part missing in DOCX template.")
            return 1 # Fallback safe ID

        # -------------------------------------------------------------
        # STEP 1: GET OR CREATE ABSTRACT DEFINITION (The "Class")
        # -------------------------------------------------------------
        # Only create a new style definition if we haven't seen this type before.
        # UNLESS there are specific CSS Overrides that change the look (e.g. Image bullets)
        # For simplicity, we cache based on basic type only.
        
        abstract_id = self._abstract_cache.get(style_type)
        
        # Override logic: If heavy CSS overrides exist (rare for lists), we might force new Abstract.
        # But indentation overrides (padding) happen at Instance level (handled in ListController).
        # So caching standard abstracts is safe.

        if abstract_id is None:
            abstract_id = self._create_abstract_definition(part, style_type)
            self._abstract_cache[style_type] = abstract_id

        # -------------------------------------------------------------
        # STEP 2: CREATE LIST INSTANCE (The "Object")
        # -------------------------------------------------------------
        # Every generic list (<ul>) gets a NEW instance so it starts from 1.
        # Random unique ID for the instance
        num_id = random.randint(1000, 2000000)
        
        XmlBuilder.register_list_instance(part, num_id, abstract_id)
       
       # [DEBUG LOG]
        if getattr(AppConfig, 'DEBUG_LISTS', False):
            logger.debug(f"   🔢 [NumberingManager] Created New Instance | ID: {num_id} | Abstract: {abstract_id} | Type: {style_type}")
            
        return num_id    

    # -------------------------------------------------------------------------
    # 🏭 INTERNAL BUILDERS
    # -------------------------------------------------------------------------

    def _create_abstract_definition(self, part, style_type):
        """
        Builds the complex <w:abstractNum> structure by merging Design + Math.
        [STEP 5 FIX]: Robust ID Generation & Layout Logic.
        """
        # A. Secure ID Generation
        # हम केवल Random पर निर्भर नहीं रह सकते। हमें एक 'Safe Range' चाहिए।
        # Word के इंटरनल IDs अक्सर छोटे (0-100) होते हैं। 
        # हम 0x9000 (36864) से शुरू करेंगे ताकि टकराव (Collision) न हो।
        base_id = 0x9000 
        offset = len(self._abstract_cache) + random.randint(1, 1000)
        new_abstract_id = base_id + offset

        # B. Get Components (Visuals from StyleFactory)
        style_levels = StyleFactory.get_style_config(style_type)
        
        # C. Merge Loop (Inject Geometry/Math)
        full_levels_config = []
        
        for level_cfg in style_levels:
            lvl_idx = level_cfg['level']
            
            # [MATH INTEGRATION]
            # IndentMath से सटीक दूरी (Left Indent, Hanging) प्राप्त करें
            left, hanging = IndentMath.calculate(lvl_idx)
            
            # कॉन्फ़िगरेशन को मर्ज करें
            merged_config = level_cfg.copy()
            merged_config['left'] = left
            merged_config['hanging'] = hanging
            
            full_levels_config.append(merged_config)

        # D. XML Injection via Factory
        # नोट: NSID (Hex Signature) का निर्माण अब 'NumberingXml' फैक्ट्री के अंदर 
        # अपने आप होता है (Step 1 में सेट किया गया था)।
        XmlBuilder.register_abstract_list(part, new_abstract_id, full_levels_config)
        
        return new_abstract_id