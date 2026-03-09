"""
MATH OBJECTS PACKAGE (The Scientific Engine)
--------------------------------------------
यह पैकेज वैज्ञानिक समीकरणों (Scientific Equations) और गणितीय सूत्रों को
MS Word के Native XML (OMML) में बदलने के लिए जिम्मेदार है।

Pipeline Flow:
1. Input: LaTeX ($$ E=mc^2 $$) या MathML टैग्स।
2. Parsing: `LatexParser` गंदगी साफ़ करता है और मैट्रिक्स सिंटेक्स ठीक करता है।
3. Conversion: `OmmlEngine` XSLT का उपयोग करके इसे Word XML में बदलता है।
4. Styling: `StyleApplicator` इसमें रंग और फोंट भरता है।
5. Controller: `MathController` इसे डॉक्यूमेंट में सही जगह (Inline/Block) प्लेस करता है।

Usage:
    from kritidocx.objects.math import MathController
    ctrl = MathController(doc)
    ctrl.process_math("E=mc^2", container, ...)
"""

# The Main Orchestrator (Used by Router)
# सबसे मुख्य क्लास जिसका उपयोग सिस्टम करेगा
from .math_controller import MathController

# Utilities (Exposed for Testing/Parsers)
# यदि Markdown Parser को सिर्फ क्लीनिंग की जरूरत हो
from .latex_parser import LatexParser

# Engine (Exposed for health checks)
# यह जांचने के लिए कि क्या सिस्टम गणित रेंडर कर सकता है?
from .omml_engine import OmmlEngine

# Explicit API definition
__all__ = [
    'MathController',
    'LatexParser',
    'OmmlEngine'
]