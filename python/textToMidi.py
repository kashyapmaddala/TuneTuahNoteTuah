import sys
import os
import random
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
import numpy as np
from scipy.io import wavfile

# ===================== TEXT TO MUSIC PARAMETERS =====================
def interpret_mood(text):
    """Convert text description to musical parameters"""
    text = text.lower()
    params = {
        'scale': 'major',
        'tempo': 120,
        'articulation': 'legato',
        'rhythm': 'medium',
        'register': 'middle',
        'complexity': 0.5
    }

    if 'sad' in text or 'dark' in text or 'foreboding' in text:
        params['scale'] = 'minor'
        params['tempo'] = 80
        params['articulation'] = 'legato'
    if 'happy' in text or 'lighthearted' in text:
        params['tempo'] = 140
        params['rhythm'] = 'bouncy'
    if 'angry' in text or 'intense' in text:
        params['tempo'] = 160
        params['articulation'] = 'staccato'
        params['complexity'] = 0.8
    if 'calm' in text or 'relaxing' in text:
        params['tempo'] = 90
        params['rhythm'] = 'slow'
    
    if 'blues' in text:
        params['scale'] = 'blues'
    if 'jazz' in text:
        params['scale'] = 'jazz'
    
    return params

def get_scale(root=60, scale_type='major'):
    """Return MIDI notes for different scales"""
    scales = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'minor': [0, 2, 3, 5, 7, 8, 10],
        'blues': [0, 3, 5, 6, 7, 10],
        'jazz': [0, 2, 4, 6, 7, 9, 10, 11]
    }
    return [root + interval for interval in scales.get(scale_type, scales['major'])]

# ===================== MELODY GENERATION =====================
def generate_melody_from_text(text, length=16):
    """Generate melody based on text description"""
    params = interpret_mood(text)
    root_note = 60  # Middle C
    scale = get_scale(root_note, params['scale'])
    
    melody = []
    current_note = root_note
    
    for _ in range(length):
        if params['rhythm'] == 'bouncy':
            durations = [240, 480, 720]
        elif params['rhythm'] == 'slow':
            durations = [480, 960]
        else:
            durations = [480]
        
        step = random.choice([-2, -1, 1, 2])
        current_note = scale[(scale.index(current_note) + step) % len(scale)]
        
        melody.append({
            'note': current_note,
            'duration': random.choice(durations),
            'velocity': random.randint(60, 100)
        })
    
    return melody, params

# ===================== MAIN INTERFACE =====================
def main(input_file):
    try:
        with open(input_file, 'r') as f:
            user_input = f.read().strip()
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found")
        return
    except Exception as e:
        print(f"Error reading input file: {str(e)}")
        return

    if not user_input:
        print("Error: Empty input file")
        return

    melody, params = generate_melody_from_text(user_input)
    
    # Create output directory if needed
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'server')
    os.makedirs(output_dir, exist_ok=True)
    
    # Save MIDI
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(params['tempo'])))
    
    for note in melody:
        track.append(Message('note_on', note=note['note'], 
                         velocity=note['note'], time=0))
        track.append(Message('note_off', note=note['note'], 
                         velocity=0, time=note['duration']))
    
    output_path = os.path.join(output_dir, 'generated2.mid')
    mid.save(output_path)
    print(f"Generated MIDI saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python textToMidi.py <input_file.txt>")
        sys.exit(1)
    
    main(sys.argv[1])