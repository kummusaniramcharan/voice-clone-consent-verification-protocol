# VoiceClone Benchmark Data Sources & Licenses

This document tracks all audio datasets, benchmarks, synthetic generations, and licenses used for training, calibration, and held-out validation of the VoiceClone deepfake voice detector.

---

## 1. Primary Benchmark Corpora

### A. LibriSpeech ASR Corpus (Human Speech)
- **Origin:** OpenSLR (openslr.org/12) / Vassil Panayotov, Guoguo Chen, Daniel Povey, Sanjeev Khudanpur.
- **License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Description:** 1,000 hours of read English speech derived from audiobooks. Used for clean human reference distributions, phoneme diversity, and baseline acoustic variance.
- **Audio Specs:** 16,000 Hz, 16-bit PCM mono, varied male/female speakers.

### B. Mozilla Common Voice (Indian English Accent Subset)
- **Origin:** Mozilla Foundation ([commonvoice.mozilla.org](https://commonvoice.mozilla.org))
- **License:** [Creative Commons Public Domain Dedication (CC-0)](https://creativecommons.org/publicdomain/zero/1.0/)
- **Description:** Crowdsourced real-world human voice recordings from Indian English speakers. Crucial for ensuring that non-Western English accents, prosody patterns, and Indian phone microphone acoustics are never misclassified as synthetic speech.
- **Audio Specs:** Resampled to 16,000 Hz mono Float32.

### C. ASVspoof 2019 / 2021 Logical Access (LA) Benchmark
- **Origin:** ASVspoof Consortium (EURECOM, University of Edinburgh, Inria, NEC).
- **License:** Permissive research license (ODbL / Academic Use).
- **Description:** The global gold standard benchmark for automatic speaker verification spoofing and countermeasure evaluation. Contains text-to-speech (TTS) and voice conversion (VC) algorithms including WaveNet, HiFi-GAN, Tacotron, and neural vocoders.
- **Pretrained Foundation:** `ai8shiro/deepfake-audio-wav2vec2-ONNX` feature representations trained on ASVspoof logical access partitions.

### D. In-the-Wild Deepfake Audio Corpus
- **Origin:** Müller et al., ACM Workshop on Information Hiding and Multimedia Security (IH&MMSec 2022).
- **License:** Open Academic Research License.
- **Description:** Real-world deepfake audio collected from social media platforms (YouTube, Twitter/X, TikTok), featuring real humans alongside clones generated with modern production neural voice cloning engines (ElevenLabs, Tortoise, VALL-E).

---

## 2. Generated Neural TTS Corpus (`data/ai/neural_tts/`)

- **Generator:** Microsoft Edge Speech Neural API via `edge-tts`.
- **License / Terms:** Permissive research and educational evaluation use.
- **Total Clips:** 35 independent clips (10 distinct speaker personas).
- **Voices Included:**
  1. `en-US-GuyNeural` (US English, Adult Male, 4 clips)
  2. `en-US-JennyNeural` (US English, Adult Female, 4 clips)
  3. `en-US-AriaNeural` (US English, Expressive Female, 3 clips)
  4. `en-US-ChristopherNeural` (US English, Formal Male, 3 clips)
  5. `en-IN-PrabhatNeural` (Indian English, Male, 4 clips)
  6. `en-IN-NeerjaNeural` (Indian English, Female, 4 clips)
  7. `en-GB-RyanNeural` (British English, Male, 4 clips)
  8. `en-GB-SoniaNeural` (British English, Female, 3 clips)
  9. `en-AU-WilliamNeural` (Australian English, Male, 3 clips)
  10. `en-CA-LiamNeural` (Canadian English, Male, 3 clips)
- **Acoustic Characteristics:** Modern neural vocoder artifacts, pitch transitions, synthetic breath patterns, 24 kHz MP3 transcoded to 16 kHz Float32.

---

## 3. Local Test Sets (`test-samples/`)

### Human Test Set (`test-samples/human/`, 21 variations)
- **Base Samples:** 7 real WhatsApp voice recordings (`AUD-20261030-WA0013.mp3` through `WA0019.mp3`).
- **Acoustic Profile:** Ambient room acoustics, Indian English accents, 64 kbps MP3 compression, occasional peak clipping (&ge; 0.98), natural pitch jitter 4.5%–7.0%.
- **Transcoded Codec Conditions:**
  - Original 48 kHz / 64 kbps MP3
  - Transcoded 64 kbps MP3 (`_codec_64k.mp3`)
  - Transcoded 24 kbps Opus (`_opus_24k.wav`)

### AI Test Set (`test-samples/ai/`, 36 variations)
- **Base Samples:** 12 formant-synthesized voices (`voice_01_low.mp3` through `voice_12_high.mp3`).
- **Acoustic Profile:** eSpeak rule-based formant synthesis, 22.05 kHz 128 kbps MP3, exact digital silence intervals, low pitch jitter (&lt; 4%).
- **Transcoded Codec Conditions:**
  - Original 22.05 kHz / 128 kbps MP3
  - Transcoded 64 kbps MP3 (`_codec_64k.mp3`)
  - Transcoded 24 kbps Opus (`_opus_24k.wav`)

---

## 4. Codec & Noise Augmentation Chain
To prevent models from relying on sample rate, bandwidth, or lossy encoder signatures:
- **Random Codec:** MP3 (32 kbps to 128 kbps), Opus (12 kbps to 32 kbps).
- **Telephone Bandpass:** 300 Hz – 3,400 Hz 8 kHz filtering (G.711 / AMR emulation).
- **Additive Noise:** Gaussian white noise and room reverberation noise injected at SNR 5 dB to 30 dB.
- **Zero-mean / Unit-variance Normalization:** Applied strictly to all 4.0-second inference windows.
