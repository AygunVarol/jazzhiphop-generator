#!/usr/bin/env python3
"""
Jazz-Hip Hop Music Generator
Generates smooth jazz instrumental tracks with hip-hop elements
"""

import random
import json
import os
from datetime import datetime
import numpy as np
import pretty_midi
from music.chord_progressions import JazzChords
from music.drum_patterns import HipHopDrums
from music.bass_lines import SmoothBass
from music.piano_voicings import JazzPiano
from music.composition import TrackComposer

class JazzHipHopGenerator:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        self.tempo = random.randint(70, 120)  # BPM range for jazz-hip hop
        self.key = random.choice(['C', 'Dm', 'F', 'G', 'Am', 'Bb', 'Eb'])
        self.time_signature = (4, 4)
        
        # Initialize music components
        self.chords = JazzChords(self.key)
        self.drums = HipHopDrums(self.tempo)
        self.bass = SmoothBass(self.key, self.tempo)
        self.piano = JazzPiano(self.key)
        self.composer = TrackComposer(self.tempo)
        
    def generate_track(self):
        """Generate a complete jazz-hip hop track"""
        print(f"🎵 Generating jazz-hip hop track in {self.key} at {self.tempo} BPM...")
        
        # Create MIDI file
        midi = pretty_midi.PrettyMIDI(initial_tempo=self.tempo)
        
        # Track structure: Intro(8) - Verse(16) - Chorus(16) - Verse(16) - Chorus(16) - Outro(8)
        structure = {
            'intro': 8,
            'verse_a': 16, 
            'chorus': 16,
            'verse_b': 16,
            'chorus_2': 16,
            'outro': 8
        }
        
        current_time = 0
        
        for section, bars in structure.items():
            section_length = bars * (60 / self.tempo) * 4  # 4 beats per bar
            
            # Generate chord progression for section
            progression = self.chords.get_progression(section, bars)
            
            # Add instruments
            if section != 'intro':  # Drums enter after intro
                drum_track = self.drums.generate_pattern(current_time, section_length, section)
                midi.instruments.append(drum_track)
            
            # Piano comping
            piano_track = self.piano.generate_comping(progression, current_time, section_length)
            midi.instruments.append(piano_track)
            
            # Bass line
            bass_track = self.bass.generate_line(progression, current_time, section_length)
            midi.instruments.append(bass_track)
            
            # Add lead elements in chorus sections
            if 'chorus' in section:
                lead_piano = self.piano.generate_lead(progression, current_time, section_length)
                midi.instruments.append(lead_piano)
            
            current_time += section_length
        
        return midi
    
    def apply_swing(self, midi):
        """Apply subtle swing feel to the track"""
        swing_ratio = 0.15  # Subtle swing
        for instrument in midi.instruments:
            if not instrument.is_drum:
                for note in instrument.notes:
                    beat_pos = (note.start * self.tempo / 60) % 1
                    if 0.4 < beat_pos < 0.6:  # Swing the off-beats
                        note.start += swing_ratio * (60 / self.tempo) / 4
                        note.end += swing_ratio * (60 / self.tempo) / 4
    
    def save_track(self, midi):
        """Save the generated track"""
        os.makedirs('output', exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jazzhiphop_{self.key}_{self.tempo}bpm_{timestamp}"
        
        # Save MIDI
        midi_path = f"output/{filename}.mid"
        midi.write(midi_path)
        
        # Save metadata
        metadata = {
            'title': f"Jazz-Hip Hop Track {timestamp}",
            'key': self.key,
            'tempo': self.tempo,
            'genre': 'Jazz-Hip Hop',
            'hashtags': ['#jazzhiphop', '#smoothjazzinstrumental', '#jazzpiano', 
                        '#jazzfunk', '#soulmusic'],
            'generated_at': timestamp,
            'duration_bars': 80
        }
        
        with open(f"output/{filename}_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Track saved: {midi_path}")
        print(f"🎹 Key: {self.key} | 🥁 Tempo: {self.tempo} BPM")
        print(f"🏷️  Tags: {' '.join(metadata['hashtags'])}")
        
        return midi_path

def main():
    """Main generation function"""
    print("🎼 Jazz-Hip Hop Music Generator")
    print("=" * 40)
    
    # Load configuration
    config_file = 'config.json'
    if not os.path.exists(config_file):
        # Create default config
        default_config = {
            "tempo_range": [70, 120],
            "preferred_keys": ["C", "Dm", "F", "G", "Am", "Bb", "Eb"],
            "track_length_bars": 80,
            "swing_amount": 0.15,
            "instruments": {
                "piano": {"velocity": 80, "channel": 0},
                "bass": {"velocity": 90, "channel": 1}, 
                "drums": {"velocity": 100, "channel": 9}
            }
        }
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"📝 Created default config: {config_file}")
    
    # Generate track
    generator = JazzHipHopGenerator(config_file)
    midi = generator.generate_track()
    
    # Apply musical feel
    generator.apply_swing(midi)
    
    # Save the track
    output_path = generator.save_track(midi)
    
    print(f"\n🎵 New jazz-hip hop track generated!")
    print(f"📁 Output: {output_path}")
    print(f"🎧 Ready for your smooth jazz playlist!")

if __name__ == "__main__":
    main()