"""
Pipeline module for code extraction and processing.

Main components:
- code_extract: Extract fault and component codes from free text
- pipeline: Main pipeline for processing claims with language detection and translation
- Other specialized processors: dtc_lookup, extractor, classifier, etc.
"""

from .code_extract import extract_codes, augment_dataframe
from .pipeline import run_pipeline

__all__ = [
    'extract_codes',
    'augment_dataframe',
    'run_pipeline',
]
