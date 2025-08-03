"""
Smooth bass lines for jazz-hip hop tracks
"""
import random
import pretty_midi
import numpy as np

class SmoothBass:
    def __init__(self, key='C', tempo=90):
        self.key = key
        self.tempo = tempo
        self.scale_degrees = self._get_scale_degrees(key)
        
        # Bass line patterns (rhythmic patterns in 16th notes)
        self.rhythmic_patterns = {
            'verse_a': [
                [1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],  # Classic hip-hop
                [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0],  # Syncopated
                [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0]   # Smooth
            ],
            'verse_b': [
                [1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0],
                [1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
                [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0]
            ],
            'chorus': [
                [1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0],  # More active
                [1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0],
                [1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0]
            ],
            'chorus_2': [
                [1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0],
                [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 0, 0]
            ],
            'outro': [
                [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],  # Sparse
                [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
            ]
        }
        
        # Melodic movement patterns
        self.melodic_patterns = {
            'root_fifth': [0, 4],  # Root and fifth
            'walking': [0, 1, 2, 4],  # Walking bass
            'chord_tones': [0, 2, 4, 6],  # Chord tones
            'chromatic': [0, 0.5, 1, 1.5],  # Chromatic approach
            'octave_jump': [0, 7, 0, 4]  # Octave displacement
        }
    
    def _get_scale_degrees(self, key):
        """Get MIDI note numbers for scale degrees in the given key"""
        key_roots = {
            'C': 36, 'Db': 37, 'D': 38, 'Eb': 39, 'E': 40, 'F': 41,
            'Gb': 42, 'G': 43, 'Ab': 44, 'A': 45, 'Bb': 46, 'B': 47,
            'Dm': 38, 'Em': 40, 'Am': 45, 'Fm': 41, 'Gm': 43, 'Cm': 36
        }
        
        root = key_roots.get(key, 36)  # Bass octave
        
        # Major scale intervals
        if 'm' not in key:
            intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale
        else:
            intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale
        
        return [root + interval for interval in intervals]
    
    def _chord_to_bass_notes(self, chord_symbol):
        """Get bass notes for a chord symbol"""
        degree_map = {
            'I': 0, 'ii': 1, 'iii': 2, 'IV': 3, 'V': 4, 'vi': 5, 'vii': 6,
            'i': 0, 'ii': 1, 'III': 2, 'iv': 3, 'v': 4, 'VI': 5, 'VII': 6
        }
        
        # Extract root degree
        if chord_symbol.startswith(('ii', 'iii', 'vi', 'vii')):
            root_degree = degree_map[chord_symbol[:2]]
        else:
            root_degree = degree_map[chord_symbol[0]]
        
        root_note = self.scale_degrees[root_degree]
        
        # Return available notes for this chord (root, third, fifth, seventh)
        chord_tones = [
            root_note,                    # Root
            root_note + 3,               # Third (approximate)
            root_note + 7,               # Fifth
            root_note + 10,              # Seventh (approximate)
            root_note + 12               # Octave
        ]
        
        return chord_tones
    
    def _generate_bass_line_for_chord(self, chord_symbol, pattern, start_note=None):
        """Generate bass line for a single chord"""
        available_notes = self._chord_to_bass_notes(chord_symbol)
        
        if start_note is None:
            start_note = available_notes[0]  # Start with root
        
        bass_notes = []
        current_note = start_note
        
        # Choose melodic movement pattern
        movement_type = random.choice(list(self.melodic_patterns.keys()))
        movement_pattern = self.melodic_patterns[movement_type]
        
        note_index = 0
        for i, hit in enumerate(pattern):
            if hit:
                # Select note based on movement pattern
                if movement_type == 'chromatic':
                    # Chromatic movement
                    offset = int(movement_pattern[note_index % len(movement_pattern)])
                    note = current_note + offset
                else:
                    # Chord tone movement
                    tone_index = int(movement_pattern[note_index % len(movement_pattern)])
                    note = available_notes[tone_index % len(available_notes)]
                
                bass_notes.append(note)
                current_note = note
                note_index += 1
            else:
                bass_notes.append(None)  # Rest
        
        return bass_notes, current_note
    
    def generate_line(self, chord_progression, start_time, duration):
        """Generate bass line for a chord progression"""
        instrument = pretty_midi.Instrument(program=33)  # Electric Bass (finger)
        
        # Calculate timing
        chords_per_bar = 4 if len(chord_progression) > 8 else 2
        chord_duration = (60 / self.tempo) * (4 / chords_per_bar)
        sixteenth_duration = chord_duration / 4
        
        current_time = start_time
        last_note = None
        
        for chord_idx, chord in enumerate(chord_progression):
            if current_time >= start_time + duration:
                break
            
            # Select section type based on progression position
            if chord_idx < len(chord_progression) * 0.3:
                section = 'verse_a'
            elif chord_idx < len(chord_progression) * 0.7:
                section = 'chorus'
            else:
                section = 'verse_b'
            
            # Get rhythmic pattern
            available_patterns = self.rhythmic_patterns.get(section, self.rhythmic_patterns['verse_a'])
            rhythm_pattern = random.choice(available_patterns)
            
            # Generate bass line for this chord
            bass_notes, last_note = self._generate_bass_line_for_chord(
                chord, rhythm_pattern, last_note
            )
            
            # Create MIDI notes
            for step, note in enumerate(bass_notes):
                if note is not None:
                    note_start = current_time + (step * sixteenth_duration)
                    note_end = note_start + sixteenth_duration * 0.8
                    
                    # Add some humanization
                    velocity = random.randint(75, 95)
                    note_start += random.uniform(-0.005, 0.005)  # Slight timing variation
                    
                    midi_note = pretty_midi.Note(
                        velocity=velocity,
                        pitch=int(note),
                        start=note_start,
                        end=note_end
                    )
                    instrument.notes.append(midi_note)
            
            current_time += chord_duration
        
        return instrument
    
    def generate_walking_bass(self, chord_progression, start_time, duration):
        """Generate a walking bass line"""
        instrument = pretty_midi.Instrument(program=32)  # Acoustic Bass
        
        chord_duration = (60 / self.tempo) * 2  # Half note per chord
        quarter_duration = chord_duration / 2
        
        current_time = start_time
        
        for i, chord in enumerate(chord_progression):
            if current_time >= start_time + duration:
                break
            
            chord_tones = self._chord_to_bass_notes(chord)
            
            # Walking pattern: root, third, fifth, approach tone
            notes = [
                chord_tones[0],  # Root
                chord_tones[1],  # Third
                chord_tones[2],  # Fifth
                chord_tones[0] + random.choice([-1, 1, 2])  # Approach tone
            ]
            
            for j, note in enumerate(notes):
                if current_time + (j * quarter_duration) >= start_time + duration:
                    break
                
                note_start = current_time + (j * quarter_duration)
                note_end = note_start + quarter_duration * 0.9
                
                midi_note = pretty_midi.Note(
                    velocity=random.randint(70, 85),
                    pitch=int(note),
                    start=note_start,
                    end=note_end
                )
                instrument.notes.append(midi_note)
            
            current_time += chord_duration
        
        return instrument