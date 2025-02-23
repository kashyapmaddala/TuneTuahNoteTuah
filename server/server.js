const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { Midi } = require('@tonejs/midi'); // Add this for MIDI generation
const { spawn } = require('child_process'); // Used to run midi_generator.py
const axios = require('axios'); // Add axios for HTTP requests


const app = express();
const PORT = 5002;

const serverDir = __dirname;
const pythonScriptPath = path.join(serverDir, '..', 'python', 'textToMidi.py');

// Enable CORS to allow frontend to access the backend
app.use(cors());

// Serve static files (index.html, app.js, styles.css, etc.) from the root directory
app.use(express.static(path.join(__dirname, '..')));
//app.use('/server', express.static(serverDir)); 

// Serve sounds from the /sounds2 directory
app.use('/sounds2', express.static(path.join(__dirname, '..', 'sounds2')));

// Middleware to parse JSON data from the frontend
app.use(express.json());

// Serve index.html when accessing the root URL
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, '..', 'index.html')); // Ensure it loads index.html correctly
});

// POST route to save MIDI data
app.post("/save-midi", (req, res) => {
    const recordedNotes = req.body.notes;

    if (!recordedNotes || recordedNotes.length === 0) {
        return res.status(400).json({ error: "No notes recorded." });
    }

    // Create a new MIDI file
    const midi = new Midi();

    // Create a track for the recorded notes
    const track = midi.addTrack();

    // Add notes to the track
    recordedNotes.forEach(({ note, time }) => {
        const midiNote = noteToMidi(note); // Convert note to MIDI number
        track.addNote({
            midi: midiNote,
            time: time,
            duration: 1, // You can adjust the duration as needed
        });
    });

    // Save the MIDI file to the server directory (outside of the public folder for safety)
    const filePath = path.join(__dirname, 'recorded.mid'); // Save it directly under the server folder
    fs.writeFileSync(filePath, Buffer.from(midi.toArray()));

    console.log("MIDI file saved:", filePath);

    // Run midi_generator.py to process the MIDI file
    const pythonProcess = spawn('python3', [path.join(__dirname, '..', 'python', 'midi_generator.py')]);

    let outputData = '';
    let errorData = '';

    // Capture the standard output (stdout)
    pythonProcess.stdout.on('data', (data) => {
        outputData += data.toString();
    });

    // Capture the standard error (stderr)
    pythonProcess.stderr.on('data', (data) => {
        errorData += data.toString();
    });

    // Handle the Python process completion
    pythonProcess.on('close', (code) => {
        if (code === 0) {
            console.log("midi_generator.py processing completed.");
            console.log("Output: ", outputData);

            // Save the generated MIDI to a new file
            const generatedFilePath = path.join(__dirname, 'server', 'generated.mid');
            // Return the generated file path for frontend
            res.json({ message: "MIDI file saved and generated successfully", filePath: `/server/generated.mid` });
        } else {
            console.error(`midi_generator.py exited with code ${code}`);
            console.error("Error Output: ", errorData);
            res.status(500).json({ error: `Error processing MIDI file: ${errorData}` });
        }
    });
});

app.post('/save-text', async (req, res) => {
    const text = req.body.text;

    if (!text || text.trim() === '') {
        return res.status(400).json({ error: "No text provided" });
    }

    try {
        // Call the FastAPI endpoint
        const response = await axios.post('http://localhost:8000/generate_music/', new URLSearchParams({ text }));

        if (response.status !== 200) {
            throw new Error('Failed to generate music');
        }

        const { audio, midi } = response.data;

        res.json({
            message: 'Melody generated successfully',
            audioPath: audio,
            midiPath: midi
        });
    } catch (error) {
        console.error('Error generating melody:', error);
        res.status(500).json({
            error: 'Melody generation failed',
            details: error.message
        });
    }
});

// Utility function to convert note name to MIDI number
function noteToMidi(note) {
    const noteMap = {
        C: 0, "C#": 1, D: 2, "D#": 3, E: 4, F: 5, "F#": 6, G: 7, "G#": 8, A: 9, "A#": 10, B: 11
    };
    const octave = parseInt(note[note.length - 1], 10); // Get the octave number
    const noteName = note.slice(0, -1); // Get the note name without the octave
    return noteMap[noteName] + (octave + 1) * 12; // Convert to MIDI number
}

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});