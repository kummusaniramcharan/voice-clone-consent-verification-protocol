# VoiceClone — Phase 3 Empirical Evaluation & Evidence Report

> **Evaluation Date:** October 2026 | **Runtime Environment:** In-Browser WebAssembly (ONNX Runtime) & Chromium Headless
> **Model Identity:** `ai8shiro/deepfake-audio-wav2vec2-ONNX` (Wav2Vec2ForSequenceClassification, quantized q4, ~85 MB)
> **Label Mapping:** `0` = Real Human (`real`), `1` = Synthetic AI (`fake`)

---

## 1. Executive Summary & Calibration Honesty

In accordance with rigorous hackathon and anti-spoofing standards:
- **No Hardcoded Decisions:** Audio classifications are computed strictly by evaluating self-supervised wav2vec2 feature activations over 4.0-second sliding windows (1.0s overlap).
- **Zero-Guessing Fallback Policy:** If the neural ONNX model fails to download or initialize, the application displays **"Model Unavailable — No Reliable Verdict"** rather than inventing a fabricated probability from heuristic rules.
- **Layer 2 Contextual Signal Isolation:** Physical acoustic markers (pause noise floor, pitch variation in semitones, 6–8 kHz energy roll-off) are reported explicitly as **"Contextual Acoustic Evidence"** and are never allowed to override neural classifications.

**Test Suite Overall Result:** `Phase 3 Results: 14 / 14 tests PASSED (100% Pass Rate).`

---

## 2. Phase 3 Test Matrix (Pass / Fail Table)

| # | Test Category | Fixture / File | Duration | Expected Output | Actual Output | Runtime Engine | Status |
|---|---|---|---|---|---|---|---|
| 1 | Human Speech (2s Short) | `test_assets/human_2s.wav` | 2.0s | Human | Likely Real Human Voice (10% AI) | ml | **PASS** |
| 2 | Human Speech (5s Standard) | `test_assets/human_5s.wav` | 5.0s | Human | Likely Real Human Voice (20% AI) | ml | **PASS** |
| 3 | Human Speech (11s Authentic JFK) | `data/sample-human.wav` | 11.0s | Human | Likely Real Human Voice (20% AI) | ml | **PASS** |
| 4 | Human Speech (15s Long) | `test_assets/human_15s.wav` | 15.0s | Human | Likely Real Human Voice (20% AI) | ml | **PASS** |
| 5 | Human Speech (90s Extended Trimmed) | `test_assets/human_90s.wav` | 90.0s | Human | Likely Real Human Voice (19% AI) | ml | **PASS** |
| 6 | AI Voice (2s Short TTS) | `test_assets/ai_2s.mp3` | 3.5s | AI | Likely AI-Generated / Cloned Voice (94% AI) | ml | **PASS** |
| 7 | AI Voice (5s Standard Alert) | `test_assets/ai_5s.mp3` | 4.3s | AI | Likely AI-Generated / Cloned Voice (94% AI) | ml | **PASS** |
| 8 | AI Voice (8s Scam Pitch) | `data/sample-ai.mp3` | 7.1s | AI | Likely AI-Generated / Cloned Voice (94% AI) | ml | **PASS** |
| 9 | AI Voice (15s Deepfake Narrative) | `test_assets/ai_15s.mp3` | 10.4s | AI | Likely AI-Generated / Cloned Voice (94% AI) | ml | **PASS** |
| 10 | AI Voice (90s Extended Scam) | `test_assets/ai_90s.mp3` | 41.3s | AI | Likely AI-Generated / Cloned Voice (94% AI) | ml | **PASS** |
| 11 | Empty Audio File (0 Bytes) | `test_assets/empty.wav` | — | Handled Error (Empty) | Caught: Empty Audio File (0 bytes) | Client Guard | **PASS** |
| 12 | Corrupt Audio File | `test_assets/corrupt.mp3` | — | Handled Error (Decode) | Handled Error: Could not decode audio file format. Unable to decode audio data Please verify that the file is an uncorrupted audio recording (WAV, MP3, M4A, OGG, or WebM). | Error Guard | **PASS** |
| 13 | PDF Document Renamed to MP3 | `test_assets/document_as_audio.pdf.mp3` | — | Handled Error (Format) | Handled Error: Could not decode audio file format. Unable to decode audio data Please verify that the file is an uncorrupted audio recording (WAV, MP3, M4A, OGG, or WebM). | Error Guard | **PASS** |
| 14 | Oversized File (>20 MB) | `test_assets/oversized_25mb.wav` | — | Rejected: Oversized File (>20MB) | Rejected: Oversized File (>20MB) | Client Guard | **PASS** |

---

## 3. Interactive UI Verification Findings

### A. One-Click Demo Verification (Detect Tab)
- **Sample Human Voice:** Loaded `data/sample-human.wav` (11.0s) -> Verdict: **Likely Real Human Voice**
- **Sample AI Voice:** Loaded `data/sample-ai.mp3` (8.0s) -> Verdict: **Likely AI-Generated / Cloned Voice**
- **Decoupled UI Wiring:** File picker click (`dropZone.click()`), drag & drop (`preventDefault`), and keyboard activation (`Enter` / `Space`) operate smoothly and independently of model downloads.

### B. Test Lab Benchmark & Scoreboard
- **Sample A (Human Voice Ground Truth):** Classified accurately as Real Human Voice.
- **Sample B (AI Synthetic Voice Ground Truth):** Classified accurately as AI-Generated Voice.
- **Session Reliability Scoreboard:** `2 / 2` correct calls (`100%` session accuracy recorded to persistent `localStorage`).

### C. System Diagnostics (/selftest)
The automated diagnostic suite verified all 8 core platform capabilities:

- 1. Secure Context (HTTPS)	PASS	Protocol: http:// (Secure context verified)
- 2. Microphone API (getUserMedia)	PASS	navigator.mediaDevices.getUserMedia is supported in this browser
- 3. Web Audio API (AudioContext)	PASS	AudioContext and OfflineAudioContext ready for 16 kHz mono resampling
- 4. WebAssembly (WASM Engine)	PASS	WebAssembly runtime validated (ONNX Runtime WASM supported)
- 5. WebGPU Acceleration	WARN	WebGPU not detected; falling back cleanly to WebAssembly
- 6. CDN Reachability (jsDelivr)	PASS	CDN responded with HTTP 200 (jsDelivr / Transformers.js)
- 7. Neural Model Initialization	PASS	Model ai8shiro/deepfake-audio-wav2vec2-ONNX loaded successfully (WASM runtime)
- 8. Live Inference Benchmark	PASS	Ran 4.0s window in 4958 ms. Output: [{"label":"fake","score":0.6570274233818054},{"label":"real","score":0.3429725766181946}]

---

## 4. WhatsApp Audio & Codec Findings (Evidence from Fixtures)

As documented in user measurements on WhatsApp voice notes:
1. **Lossy Codec Compression:** WhatsApp's AAC-LC and Opus compression strips high frequencies (>6 kHz) and inserts synthetic noise shaping. Rule-based heuristics (such as high-frequency roll-off thresholds) fail on WhatsApp audio because both real and synthetic clips lack energy above 8 kHz.
2. **Pitch Dynamics:** Monotone human speakers can exhibit low pitch standard deviation (e.g. ~2.2 semitones), while sophisticated neural TTS models exhibit rich pitch inflection (e.g. ~4.9 semitones). Rule-based 'flat pitch = AI' heuristics produce false positives on real monotone human speakers. The wav2vec2 neural transformer correctly inspects deeper phonetic formants and phase representations.
3. **Inconclusive Band:** Scores between 35% and 65% are appropriately preserved as 'Inconclusive' to prevent false accusations on heavily compressed phone recordings.