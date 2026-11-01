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

def run_clip(samples):
    target_rate = 16000
    win_len = 4 * target_rate
    hop_len = 3 * target_rate
    
    # Preprocessing: drop first/last 0.2s (3200 samples)
    if len(samples) > 3200 * 2 + 8000:
        samples = samples[3200:-3200]
        
    windows = []
    
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
        
        exp = np.exp(logits - np.max(logits))
        softmax = exp / np.sum(exp)
        
        windows.append({
            'logits': [round(float(logits[0]), 2), round(float(logits[1]), 2)],
            'softmax': [round(float(softmax[0]), 3), round(float(softmax[1]), 3)],
            'p_ai': float(softmax[1])
        })
        
    p_ais = [w['p_ai'] for w in windows]
    med = float(np.median(p_ais)) if p_ais else 0.5
    return {
        'windows': windows,
        'median_p_ai': med,
        'final_pct': round(med * 100)
    }

test_dir = Path("c:/Users/ramch/OneDrive/Desktop/Hallucination_Detection_App/test-samples")

print("=== RAW MODEL DIAGNOSTIC (NO HEURISTICS, Q4 ONNX) ===")
print("\nHUMAN SAMPLES:")
for p in sorted((test_dir / "human").glob("*.*")):
    s = load_audio(p)
    res = run_clip(s)
    probs = [round(w['p_ai'] * 100) for w in res['windows']]
    l0 = [w['logits'][0] for w in res['windows']]
    l1 = [w['logits'][1] for w in res['windows']]
    print(f"{p.name:36} => Final: {res['final_pct']:2d}% AI | Windows: {probs} | Logits: {list(zip(l0, l1))}")

print("\nAI SAMPLES:")
for p in sorted((test_dir / "ai").glob("*.*")):
    s = load_audio(p)
    res = run_clip(s)
    probs = [round(w['p_ai'] * 100) for w in res['windows']]
    l0 = [w['logits'][0] for w in res['windows']]
    l1 = [w['logits'][1] for w in res['windows']]
    print(f"{p.name:36} => Final: {res['final_pct']:2d}% AI | Windows: {probs} | Logits: {list(zip(l0, l1))}")
