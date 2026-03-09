"""
FORM OBJECTS PACKAGE (The Interactive Elements)
-----------------------------------------------
यह पैकेज HTML फॉर्म इनपुट्स (<input>, <select>, <textarea>) को
नेटिव Microsoft Word Structured Document Tags (SDT) में बदलता है।

Key Capabilities:
1. Interaction: चेकबॉक्स और ड्रॉपडाउन को क्लिक करने योग्य (Clickable) बनाना।
2. Placeholders: टेक्स्ट फील्ड्स में "Click to enter text" जैसे संकेत देना।
3. Standardization: सभी फॉर्म्स को एक समान फॉन्ट और स्टाइल में रेंडर करना।

Main Architecture:
- FormController: ट्रैफिक पुलिस (Router का इंटरफ़ेस)।
- Specific Handlers: अलग-अलग टैग्स के विशेषज्ञ।
"""

# 1. The Main Dispatcher (Used by Router)
# सबसे अधिक उपयोग होने वाली क्लास
from .form_controller import FormController

# 2. Specialized Handlers (Exposed for Direct API usage)
# यदि आप HTML के बिना सीधे कोड से फॉर्म बनाना चाहें, तो इनका उपयोग करें
from .checkbox_handler import CheckboxHandler
from .dropdown_handler import DropdownHandler
from .text_input_handler import TextInputHandler

# 3. Explicitly define public interface
__all__ = [
    'FormController',
    'CheckboxHandler',
    'DropdownHandler',
    'TextInputHandler'
]