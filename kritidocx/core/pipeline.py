"""
PIPELINE ORCHESTRATOR (The Workflow Manager)
--------------------------------------------
Responsibility:
Integrates Readers (Parsers) -> Logic (Router) -> Writer (Driver).

Key Capabilities:
1. Auto-Detection: Automatically selects HTML or Markdown parser based on input.
2. Health Checks: Verifies assets (XSLT) presence before starting.
3. Performance Metrics: Times every stage of the generation process.
4. Finalization: Saves file and optionally opens it (Auto-Launch).

Usage:
    pipeline = Pipeline()
    pipeline.run("input.md", "output.docx")
"""

import os
import sys
import subprocess
from datetime import datetime
from kritidocx.exceptions import ConversionFailedError, InputNotFoundError
from typing import Optional

# Config & Utils
from kritidocx.config import AppConfig, initialize_system
from kritidocx.utils.logger import logger
from kritidocx.utils.performance import Timer

# Core Components
from .docx_driver import DocxDriver
from .router import Router
from kritidocx.parsers.html_parser import HtmlParser
from kritidocx.parsers.markdown_parser import MarkdownParser

class Pipeline:
    """
    Main Execution Engine.
    Instantiates the entire object graph for document generation.
    """

    def __init__(self, template_path=None, config=None):
        """
        Initializes the Engine components with optional runtime config.
        """
        # 0. Apply Runtime Configuration Override (Priority)
        if config:
            AppConfig.override(config)
            
        # 1. System Bootstrap (Silent)
        initialize_system(silent=True)

        logger.info("🔧 Initializing Pipeline...")

        # 2. Build Dependency Graph
        self.driver = DocxDriver(template_path=template_path)
        self.router = Router(self.driver)
        self.html_parser = HtmlParser(self.router)
        self.md_parser = MarkdownParser(self.router)

        # 3. Validation - DISABLED
        # (Assets checking is now internal to OmmlEngine using importlib)
        # self._validate_environment()  <-- DELETE OR COMMENT THIS LINE
        
    def run(self, input_path: str, output_path: Optional[str] = None, data_source: Optional[str] = None) -> bool:
        """
        Executes the main conversion pipeline. Handles routing between Hybrid or Standard mode.
        
        Args:
            input_path (str): Filepath to read (Must be .md or .html).
            output_path (Optional[str]): Where to save. Defaults to working dir.
            data_source (Optional[str]): External payload (Markdown).

        Returns:
            bool: Success status of conversion pipeline.
        """

        if not os.path.exists(input_path):
            logger.error(f"❌ Input file not found: {input_path}")
            return False

        # Determine Output Path
        final_output = output_path
        if not final_output:
            filename = os.path.basename(input_path).rsplit('.', 1)[0] + ".docx"
            final_output = os.path.join(AppConfig.OUTPUT_DIR, filename)

        start_time = datetime.now()
        logger.info(f"🚀 Starting Conversion: {os.path.basename(input_path)}")
        
        if data_source:
            logger.info(f"   ➕ Data Source: {os.path.basename(data_source)}")
            
        logger.info(f"   📂 Target: {final_output}")

        try:
            # 1. PARSING PHASE
            with Timer("Parsing & Object Construction"):
                
                # [NEW SWITCH LOGIC]
                if data_source and os.path.exists(data_source):
                    # Hybrid Mode: HTML Template + MD Data
                    success = self._process_hybrid_input(input_path, data_source)
                else:
                    # Classic Mode: Single file
                    success = self._process_file_by_extension(input_path)
                
                if not success:
                    return False

            # 2. SAVING PHASE
            # We use the Driver's safe save (handles permission errors)
            with Timer("XML Assembly & IO"):
                self.driver.save(final_output)

            # 3. POST-PROCESSING (Auto-Open)
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✨ DONE! Completed in {elapsed:.2f} seconds.")

            if AppConfig.AUTO_OPEN_FILE and os.path.exists(final_output):
                # एब्सोल्यूट पाथ (Full Path) ज्यादा सुरक्षित होता है
                abs_output_path = os.path.abspath(final_output)
                self._open_file(abs_output_path)


            return True

        except InputNotFoundError:
            # अगर फाइल नहीं मिली, तो उसे ऊपर (User Script) तक जाने दें
            raise

        except Exception as e:
            logger.critical(f"🔥 Critical Pipeline Failure: {e}")
            # जेनेरिक क्रैश के लिए लाइब्रेरी स्पेसिफिक एरर उठाएं
            if not AppConfig.CONTINUE_ON_ERROR:
                raise ConversionFailedError(f"Document generation failed: {str(e)}") from e
            return False

    def _process_file_by_extension(self, path):
        """Selects parser strategy."""
        _, ext = os.path.splitext(path)
        ext = ext.lower()

        if ext in ['.html', '.htm']:
            logger.debug("   👉 Strategy: HTML Parser")
            self.html_parser.parse_file(path)
            return True

        elif ext in ['.md', '.markdown']:
            logger.debug("   👉 Strategy: Markdown Parser")
            # MD Parser internally converts MD -> HTML -> calls HtmlParser
            self.md_parser.parse_file(path)
            return True

        else:
            logger.error(f"❌ Unsupported file format: {ext}")
            return False

    def _process_hybrid_input(self, template_file, data_file):
        """
        [STEP 4 LOGIC]: Integrates Markdown Data into HTML Template.
        Flow: Read MD -> Convert to HTML str -> Inject into Template -> Run.
        """
        # A. Validate extensions
        # Template must be HTML
        if not template_file.lower().endswith(('.html', '.htm')):
            logger.error("❌ Hybrid Mode Error: 'input_path' must be an HTML Template file.")
            return False
            
        # Data source likely Markdown (or text)
        # Note: HTML fragment as data is also theoretically valid
        
        # B. Read Data Content
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                raw_data = f.read()
        except Exception as e:
            logger.error(f"❌ Failed to read data source: {e}")
            return False

        # C. Convert Markdown to clean HTML string
        # Using our DECOUPLED method from Step 1
        html_content_fragment = self.md_parser.convert_to_html(raw_data)
        
        if not html_content_fragment:
            logger.warning("⚠️ Warning: Data source yielded empty content.")
            return False

        # D. Inject and Run
        # Using our SURGICAL method from Step 2
        # Default target ID is 'content' (Standard convention)
        # You could expose target_id as a parameter later if needed.
        self.html_parser.parse_with_template(
            template_path=template_file, 
            injected_content_html=html_content_fragment,
            target_id="content"
        )
        
        return True


    def _open_file(self, filepath):
        """Cross-platform Auto-open Logic."""
        try:
            logger.debug(f"Attempting to open: {filepath}")
            
            if sys.platform == 'win32':
                os.startfile(filepath)
                
            elif sys.platform == 'darwin': # macOS
                subprocess.call(['open', filepath])
                
            else: # Linux / Unix
                subprocess.call(['xdg-open', filepath])
            
            logger.debug("   👀 Launched viewer successfully.")
            
        except Exception as e:
            # यह क्रिटिकल नहीं है, इसलिए सिर्फ वार्निंग दें, क्रैश न करें
            logger.warning(f"⚠️ Could not auto-open file: {e}")