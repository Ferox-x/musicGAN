import os
import numpy as np
import random
from music21 import converter, instrument, note, chord, stream
from keras.models import load_model

folder_path = 'MIDI'
notes_and_instruments = []
instrument_names = []

for file in os.listdir(folder_path):
    if file.endswith('.mid'):
        file_path = os.path.join(folder_path, file)
        midi = converter.parse(file_path)

        try:
            instruments = instrument.partitionByInstrument(midi)
            instrument_name = instruments.parts[0].getInstrument().instrumentName
            class_instance = getattr(instrument, instrument_name)()
            instrument_names.append(instrument_name)
        except Exception:
            pass

        notes_to_parse = None
        try:
            instrument_in_midi = instrument.partitionByInstrument(midi)
            notes_to_parse = instrument_in_midi.parts[0].recurse()
        except Exception:
            notes_to_parse = midi.flat.notes

        for element in notes_to_parse:
            if isinstance(element, note.Note):
                element: note.Note
                if not instrument_name:
                    instrument_name = random.choice(instrument_names)
                notes_and_instruments.append((element.name, instrument_name))

pitch_names = sorted(set(str(item[0]) for item in notes_and_instruments))
instrument_names = sorted(set(item[1] for item in notes_and_instruments))

note_to_int = dict((note, number) for number, note in enumerate(pitch_names))
int_to_note = dict((number, note) for number, note in enumerate(pitch_names))
instrument_to_int = dict((instrument, number) for number, instrument in enumerate(instrument_names))
int_to_instrument = dict((number, instrument) for number, instrument in enumerate(instrument_names))

sequence_length = 10
network_input = []
network_output_notes = []
network_output_instruments = []

for i in range(len(notes_and_instruments) - sequence_length):
    sequence_in = notes_and_instruments[i:i + sequence_length]
    sequence_out_note = notes_and_instruments[i + sequence_length][0]
    sequence_out_instrument = notes_and_instruments[i + sequence_length][1]

    network_input.append([note_to_int[str(item[0])] for item in sequence_in] + [instrument_to_int[sequence_in[-1][1]]])
    network_output_notes.append(note_to_int[str(sequence_out_note)])
    network_output_instruments.append(instrument_to_int[sequence_out_instrument])


model = load_model('./model')

start = np.random.randint(0, len(network_input))
pattern = network_input[start][:sequence_length]

prediction_output_notes = []
prediction_output_instruments = []

for _ in range(150):
    pattern_with_instrument = pattern + [instrument_to_int[random.choice(instrument_names)]]
    prediction_input = np.reshape(pattern_with_instrument, (1, len(pattern_with_instrument), 1))
    prediction_input = prediction_input / float(len(pitch_names))

    prediction = model.predict(prediction_input, verbose=0)
    index_note = np.random.choice(len(prediction[0][0]), p=prediction[0][0])
    index_instrument = np.random.choice(len(prediction[1][0]), p=prediction[1][0])

    result_note = int_to_note[index_note]
    result_instrument = int_to_instrument[index_instrument]

    prediction_output_notes.append(result_note)
    prediction_output_instruments.append(result_instrument)

    pattern.append(index_note)
    pattern = pattern[1:]

generated_music = stream.Score()

for i in range(len(prediction_output_notes)):
    note_or_chord = prediction_output_notes[i]
    instrument_name = prediction_output_instruments[i]
    print(note_or_chord)
    if len(note_or_chord) > 1 and ' ' in note_or_chord:
        pitches = []
        print(note_or_chord)
        for p in note_or_chord.split(' '):
            new_note = note.Note(p)
            new_note.instrument = getattr(instrument, instrument_name)()

        new_chord = chord.Chord(pitches)
        new_chord.storedInstrument = instrument_name
        generated_music.append(new_chord)
    else:
        new_note = note.Note(note_or_chord)
        new_note.instrument = getattr(instrument, instrument_name)()
        generated_music.append(new_note)

generated_music.write('midi', fp='generated_music_with_instruments.mid')
