"""
Track composition and arrangement logic
"""
import random
import pretty_midi
import numpy as np

class TrackComposer:
    def __init__(self, tempo=90):
        self.tempo = tempo
        
        # Standard song structures
        self.structures = {
            'standard': ['intro', 'verse_a', 'chorus', 'verse_b', 'chorus', 'outro'],
            'extended': ['intro', 'verse_a', 'chorus', 'verse_b', 'chorus', 'bridge', 'chorus', 'outro'],
            'simple': ['intro', 'verse_a', 'verse_b', 'chorus', 'outro'],
            'jazz_standard': ['intro', 'head', 'solo_section', 'head', 'outro']
        }
        
        # Section lengths in bars
        self.section_lengths = {
            'intro': 8,
            'verse_a': 16,
            'verse_b': 16,
            'chorus': 16,
            'bridge': 8,
            'solo_section': 32,
            'head': 16,
            'outro': 8
        }
        
        # Arrangement templates
        self.arrangements = {
            'minimal': {
                'intro': ['piano', 'bass'],
                'verse_a': ['piano', 'bass'],
                'chorus': ['piano', 'bass', 'drums'],
                'verse_b': ['piano', 'bass', 'drums'],
                'outro': ['piano']
            },
            'full': {
                'intro': ['piano', 'bass'],
                'verse_a': ['piano', 'bass', 'drums'],
                'chorus': ['piano', 'bass', 'drums', 'lead_piano'],
                'verse_b': ['piano', 'bass', 'drums'],
                'outro': ['piano', 'bass']
            },
            'building': {
                'intro': ['piano'],
                'verse_a': ['piano', 'bass'],
                'chorus': ['piano', 'bass', 'drums'],
                'verse_b': ['piano', 'bass', 'drums', 'percussion'],
                'outro': ['piano', 'bass']
            }
        }
    
    def generate_structure(self, style='standard'):
        """Generate song structure"""
        if style in self.structures:
            return self.structures[style].copy()
        else:
            return random.choice(list(self.structures.values())).copy()
    
    def get_arrangement(self, section, style='full'):
        """Get instrument arrangement for a section"""
        arrangement = self.arrangements.get(style, self.arrangements['full'])
        return arrangement.get(section, ['piano', 'bass', 'drums'])
    
    def calculate_dynamics(self, section, bar_number, total_bars):
        """Calculate dynamic level for a section"""
        base_dynamics = {
            'intro': 0.6,
            'verse_a': 0.7,
            'verse_b': 0.75,
            'chorus': 0.85,
            'bridge': 0.8,
            'solo_section': 0.9,
            'outro': 0.6
        }
        
        base_level = base_dynamics.get(section, 0.7)
        
        # Add dynamic arc within section
        section_progress = bar_number / total_bars
        
        if section in ['chorus', 'solo_section']:
            # Build energy in chorus/solo
            dynamic_curve = 0.9 + (0.1 * section_progress)
        elif section == 'outro':
            # Fade out in outro
            dynamic_curve = 1.0 - (0.4 * section_progress)
        else:
            # Slight build in verses
            dynamic_curve = 0.95 + (0.05 * section_progress)
        
        return base_level * dynamic_curve
    
    def add_transitions(self, midi, structure_timing):
        """Add transitional elements between sections"""
        for i in range(len(structure_timing) - 1):
            current_section, current_end = structure_timing[i]
            next_section, next_start = structure_timing[i + 1]
            
            # Add fill or transition based on sections
            if self._needs_drum_fill(current_section, next_section):
                self._add_drum_fill(midi, current_end - 1.0, 1.0)
            
            if self._needs_harmonic_transition(current_section, next_section):
                self._add_harmonic_transition(midi, current_end - 0.5, 0.5)
    
    def _needs_drum_fill(self, current_section, next_section):
        """Determine if a drum fill is needed"""
        fill_transitions = [
            ('verse_a', 'chorus'),
            ('verse_b', 'chorus'),
            ('chorus', 'bridge'),
            ('bridge', 'chorus'),
            ('solo_section', 'head')
        ]
        return (current_section, next_section) in fill_transitions
    
    def _needs_harmonic_transition(self, current_section, next_section):
        """Determine if harmonic transition is needed"""
        return current_section != next_section and next_section in ['chorus', 'bridge']
    
    def _add_drum_fill(self, midi, start_time, duration):
        """Add a drum fill transition"""
        fill_instrument = pretty_midi.Instrument(program=0, is_drum=True)
        
        # Simple tom fill
        fill_notes = [
            (0.0, 50, 90),   # High tom
            (0.25, 47, 85),  # Mid tom  
            (0.5, 41, 95),   # Low tom
            (0.75, 38, 100), # Snare
            (1.0, 49, 110)   # Crash
        ]
        
        for timing, drum_note, velocity in fill_notes:
            if timing < duration:
                note_start = start_time + timing
                note_end = note_start + 0.2
                
                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=drum_note,
                    start=note_start,
                    end=note_end
                )
                fill_instrument.notes.append(note)
        
        midi.instruments.append(fill_instrument)
    
    def _add_harmonic_transition(self, midi, start_time, duration):
        """Add harmonic transition chord"""
        transition_instrument = pretty_midi.Instrument(program=0)  # Piano
        
        # Simple dominant chord leading to next section
        transition_notes = [60, 64, 67, 70]  # C7 chord
        
        for note_pitch in transition_notes:
            note = pretty_midi.Note(
                velocity=70,
                pitch=note_pitch,
                start=start_time,
                end=start_time + duration
            )
            transition_instrument.notes.append(note)
        
        midi.instruments.append(transition_instrument)
    
    def apply_swing_feel(self, midi, swing_amount=0.1):
        """Apply swing feel to all non-drum instruments"""
        beat_duration = 60 / self.tempo
        
        for instrument in midi.instruments:
            if not instrument.is_drum:
                for note in instrument.notes:
                    # Calculate beat position
                    beat_position = (note.start / beat_duration) % 1
                    
                    # Apply swing to off-beats (around 0.5)
                    if 0.4 <= beat_position <= 0.6:
                        swing_offset = swing_amount * beat_duration * 0.25
                        note.start += swing_offset
                        note.end += swing_offset
    
    def balance_mix(self, midi):
        """Balance instrument levels in the mix"""
        instrument_levels = {
            'drums': 1.0,      # Reference level
            'bass': 0.9,       # Slightly lower than drums
            'piano': 0.8,      # Comping level
            'lead_piano': 0.95, # Lead level
            'percussion': 0.6   # Background level
        }
        
        for i, instrument in enumerate(midi.instruments):
            # Determine instrument type (simplified)
            if instrument.is_drum:
                level = instrument_levels['drums']
            elif instrument.program == 33:  # Bass
                level = instrument_levels['bass']
            elif instrument.program == 0:   # Piano
                # Distinguish between comping and lead based on note density
                note_density = len(instrument.notes) / (midi.get_end_time() or 1)
                if note_density > 10:  # High density = lead
                    level = instrument_levels['lead_piano']
                else:
                    level = instrument_levels['piano']
            else:
                level = 0.8  # Default level
            
            # Apply level adjustment
            for note in instrument.notes:
                note.velocity = int(note.velocity * level)
                note.velocity = max(1, min(127, note.velocity))
    
    def add_ambient_elements(self, midi, start_time, duration):
        """Add ambient elements like reverb tails, soft pads"""
        pad_instrument = pretty_midi.Instrument(program=88)  # New Age pad
        
        # Add long, soft pad notes
        pad_notes = [48, 52, 55, 60]  # Simple chord
        
        for note_pitch in pad_notes:
            note = pretty_midi.Note(
                velocity=30,
                pitch=note_pitch,
                start=start_time,
                end=start_time + duration
            )
            pad_instrument.notes.append(note)
        
        midi.instruments.append(pad_instrument)
    
    def create_complete_arrangement(self, chord_progression, key='C', structure_style='standard'):
        """Create a complete track arrangement"""
        # Generate structure
        structure = self.generate_structure(structure_style)
        
        # Calculate timing for each section
        current_time = 0
        structure_timing = []
        
        for section in structure:
            section_length_bars = self.section_lengths[section]
            section_duration = (60 / self.tempo) * 4 * section_length_bars
            
            structure_timing.append((section, current_time, section_duration))
            current_time += section_duration
        
        return structure, structure_timing
    
    def optimize_voice_leading(self, chord_progression):
        """Optimize voice leading between chords"""
        # Simple voice leading optimization
        # This would analyze chord progressions and suggest smoother voice movements
        optimized_progression = chord_progression.copy()
        
        # Add voice leading rules here
        # For now, return original progression
        return optimized_progression