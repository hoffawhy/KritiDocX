"""
CUSTOM EXCEPTIONS
-----------------
Defines standard errors for the KritiDocX library.
Allows users to catch specific library failures.
"""

class KritiDocXError(Exception):
    """Base exception for all KritiDocX errors."""
    pass

class InputNotFoundError(KritiDocXError):
    """Raised when the input HTML/Markdown file is missing."""
    pass

class ConversionFailedError(KritiDocXError):
    """Raised when the pipeline fails unexpectedly."""
    pass