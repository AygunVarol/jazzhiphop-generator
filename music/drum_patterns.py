"""
Hip-hop drum patterns for jazz-hip hop tracks
"""
import random
import pretty_midi
import numpy as np

class HipHopDrums:
    def __init__(self, tempo=90):
        self.tempo = tempo
        
        # Standard drum kit mapping (General MIDI)
        self.drum_map = {
            'kick': 36,
            'snare': 38,
            'hihat_closed': 42,
            'hihat_open': 46,
            'crash': 49,
            'ride': 51,
            'rim': 37,
            'tom_low': 41,
            'tom_mid': 47,
            'tom_high': 50
        }
        
        # Hip-hop drum patterns (16th note grid)
        self.patterns = {
            'verse_a': {
                'kick': [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                'hihat_closed': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
                'hihat_open': [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
            },
            'verse_b': {
                'kick': [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
                'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0],
                'hihat_closed': [1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0],
                'rim': [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1]
            },
            'chorus': {
                'kick': [1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
                'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                'hihat_closed': [1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1],
                'crash': [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            },
            'chorus_2': {
                'kick': [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0],
                'snare': [0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1],
                'hihat_closed': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                'hihat_open': [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0]
            },
            'outro': {
                'kick': [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                'snare': [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                'hihat_closed': [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
                'ride': [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
            }
        }
    
    def _add_humanization(self, timing, velocity):
        """Add slight timing and velocity variations for human feel"""
        # Timing humanization (±10ms)
        timing_variation = random.uniform(-0.01, 0.01)
        
        # Velocity humanization (±15)
        velocity_variation = random.randint(-15, 15)
        
        return (
            max(0, timing + timing_variation),
            max(1, min(127, velocity + velocity_variation))
        )
    
    def _apply_swing(self, pattern, swing_amount=0.1):
        """Apply subtle swing to off-beat hits"""
        swung_pattern = pattern.copy()
        
        # Apply swing to 16th note off-beats (positions 1, 3, 5, 7, 9, 11, 13, 15)
        for i in range(1, 16, 2):
            if pattern[i] > 0:
                # Delay off-beats slightly
                swing_delay = swing_amount * (60 / self.tempo) / 4
                swung_pattern[i] = (pattern[i], swing_delay)
        
        return swung_pattern
    
    def generate_pattern(self, start_time, duration, section='verse_a'):
        """Generate drum pattern for a section"""
        instrument = pretty_midi.Instrument(program=0, is_drum=True)
        
        # Get pattern for section, fallback to verse_a
        pattern_set = self.patterns.get(section, self.patterns['verse_a'])
        
        # Calculate timing
        bar_duration = (60 / self.tempo) * 4  # 4 beats per bar
        sixteenth_duration = bar_duration / 16
        
        current_time = start_time
        end_time = start_time + duration
        
        while current_time < end_time:
            # Add some pattern variation every few bars
            if random.random() < 0.2:  # 20% chance of variation
                pattern_set = self._add_pattern_variation(pattern_set)
            
            # Generate one bar
            for step in range(16):
                step_time = current_time + (step * sixteenth_duration)
                
                if step_time >= end_time:
                    break
                
                for drum_name, pattern in pattern_set.items():
                    if step < len(pattern) and pattern[step] > 0:
                        # Get drum MIDI note
                        drum_note = self.drum_map.get(drum_name, 36)
                        
                        # Base velocity based on drum type
                        base_velocity = {
                            'kick': 100,
                            'snare': 95,
                            'hihat_closed': 70,
                            'hihat_open': 80,
                            'crash': 110,
                            'ride': 75,
                            'rim': 60
                        }.get(drum_name, 80)
                        
                        # Apply humanization
                        note_time, velocity = self._add_humanization(step_time, base_velocity)
                        
                        # Create note
                        note = pretty_midi.Note(
                            velocity=velocity,
                            pitch=drum_note,
                            start=note_time,
                            end=note_time + sixteenth_duration * 0.5
                        )
                        instrument.notes.append(note)
            
            current_time += bar_duration
        
        return instrument
    
    def _add_pattern_variation(self, pattern_set):
        """Add subtle variations to keep the pattern interesting"""
        varied_pattern = {}
        
        for drum_name, pattern in pattern_set.items():
            new_pattern = pattern.copy()
            
            # Randomly add or remove hits (low probability)
            for i in range(len(pattern)):
                if random.random() < 0.05:  # 5% chance
                    if pattern[i] == 0 and drum_name in ['hihat_closed', 'rim']:
                        new_pattern[i] = 1  # Add ghost note
                    elif pattern[i] == 1 and random.random() < 0.3:
                        new_pattern[i] = 0  # Remove hit occasionally
            
            varied_pattern[drum_name] = new_pattern
        
        return varied_pattern
    
    def create_fill(self, start_time, duration=1.0):
        """Create a drum fill"""
        instrument = pretty_midi.Instrument(program=0, is_drum=True)
        
        # Simple tom fill pattern
        fill_pattern = [
            (0.0, 'tom_high', 90),
            (0.25, 'tom_mid', 85),
            (0.5, 'tom_low', 95),
            (0.75, 'snare', 100),
            (1.0, 'crash', 110)
        ]
        
        for timing, drum, velocity in fill_pattern:
            if timing < duration:
                note_time = start_time + timing
                drum_note = self.drum_map.get(drum, 38)
                
                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=drum_note,
                    start=note_time,
                    end=note_time + 0.2
                )
                instrument.notes.append(note)
        
        return instrument