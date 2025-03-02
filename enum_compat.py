"""
This module provides compatibility for StrEnum in older Python versions.
Import from this module instead of enum to get StrEnum regardless of Python version.
"""

import enum
from aenum import StrEnum as AEnumStrEnum

# Monkey patch the enum module to add StrEnum if it doesn't exist
if not hasattr(enum, 'StrEnum'):
    class StrEnum(str, enum.Enum):
        """Enum where members are also str instances."""
        def __str__(self):
            return self.value
            
        def __repr__(self):
            return f"{self.__class__.__name__}.{self.name}"
            
    # Add to the enum module
    enum.StrEnum = StrEnum

# For direct imports from this module
StrEnum = enum.StrEnum