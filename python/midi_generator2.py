import argparse
import numpy as np
import mido
import requests
import json
from mido import MidiFile, MidiTrack, Message, MetaMessage
from collections import defaultdict
from music21 import key, chord, stream, note
import os

# Configuration for AI-based music generation
DEEPSEEK_CONFIG = {
    'endpoint': 'http://localhost:5000/music',
    'timeout': 45,
    'model': 'deepseek-music-v1',
    'max_tokens': 2000
}

class MidiProcessor:
    """Processes MIDI files and extracts musical data."""
    def __init__(self, midi_path):
        self.midi = MidiFile(midi_path)
        self.analysis = {
            'notes': [],
            'chords': [],
            'key': None,
            'tempo_changes': [],
            'metadata': {'ticks_per_beat': self.midi.ticks_per_beat, 'duration': self.midi.length}
        }
    
    def parse(self):
        """Parses a MIDI file and extracts notes, key, and tempo information."""
        current_time = 0
        for track in self.midi.tracks:
            for msg in track:
                current_time += msg.time
                self._process_message(msg, current_time)
        
        self.analysis['key'] = self.detect_key()
        return self.analysis

    def detect_key(self):
        """Detects the key signature of the given melody using music21."""
        s = stream.Stream()
        for n in self.analysis['notes']:
            s.append(note.Note(n['note']))
        return s.analyze('key')

    def _process_message(self, msg, time):
        """Processes individual MIDI messages."""
        if msg.type == 'set_tempo':
            self.analysis['tempo_changes'].append({
                'time': time,
                'bpm': mido.tempo2bpm(msg.tempo),
                'tempo': msg.tempo
            })
        elif msg.type == 'note_on' and msg.velocity > 0:
            self.analysis['notes'].append({
                'note': msg.note,
                'time': time,
                'velocity': msg.velocity,
                'duration': None
            })
        elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
            self._handle_note_off(msg.note, time)

    def _handle_note_off(self, note, time):
        """Handles note-off events by assigning duration to the corresponding note."""
        for n in reversed(self.analysis['notes']):
            if n['note'] == note and n['duration'] is None:
                n['duration'] = time - n['time']
                break

class AIComposer:
    """Handles AI-based music generation using DeepSeek or a fallback method."""
    def __init__(self, config):
        self.config = config

    def generate(self, analysis):
        """Attempts AI-based continuation. Falls back if AI fails."""
        try:
            return self._query_deepseek(analysis)
        except Exception as e:
            print(f"AI generation failed: {str(e)}")
            return self.fallback(analysis)

    def _query_deepseek(self, analysis):
        """Sends a request to DeepSeek API and parses the response."""
        prompt = self._build_prompt(analysis)
        response = requests.post(
            self.config['endpoint'],
            json={'model': self.config['model'], 'prompt': prompt, 'max_tokens': self.config['max_tokens']},
            timeout=self.config['timeout']
        )
        return self._parse_response(response.json())

    def _build_prompt(self, analysis):
        return f"""
        Compose a musically appropriate continuation:
        - Key: {analysis['key']}
        - Recent chords: {analysis['chords'][-3:]}
        - Tempo: {analysis['tempo_changes'][-1]['bpm'] if analysis['tempo_changes'] else 120} BPM
        - Melody: {[n['note'] for n in analysis['notes'][-8:]]}

        Guidelines:
        - Maintain harmonic function
        - Use smooth voice leading
        - Balance tension and release
        - Output JSON format:
        {{
            "notes": [MIDI numbers],
            "dynamics": [velocity values],
            "rationale": "Brief music theory explanation"
        }}
        """

    def _parse_response(self, response):
        """Parses the AI API response."""
        try:
            return json.loads(response['choices'][0]['message']['content'])
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            print(f"Invalid AI response: {str(e)}")
            return self.fallback(response)

    def fallback(self, analysis):
        """Generates a fallback melody using scale degrees and simple rules."""
        key_scale = self._get_key_scale(analysis['key'])
        last_chord = analysis['chords'][-1] if analysis['chords'] else None

        new_notes = []
        for i in range(8):
            pitch = np.random.choice(last_chord['pitches']) if last_chord else np.random.choice(key_scale)
            new_notes.append({
                'pitch': int(pitch),
                'velocity': 64,
                'duration': 480  # Default duration
            })
        return new_notes

    def _get_key_scale(self, key_obj):
        """Extracts the scale degrees while avoiding dissonances."""
        return [p.midi for p in key_obj.pitches if p.midi % 12 != key_obj.tonic.midi]

def save_midi(input_midi_path, new_notes, output_path):
    """Saves the original notes from input MIDI concatenated with the generated notes as a new MIDI file."""
    # Load the input MIDI file to extract its notes
    input_midi = MidiFile(input_midi_path)
    input_notes = []

    # Extract notes from the input MIDI file
    for track in input_midi.tracks:
        current_time = 0
        for msg in track:
            current_time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                input_notes.append({
                    'note': msg.note,
                    'time': current_time,
                    'velocity': msg.velocity,
                    'duration': None
                })
            elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
                # Handle note-off events to assign durations
                for note in reversed(input_notes):
                    if note['note'] == msg.note and note['duration'] is None:
                        note['duration'] = current_time - note['time']
                        break

    # Get the last time from the original input notes
    last_time = max(n['time'] for n in input_notes) if input_notes else 0

    # Combine the input notes and new generated notes
    all_notes = [
        {
            'note': max(0, min(n['note'], 127)),  # Ensure MIDI note is in valid range
            'time': n['time'],  # Keep original note timings
            'velocity': max(0, min(n['velocity'], 127)),
            'duration': max(1, n.get('duration', 480))
        }
        for n in input_notes
    ] + [
        {
            'note': max(0, min(n['pitch'], 127)),  # Ensure MIDI note is in valid range
            'time': last_time + 480 * (i + 1),  # Offset new notes to start after the original melody
            'velocity': max(0, min(n['velocity'], 127)),
            'duration': max(1, n.get('duration', 480))
        }
        for i, n in enumerate(new_notes)
    ]

    # Sort all notes in ascending order of time
    all_notes.sort(key=lambda x: x['time'])
    current_time = 0

    # Create a new MIDI file to save the concatenated notes
    mid = MidiFile(ticks_per_beat=480)  # Same as input's ticks_per_beat
    track = MidiTrack()
    mid.tracks.append(track)

    # Convert to MIDI messages and write to the track
    for note in all_notes:
        delta = note['time'] - current_time
        delta = max(0, delta)  # Ensure time is non-negative
        track.append(Message('note_on', note=note['note'], velocity=note['velocity'], time=delta))
        track.append(Message('note_off', note=note['note'], velocity=0, time=note['duration']))
        current_time = note['time']

    # Save the concatenated MIDI file
    mid.save(output_path)
    print(f"🎵 Saved concatenated MIDI file to {output_path}")



if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, '..', 'server', 'recorded.mid')
    output_path = os.path.join(script_dir, '..', 'server', 'generated.mid')

    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        exit(1)

    processor = MidiProcessor(input_path)
    analysis = processor.parse()

    composer = AIComposer(DEEPSEEK_CONFIG)
    continuation = composer.generate(analysis)

    save_midi(input_path, continuation, output_path)
