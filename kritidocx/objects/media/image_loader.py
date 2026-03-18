"""
IMAGE LOADER MODULE (The Resource Manager)
------------------------------------------
Responsibility:
Fetch, Validate, and Prepare images for insertion.

Features:
1. Sources: HTTP(S), Local Paths, Base64 Data Strings.
2. Robustness: Never crashes document generation; returns a placeholder on failure.
3. Optimization: Caches downloaded images to prevent redundant network calls.
4. Analysis: Reads metadata (DPI, Width, Height) using Pillow.

Dependency:
- PIL (Pillow): For image processing.
- Requests: For downloading.
"""

import os
import requests
import hashlib
import base64
import tempfile
import io
import re
import importlib.resources as pkg_resources
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from kritidocx.config.settings import AppConfig
# If we have a central logger, use it. Else use standard.
import warnings
import urllib3  # इसे सीधे इम्पोर्ट करें

# SSL वार्निंग को म्यूट करें
warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)
    
try:
    from kritidocx.utils.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger("MyDocX_ImageLoader")

class ImageLoader:
    """
    Central Logic for acquiring Image Resources.
    """

    # Image cache to track URL -> TempPath
    # Prevents downloading "logo.png" 50 times for 50 headers.
    _cache = {}

    @classmethod
    def get_processed_image(cls, src_string, style_data=None):

        """
        MASTER METHOD: Accepts any image source string.
        Returns: (path_to_valid_file, metadata_dict)
        """
        if not src_string:
            return cls._generate_error_placeholder("No Source Provided")

        # 1. Try resolving the resource
        local_path = None
        error_msg = None

        try:
            # Case A: Base64 String
            if src_string.startswith('data:image'):
                local_path = cls._handle_base64(src_string)
            
            # Case B: Web URL (http/https)
            elif src_string.startswith(('http://', 'https://')):
                local_path = cls._handle_url(src_string)
            
            # Case C: Local File Path
            else:
                local_path = cls._handle_local_path(src_string)

        except Exception as e:
            error_msg = f"Process Error: {str(e)[:50]}..."
            local_path = None

        # 2. Analyze the result
        if local_path and os.path.exists(local_path):
            try:
                # Open with Pillow to get dimensions & verify integrity
                metadata = cls._analyze_image_data(local_path)
                return local_path, metadata
            except Exception as e:
                logger.error(f"Image Corruption: {src_string} - {e}")
                error_msg = "Corrupt Image File"
        
        # अंत में Fallback को style_data पास करें
        if not local_path or not os.path.exists(local_path):
            error_msg = error_msg or "File Not Found"
            # यहाँ अब style_data पास होगा
            placeholder_path, dims = cls._generate_error_placeholder(error_msg, src_string, style_data)
            return placeholder_path, dims

    # =========================================================================
    # 🕵️ SOURCE HANDLERS
    # =========================================================================

    @classmethod
    def _handle_local_path(cls, path):
        """Checks absolute paths or internal library assets."""
        
        # 1. Check direct absolute path
        if os.path.exists(path):
            return os.path.abspath(path)
        
        # 2. Check in Library Internal Assets
        try:
            filename = os.path.basename(path)
            
            # लाइब्रेरी के अंदर images पैकेज को इंपोर्ट करें
            # ध्यान दें: आपकी __init__.py फाइलों के कारण Python इसे एक मॉड्यूल मानेगा
            import kritidocx.assets.images as img_pkg
            
            # सुरक्षित तरीका (Resource Check)
            # is_resource सिर्फ 3.9+ में है, इसलिए हम सीधा context manager try करेंगे
            # अगर फाइल नहीं मिली, तो यह अपने आप Exception में जाएगा
            
            # नोट: 'with' ब्लॉक के बाहर path का उपयोग करने के लिए 
            # हमें इसे स्ट्रिंग में कन्वर्ट करके तुरंत रिटर्न नहीं करना चाहिए 
            # क्योंकि context manager बंद होते ही temp फाइल गायब हो सकती है (zip के मामले में)।
            # लेकिन साधारण फोल्डर संरचना के लिए 'str(p)' काम करता है।
            
            with pkg_resources.path(img_pkg, filename) as p:
                if p.exists():
                    return str(p)

        except (ImportError, TypeError, FileNotFoundError, Exception):
            # अगर लाइब्रेरी के एसेट्स में नहीं मिला, तो पुराने तरीके से चेक करें
            pass

        # 3. Fallback: Check using AppConfig paths (for dev mode consistency)
        internal_p = os.path.join(AppConfig.INTERNAL_ASSETS_DIR, "images", os.path.basename(path))
        if os.path.exists(internal_p): 
            return internal_p
        
        return None

    @classmethod
    def _handle_url(cls, url):
        """Downloads web image with Caching."""
        
        # 1. Check Memory Cache
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        if url_hash in cls._cache:
            path = cls._cache[url_hash]
            if os.path.exists(path):
                return path
            else:
                # यदि फाइल सिस्टम पर नहीं है, तो उसे कैश मेमोरी से भी तुरंत डिलीट करें
                del cls._cache[url_hash]

        # 2. Setup Request
        try:
            # Using headers from Config to bypass bot protection
            response = requests.get(
                url, 
                headers=AppConfig.HTTP_HEADERS, 
                timeout=AppConfig.REQUEST_TIMEOUT, 
                verify=False # SSL Verify OFF (Risk accepted for robustness)
            )
            response.raise_for_status() # Check for 404
            
            # 3. Determine Extension
            content_type = response.headers.get('content-type', '')
            ext = '.png' # Default
            if 'jpeg' in content_type: ext = '.jpg'
            elif 'gif' in content_type: ext = '.gif'
            elif 'bmp' in content_type: ext = '.bmp'
            elif 'svg' in content_type: return None # SVG Not supported directly in python-docx yet
            
            # 4. Save to Temp (Safe Dir checking)
            safe_temp_dir = AppConfig.TEMP_DIR if os.path.exists(AppConfig.TEMP_DIR) else None
            fd, tmp_path = tempfile.mkstemp(prefix=f"web_img_{url_hash[:6]}_", suffix=ext, dir=safe_temp_dir)
            with os.fdopen(fd, 'wb') as f:
                f.write(response.content)
            
            # 5. Store in Cache (Secured against infinite RAM growth)
            if AppConfig.CACHE_DOWNLOADED_IMAGES:
                cls._cache[url_hash] = tmp_path
                
                # 🛑 MEMORY OPTIMIZATION: कैश में केवल ताज़ा 50 या 100 फाइलें ही रहने दें
                if len(cls._cache) > 100:
                    # Python 3.7+ में डिक्शनरी क्रम बनाए रखती है। सबसे पहली Key 'Oldest' होती है।
                    oldest_key = next(iter(cls._cache))
                    old_path = cls._cache.pop(oldest_key)
                    
                    # फालतू फाइल को डिस्क (Server /tmp) से भी उड़ा दें ताकि स्पेस खाली रहे
                    try:
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception:
                        pass
                
            return tmp_path

        except Exception as e:
            logger.warning(f"Download failed: {url} -> {e}")
            return None

    @classmethod
    def _handle_base64(cls, data_str):
        """
        Decodes 'data:image/png;base64,....'.
        [ROBUST UPDATE]: Handles Unquote, Newlines, and Padding.
        """
        import binascii
        import urllib.parse

        try:
            # 1. Clean URL Encoding (e.g. data:image/png;base64,%20ABC...)
            clean_str = urllib.parse.unquote(data_str).strip()

            # 2. Extract Data Payload
            if ',' in clean_str:
                _, encoded = clean_str.split(',', 1)
            else:
                encoded = clean_str

            # 3. 🛡️ SUPER CLEANER: Remove whitespace/newlines (The Root Cause)
            encoded = "".join(encoded.split()) 

            # 4. 🛡️ PADDING FIX: Base64 must be divisible by 4
            missing_padding = len(encoded) % 4
            if missing_padding:
                encoded += '=' * (4 - missing_padding)

            # 5. Decode
            img_data = base64.b64decode(encoded)
            
            # Create Unique Name
            # Use strict alphanumeric only for filename safety (avoid Windows path issues)
            safe_hash = hashlib.md5(img_data).hexdigest()[:10]
            
            safe_temp_dir = AppConfig.TEMP_DIR if os.path.exists(AppConfig.TEMP_DIR) else None
            fd, tmp_path = tempfile.mkstemp(prefix=f"b64_{safe_hash}_", suffix=".png", dir=safe_temp_dir)
            with os.fdopen(fd, 'wb') as f:
                f.write(img_data)
                
            return tmp_path

        except (binascii.Error, ValueError, Exception) as e:
            # डीबग के लिए: कंसोल में error दिखाएं ताकि पता चले क्या फटा
            logger.error(f"   ⚠️ Base64 Decode Failed: {str(e)}") 
            return None

    # =========================================================================
    # 📊 ANALYSIS & UTILS
    # =========================================================================

    @staticmethod
    def _analyze_image_data(path):
        """Opens image to get physical dimensions."""
        with Image.open(path) as img:
            # DPI can be None in some formats
            info = img.info
            dpi = info.get('dpi', (96, 96)) 
            if not dpi: dpi = (96, 96)
            
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'dpi': dpi,
                'aspect_ratio': img.width / (img.height or 1)
            }

    @staticmethod
    def _generate_error_placeholder(error_text="Image Error", original_src="", style_data=None):
        """
        [DYNAMIC SCALE FIX]: Generates placeholder based on CSS Width/Height.
        Ensures the box stays within limits and looks good.
        """
        from kritidocx.basics.unit_converter import UnitConverter
        from kritidocx.config.constants import DocConstants

        # 1. डायनामिक साइज़ कैलकुलेशन (Dimensions Logic)
        # डिफ़ॉल्ट आकार: 400x300
        w_px = 400
        h_px = 300

        if style_data:
            css_w = style_data.get('width')
            css_h = style_data.get('height')

            # अगर HTML में % है, तो उपलब्ध पिक्सेल एरिया (लगभग 624px ए4 के लिए) के अनुसार लें
            if css_w:
                if '%' in str(css_w):
                    pct = float(str(css_w).replace('%', ''))
                    w_px = int(6.5 * 96 * (pct / 100.0)) # A4 writable is ~6.5 inch
                else:
                    # Convert '200px' or '2in' to px (via Twips conversion factor for safety)
                    w_px = UnitConverter.to_twips(str(css_w)) // 15 # 1px = 15 twips
            
            if css_h:
                if '%' in str(css_h):
                    h_px = 250 # % height Word में अनिश्चित होती है, सुरक्षित रखें
                else:
                    h_px = UnitConverter.to_twips(str(css_h)) // 15
            elif css_w and not css_h:
                # एस्पेक्ट रेश्यो (4:3) बनाए रखें अगर सिर्फ width दी है
                h_px = int(w_px * 0.75)

        # सुरक्षा (Constraint Check): बहुत छोटा (Unreadable) न होने दें
        final_w = max(120, min(w_px, 1200)) # 1200px max
        final_h = max(60, min(h_px, 1000))

        # 2. चित्र निर्माण (Image Generation)
        try:
            img = Image.new('RGB', (final_w, final_h), color='#F2F2F2')
            draw = ImageDraw.Draw(img)
            
            # डेंजर रेड बॉर्डर
            border_col = '#D9534F'
            draw.rectangle([(0,0), (final_w-1, final_h-1)], outline=border_col, width=4)
            
            # X Mark (पतली ग्रे रेखाएं)
            draw.line([(0, 0), (final_w, final_h)], fill='#E6E6E6', width=2)
            draw.line([(0, final_h), (final_w, 0)], fill='#E6E6E6', width=2)
            
            # 3. टेक्स्ट अलाइनमेंट (Text Placement Logic)
            try: font = ImageFont.load_default()
            except: font = None

            mid_x = final_w // 2
            mid_y = final_h // 2

            # यदि बॉक्स बहुत छोटा है, तो कम जानकारी दिखाएं
            is_mini = final_h < 100
            
            if not is_mini:
                draw.text((20, mid_y - 30), "[MISSING IMAGE]", fill=border_col, font=font)
                draw.text((20, mid_y), f"Status: {error_text[:20]}", fill='#555555', font=font)
                
                clean_src = os.path.basename(original_src or "")[:35]
                draw.text((20, mid_y + 25), f"File: {clean_src}", fill='#888888', font=font)
            else:
                # Mini Box view
                draw.text((10, mid_y - 10), "IMAGE ERROR", fill=border_col, font=font)

            # 4. Save & Registry
            fd, tmp_path = tempfile.mkstemp(prefix="err_", suffix=".png", dir=AppConfig.TEMP_DIR)
            with os.fdopen(fd, 'wb') as f:
                img.save(f, format="PNG")
                
            # Registry Metadata passback
            return tmp_path, {'width': final_w, 'height': final_h}

        except Exception as e:
            logger.error(f"⚠️ Placeholder Crash: {e}")
            return None, {'width': 100, 'height': 50}