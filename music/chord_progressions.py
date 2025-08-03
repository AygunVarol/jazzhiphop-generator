"""
Jazz chord progressions for smooth jazz-hip hop generation
"""
import random
import pretty_midi

class JazzChords:
    def __init__(self, key='C'):
        self.key = key
        self.scale_degrees = self._get_scale_degrees(key)
        
        # Common jazz progressions
        self.progressions = {
            'intro': [
                ['Imaj7', 'vi7', 'ii7', 'V7'],
                ['Imaj7', 'IV7', 'iii7', 'vi7'],
                ['vi7', 'ii7', 'V7', 'Imaj7']
            ],
            'verse_a': [
                ['Imaj7', 'vi7', 'ii7', 'V7', 'iii7', 'vi7', 'ii7', 'V7'],
                ['Imaj7', 'I7', 'IVmaj7', 'iv7', 'iii7', 'vi7', 'ii7', 'V7'],
                ['vi7', 'ii7', 'V7', 'Imaj7', 'vi7', 'ii7', 'V7', 'Imaj7']
            ],
            'verse_b': [
                ['IVmaj7', 'iv7', 'iii7', 'vi7', 'ii7', 'V7', 'Imaj7', 'V7'],
                ['Imaj7', 'vi7', 'IVmaj7', 'IV7', 'iii7', 'vi7', 'ii7', 'V7'],
                ['vi7', 'V7', 'Imaj7', 'vi7', 'ii7', 'V7', 'Imaj7', 'Imaj7']
            ],
            'chorus': [
                ['Imaj7', 'vi7', 'ii7', 'V7', 'Imaj7', 'vi7', 'ii7', 'V7'],
                ['IVmaj7', 'V7', 'iii7', 'vi7', 'ii7', 'V7', 'Imaj7', 'V7'],
                ['vi7', 'ii7', 'V7', 'Imaj7', 'IVmaj7', 'iii7', 'ii7', 'V7']
            ],
            'chorus_2': [
                ['Imaj7', 'I7', 'IVmaj7', 'iv7', 'iii7', 'VI7', 'ii7', 'V7'],
                ['vi7', 'ii7', 'V7', 'Imaj7', 'vi7', 'ii7', 'V7', 'Imaj7'],
                ['IVmaj7', 'V7', 'vi7', 'iii7', 'ii7', 'V7', 'Imaj7', 'V7']
            ],
            'outro': [
                ['ii7', 'V7', 'Imaj7', 'Imaj7'],
                ['vi7', 'ii7', 'V7', 'Imaj7'],
                ['IVmaj7', 'V7', 'Imaj7', 'Imaj7']
            ]
        }
    
    def _get_scale_degrees(self, key):
        """Get MIDI note numbers for scale degrees in the given key"""
        key_roots = {
            'C': 60, 'Db': 61, 'D': 62, 'Eb': 63, 'E': 64, 'F': 65,
            'Gb': 66, 'G': 67, 'Ab': 68, 'A': 69, 'Bb': 70, 'B': 71,
            'Dm': 62, 'Em': 64, 'Am': 69, 'Fm': 65, 'Gm': 67, 'Cm': 60
        }
        
        root = key_roots.get(key, 60)
        
        # Major scale intervals
        if 'm' not in key:
            intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale
        else:
            intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale
        
        return [root + interval for interval in intervals]
    
    def _chord_to_notes(self, chord_symbol, octave=4):
        """Convert chord symbol to MIDI notes"""
        degree_map = {
            'I': 0, 'ii': 1, 'iii': 2, 'IV': 3, 'V': 4, 'vi': 5, 'vii': 6,
            'i': 0, 'ii': 1, 'III': 2, 'iv': 3, 'v': 4, 'VI': 5, 'VII': 6
        }
        
        # Extract root and quality
        if chord_symbol.startswith(('ii', 'iii', 'vi', 'vii')):
            root_degree = degree_map[chord_symbol[:2]]
            quality = chord_symbol[2:]
        elif chord_symbol.startswith(('I', 'V')):
            root_degree = degree_map[chord_symbol[0]]
            quality = chord_symbol[1:]
        else:
            root_degree = degree_map[chord_symbol[:2]]
            quality = chord_symbol[2:]
        
        root_note = self.scale_degrees[root_degree] + (octave - 4) * 12
        
        # Build chord based on quality
        if quality == 'maj7':
            intervals = [0, 4, 7, 11]
        elif quality == '7':
            intervals = [0, 4, 7, 10]
        elif quality == 'm7':
            intervals = [0, 3, 7, 10]
        elif quality == 'dim7':
            intervals = [0, 3, 6, 9]
        else:  # Default to major triad
            intervals = [0, 4, 7]
        
        return [root_note + interval for interval in intervals]
    
    def get_progression(self, section, bars):
        """Get chord progression for a section"""
        available_progressions = self.progressions.get(section, self.progressions['verse_a'])
        progression = random.choice(available_progressions)
        
        # Extend or truncate to match bar count
        while len(progression) < bars:
            progression.extend(progression[:bars - len(progression)])
        
        return progression[:bars]
    
    def get_chord_notes(self, chord_symbol, octave=4):
        """Get MIDI notes for a chord symbol"""
        return self._chord_to_notes(chord_symbol, octave)
    
    def create_chord_track(self, progression, start_time, duration_per_chord):
        """Create a MIDI track with chord progression"""
        instrument = pretty_midi.Instrument(program=0)  # Piano
        
        current_time = start_time
        for chord in progression:
            notes = self.get_chord_notes(chord, octave=4)
            
            for note_number in notes:
                note = pretty_midi.Note(
                    velocity=60,
                    pitch=note_number,
                    start=current_time,
                    end=current_time + duration_per_chord * 0.9
                )
                instrument.notes.append(note)
            
            current_time += duration_per_chord
        
        return instrument