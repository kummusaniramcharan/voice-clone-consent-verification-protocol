import onnxruntime as ort
import numpy as np
from pathlib import Path
import imageio_ffmpeg
import subprocess

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
model_path = "c:/Users/ramch/OneDrive/Desktop/Hallucination_Detection_App/models/deepfake-audio-wav2vec2-ONNX/onnx/model_q4.onnx"
session = ort.InferenceSession(model_path)

def load_audio(path):
    cmd = [ffmpeg_exe, "-y", "-i", str(path), "-ar", "16000", "-ac", "1", "-f", "wav", "-"]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)
    samples = np.frombuffer(proc.stdout[44:], dtype=np.int16).astype(np.float32) / 32768.0
    return samples

def run_pure_inference(samples, name=""):
    target_rate = 16000
    win_len = 4 * target_rate
    hop_len = 3 * target_rate
    
    # Preprocessing: drop first/last 0.2s (3200 samples)
    if len(samples) > 3200 * 2 + 8000:
        samples = samples[3200:-3200]
        
    windows_data = []
    
    for off in range(0, max(1, len(samples) - 16000 + 1), hop_len):
        raw = samples[off:off + win_len]
        if len(raw) < 1600:
            continue
        slice4s = np.zeros(win_len, dtype=np.float32)
        slice4s[:len(raw)] = raw
        
        # Zero-mean unit-variance
        mean = np.mean(slice4s)
        std = np.std(slice4s) + 1e-7
        norm = (slice4s - mean) / std
        
        inp = norm.reshape(1, -1)
        outputs = session.run(["logits"], {"input_values": inp})
        logits = outputs[0][0]
        
        # Softmax: id2label: {0: 'real', 1: 'fake'}
        exp = np.exp(logits - np.max(logits))
        softmax = exp / np.sum(exp)
        
        windows_data.append({
            'logits': [float(logits[0]), float(logits[1])],
            'softmax': [float(softmax[0]), float(softmax[1])],
            'prob_ai': float(softmax[1])
        })
        
    if not windows_data:
        return None
        
    median_ai = np.median([w['prob_ai'] for w in windows_data])
    return {
        'name': name,
        'windows': windows_data,
        'median_prob_ai': float(median_ai),
        'median_pct': round(float(median_ai) * 100)
    }

# Synthetic test signals (10s each at 16kHz)
sr = 16000
dur = 10
# 1. Silence
silence = np.zeros(sr * dur, dtype=np.float32)
# 2. White noise
np.random.seed(42)
white_noise = (np.random.uniform(-0.1, 0.1, sr * dur)).astype(np.float32)
# 3. 440 Hz tone
t = np.linspace(0, dur, sr * dur, endpoint=False)
sine_440 = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

print("=== SYNTHETIC CONTROL SIGNALS ===")
for sig, name in [(silence, "10s Silence (all zeros)"), 
                  (white_noise, "10s White Noise (uniform [-0.1, 0.1])"), 
                  (sine_440, "10s 440 Hz Sine Tone (amp 0.5)")]:
    res = run_pure_inference(sig, name)
    w_probs = [round(w['prob_ai'], 3) for w in res['windows']]
    l0 = [round(w['logits'][0], 2) for w in res['windows']]
    l1 = [round(w['logits'][1], 2) for w in res['windows']]
    print(f"\n{name}:")
    print(f"  Windows count: {len(res['windows'])}")
    print(f"  Logits [real, fake]: {list(zip(l0, l1))}")
    print(f"  P(AI) per window: {w_probs}")
    print(f"  Final Median AI %: {res['median_pct']}% (P(AI)={res['median_prob_ai']:.4f})")
