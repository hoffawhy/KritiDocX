"""
XML FACTORY PACKAGE (The Output Engine)
---------------------------------------
This package is responsible for generating low-level MS Word OpenXML (OOXML).

Architecture:
    - **Facade Pattern:** Use `XmlBuilder` for all XML operations.
    - **Separation of Concern:** This layer handles Tags, Namespaces, and Schema Ordering.
      It does NOT perform business logic calculations (Math/Units), only rendering.

Key Classes:
    - XmlBuilder: The main interface for Controllers/Objects.
    - XmlBase: Provides standard creation methods and Schema Sorting.
"""

# The Main Public Interface
# बाहरी दुनिया को केवल इसी की जरूरत होनी चाहिए
from .xml_builder import XmlBuilder

# The Foundation (Optional for extension)
# अगर भविष्य में कोई कस्टम Factory बनानी हो, तो Base की जरूरत पड़ सकती है
from .base import XmlBase

# Explicitly define the Public API
# 'from kritidocx.xml_factory import *' करने पर सिर्फ यही दो मिलेंगे
__all__ = [
    'XmlBuilder',
    'XmlBase'
]