import argparse
import numpy as np
import mido
import torch
from mido import MidiFile, MidiTrack, Message
from music21 import key, chord, stream, note
import os
import librosa
import soundfile as sf
from transformers import AutoProcessor, MusicgenForConditionalGeneration

# Configuration for MusicGen Melody
MUSICGEN_CONFIG = {
    'model_name': 'facebook/musicgen-melody',
    'duration': 30,  # Duration in seconds
    'sampling_rate': 44100
}

class MidiProcessor:
    """Processes MIDI files and extracts musical data with improved parsing"""
    def __init__(self, midi_path):
        self.midi = MidiFile(midi_path)
        self.analysis = {
            'notes': [],
            'chords': [],
            'key': None,
            'tempo_changes': [],
            'metadata': {
                'ticks_per_beat': self.midi.ticks_per_beat,
                'duration': self.midi.length
            }
        }
        self.active_notes = {}

    def parse(self):
        """Improved parsing with accurate timing and chord detection"""
        current_time = 0
        for track in self.midi.tracks:
            for msg in track:
                current_time += msg.time
                self._process_message(msg, current_time)
       
        self.analysis['key'] = self.detect_key()
        self._detect_chords()
        return self.analysis

    def _process_message(self, msg, time):
        """Handle MIDI messages with precise timing"""
        if msg.type == 'set_tempo':
            self.analysis['tempo_changes'].append({
                'time': time,
                'bpm': mido.tempo2bpm(msg.tempo)
            })
        elif msg.type == 'note_on' and msg.velocity > 0:
            self.active_notes[msg.note] = {
                'start': time,
                'velocity': msg.velocity
            }
        elif msg.type in ['note_off', 'note_on'] and msg.velocity == 0:
            if msg.note in self.active_notes:
                note_data = self.active_notes.pop(msg.note)
                self.analysis['notes'].append({
                    'note': msg.note,
                    'start': note_data['start'],
                    'end': time,
                    'duration': time - note_data['start'],
                    'velocity': note_data['velocity']
                })

    def _detect_chords(self):
        """Chord detection with temporal alignment"""
        notes = sorted(self.analysis['notes'], key=lambda x: x['start'])
        current_chord = []
        current_time = 0

        for n in notes:
            if n['start'] > current_time:
                if len(current_chord) > 0:
                    self._add_chord(current_chord, current_time)
                current_time = n['start']
                current_chord = [n['note']]
            else:
                current_chord.append(n['note'])
       
        if len(current_chord) > 0:
            self._add_chord(current_chord, current_time)

    def _add_chord(self, notes, time):
        """Add recognized chord to analysis"""
        music21_chord = chord.Chord(notes)
        self.analysis['chords'].append({
            'time': time,
            'chord': music21_chord.pitchedCommonName,
            'pitches': [p.midi for p in music21_chord.pitches]
        })

    def detect_key(self):
        """Improved key detection using music21"""
        s = stream.Stream()
        for n in self.analysis['notes']:
            s.append(note.Note(n['note'], quarterLength=n['duration']/self.midi.ticks_per_beat))
        return s.analyze('key')

class MusicGenComposer:
    """Handles music generation using MusicGen Melody model"""
    def __init__(self, config):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = MusicgenForConditionalGeneration.from_pretrained(
            config['model_name']
        ).to(self.device)
        self.processor = AutoProcessor.from_pretrained(config['model_name'])
        self.config = config

    def generate(self, midi_path, analysis):
        """Generate continuation using MusicGen with melody conditioning"""
        # Convert MIDI to audio for melody conditioning
        melody, sr = self.midi_to_audio(midi_path)
       
        # Create text prompt from musical analysis
        prompt = self._create_prompt(analysis)
       
        # Process inputs and generate
        inputs = self.processor(
            text=[prompt],
            audio=melody,
            sampling_rate=sr,
            padding=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            audio_values = self.model.generate(
                **inputs,
                do_sample=True,
                guidance_scale=3,
                max_new_tokens=self.config['duration']*50
            )

        return audio_values.cpu().numpy().squeeze()

    def midi_to_audio(self, midi_path):
        """Convert MIDI to audio waveform using pretty_midi"""
        pm = mido.MidiFile(midi_path)
        synth = pretty_midi.PrettyMIDI()
        synth.tempo_changes = [
            pretty_midi.TempoChange(tempo=msg.tempo, time=msg.time)
            for msg in pm if msg.type == 'set_tempo'
        ]
       
        # Process MIDI messages into pretty_midi format
        # (Implementation details omitted for brevity)
       
        audio = synth.synthesize()
        return audio, synth.get_end_time()

    def _create_prompt(self, analysis):
        """Create descriptive text prompt from musical analysis"""
        return (
            f"Musical continuation in {analysis['key']} major, "
            f"tempo {analysis['tempo_changes'][-1]['bpm'] if analysis['tempo_changes'] else 120} BPM, "
            f"featuring {analysis['chords'][-1]['chord'] if analysis['chords'] else 'harmonic'} progression, "
            "with emotional development and dynamic variation, "
            "maintaining melodic coherence while introducing new motifs"
        )

def save_output(audio_array, output_path, sr=44100):
    """Save generated audio to file"""
    sf.write(output_path, audio_array, sr)
    print(f"🎵 Saved generated audio to {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(script_dir, '..', 'server', 'recorded.mid')
    output_path = os.path.join(script_dir, '..', 'server', 'generated.wav')

    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        exit(1)

    # Process MIDI input
    processor = MidiProcessor(input_path)
    analysis = processor.parse()

    # Generate continuation with MusicGen
    composer = MusicGenComposer(MUSICGEN_CONFIG)
    generated_audio = composer.generate(input_path, analysis)

    # Save final output
    save_output(generated_audio, output_path)