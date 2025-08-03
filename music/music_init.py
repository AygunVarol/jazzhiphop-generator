"""
Jazz-Hip Hop Music Generation Module

This module contains the core components for generating smooth jazz-hip hop instrumentals:
- Chord progressions and harmonic structures
- Hip-hop drum patterns and rhythms  
- Smooth bass lines and walking bass
- Jazz piano voicings and comping
- Track composition and arrangement logic
"""

from .chord_progressions import JazzChords
from .drum_patterns import HipHopDrums
from .bass_lines import SmoothBass
from .piano_voicings import JazzPiano
from .composition import TrackComposer

__version__ = "1.0.0"
__author__ = "Jazz-Hip Hop Generator"

__all__ = [
    'JazzChords',
    'HipHopDrums', 
    'SmoothBass',
    'JazzPiano',
    'TrackComposer'
]