# Jazz-Hip Hop Music Generator 🎵

Automatic generation of smooth jazz-hip hop instrumentals with piano, funk, and soul elements.

## Features
- Generates unique jazz-hip hop tracks with each run
- Smooth jazz piano progressions
- Hip-hop drum patterns
- Bass lines and chord progressions
- Configurable tempo, key, and length
- Export to WAV/MIDI formats

## Installation

```bash
git clone https://github.com/AygunVarol/jazzhiphop-generator.git
cd jazzhiphop-generator
pip install -r requirements.txt
```

## Usage

```bash
python generate.py
```

Each run creates a new track in the `output/` directory with timestamp.

## Project Structure

```
jazzhiphop-generator/
├── generate.py              # Main generation script
├── requirements.txt         # Dependencies
├── music/
│   ├── __init__.py
│   ├── chord_progressions.py # Jazz chord sequences
│   ├── drum_patterns.py     # Hip-hop drum loops
│   ├── bass_lines.py        # Smooth bass patterns
│   ├── piano_voicings.py    # Jazz piano arrangements
│   └── composition.py       # Track composition logic
├── presets/
│   ├── smooth_jazz.json     # Smooth jazz preset
│   ├── jazz_funk.json       # Jazz-funk preset
│   └── neo_soul.json        # Neo-soul preset
├── output/                  # Generated tracks
└── README.md
```

## Configuration

Edit `config.json` to customize:
- Tempo (60-140 BPM)
- Key signatures
- Track length (2-8 minutes)
- Instrument mix levels
- Effects processing

## Generated Music Style
- **Genre**: Jazz-Hip Hop/Smooth Jazz Instrumental
- **Elements**: Jazz piano, hip-hop drums, smooth bass, subtle percussion
- **Mood**: Relaxed, sophisticated, groove-oriented
- **Hashtags**: #jazzhiphop #smoothjazzinstrumental #jazzpiano #jazzfunk #soulmusic

## Dependencies
- `mido` - MIDI file handling
- `numpy` - Audio processing
- `scipy` - Signal processing
- `pyaudio` - Audio playback
- `pretty_midi` - MIDI manipulation
- `librosa` - Audio analysis

## Examples

Listen to generated samples in `/examples` folder:
- `smooth_jazz_example.wav`
- `jazz_funk_example.wav`
- `neo_soul_example.wav`

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-pattern`)
3. Commit changes (`git commit -am 'Add new drum pattern'`)
4. Push to branch (`git push origin feature/new-pattern`)
5. Create Pull Request

## License

MIT License - See LICENSE file for details

## Credits

Created by Aygün Varol - Music Producer & Software Developer
