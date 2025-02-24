//import { Midi } from '@tonejs/midi';

console.log("Script2.js is loading");

document.getElementById("start-audio").addEventListener("click", async () => {
    await Tone.start();
    console.log("Audio started!");
});

document.addEventListener("DOMContentLoaded", () => {
    
    // Separate playback functionality for generated melody (based on the input melody)
    const playGeneratedBtn = document.getElementById('play-generated');

    // Generate a quick melody based on some text
    const generateButton = document.getElementById('generate-button');
    const melodyText = document.getElementById('melody-text');

    // Record, stop, playback functions    
    const recordButton = document.getElementById("record");
    const stopButton = document.getElementById("stop");
    const playbackButton = document.getElementById("playback");


    // Alternate textToMidi code 1

    // async function convertTextToMidi(text) {
    //     try {
    //         const response = await fetch('/save-text', {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/json'
    //             },
    //             body: JSON.stringify({ text })
    //         });
    
    //         if (!response.ok) throw new Error('Failed to convert text to MIDI');
    
    //         const data = await response.json();
    //         return data.midiPath;
    //     } catch (error) {
    //         console.error('Error converting text to MIDI:', error);
    //         throw error;
    //     }
    // }
    
    // document.getElementById('generate-button').addEventListener('click', async () => {
    //     const text = melodyText.value.trim();
    //     if (!text) {
    //         alert('Please enter a melody description');
    //         return;
    //     }
    
    //     try {
    //         const midiPath = await convertTextToMidi(text);
    //         console.log('Generated MIDI file path:', midiPath);
    //         // You can now use the midiPath to play the generated MIDI file
    //     } catch (error) {
    //         alert('Error generating MIDI file. Please try again.');
    //     }
    // });

    // document.getElementById('play-generated').addEventListener('click', async () => {
    //     try {
    //         // Stop any current playback
    //         Tone.Transport.stop();
            
    //         // Fetch the generated MIDI file
    //         const response = await fetch('/server/generated.mid');
    //         const arrayBuffer = await response.arrayBuffer();
    
    //         // Create a MIDI object from the file
    //         const midi = new Midi(arrayBuffer);
    
    //         // Start with a clean transport
    //         Tone.Transport.cancel();
            
    //         // Schedule all notes from the generated MIDI
    //         midi.tracks.forEach(track => {
    //             track.notes.forEach(note => {
    //                 Tone.Transport.scheduleOnce(time => {
    //                     synth.triggerAttackRelease(note.name, note.duration, time);
    //                 }, note.time);
    //             });
    //         });
    
    //         // Start the audio context and transport
    //         await Tone.start();
    //         console.log("Playing the generated melody!");
    //         Tone.Transport.start();
    
    //     } catch (error) {
    //         console.error("Error playing generated melody:", error);
    //     }
    // });

    // Alternate textToMidi code 2

    // async function convertTextToAudio(text) {
    //     try {
    //         const response = await fetch('/save-text', {
    //             method: 'POST',
    //             headers: {
    //                 'Content-Type': 'application/json'
    //             },
    //             body: JSON.stringify({ text })
    //         });
    
    //         if (!response.ok) throw new Error('Failed to convert text to audio');
    
    //         const data = await response.json();
    //         return data.audioPath;
    //     } catch (error) {
    //         console.error('Error converting text to audio:', error);
    //         throw error;
    //     }
    // }
    
    // document.getElementById('generate-button').addEventListener('click', async () => {
    //     const text = document.getElementById('melody-text').value.trim();
    //     if (!text) {
    //         alert('Please enter a melody description');
    //         return;
    //     }
    
    //     try {
    //         const audioPath = await convertTextToAudio(text);
    //         console.log('Generated audio file path:', audioPath);
    //         // You can now use the audioPath to play the generated audio file
    //     } catch (error) {
    //         alert('Error generating audio file. Please try again.');
    //     }
    // });
    
    // document.getElementById('play-generated').addEventListener('click', async () => {
    //     try {
    //         // Fetch the generated audio file
    //         const response = await fetch('/server/generated.wav');
    //         const arrayBuffer = await response.arrayBuffer();
    //         const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    //         const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
    
    //         // Create a buffer source and play the audio
    //         const source = audioContext.createBufferSource();
    //         source.buffer = audioBuffer;
    //         source.connect(audioContext.destination);
    //         source.start(0);
    
    //         console.log("Playing the generated melody!");
    
    //     } catch (error) {
    //         console.error("Error playing generated melody:", error);
    //     }
    // });


    //ORIGINAL generateButton code
    generateButton.addEventListener('click', async () => {
        const text = melodyText.value.trim();
        
        if (!text) {
            alert('Please enter a melody description');
            return;
        }

        try {
            // Save text to server
            const response = await fetch('/save-text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) throw new Error('Failed to save text');

            // Reset input field with feedback
            melodyText.value = '';
            const originalPlaceholder = melodyText.placeholder;
            melodyText.placeholder = 'Description sent to AI! ✅';
            
            setTimeout(() => {
                melodyText.placeholder = originalPlaceholder;
            }, 2000);

            console.log('Text input saved and sent for processing');

        } catch (error) {
            console.error('Generation error:', error);
            alert('Error processing request. Please try again.');
        }
        
        recordButton.disabled = true;
        stopButton.disabled = true;
        playbackButton.disabled = true;
        generateButton.disabled = true;
        playGeneratedBtn.disabled = true;
        try {
            // Stop any current playback
            Tone.Transport.stop();
            
            // Fetch the generated MIDI file
            const response = await fetch('/server/generated2.mid');
            const arrayBuffer = await response.arrayBuffer();

            // Create a MIDI object from the file
            const midi = new Midi(arrayBuffer);

            // Start with a clean transport
            Tone.Transport.cancel();
            
            // Schedule all notes from the generated MIDI
            midi.tracks.forEach(track => {
                track.notes.forEach(note => {
                    Tone.Transport.scheduleOnce(time => {
                        synth.triggerAttackRelease(note.name, note.duration, time);
                    }, note.time);
                });
            });

            // Start the audio context and transport
            await Tone.start();
            console.log("Playing the generated melody!");
            Tone.Transport.start();
            
        } catch (error) {
            console.error("Error playing generated melody:", error);
        }

        recordButton.disabled = false;
        stopButton.disabled = true;
        playbackButton.disabled = false;
        generateButton.disabled = false;
        playGeneratedBtn.disabled = false;
    });


    const synth = new Tone.Sampler({
        urls: {
            C1: "C1.mp3", "C#1": "C1s.mp3", D1: "D1.mp3", "D#1": "D1s.mp3",
            E1: "E1.mp3", F1: "F1.mp3", "F#1": "F1s.mp3", G1: "G1.mp3",
            "G#1": "G1s.mp3", A1: "A1.mp3", "A#1": "A1s.mp3", B1: "B1.mp3",
            C2: "C2.mp3", "C#2": "C2s.mp3", D2: "D2.mp3", "D#2": "D2s.mp3",
            E2: "E2.mp3", F2: "F2.mp3", "F#2": "F2s.mp3", G2: "G2.mp3",
            "G#2": "G2s.mp3", A2: "A2.mp3", "A#2": "A2s.mp3", B2: "B2.mp3",
            C3: "C3.mp3", "C#3": "C3s.mp3", D3: "D3.mp3", "D#3": "D3s.mp3",
            E3: "E3.mp3", F3: "F3.mp3", "F#3": "F3s.mp3", G3: "G3.mp3",
            "G#3": "G3s.mp3", A3: "A3.mp3", "A#3": "A3s.mp3", B3: "B3.mp3",
            C4: "C4.mp3", "C#4": "C4s.mp3", D4: "D4.mp3", "D#4": "D4s.mp3",
            E4: "E4.mp3", F4: "F4.mp3", "F#4": "F4s.mp3", G4: "G4.mp3",
            "G#4": "G4s.mp3", A4: "A4.mp3", "A#4": "A4s.mp3", B4: "B4.mp3",
            C5: "C5.mp3",
        },
        release: 1,
        baseUrl: "/sounds2/",
    }).toDestination();

    const keys = [
        { note: "C", isBlack: false }, { note: "C#", isBlack: true }, { note: "D", isBlack: false }, { note: "D#", isBlack: true },
        { note: "E", isBlack: false }, { note: "F", isBlack: false }, { note: "F#", isBlack: true }, { note: "G", isBlack: false },
        { note: "G#", isBlack: true }, { note: "A", isBlack: false }, { note: "A#", isBlack: true }, { note: "B", isBlack: false }
    ];

    const piano = document.getElementById("piano");
    let recording = false;
    let recordedNotes = [];
    let startTime = 0;
    let transportPlaying = false;

    for (let octave = 1; octave <= 5; octave++) {
        keys.forEach(key => {
            const keyElement = document.createElement("div");
            keyElement.classList.add("key");
            if (key.isBlack) keyElement.classList.add("black");
            keyElement.dataset.note = `${key.note}${octave}`;
            keyElement.innerText = key.note;
            keyElement.addEventListener("click", () => playSound(keyElement.dataset.note));
            piano.appendChild(keyElement);
        });
    }

    function playSound(note) {
        synth.triggerAttackRelease(note, "8n");
        if (recording) {
            const time = Tone.now() - startTime;
            recordedNotes.push({ note, time });
        }
    }

    recordButton.addEventListener("click", () => {
        recordedNotes = [];
        recording = true;
        Tone.Transport.stop();
        Tone.Transport.cancel();
        startTime = Tone.now();
        recordButton.disabled = true;
        stopButton.disabled = false;
        generateButton.disabled = true;

        playGeneratedBtn.disabled = true;
        playbackButton.disabled = true;
        
        console.log("Recording started...");
    });

    stopButton.addEventListener("click", () => {
        recording = false;
        recordButton.disabled = false;
        stopButton.disabled = true;
        playbackButton.disabled = recordedNotes.length === 0 ? true : false;

        playGeneratedBtn.disabled = recordedNotes.length === 0 ? true : false;
        generateButton.disabled = false;
        console.log("Recording stopped:", recordedNotes);

        // Send recorded notes to the server to save as MIDI
        fetch("/save-midi", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ notes: recordedNotes })
        })
        .then(response => response.json())
        .then(data => {
            console.log("MIDI saved:", data);
        })
        .catch(error => console.error("Error saving MIDI:", error));
    });

    // ... (keep all the previous code until the playbackButton section)

    playbackButton.addEventListener("click", () => {
        recordButton.disabled = true;
        stopButton.disabled = true;
        playbackButton.disabled = true;
        generateButton.disabled = true;
        playGeneratedBtn.disabled = true;

        if (transportPlaying) {
            Tone.Transport.stop();
            transportPlaying = false;
            console.log("Recorded playback stopped.");
        } else {
            transportPlaying = true;
            console.log("Playing back recorded notes...");
            recordedNotes.forEach(({ note, time }) => {
                Tone.Transport.scheduleOnce(() => {
                    synth.triggerAttackRelease(note, "8n");
                }, time);
            });
            Tone.Transport.start();
        }

        recordButton.disabled = false;
        stopButton.disabled = true;
        playbackButton.disabled = false;
        generateButton.disabled = false;
        playGeneratedBtn.disabled = false;
    });

    // ORIGINAL playGeneratedBtn code
    playGeneratedBtn.addEventListener('click', async () => {
        try {

            // Stop any current playback
            Tone.Transport.stop();
            
            // Fetch the generated MIDI file
            const response = await fetch('/server/generated.mid');
            const arrayBuffer = await response.arrayBuffer();

            // Create a MIDI object from the file
            const midi = new Midi(arrayBuffer);

            // Start with a clean transport
            Tone.Transport.cancel();
            
            // Schedule all notes from the generated MIDI
            midi.tracks.forEach(track => {
                track.notes.forEach(note => {
                    Tone.Transport.scheduleOnce(time => {
                        synth.triggerAttackRelease(note.name, note.duration, time);
                    }, note.time);
                });
            });

            // Start the audio context and transport
            await Tone.start();
            console.log("Playing the generated melody!");
            Tone.Transport.start();
    
        } catch (error) {
            console.error("Error playing generated melody:", error);
        }
    });
});




