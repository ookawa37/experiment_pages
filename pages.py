import streamlit as st
import pretty_midi
import io
import convert as cv
import midi_utils as mu
import tempfile
from PIL import Image


class TempoChangerPage():
    def __init__(self, title) -> None:
        self.title = title
        st.title(title)

        if 'initialized' not in st.session_state:
            st.session_state.midi_file = None
            st.session_state.midi_data = None
            st.session_state.uploaded_file = None
            st.session_state.user_tempo = 100
            st.session_state.default_tempo = None
            st.session_state.generated_audio = None
            st.session_state.audio_playback = None
            st.session_state.start_time = 0.0
            st.session_state.end_time = 8.0
            st.session_state.full_audio = None
            st.session_state.temp_dir = tempfile.TemporaryDirectory()
            st.session_state["temp_files"] = []
            st.session_state.note_numbers = []
            st.session_state.generated_score = None
            st.session_state.initialized = True
            st.session_state.step = False
            st.session_state.audio = False


    def upload_and_convert_file(self):
        uploaded_file = st.file_uploader("MIDIファイルをアップロードしてください", type=["mid"])
        if uploaded_file:
            st.session_state.midi_file = io.BytesIO(uploaded_file.read())
            st.session_state.midi_file.seek(0)
            
            # アップロードしたMIDIファイルを全体音源としてWAVに変換
            st.session_state.midi_data = pretty_midi.PrettyMIDI(st.session_state.midi_file)
            st.session_state.full_audio = cv.convert_midi_to_wav(st.session_state.midi_data)
            st.session_state.step = True


    def upload_image(self):
        # 画像ファイルのアップロード
        st.session_state.uploaded_file = st.file_uploader("画像ファイルをアップロードしてください", type=["png", "jpg", "jpeg"])


    def display_image(self):
        # アップロードされた画像をPillowで開く
        image = Image.open(st.session_state.uploaded_file)
        
        # 画像を表示
        st.image(image, use_container_width=True)



    def play_full_audio(self):
        if st.session_state.full_audio:
            st.write("アップロードしたファイルの音源:")
            audio_file = open(st.session_state.full_audio, 'rb')
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")


    def select_range_and_tempo(self):
        user_tempo = st.number_input("テンポを指定してください", min_value=20, max_value=300, value=st.session_state.user_tempo)
        st.session_state.user_tempo = user_tempo

        if st.session_state.midi_file:
            st.session_state.midi_file.seek(0)
            midi_data = pretty_midi.PrettyMIDI(st.session_state.midi_file)
            midi_duration = midi_data.get_end_time()

            # スライダーで範囲指定
            start_time, end_time = st.slider("練習したい範囲を選択してください", 0.0, midi_duration, (0.0, min(8.0, midi_duration)))
            st.session_state.start_time = start_time
            st.session_state.end_time = end_time
            st.write(f"選択された範囲: {start_time:.2f}秒 から {end_time:.2f}秒")


    def adjust_select_range(self):
        self.select_range_and_tempo()
        closest_beats = mu.get_closeest_downbeats(st.session_state.midi_data, st.session_state.start_time, st.session_state.end_time)
        st.session_state.start_time, st.session_state.end_time = closest_beats[:2]
        print(f"start_time{st.session_state.start_time}, end_time{st.session_state.end_time}")

    
    def convert_and_store_audio(self, adjusted_midi):
        if adjusted_midi:
            wav_path = cv.convert_midi_to_wav(adjusted_midi)
            st.session_state.generated_audio = wav_path


    def display_generated_audio(self):
        if st.session_state.generated_audio:
            st.write("指定された範囲の音源:")
            audio_file = open(st.session_state.generated_audio, 'rb')
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")


    def run_pages(self):
        self.upload_and_convert_file()
        self.upload_image()
        if st.session_state.step:
            self.play_full_audio()
            self.adjust_select_range()

        if st.session_state.midi_file is not None:
            if st.button("指定された範囲の音源を生成"):
                st.session_state.default_tempo, tempo_times_one = mu.get_tempo(st.session_state.start_time, st.session_state.end_time, st.session_state.midi_data)
                print(f"default_tempo{st.session_state.default_tempo}")
                count_in_midi = mu.run_midi_trimmed(st.session_state.midi_file, st.session_state.start_time, st.session_state.end_time, st.session_state.default_tempo, tempo_times_one)
                adjusted_midi = cv.change_tempo(count_in_midi, st.session_state.user_tempo, st.session_state.default_tempo)
                self.convert_and_store_audio(adjusted_midi)
                self.display_generated_audio()
                st.session_state.audio = True

            elif st.session_state.generated_audio:
                self.display_generated_audio()

        if st.session_state.uploaded_file is not None:
            self.display_image()
