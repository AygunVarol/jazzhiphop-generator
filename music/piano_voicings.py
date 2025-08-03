"""
Jazz piano voicings and comping patterns
"""
import random
import pretty_midi
import numpy as np

class JazzPiano:
    def __init__(self, key='C'):
        self.key = key
        self.scale_degrees = self._get_scale_degrees(key)
        
        # Comping patterns (16th note grid)
        self.comp_patterns = {
            'verse_a': [
                [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],  # Simple
                [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],  # Moderate
                [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0]   # On beat
            ],
            'verse_b': [
                [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0],
                [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0],
                [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1]
            ],
            'chorus': [
                [0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0],  # Active
                [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
                [0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0]
            ],
            'chorus_2': [
                [0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0],
                [1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0]
            ],
            'outro': [
                [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],  # Sparse
                [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
            ]
        }
        
        # Lead melody patterns for chorus sections
        self.lead_patterns = {
            'scalar': [0, 1, 2, 3, 2, 1, 0, -1],  # Scale runs
            'arpeggiated': [0, 2, 4, 6, 4, 2, 0],  # Chord arpeggios
            'bluesy': [0, 2, 3, 2, 0, -1, 0],  # Blues inflections
            'chromatic': [0, 0.5, 1, 1.5, 2, 1.5, 1, 0.5]  # Chromatic approaches
        }
    
    def _get_scale_degrees(self, key):
        """Get MIDI note numbers for scale degrees"""
        key_roots = {
            'C': 60, 'Db': 61, 'D': 62, 'Eb': 63, 'E': 64, 'F': 65,
            'Gb': 66, 'G': 67, 'Ab': 68, 'A': 69, 'Bb': 70, 'B': 71,
            'Dm': 62, 'Em': 64, 'Am': 69, 'Fm': 65, 'Gm': 67, 'Cm': 60
        }
        
        root = key_roots.get(key, 60)
        
        if 'm' not in key:
            intervals = [0, 2, 4, 5, 7, 9, 11]  # Major scale
        else:
            intervals = [0, 2, 3, 5, 7, 8, 10]  # Natural minor scale
        
        return [root + interval for interval in intervals]
    
    def _get_chord_voicing(self, chord_symbol, octave=4, voicing_type='rootless'):
        """Get jazz piano voicing for chord"""
        degree_map = {
            'I': 0, 'ii': 1, 'iii': 2, 'IV': 3, 'V': 4, 'vi': 5, 'vii': 6,
            'i': 0, 'ii': 1, 'III': 2, 'iv': 3, 'v': 4, 'VI': 5, 'VII': 6
        }
        
        # Extract root and quality
        if chord_symbol.startswith(('ii', 'iii', 'vi', 'vii')):
            root_degree = degree_map[chord_symbol[:2]]
            quality = chord_symbol[2:]
        else:
            root_degree = degree_map[chord_symbol[0]]
            quality = chord_symbol[1:]
        
        root_note = self.scale_degrees[root_degree] + (octave - 4) * 12
        
        if voicing_type == 'rootless':
            # Rootless voicings (common in jazz)
            if quality == 'maj7':
                # 3, 5, 7, 9
                intervals = [4, 7, 11, 14]
            elif quality == '7':
                # 3, 6, 7, 9 (altered)
                intervals = [4, 9, 10, 14]
            elif quality == 'm7':
                # 3, 5, 7, 9
                intervals = [3, 7, 10, 14]
            else:
                intervals = [4, 7, 11]  # Major triad
        else:
            # Block chords
            if quality == 'maj7':
                intervals = [0, 4, 7, 11]
            elif quality == '7':
                intervals = [0, 4, 7, 10]
            elif quality == 'm7':
                intervals = [0, 3, 7, 10]
            else:
                intervals = [0, 4, 7]
        
        return [root_note + interval for interval in intervals]
    
    def generate_comping(self, chord_progression, start_time, duration):
        """Generate piano comping track"""
        instrument = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano
        
        # Determine section type from progression length
        if len(chord_progression) <= 4:
            section = 'intro'
        elif len(chord_progression) <= 8:
            section = 'verse_a'
        else:
            section = 'chorus'
        
        # Get comping pattern
        available_patterns = self.comp_patterns.get(section, self.comp_patterns['verse_a'])
        rhythm_pattern = random.choice(available_patterns)
        
        # Calculate timing
        chord_duration = duration / len(chord_progression)
        sixteenth_duration = chord_duration / 4
        
        current_time = start_time
        
        for chord in chord_progression:
            if current_time >= start_time + duration:
                break
            
            # Get chord voicing
            voicing = self._get_chord_voicing(chord, octave=4, voicing_type='rootless')
            
            # Apply rhythm pattern
            for step, hit in enumerate(rhythm_pattern):
                if hit and step < 4:  # Only use first 4 steps per chord
                    note_start = current_time + (step * sixteenth_duration)
                    note_end = note_start + sixteenth_duration * 2
                    
                    # Add slight humanization
                    timing_variation = random.uniform(-0.01, 0.01)
                    velocity_variation = random.randint(-10, 10)
                    
                    for note_pitch in voicing:
                        note = pretty_midi.Note(
                            velocity=max(40, min(80, 65 + velocity_variation)),
                            pitch=note_pitch,
                            start=note_start + timing_variation,
                            end=note_end
                        )
                        instrument.notes.append(note)
            
            current_time += chord_duration
        
        return instrument
    
    def generate_lead(self, chord_progression, start_time, duration):
        """Generate lead piano melody for chorus sections"""
        instrument = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano
        
        # Calculate timing
        chord_duration = duration / len(chord_progression)
        eighth_duration = chord_duration / 2
        
        current_time = start_time
        current_octave = 5  # Higher octave for lead
        
        for chord in chord_progression:
            if current_time >= start_time + duration:
                break
            
            # Choose melodic pattern
            pattern_type = random.choice(list(self.lead_patterns.keys()))
            pattern = self.lead_patterns[pattern_type]
            
            # Get chord tones for reference
            chord_tones = self._get_chord_voicing(chord, octave=current_octave, voicing_type='block')
            root_note = chord_tones[0]
            
            # Generate melody notes
            melody_notes = []
            for i, interval in enumerate(pattern):
                if pattern_type == 'chromatic':
                    note = root_note + int(interval * 2)  # Chromatic steps
                else:
                    scale_step = int(interval)
                    note = root_note + (scale_step * 2)  # Scale steps
                
                melody_notes.append(note)
                
                if len(melody_notes) >= 4:  # Max 4 notes per chord
                    break
            
            # Create MIDI notes
            for i, note_pitch in enumerate(melody_notes):
                note_start = current_time + (i * eighth_duration)
                note_end = note_start + eighth_duration * 0.8
                
                if note_start >= start_time + duration:
                    break
                
                # Add expression
                velocity = random.randint(80, 100)
                timing_variation = random.uniform(-0.005, 0.005)
                
                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=int(note_pitch),
                    start=note_start + timing_variation,
                    end=note_end
                )
                instrument.notes.append(note)
            
            current_time += chord_duration
        
        return instrument
    
    def generate_solo(self, chord_progression, start_time, duration):
        """Generate a jazz piano solo"""
        instrument = pretty_midi.Instrument(program=0)
        
        # More active solo patterns
        solo_density = random.choice([8, 12, 16])  # Notes per chord
        chord_duration = duration / len(chord_progression)
        note_duration = chord_duration / solo_density
        
        current_time = start_time
        
        for chord in chord_progression:
            if current_time >= start_time + duration:
                break
            
            # Get scale for this chord
            chord_scale = self._get_chord_scale(chord)
            
            # Generate solo line
            for i in range(solo_density):
                note_start = current_time + (i * note_duration)
                
                if note_start >= start_time + duration:
                    break
                
                # Choose note from chord scale
                scale_degree = random.choice(range(len(chord_scale)))
                note_pitch = chord_scale[scale_degree] + 12  # Octave higher
                
                # Add some chromaticism
                if random.random() < 0.2:  # 20% chance
                    note_pitch += random.choice([-1, 1])
                
                note_end = note_start + note_duration * random.uniform(0.6, 0.9)
                velocity = random.randint(70, 95)
                
                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=int(note_pitch),
                    start=note_start,
                    end=note_end
                )
                instrument.notes.append(note)
            
            current_time += chord_duration
        
        return instrument
    
    def _get_chord_scale(self, chord_symbol):
        """Get appropriate scale for chord symbol"""
        # Simplified - returns basic chord tones + passing tones
        voicing = self._get_chord_voicing(chord_symbol, octave=5)
        scale = voicing + [note + 12 for note in voicing[:3]]  # Add octave
        return sorted(scale)