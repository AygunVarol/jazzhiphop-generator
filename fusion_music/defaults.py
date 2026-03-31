KEY_TO_SEMITONE = {
    "C": 0,
    "Db": 1,
    "D": 2,
    "Eb": 3,
    "E": 4,
    "F": 5,
    "Gb": 6,
    "G": 7,
    "Ab": 8,
    "A": 9,
    "Bb": 10,
    "B": 11,
}

MODE_INTERVALS = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
}

TEXTURES = (
    "dusty_warm",
    "silky_nocturne",
    "smoked_tape",
    "sunset_haze",
)

IMMERSION_MODES = (
    "music",
    "atmosphere",
    "world",
    "manual",
)

AMBIENCE_LAYERS = (
    "vinyl",
    "rain",
    "wind",
    "city",
    "fire",
    "waves",
    "night",
    "train",
)

DRUM_STYLES = (
    "boom_bap_jazz",
    "laid_back_lofi",
    "swing_knock",
    "neo_soul_snap",
)

KEYS_SOUNDS = (
    "rhodes",
    "upright_piano",
    "wurlitzer",
    "jazz_guitar",
    "detuned_keys",
)

BASS_STYLES = (
    "root_pocket",
    "walking_glide",
    "counter_melody",
    "octave_bounce",
)

BASS_SOUNDS = (
    "electric_bass",
    "upright_bass",
    "fretless_bass",
    "sine_sub",
)

PIANO_STYLES = (
    "dusty_chords",
    "broken_voicings",
    "lush_spread",
)

LEAD_STYLES = (
    "motivic_reply",
    "airy_runs",
    "vibraphone_hook",
    "blues_smear",
)

LEAD_SOUNDS = (
    "vibes",
    "flute",
    "muted_trumpet",
    "analog_lead",
    "electric_piano_lead",
)

PAD_SOUNDS = (
    "warm_pad",
    "string_pad",
    "choir_pad",
    "organ_pad",
)

COUNTER_SOUNDS = (
    "none",
    "bell_pluck",
    "guitar_harmonics",
    "clarinet",
    "marimba",
)

PERCUSSION_STYLES = (
    "none",
    "shaker",
    "ride",
    "conga",
    "rimshot",
)

RIFF_SHAPES = (
    "ascending",
    "descending",
    "arched",
    "circular",
    "question_answer",
    "staircase",
)

MOTIF_VARIATIONS = (
    "sequence",
    "rhythm_flip",
    "ornament",
    "invert",
    "expand",
    "call_response",
)

ARRANGEMENT_STYLES = (
    "cinematic_build",
    "head_nod",
    "suite_arc",
)

SECTION_NAMES = (
    "intro",
    "verse_a",
    "chorus",
    "verse_b",
    "bridge",
    "outro",
)

SECTION_VARIATIONS = (
    "steady",
    "lift",
    "settle",
    "answer",
    "breakdown",
    "release",
)

LAYERS = ("keys", "bass", "drums", "lead", "pad", "counter", "percussion")

SECTION_TEMPLATES = {
    "cinematic_build": [
        {"name": "intro", "bars": 8, "intensity": 0.32, "layers": ["keys", "pad"], "variation": "settle", "lead_density": 0.0},
        {"name": "verse_a", "bars": 16, "intensity": 0.58, "layers": ["keys", "bass", "counter"], "variation": "steady", "lead_density": 0.0},
        {"name": "chorus", "bars": 16, "intensity": 0.82, "layers": ["keys", "bass", "drums", "lead", "pad", "percussion"], "variation": "lift", "lead_density": 0.72},
        {"name": "verse_b", "bars": 16, "intensity": 0.68, "layers": ["keys", "bass", "drums", "pad", "counter"], "variation": "answer", "lead_density": 0.24},
        {"name": "bridge", "bars": 8, "intensity": 0.46, "layers": ["keys", "bass", "pad", "counter"], "variation": "breakdown", "lead_density": 0.18},
        {"name": "chorus", "bars": 16, "intensity": 0.94, "layers": ["keys", "bass", "drums", "lead", "pad", "percussion", "counter"], "variation": "release", "lead_density": 0.88},
        {"name": "outro", "bars": 8, "intensity": 0.28, "layers": ["keys", "pad"], "variation": "settle", "lead_density": 0.0},
    ],
    "head_nod": [
        {"name": "intro", "bars": 4, "intensity": 0.30, "layers": ["keys"], "variation": "settle", "lead_density": 0.0},
        {"name": "verse_a", "bars": 16, "intensity": 0.62, "layers": ["keys", "bass", "drums", "percussion"], "variation": "steady", "lead_density": 0.10},
        {"name": "chorus", "bars": 8, "intensity": 0.86, "layers": ["keys", "bass", "drums", "lead", "counter", "percussion"], "variation": "lift", "lead_density": 0.62},
        {"name": "verse_b", "bars": 16, "intensity": 0.66, "layers": ["keys", "bass", "drums", "counter"], "variation": "answer", "lead_density": 0.18},
        {"name": "chorus", "bars": 8, "intensity": 0.92, "layers": ["keys", "bass", "drums", "lead", "pad", "counter", "percussion"], "variation": "release", "lead_density": 0.78},
        {"name": "outro", "bars": 4, "intensity": 0.26, "layers": ["keys", "pad"], "variation": "settle", "lead_density": 0.0},
    ],
    "suite_arc": [
        {"name": "intro", "bars": 8, "intensity": 0.34, "layers": ["keys", "pad"], "variation": "settle", "lead_density": 0.0},
        {"name": "verse_a", "bars": 12, "intensity": 0.56, "layers": ["keys", "bass", "drums", "counter"], "variation": "steady", "lead_density": 0.12},
        {"name": "chorus", "bars": 12, "intensity": 0.80, "layers": ["keys", "bass", "drums", "lead", "pad", "percussion"], "variation": "lift", "lead_density": 0.66},
        {"name": "bridge", "bars": 8, "intensity": 0.48, "layers": ["keys", "bass", "pad", "counter"], "variation": "breakdown", "lead_density": 0.12},
        {"name": "verse_b", "bars": 12, "intensity": 0.68, "layers": ["keys", "bass", "drums", "counter", "percussion"], "variation": "answer", "lead_density": 0.22},
        {"name": "chorus", "bars": 12, "intensity": 0.92, "layers": ["keys", "bass", "drums", "lead", "pad", "counter", "percussion"], "variation": "release", "lead_density": 0.82},
        {"name": "outro", "bars": 8, "intensity": 0.25, "layers": ["keys", "pad"], "variation": "settle", "lead_density": 0.0},
    ],
}

PROGRESSION_LIBRARY = {
    "after_hours": [
        ["ii9", "V13", "Imaj9", "vi11"],
        ["Imaj9", "vi11", "ii9", "V13"],
        ["iii7", "vi9", "ii9", "V13"],
    ],
    "smoke_and_rain": [
        ["i9", "iv11", "VII13", "IIImaj9"],
        ["i9", "VImaj7", "IIImaj9", "VII13"],
        ["i9", "V9", "iv11", "VII13"],
    ],
    "neo_soul": [
        ["Imaj9", "III7", "vi9", "ii13"],
        ["vi9", "ii11", "V13", "Imaj9"],
        ["IVmaj9", "III7", "vi9", "V13"],
    ],
    "dorian_drive": [
        ["i9", "IV13", "i9", "VII13"],
        ["i9", "IV13", "IIImaj9", "VII13"],
        ["i9", "IV13", "VImaj7", "V9"],
    ],
    "golden_hour": [
        ["Imaj9", "IVmaj9", "iii7", "vi9"],
        ["Imaj9", "iii7", "IVmaj9", "ii9"],
        ["vi9", "IVmaj9", "Imaj9", "V13"],
    ],
}

FAMILY_PREFERRED_MODES = {
    "after_hours": ("major", "mixolydian"),
    "smoke_and_rain": ("minor", "dorian"),
    "neo_soul": ("major", "minor"),
    "dorian_drive": ("dorian", "minor"),
    "golden_hour": ("major", "mixolydian"),
}

FAMILY_DEGREE_CHORDS = {
    "after_hours": {
        "I": "Imaj9",
        "ii": "ii9",
        "iii": "iii7",
        "IV": "IVmaj9",
        "V": "V13",
        "vi": "vi11",
        "VII": "VII13",
    },
    "smoke_and_rain": {
        "i": "i9",
        "ii": "ii9",
        "III": "IIImaj9",
        "iv": "iv11",
        "V": "V9",
        "VI": "VImaj7",
        "VII": "VII13",
    },
    "neo_soul": {
        "I": "Imaj9",
        "ii": "ii13",
        "iii": "III7",
        "IV": "IVmaj9",
        "V": "V13",
        "vi": "vi9",
        "VII": "VII13",
    },
    "dorian_drive": {
        "i": "i9",
        "ii": "ii9",
        "III": "IIImaj9",
        "IV": "IV13",
        "V": "V9",
        "VI": "VImaj7",
        "VII": "VII13",
    },
    "golden_hour": {
        "I": "Imaj9",
        "ii": "ii9",
        "iii": "iii7",
        "IV": "IVmaj9",
        "V": "V13",
        "vi": "vi9",
        "VII": "VII13",
    },
}

MAJOR_TRANSITIONS = {
    "I": ("ii", "iii", "IV", "V", "vi", "VII"),
    "ii": ("iii", "V", "VII"),
    "iii": ("IV", "vi"),
    "IV": ("ii", "V", "I"),
    "V": ("I", "iii", "vi"),
    "vi": ("ii", "IV"),
    "VII": ("I", "iii"),
}

MINOR_TRANSITIONS = {
    "i": ("iv", "V", "VI", "VII"),
    "ii": ("V", "VII"),
    "III": ("iv", "VI"),
    "iv": ("i", "V", "VII"),
    "V": ("i", "VI", "III"),
    "VI": ("ii", "iv", "VII"),
    "VII": ("i", "III", "VI"),
}

PIANO_PATTERNS = {
    "dusty_chords": [
        [2, 10],
        [0, 7, 11],
        [3, 6, 10, 14],
    ],
    "broken_voicings": [
        [0, 6, 10, 14],
        [2, 7, 12],
        [0, 3, 8, 11, 15],
    ],
    "lush_spread": [
        [0, 4, 8, 12],
        [2, 6, 10, 14],
        [0, 5, 9, 13],
    ],
}

BASS_PATTERNS = {
    "root_pocket": [
        [0, 4, 8, 12],
        [0, 6, 8, 14],
        [0, 4, 10, 12],
    ],
    "walking_glide": [
        [0, 4, 8, 12],
        [0, 4, 7, 10, 12, 15],
        [0, 3, 6, 9, 12, 15],
    ],
    "counter_melody": [
        [0, 3, 6, 10, 12, 14],
        [0, 2, 6, 8, 11, 14],
        [0, 4, 6, 9, 12, 13],
    ],
    "octave_bounce": [
        [0, 4, 8, 10, 12, 14],
        [0, 2, 8, 10, 12, 15],
        [0, 4, 7, 11, 12, 14],
    ],
}

LEAD_PATTERNS = {
    "motivic_reply": [
        [0, 2, 4, 2, 1, -1],
        [0, 3, 5, 3, 2, 0],
        [2, 4, 5, 4, 2, 1],
    ],
    "airy_runs": [
        [4, 5, 2, 1, 0, -2],
        [2, 4, 5, 7, 5, 4, 2],
        [5, 4, 2, 1, 0, -1],
    ],
    "vibraphone_hook": [
        [0, 4, 7, 9, 7, 4],
        [0, 2, 4, 7, 4, 2],
        [2, 4, 7, 9, 7, 5],
    ],
    "blues_smear": [
        [0, 3, 5, 6, 5, 3, 0],
        [0, 3, 4, 5, 7, 6, 5],
        [2, 3, 5, 6, 5, 3, 2],
    ],
}

DRUM_PATTERNS = {
    "boom_bap_jazz": [
        {
            "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0],
            "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hat": [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
            "ghost": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            "open": [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
        },
        {
            "kick": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
            "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0],
            "hat": [1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0],
            "ghost": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
            "open": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        },
    ],
    "laid_back_lofi": [
        {
            "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0],
            "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hat": [1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1],
            "ghost": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
            "open": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        },
        {
            "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
            "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hat": [1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0],
            "ghost": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
            "open": [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        },
    ],
    "swing_knock": [
        {
            "kick": [1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0],
            "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hat": [1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0],
            "ghost": [0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0],
            "open": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        },
        {
            "kick": [1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            "snare": [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1],
            "hat": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            "ghost": [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
            "open": [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0],
        },
    ],
    "neo_soul_snap": [
        {
            "kick": [1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0],
            "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hat": [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1],
            "ghost": [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0],
            "open": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        },
        {
            "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0],
            "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
            "hat": [1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1],
            "ghost": [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
            "open": [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        },
    ],
}
