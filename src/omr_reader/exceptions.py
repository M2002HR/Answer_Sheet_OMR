class OMRReaderError(Exception):
    """Base exception for the OMR reader."""


class ImageLoadError(OMRReaderError):
    """Raised when an image cannot be loaded."""


class TemplateValidationError(OMRReaderError):
    """Raised when a template file is invalid."""


class AlignmentError(OMRReaderError):
    """Raised when sheet alignment fails."""


class OutputWriteError(OMRReaderError):
    """Raised when an output artifact cannot be written."""
