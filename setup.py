import os
from setuptools import setup, find_packages

# Read long description from README
# (ताकि PyPI पर प्रोजेक्ट का पूरा विवरण दिखे)
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kritidocx",  # पैकेज का नाम (pip install kritidocx)
    version="0.1.0.dev5",
    author="KritiDocX Team",
    author_email="your_email@example.com",
    description="A Pro-Level HTML to DOCX Converter with Math/Latex Support.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/kritidocx",
    
    # 🕵️ Source Finding Logic
    packages=find_packages(),
    
    # 🎨 Asset Inclusion (Templates & XSLT)
    # यह 'MANIFEST.in' के साथ मिलकर काम करता है
    include_package_data=True,
    
    # ⚙️ Python Compatibility
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Office/Business :: Office Suites",
    ],
    
    python_requires='>=3.8',
    
    # 📦 Required Libraries (pip इसे अपने आप डाउनलोड करेगा)
    # हमने requirements.txt की सामग्री को यहाँ डाल दिया है
    install_requires=[
        "python-docx>=0.8.11",
        "beautifulsoup4>=4.9.0",
        "lxml>=4.6.0",
        "Pillow>=8.0.0",
        "requests>=2.25.0",
        "Markdown>=3.3.0",
        "psutil>=5.8.0",
        "latex2mathml>=1.9.0",
        # For Safe imports resources in Step 2 (Optional for old Pythons)
        "importlib_resources; python_version<'3.9'", 
    ],
    
    # 🔌 Entry Point (Optional)
    # अगर आप कमांड लाइन टूल बनाना चाहते हैं: `kritidocx input.html`
    entry_points={
        'console_scripts': [
            'kritidocx=kritidocx.__main__:main',
        ],
    },
)