import os
import numpy as np
import random
from music21 import converter, instrument, note, chord, stream
from keras.utils import to_categorical

folder_path = 'MIDI'
notes_and_instruments = []
instrument_names = []

for file in os.listdir(folder_path):
    if file.endswith('.mid'):
        file_path = os.path.join(folder_path, file)
        midi = converter.parse(file_path)

        instruments = instrument.partitionByInstrument(midi)
        parsed_instrument = instruments.parts[0].getInstrument()
        instrument_names.append(parsed_instrument.classes[0])
        notes_to_parse = None
        try:
            notes_to_parse = parsed_instrument.parts[0].recurse()
        except Exception:
            notes_to_parse = midi.flat.notes
        for element in notes_to_parse:
            if isinstance(element, note.Note):
                element: note.Note
                if not parsed_instrument:
                    parsed_instrument = random.choice(instrument_names)
                notes_and_instruments.append((element.name, parsed_instrument.classes[0]))


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

X = np.reshape(network_input, (len(network_input), sequence_length + 1, 1))
X = X / float(len(pitch_names))
y_notes = to_categorical(network_output_notes)
y_instruments = to_categorical(network_output_instruments)

from keras.models import Model
from keras.layers import Input, LSTM, Dense

input_layer = Input(shape=(X.shape[1], X.shape[2]))

lstm_layer = LSTM(256)(input_layer)

output_notes = Dense(y_notes.shape[1], activation='softmax', name='output_notes')(lstm_layer)

# Второй выход для инструмента
output_instruments = Dense(y_instruments.shape[1], activation='softmax', name='output_instruments')(lstm_layer)

model = Model(inputs=input_layer, outputs=[output_notes, output_instruments])
model.compile(loss='categorical_crossentropy', optimizer='adam')

# Обучение модели
model.fit(X, [y_notes, y_instruments], epochs=20, batch_size=128)

model.save('./model')

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
    print(note_or_chord, instrument_name)
    if len(note_or_chord) > 1 and ' ' in note_or_chord:
        pitches = []
        for p in note_or_chord.split(' '):
            new_note = note.Note(p)
            new_note.storedInstrument = getattr(instrument, instrument_name)()

        new_chord = chord.Chord(pitches)
        generated_music.append(new_chord)
    else:
        new_note = note.Note(note_or_chord)
        new_note.storedInstrument = getattr(instrument, instrument_name)()
        generated_music.append(new_note)

for _ in generated_music:
    if isinstance(_, note.Note):
        print(_, _.getInstrument(), 'Note')
    if isinstance(_, chord.Chord):
        for note in _.notes:
            print(_, _.getInstrument(), 'Note in Chord')
generated_music.write('midi', fp='generated_music.mid')
