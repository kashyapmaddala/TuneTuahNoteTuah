import numpy as np
import os
import random
from collections import defaultdict
from music21 import converter, instrument, note, chord, stream, tempo, scale

class MelodyGenerator:
    def __init__(self, order=2, chord_interval=4, max_leap=5):
        self.order = order
        self.chord_interval = chord_interval
        self.max_leap = max_leap
        self.scale_pitches = []
        self.scale_degrees = []
        self.current_key = None

    def parse_midi(self, midi_path):
        """Parse MIDI with enhanced scale analysis"""
        try:
            midi_stream = converter.parse(midi_path)
            self.current_key = midi_stream.analyze('key')
            print(f"Detected key: {self.current_key.tonic.name} {self.current_key.mode}")
            
            # Get scale properties
            self.scale_pitches = [p.midi for p in self.current_key.getPitches()]
            self.scale_degrees = list(range(1, 8))  # 1-7 scale degrees
            
            elements = midi_stream.flatten().elements
            notes = []
            current_chord = []
            
            for element in elements:
                if isinstance(element, note.Note):
                    notes.append({
                        'pitch': element.pitch.midi,
                        'degree': self._get_scale_degree(element),
                        'duration': element.duration.quarterLength,
                        'offset': element.offset
                    })
                elif isinstance(element, chord.Chord):
                    current_chord = [p.midi for p in element.pitches]
            
            return notes, current_chord, midi_stream
        except Exception as e:
            raise RuntimeError(f"MIDI parsing failed: {str(e)}")

    def _get_scale_degree(self, element):
        """Get scale degree ensuring it stays within detected scale"""
        try:
            degree = self.current_key.getScaleDegreeFromPitch(element.pitch)
            return degree if degree in self.scale_degrees else self._nearest_scale_degree(element.pitch.midi)
        except:
            return self._nearest_scale_degree(element.pitch.midi)

    def _nearest_scale_degree(self, pitch):
        """Find the nearest valid scale degree"""
        nearest_pitch = min(self.scale_pitches, key=lambda x: abs(x - pitch))
        return self.scale_degrees[self.scale_pitches.index(nearest_pitch)]

    def build_models(self, notes):
        """Build models with scale-constrained transitions"""
        degree_model = defaultdict(list)
        duration_model = defaultdict(list)
        
        for i in range(len(notes)-self.order):
            # Only consider transitions that stay in scale
            if all(n['degree'] in self.scale_degrees for n in notes[i:i+self.order+1]):
                degree_state = tuple(n['degree'] for n in notes[i:i+self.order])
                degree_model[degree_state].append(notes[i+self.order]['degree'])
                
                duration_state = tuple(n['duration'] for n in notes[i:i+self.order])
                duration_model[duration_state].append(notes[i+self.order]['duration'])
        
        return degree_model, duration_model

    def generate(self, notes, length=50):
        """Generate scale-constrained melody with rhythmic consistency"""
        degree_model, duration_model = self.build_models(notes)
        melody = []
        
        # Initialize states with scale-constrained values
        last_degree = notes[-1]['degree'] if notes else random.choice(self.scale_degrees)
        last_duration = notes[-1]['duration'] if notes else 1.0
        duration_state = tuple(n['duration'] for n in notes[-self.order:]) if notes else ()
        
        for _ in range(length):
            # Generate rhythm first to maintain pattern
            duration = self._generate_duration(duration_model, duration_state)
            duration_state = tuple(list(duration_state[1:]) + [duration])
            
            # Generate melody note constrained to scale
            degree = self._generate_scale_degree(degree_model, last_degree)
            pitch = self._degree_to_pitch(degree, last_degree)
            
            # Add harmonic support within scale
            if random.random() < 0.3:  # 30% chance of in-scale harmony
                harmony_degree = self._get_harmony_degree(degree)
                harmony_pitch = self._degree_to_pitch(harmony_degree, degree)
                melody.append({'pitches': sorted([pitch, harmony_pitch]), 'duration': duration})
            else:
                melody.append({'pitch': pitch, 'duration': duration})
            
            last_degree = degree
        
        return melody

    def _generate_duration(self, model, state):
        """Generate rhythm following input patterns"""
        if state in model and model[state]:
            return random.choice(model[state])
        # Fallback to most common duration in model
        all_durations = [d for durations in model.values() for d in durations]
        return random.choice(all_durations) if all_durations else 1.0

    def _generate_scale_degree(self, model, last_degree):
        """Generate next degree strictly within scale"""
        state = tuple([last_degree])
        return random.choice(model.get(state, self.scale_degrees))

    def _degree_to_pitch(self, degree, last_degree):
        """Convert degree to pitch with voice leading constraints"""
        base_pitch = self.current_key.pitchFromDegree(degree).midi
        # Ensure we stay within scale
        if base_pitch not in self.scale_pitches:
            base_pitch = self.scale_pitches[self.scale_degrees.index(degree)]
        
        # Apply smooth voice leading
        if abs(base_pitch - self.current_key.pitchFromDegree(last_degree).midi) > self.max_leap:
            direction = 1 if base_pitch > self.current_key.pitchFromDegree(last_degree).midi else -1
            return self.current_key.pitchFromDegree(last_degree + direction).midi
        return base_pitch

    def _get_harmony_degree(self, degree):
        """Get harmonically related scale degree"""
        intervals = [2, 4]  # Third and fifth intervals
        interval = random.choice(intervals)
        harmony_degree = (degree + interval - 1) % 7 + 1
        return harmony_degree if harmony_degree in self.scale_degrees else degree

    def save_midi(self, original_stream, generated, output_path):
        """Save MIDI with scale validation"""
        output = stream.Stream()
        
        # Preserve original elements
        for elem in original_stream:
            if isinstance(elem, (tempo.MetronomeMark, instrument.Instrument)):
                output.append(elem)
        
        # Add original notes
        for elem in original_stream.flatten().notes:
            output.append(elem)
        
        # Add generated content with scale validation
        last_offset = max(n.offset + n.duration.quarterLength for n in original_stream.flat.notes) if original_stream.notes else 0
        current_offset = last_offset + 2.0
        
        for note_data in generated:
            if 'pitches' in note_data:
                # Ensure all chord tones are in scale
                valid_pitches = [p for p in note_data['pitches'] if p in self.scale_pitches]
                if not valid_pitches:
                    valid_pitches = [self.current_key.tonic.midi]
                c = chord.Chord(valid_pitches)
                c.duration.quarterLength = note_data['duration']
                output.insert(current_offset, c)
            else:
                n = note.Note(note_data['pitch'])
                n.duration.quarterLength = note_data['duration']
                output.insert(current_offset, n)
            current_offset += note_data['duration']
        
        output.write('midi', fp=output_path)

if __name__ == "__main__":
    # Get the directory of this script
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Configure paths using absolute paths
    input_path = os.path.join(script_dir, '..', 'server', 'recorded.mid')
    output_path = os.path.join(script_dir, '..', 'server', 'generated.mid')
    
    # Convert to absolute paths and check existence
    input_path = os.path.abspath(input_path)
    output_dir = os.path.dirname(output_path)
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Verify input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        print("Please ensure you have a 'server' directory with 'recorded.mid'")
        exit(1)
        
    # Initialize generator
    generator = MelodyGenerator(order=2, chord_interval=3, max_leap=4)
    
    # Process MIDI
    try:
        notes, chords, original_stream = generator.parse_midi(input_path)
        generated_notes = generator.generate(notes+chords)
        generator.save_midi(original_stream, generated_notes, output_path)
        print(f"Successfully generated {len(generated_notes)} notes in {output_path}")
    except Exception as e:
        print(f"Error processing MIDI: {str(e)}")
        exit(1)
