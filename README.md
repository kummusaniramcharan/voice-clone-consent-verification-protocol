# VoiceClone: Is this voice real or AI?

[![Zero-Upload Privacy](https://img.shields.io/badge/Privacy-100%25%20In--Browser%20(Zero%20Upload)-00f5d4?style=flat-square)](#privacy-guarantee)
[![Runtime](https://img.shields.io/badge/Runtime-Vanilla%20ES%20Modules%20%2B%20WebAudio%20DSP-4cc9ff?style=flat-square)](#technology-stack)
[![Netlify Deploy](https://img.shields.io/badge/Deploy-Netlify%20Drag--and--Drop-9b5cff?style=flat-square)](#deploying-to-netlify)

A client-side, zero-upload audio forensics application designed to detect AI voice-cloning fraud (such as "virtual kidnapping", emergency distress calls, and CEO wire fraud). VoiceClone inspects speech recordings in real time directly within your browser, extracting 24 acoustic and voice cues and evaluating them with an on-device trained regularized model.

---

## Table of Contents
1. [Core Features](#core-features)
2. [How It Works](#how-it-works)
3. [Privacy Guarantee (Zero Uploads)](#privacy-guarantee-zero-uploads)
4. [How to Train Your Own Detector](#how-to-train-your-own-detector)
5. [Deploying to Netlify](#deploying-to-netlify)
6. [Acceptance Verification & Test Plan](#acceptance-verification--test-plan)
7. [File Structure](#file-structure)
8. [License & Disclaimers](#license--disclaimers)

---

## Core Features

- **Reliable Universal Audio Ingestion**:
  - Accepts WAV, MP3, M4A, OGG, Opus, WebM, AAC, and FLAC (up to 20 MB, first 60 seconds analyzed).
  - High-fidelity microphone capture with operating system DSP bypassed (`echoCancellation: false`, `noiseSuppression: false`, `autoGainControl: false`) to preserve subtle synthetic artifacts.
  - Multi-stage audio quality gating: warns or refuses audio shorter than 3s, clipped (>5%), excessive silence (>70%), or low loudness (< -45 dBFS).
  - Waveform amplitude envelope preview for every loaded clip.

- **24-Feature DSP Acoustic Extraction (`js/features.js`)**:
  - **Recording cues**: `noise_floor_dbfs`, `dyn_range_db`, `digital_silence_pct`, `bandwidth_hz`.
  - **Spectral cues**: `spec_flatness`, `spec_centroid_hz`, `rolloff95_hz`, `hf_4_8k_ratio`, `spec_flux_cv`, `mfcc_temporal_std` (26 mel filters), `mfcc_delta_mean`.
  - **Voice cues**: Normalized autocorrelation pitch (70–400 Hz), `f0_mean_hz`, `f0_std_semitones`, `f0_range_semitones`, `voiced_pct`, `f0_flat_step_pct` (quantized synthetic monotone steps), `hnr_mean_db`, `hnr_std_db`, `amp_frame_shimmer_pct`.
  - **Timing cues**: `pause_per_10s`, `pause_mean_s`, `pause_cv`, `mod_peak_hz`, `mod_peak_ratio`.

- **In-Browser Training Lab (`train.html`)**:
  - Drag-and-drop batch dataset ingestion stored locally in IndexedDB.
  - Optional 4-second windowing (50% overlap).
  - Synthetic data augmentations (gain &plusmn;6 dB, pink noise 10–30 dB SNR, random low-pass 4–8 kHz, room reverb RT60 0.1–0.5s, 8–12 bit quantization) to prevent microphone bias.
  - Grouped Cross-Validation by source: guarantees speakers and microphones never leak between training and testing folds. Red banner alerts if fewer than 3 sources per class.
  - Leave-one-AI-engine-out generalization table.
  - Interactive decision threshold slider and top 10 signed weights bar chart.

- **Calibrated Detector Output (`index.html`)**:
  - Probabilistic classification: $P(\text{AI}) = \sigma(w \cdot z + b)$.
  - Calibrated verdict bands: &ge; 0.65 (*Likely AI-generated*), &le; 0.35 (*Likely human*), otherwise *Inconclusive*.
  - Plain-English explanations of top 3 contributing features comparing clip measurements to training baselines.
  - Out-of-Distribution (OOD) detector flagging recordings that deviate from training distributions ($|z| > 4$).
  - Refuses to give a verdict if no trained model exists.

---

## How It Works

```
[ Audio File / Mic ]
       │
       ▼
[ Web Audio API ] ────> Mix to mono & resample to 16 kHz (OfflineAudioContext)
       │
       ▼
[ Quality Gate ] ─────> Checks duration, clipping, silence & RMS
       │
       ▼
[ js/features.js ] ───> Extracts 24 exact physical DSP features
       │
       ▼
[ js/model.js ] ──────> Standardizes features: z = (x - mean) / std
       │                Computes logit: s = sum(w * z) + bias
       │                Sigmoid probability: P(AI) = 1 / (1 + exp(-s))
       ▼
[ Transparent UI ] ───> Gauge, Top 3 plain-English reasons, OOD warnings, Full Accordion
```

---

## Privacy Guarantee (Zero Uploads)

VoiceClone runs **100% on your device**:
- No audio data, voice recording, or biometric feature vector is ever transmitted across the network.
- The web application only makes HTTP GET requests for static assets (`.html`, `.css`, `.js`, `samples/`) and `./model.json`.
- Open your browser's Developer Tools (`F12`), switch to the **Network** tab, and record or analyze audio—you will verify that **0 bytes of audio leave your device**.

---

## How to Train Your Own Detector

1. Open **Training Lab** (`train.html`) in your browser.
2. Drag and drop audio recordings into the dataset drop area. Files named with prefix `human_` or `ai_` are automatically labeled.
3. Verify that every clip has a **Label** (Real Human or AI Synthetic) and a **Source** (e.g. *ElevenLabs*, *eSpeak*, *Ravi iPhone*, *Pixel Mic*). Training is blocked if any clip lacks a label or source.
4. Select your preferred feature preset (*All 24 Features*, *Voice & Timing Only*, or *Recording Cues Only*).
5. Ensure data augmentations are enabled to prevent the model from memorizing microphone quirks.
6. Click **Fit L2-Regularized Logistic Model**.
7. Review the **Validation Report**:
   - Cross-validated accuracy, balanced accuracy, and ROC AUC.
   - Confusion matrix and Per-Source Accuracy breakdown.
   - Leave-One-AI-Engine-Out table.
   - Top 10 signed feature weights chart.
8. Click **Use This Model Now (localStorage)** to activate it immediately in the Detector, or click **Download model.json** to save the model file.

---

## Deploying to Netlify

VoiceClone is a static site with no backend server, build step, or API keys.

### Drag-and-Drop Deployment (Recommended)
1. In your file explorer, select the VoiceClone project directory containing `index.html`, `train.html`, `css/`, `js/`, and `samples/`.
2. Go to [Netlify Drop](https://app.netlify.com/drop).
3. Drag and drop the project folder onto the Netlify upload area.
4. Netlify will deploy your site in seconds and provide a public HTTPS URL (e.g., `https://your-site.netlify.app`).

### Including a Pre-Trained `model.json`
If you trained a custom detector in the Training Lab:
1. Click **Download model.json** in the Training Lab.
2. Place the downloaded `model.json` in the root folder alongside `index.html`.
3. Drag the folder onto Netlify Drop. The site will automatically load this pre-trained model for all visitors on first visit!

---

## Acceptance Verification & Test Plan

| Test Criterion | Verification Method | Status |
| :--- | :--- | :---: |
| **1. Audio Format Ingestion** | Load MP3, WAV, M4A, OGG/Opus, and WebM files. Each renders a waveform preview, resamples to 16 kHz, and extracts the 24-feature vector without console errors. | **PASS** |
| **2. Deterministic Inference** | Train a 20-clip dataset, export `model.json`, and reload it. Exact probabilities match $\pm 0.0001\%$. | **PASS** |
| **3. Untrained Model Guard** | With an untrained placeholder `model.json` and empty `localStorage`, the Detector refuses to provide a verdict and directs the user to the Training Lab. | **PASS** |
| **4. Zero-Upload Network Audit** | DevTools Network inspection confirms no audio requests or telemetry leave the page. | **PASS** |
| **5. Responsive Design** | Mobile viewports down to 375 px width display stacked capture columns, responsive canvas graphs, and full menu access. | **PASS** |

---

## File Structure

```text
VoiceClone/
├── index.html              # Main Detector & Test Lab benchmark
├── train.html              # Training Lab (Dataset ingestion, augmentation, grouped CV)
├── how-it-works.html       # Transparent architecture & acoustic explanation
├── scam-safety.html        # Emergency checklists & searchable cybercrime directory
├── about.html              # Honest limitations, 95% cap rationale & credits
├── selftest.html           # Real-time hardware & browser diagnostic suite
├── model.json              # Untrained placeholder or exported model
├── netlify.toml            # Netlify headers & security policy
├── _redirects              # Static SPA routing rules
├── css/
│   └── styles.css          # Dark navy theme with cyan and purple neon accents
├── js/
│   ├── features.js         # Pure DSP feature extraction (24 physical features)
│   ├── model.js            # Model schema, inference, and plain-English explainers
│   ├── worker.js           # Web Worker for decoding, augmentations & gradient descent
│   ├── train.js            # Training Lab UI & IndexedDB dataset persistence
│   └── ui.js               # Audio pipeline, level meter, canvas visualizers & modals
├── data/
│   └── helplines.json      # International cybercrime contacts directory
└── samples/
    ├── sample_human.mp3    # Genuine human voice sample for 1-click demo
    ├── sample_ai.mp3       # AI synthetic voice sample for 1-click demo
    ├── ai/                 # 12 eSpeak synthetic voice samples
    └── human/              # Genuine human voice recordings
```

---

## License & Disclaimers

VoiceClone is released under the **MIT License**.

**Legal Disclaimer:** VoiceClone is a client-side probabilistic detection and educational screening tool. Synthetic speech generation is an adversarial, rapidly moving domain. Never rely exclusively on automated acoustic analysis to make financial, legal, or emergency decisions. Always verify sensitive requests through secondary channels (such as calling back on a known personal number or using a family safe-word).
