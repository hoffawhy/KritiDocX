import sys
import os

# Set library path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kritidocx

print("Generating the Hero Shot...")

success = kritidocx.convert_document(
    input_file="demo_lab/my_layouts/hero_shot.html",
    output_file="outputs/KritiDocX_Hero_Shot.docx",
    config={"DEBUG": True}
)

if success:
    print("✅ Created outputs/KritiDocX_Hero_Shot.docx")
    print("👉 OPEN IT in Word, zoom out a bit, take a neat screenshot!")