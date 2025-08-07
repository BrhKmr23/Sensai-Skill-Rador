import av
import wave
import os
import numpy as np
import speech_recognition as sr

def webm_to_wav_pyav(input_path, output_path):
    container = av.open(input_path)
    audio_stream = next(s for s in container.streams if s.type == 'audio')
    resampler = av.audio.resampler.AudioResampler(format='s16', layout='mono', rate=16000)
    samples = b''
    for packet in container.demux(audio_stream):
        for frame in packet.decode():
            resampled = resampler.resample(frame)
            if isinstance(resampled, list):
                for f in resampled:
                    samples += bytes(f.planes[0])
            else:
                samples += bytes(resampled.planes[0])
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(16000)
        wf.writeframes(samples)
    print(f"Converted {input_path} to {output_path}")

def transcribe_with_google(wav_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        print(f"Transcript for {wav_path}: {text}")
        return text
    except Exception as e:
        print(f"Recognition error for {wav_path}: {e}")
        return f"[Recognition error: {e}]"

def batch_convert_and_transcribe(candidate_id, answers_dir="answers"):
    folder = os.path.join(answers_dir, candidate_id)
    if not os.path.isdir(folder):
        print(f"No folder found for candidate: {candidate_id}")
        return
    for fname in os.listdir(folder):
        if fname.endswith(".webm"):
            webm_path = os.path.join(folder, fname)
            wav_path = os.path.splitext(webm_path)[0] + ".wav"
            txt_path = os.path.splitext(webm_path)[0] + ".txt"
            webm_to_wav_pyav(webm_path, wav_path)
            print(f"Transcribing {wav_path} with Google SpeechRecognition...")
            transcript = transcribe_with_google(wav_path)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            print(f"Transcript saved to {txt_path}")

# --- Google SpeechRecognition test for a single wav file ---
wav_path = r"answers/42f36fdb-910a-4981-8ee6-c71c5bb08775/1.wav"
txt_path = r"answers/42f36fdb-910a-4981-8ee6-c71c5bb08775/1.txt"
if os.path.exists(wav_path):
    print(f"Transcribing {wav_path} with Google SpeechRecognition...")
    transcript = transcribe_with_google(wav_path)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    print(f"Transcript saved to {txt_path}")
else:
    print(f"File not found: {wav_path}")

# Example usage:
candidate_id = "241c4008-c624-4b44-907b-a4a79426a486"
batch_convert_and_transcribe(candidate_id)