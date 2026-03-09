"""
MEDIA OBJECTS PACKAGE (The Visual Assets Engine)
------------------------------------------------
This package handles all non-text graphical elements within the document.

Primary Components:
1. MediaController: The main Facade used to insert Images, Textboxes, and Charts 
   into the document flow via the Router.
2. ImageLoader: A shared utility exposed for other modules (like Layout/Tables)
   to fetch and cache images (e.g., for background images/watermarks).

Logic Flow:
Router -> MediaController -> (PositioningEngine + ShapeFactory + ImageLoader) -> XmlFactory
"""

# The Orchestrator (Used by Router)
from .media_controller import MediaController

# The Resource Utility (Used by Router, Layout, & Tables for assets)
from .image_loader import ImageLoader

# Explicit API definition
__all__ = [
    'MediaController',
    'ImageLoader'
]