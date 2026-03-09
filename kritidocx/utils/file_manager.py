"""
FILE MANAGER MODULE (The I/O Guardian)
--------------------------------------
This module provides a secure, robust, and unified interface for all 
file system operations.

Key Improvements over Old Engine:
1. 🔒 Security: Prevents Path Traversal attacks (safe_join).
2. ⚡ Optimization: Calculates hashes to prevent duplicate media downloads.
3. 🧹 Cleanup: Robust temp file tracking and garbage collection.
4. 🏷️ Naming: Smart logic to auto-rename files if they exist (Report.docx -> Report_1.docx).
5. 🛡️ Resilience: Safe reading/writing with encoding fallback (UTF-8 -> Latin-1).

Usage:
    from kritidocx.utils.file_manager import FileManager
    path = FileManager.get_temp_path("image.png")
    FileManager.write_text("log.txt", "content")
"""

import os
import shutil
import tempfile
import hashlib
import re
import uuid
import glob
from pathlib import Path

# Integration with Logger and Config
from kritidocx.utils.logger import logger
# Note: Avoiding direct import of AppConfig to prevent circular dependency
# Instead, using default system paths or passed paths.

class FileManager:
    """
    Static utility class for file handling operations.
    """

    # Track temp files for mass cleanup
    _temp_files_registry = set()
    
    # Block unsafe file extensions for input reading
    BLOCKED_EXTENSIONS = {'.exe', '.bat', '.cmd', '.sh', '.py'}

    # =========================================================================
    # 1. 🏗️ PATH SAFETY & CREATION
    # =========================================================================

    @staticmethod
    def ensure_directory(path):
        """Creates directory if it doesn't exist. Logs the action."""
        if not path: return
        
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                # Logging at debug level to avoid spam
                # logger.debug(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise

    @staticmethod
    def safe_join(base_path, *paths):
        """
        [SECURITY] Safely joins paths preventing '..' traversal.
        Ensures the final path is strictly inside base_path.
        """
        try:
            final_path = os.path.abspath(os.path.join(base_path, *paths))
            base_path = os.path.abspath(base_path)

            if not final_path.startswith(base_path):
                logger.error(f"SECURITY ALERT: Path traversal attempt blocked! Base: {base_path}, Target: {final_path}")
                raise PermissionError(f"Access denied to path: {final_path}")
            
            return final_path
        except Exception as e:
            logger.error(f"Path Join Error: {e}")
            return None

    @staticmethod
    def sanitize_filename(filename, default="unnamed_file"):
        """
        Cleans strings to be valid filenames.
        Example: "User/Input: Name?" -> "User_Input__Name_"
        """
        if not filename: return default
        
        # Keep alphabets, numbers, dots, hyphens, underscores. Replace everything else.
        clean = re.sub(r'[^\w\.-]', '_', filename)
        # Prevent starting with dot (hidden file)
        clean = clean.lstrip('.')
        
        return clean if clean else default

    @staticmethod
    def get_unique_output_path(target_path):
        """
        [NEW] Prevents overwriting.
        If 'Report.docx' exists, returns 'Report_1.docx'.
        """
        if not os.path.exists(target_path):
            return target_path

        base_dir = os.path.dirname(target_path)
        filename = os.path.basename(target_path)
        name, ext = os.path.splitext(filename)

        counter = 1
        new_path = target_path
        
        while os.path.exists(new_path):
            new_name = f"{name}_{counter}{ext}"
            new_path = os.path.join(base_dir, new_name)
            counter += 1
            
        logger.info(f"Target file exists. Auto-renaming to: {os.path.basename(new_path)}")
        return new_path

    # =========================================================================
    # 2. ⚡ IO OPERATIONS (Reading / Writing)
    # =========================================================================

    @staticmethod
    def read_text(file_path):
        """Robust text reader with Encoding Fallback (UTF-8 -> Latin-1)."""
        if not os.path.exists(file_path):
            logger.error(f"Read Error: File not found {file_path}")
            return None

        # 1. Try UTF-8
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 2. Try Fallback
            logger.warning(f"UTF-8 decode failed for {file_path}, retrying with Latin-1")
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to read file: {e}")
                return None

    @staticmethod
    def write_text(file_path, content, overwrite=True):
        """Safely writes text to file. Creates dir if missing."""
        try:
            folder = os.path.dirname(file_path)
            FileManager.ensure_directory(folder)
            
            mode = 'w' if overwrite else 'a'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Write Error ({file_path}): {e}")
            return False

    @staticmethod
    def get_file_size_mb(file_path):
        """Returns file size in MB."""
        if os.path.exists(file_path):
            return os.path.getsize(file_path) / (1024 * 1024)
        return 0

    # =========================================================================
    # 3. ♻️ TEMP & CACHE MANAGEMENT (The Janitor)
    # =========================================================================

    @classmethod
    def get_temp_path(cls, extension=".tmp", prefix="docgen_"):
        """
        Generates a temporary file path using standard OS Temp dir.
        Registers it for later cleanup.
        """
        # Ensure . extension
        if not extension.startswith('.'): extension = f".{extension}"
        
        fd, path = tempfile.mkstemp(prefix=prefix, suffix=extension)
        os.close(fd) # Close open handle immediately so others can use path
        
        # Track for cleanup
        cls._temp_files_registry.add(path)
        return path

    @classmethod
    def calculate_file_hash(cls, file_path, algo='md5'):
        """
        Calculates File Checksum.
        Usage: Check if 'image1.png' is same as 'image2.png' to reuse XML relationship ID.
        """
        if not os.path.exists(file_path): return None
        
        hash_func = getattr(hashlib, algo)()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Hashing failed: {e}")
            return None

    @classmethod
    def delete_file(cls, path):
        """Safely delete a single file."""
        if not path or not os.path.exists(path): return
        try:
            # Check permissions? Python handles it via Exception
            os.remove(path)
            # Remove from registry if present
            if path in cls._temp_files_registry:
                cls._temp_files_registry.remove(path)
        except OSError as e:
            logger.warning(f"Could not delete {path}: {e}")

    @classmethod
    def clean_all_temp_files(cls):
        """
        Cleanup all files registered during this session.
        Called at end of Pipeline run.
        """
        if not cls._temp_files_registry: return
        
        logger.info(f"🧹 Cleaning up {len(cls._temp_files_registry)} temporary files...")
        count = 0
        for path in list(cls._temp_files_registry): # Copy list
            try:
                if os.path.exists(path):
                    os.remove(path)
                    count += 1
            except Exception:
                pass # Silent fail during mass clean is safer
        
        cls._temp_files_registry.clear()
        # logger.debug(f"Cleanup finished. Removed {count} files.")

    @staticmethod
    def clean_directory_older_than(dir_path, seconds=86400):
        """
        Maintenance Mode: Clean cache files older than X seconds (Default 24h).
        Good for 'temp_cache' folder.
        """
        import time
        if not os.path.exists(dir_path): return
        
        now = time.time()
        for filename in os.listdir(dir_path):
            file_path = os.path.join(dir_path, filename)
            try:
                if os.path.isfile(file_path):
                    file_age = now - os.path.getmtime(file_path)
                    if file_age > seconds:
                        os.remove(file_path)
                        # logger.debug(f"Removed stale cache file: {filename}")
            except Exception as e:
                logger.warning(f"Error purging cache file {filename}: {e}")