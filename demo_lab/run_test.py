"""
========================================================================
🧪 KRITIDOCX: DEMO LABORATORY & TESTER 
========================================================================
This script is designed for you to test the power of KritiDocX instantly.
It will generate 5 different Microsoft Word (.docx) documents in the
'outputs/' directory using different rendering engines.

Feel free to modify the HTML/MD files in this folder to test your own code!
"""

import sys
import os

# --- Path setup magic to allow running this script from anywhere ---
# This ensures it finds the 'kritidocx' package from the parent folder.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from kritidocx import convert_document
except ImportError:
    print("❌ Critical Error: Could not find 'kritidocx' library.")
    print("Ensure you are running this from inside the 'demo_lab' folder,")
    print("or run 'pip install -r ../requirements.txt' first.")
    sys.exit(1)

# Helper functions for terminal aesthetics
def header(title):
    print("\n" + "=" * 50)
    print(f"🚀 RUNNING TEST: {title}")
    print("=" * 50)

def footer(success_flag, file_path):
    if success_flag:
        print(f"✅ SUCCESS! Created: {file_path}")
    else:
        print(f"❌ FAILED. Please check console for internal errors.")

# Main test runner
def run_all_tests():
    # Setup working directories relative to this file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LAYOUTS = os.path.join(BASE_DIR, "my_layouts")
    DATA = os.path.join(BASE_DIR, "my_data")
    OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

    # Ensure output directory exists before generating documents
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Welcome banner
    print(f"Welcome to KritiDocX Interactive Lab! Preparing to generate Word files...")
    print(f"Target Output Directory: {OUTPUT_DIR}")

    # =======================================================================
    # TEST 1: The Styling Engine (Typography, Margins, Borders)
    # =======================================================================
    header("01 - STANDARD REPORT (CSS to Word Typography)")
    out_1 = os.path.join(OUTPUT_DIR, "01_Generated_Report.docx")
    res_1 = convert_document(
        input_file=os.path.join(LAYOUTS, "01_standard_report.html"),
        output_file=out_1,
        # Enable Engine tracing to show how detailed the parser runs (optional)
        config={"DEBUG": False} 
    )
    footer(res_1, out_1)


    # =======================================================================
    # TEST 2: The 2D Matrix Engine (Complex Span & Col-span Logic)
    # =======================================================================
    header("02 - COMPLEX TABLE MATRIX (Handling overlapping bounds)")
    out_2 = os.path.join(OUTPUT_DIR, "02_Complex_Grid.docx")
    res_2 = convert_document(
        input_file=os.path.join(LAYOUTS, "02_complex_table.html"),
        output_file=out_2
    )
    footer(res_2, out_2)


    # =======================================================================
    # TEST 3: Form Controller (SDT Content Creation)
    # =======================================================================
    header("03 - INTERACTIVE SDT FORMS (Native Word Checkboxes/Dropdowns)")
    out_3 = os.path.join(OUTPUT_DIR, "03_Interactive_Forms.docx")
    res_3 = convert_document(
        input_file=os.path.join(LAYOUTS, "04_interactive_form.html"),
        output_file=out_3
    )
    footer(res_3, out_3)


    # =======================================================================
    # TEST 4: The Scientific Mathematical Translation
    # =======================================================================
    header("04 - NATIVE MATH (OMML XSLT Rendering of Latex)")
    out_4 = os.path.join(OUTPUT_DIR, "04_Science_Equations.docx")
    res_4 = convert_document(
        # We test direct parsing of markdown files holding pure LaTeX Data
        input_file=os.path.join(DATA, "math_and_science.md"),
        output_file=out_4
    )
    footer(res_4, out_4)


    # =======================================================================
    # TEST 5: THE HYBRID INJECTION MODE (Crown Jewel Capability)
    # =======================================================================
    header("05 - HYBRID ENGINE (Injecting dynamic Markdown inside Corporate HTML)")
    out_5 = os.path.join(OUTPUT_DIR, "05_Hybrid_Automated_Letter.docx")
    res_5 = convert_document(
        # 1. Base Design File
        input_file=os.path.join(LAYOUTS, "03_corporate_layout.html"),
        
        # 2. Data payload that fits into <main id="content"> automatically!
        data_source=os.path.join(DATA, "payload_data.md"),
        
        # 3. Target Output
        output_file=out_5,
        
        # Demonstrating real-time config overriding
        config={
            "CONTINUE_ON_ERROR": True, # Ensure 100% throughput 
        }
    )
    footer(res_5, out_5)

    # Done.
    print("\n" + "*" * 50)
    print("✨ ALL TESTS EXECUTED! Please open the 'outputs' folder and check out the DOCX files.")
    print("*" * 50 + "\n")

if __name__ == "__main__":
    run_all_tests()