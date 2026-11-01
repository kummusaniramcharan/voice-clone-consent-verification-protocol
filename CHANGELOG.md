# VoiceClone — Changelog & Forensic Audit Log

All notable changes, bug fixes, root cause analyses, and architectural enhancements applied to the VoiceClone repository for the Hackathon release.

---

## 1. Model Loading & Neural Pipeline

### Bug 1.1: Missing Config & Model 404 in Hugging Face Transformers.js Pipeline
- **File:** [`js/config.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/config.js), [`js/detector.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/detector.js)
- **Root Cause:** `CONFIG.MODEL_ID` was set to `'ayush2635/Dhwani-Multilingual-Deepfake-Audio-Detection-Model'`. Direct inspection of Hugging Face repository revealed it contained only a root PyTorch `best_model.onnx` file without `config.json`, `preprocessor_config.json`, or the directory structure (`onnx/model_quantized.onnx`) required by Transformers.js `@huggingface/transformers`. Calling `pipeline('audio-classification', ...)` threw an unhandled 404 exception on every browser load, silently failing the neural detector and dropping to heuristic fallback.
- **Fix:** Switched model to `'ai8shiro/deepfake-audio-wav2vec2-ONNX'` with `dtype: 'q4'` (~85.7 MB quantized model). Confirmed repository structure possesses valid `config.json`, `preprocessor_config.json`, and `onnx/model_q4.onnx`. Verified label mapping (`id2label: {0: 'real', 1: 'fake'}`).

### Bug 1.2: WASM Threading Crash from Unchecked `SharedArrayBuffer`
- **File:** [`js/detector.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/detector.js)
- **Root Cause:** `env.backends.onnx.wasm.numThreads = Math.min(4, navigator.hardwareConcurrency)` attempted multi-threaded WASM execution unconditionally. In standard Web hosting without Cross-Origin-Opener-Policy (`COOP`) and Cross-Origin-Embedder-Policy (`COEP`) headers, `window.crossOriginIsolated` is `false` and `SharedArrayBuffer` is disabled in modern browsers. This caused WebAssembly worker instantiation to throw an immediate runtime crash.
- **Fix:** Added isolation check:
  ```javascript
  const canUseThreads = typeof SharedArrayBuffer !== 'undefined' && window.crossOriginIsolated;
  env.backends.onnx.wasm.numThreads = canUseThreads ? Math.min(4, navigator.hardwareConcurrency || 2) : 1;
  ```

### Bug 1.3: Unhandled Promise Rejections Hanging the UI
- **File:** [`js/ui.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/ui.js)
- **Root Cause:** UI listeners awaited `initModel()` inside async button handlers without comprehensive error boundaries. If offline or if the user lost internet during CDN fetch, the analyzer button remained permanently disabled with `"Analyzing..."` spinner running forever.
- **Fix:** Added robust try/catch blocks, visual status pill indicators (`#neural-model-badge`), and a graceful fallback: `"Model unavailable. No reliable verdict."` instead of fabricating fake percentages.

---

## 2. Audio Processing & Quality Gates

### Bug 2.1: Broken Stereo-to-Mono Downmixing with `createChannelMerger(1)`
- **File:** [`js/audio-utils.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/audio-utils.js)
- **Root Cause:** `resampleTo16kMono()` connected the audio buffer source to `audioCtx.createChannelMerger(1)`. A channel merger node combines multiple monophonic inputs into a multi-channel stream, but when passed `1` channel it simply passed channel 0 and completely dropped channel 1 (right stereo channel), discarding half the audio data for stereo inputs.
- **Fix:** Implemented an exact mathematical downmix by averaging all source channels into a 32-bit float mono buffer:
  ```javascript
  const monoData = new Float32Array(length);
  for (let ch = 0; ch < numChannels; ch++) {
    const chData = audioBuffer.getChannelData(ch);
    for (let i = 0; i < length; i++) {
      monoData[i] += chData[i] / numChannels;
    }
  }
  ```
  Then passed this single-channel buffer into `OfflineAudioContext(1, targetLength, 16000)`.

### Bug 2.2: Detached Audio ArrayBuffer Crash in `decodeAudioData`
- **File:** [`js/audio-utils.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/audio-utils.js)
- **Root Cause:** Web Audio's `AudioContext.decodeAudioData(arrayBuffer)` neuters (detaches) the underlying `ArrayBuffer` in standard browsers. When users analyzed a file and subsequently played or re-analyzed it, accessing the same buffer caused `TypeError: Cannot perform operation on a detached ArrayBuffer`.
- **Fix:** Always pass a `.slice(0)` copy of the ArrayBuffer to `decodeAudioData`:
  ```javascript
  const bufferCopy = arrayBuffer.slice(0);
  const audioBuffer = await ctx.decodeAudioData(bufferCopy);
  ```

### Bug 2.3: Overly Aggressive Inconclusive Lockout Gates
- **File:** [`js/audio-utils.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/audio-utils.js), [`js/detector.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/detector.js)
- **Root Cause:** Any audio under 3 seconds, audio with silence > 48%, or clipping > 0.8% set `shouldForceInconclusive = true`, completely discarding the neural model prediction and preventing valid speech from being assessed.
- **Fix:** Demoted quality check failures to advisory UI warnings (e.g. `"Audio is relatively short (<3s) — confidence may be reduced"`). The model output is preserved, and inconclusive verdicts are only reserved for extreme non-speech (<0.5s) or indeterminate probability spreads (35%–65%).

---

## 3. UI, File Upload & Media Player

### Bug 3.1: Non-Clickable "Browse Files" Drop Zone
- **File:** [`js/ui.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/ui.js), [`index.html`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/index.html)
- **Root Cause:** The drop zone `#detect-drop-zone` and the internal button `.btn-upload-browse` lacked click event listeners triggering the hidden `#detect-file-input`, and the input was not wrapped in an enclosing `<label for>`. Clicking the upload box did nothing in standard browsers.
- **Fix:** Bound explicit `click` and keyboard (`Enter` / `Space`) listeners on `#detect-drop-zone` and `.btn-upload-browse` to programmatically trigger `fileInput.click()`. Added window-level `dragover` / `drop` event interception with `e.preventDefault()` to stop the browser from accidentally opening dropped audio files in full-screen tab view.

### Bug 3.2: Frankenstein WAV Container Bug Breaking Audio Playback
- **File:** [`js/ui.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/ui.js)
- **Root Cause:** In the preview setup, `ui.js` executed `new Blob([file], { type: 'audio/wav' })` on raw uploaded MP3, M4A, or OGG files. Passing compressed MP3 bitstreams disguised as `audio/wav` confused the browser's native `<audio>` decoder, rendering previews unplayable on Chrome and Safari.
- **Fix:** Preserved original file MIME types on upload, and encoded resampled 16 kHz mono PCM into authentic 16-bit PCM WAV chunks using `encodePcmToWav()` whenever generating playback blobs for microphone captures.

### Bug 3.3: Missing 1-Click Demo Buttons for Hackathon Presentation
- **File:** [`index.html`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/index.html), [`js/ui.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/ui.js)
- **Root Cause:** Demonstrating voice detection at a judging booth previously required judges or presenters to manually find, download, and drag external files.
- **Fix:** Embedded instant 1-click sample buttons:
  - `"Try Sample Human Voice"` (fetches `data/sample-human.wav`)
  - `"Try Sample AI Voice"` (fetches `data/sample-ai.mp3`)
  Users can evaluate both ground truths in under 5 seconds with zero file friction.

---

## 4. Microphone Capture & Safari Compatibility

### Bug 4.1: AudioWorklet Initialization Failures on Safari & Mobile
- **File:** [`js/recorder.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/recorder.js)
- **Root Cause:** Safari and iOS WebKit have strict autoplay and audio context state policies that often reject AudioWorklet module registrations without an active user gesture chain or fail silently in insecure contexts.
- **Fix:** Implemented an automatic `MediaRecorder` fallback with `audio/webm;codecs=opus` and `audio/mp4` fallbacks. If `AudioWorklet` fails or is rejected, the recorder transparently falls back to `MediaRecorder` without dropping the user's mic session.

### Bug 4.2: Unreleased Microphone MediaStream Tracks
- **File:** [`js/recorder.js`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/js/recorder.js)
- **Root Cause:** After stopping recording, mic streams were not iterated and stopped. This left the browser's red recording tab indicator active, causing privacy concerns.
- **Fix:** Added exhaustive cleanup in `stopRecording()`:
  ```javascript
  if (this.stream) {
    this.stream.getTracks().forEach(track => track.stop());
    this.stream = null;
  }
  ```

---

## 5. Test Lab, Diagnostics & Netlify Deployment

### Bug 5.1: SPA Routing 404s on Netlify Reloads
- **File:** [`_redirects`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/_redirects), [`netlify.toml`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/netlify.toml)
- **Root Cause:** Navigating to `/how-it-works`, `/scam-safety`, `/about`, or `/selftest` directly via URL or page refresh resulted in a Netlify 404 page because static files were named `.html`.
- **Fix:** Added clean URL rewrites in both `_redirects` and `netlify.toml`:
  ```text
  /how-it-works    /how-it-works.html   200
  /scam-safety     /scam-safety.html    200
  /about           /about.html          200
  /selftest        /selftest.html       200
  ```

### Bug 5.2: Missing MIME Types for WASM & ONNX Files
- **File:** [`netlify.toml`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/netlify.toml)
- **Root Cause:** Without custom header configuration, static hosting servers often serve `.wasm` as `application/octet-stream`, triggering console warnings and preventing WebAssembly streaming compilation.
- **Fix:** Configured `application/wasm` for `*.wasm` and `model/onnx` for `*.onnx` in `netlify.toml`.

### Bug 5.3: Absence of Live In-Browser Diagnostics
- **File:** [`selftest.html`](file:///c:/Users/K%20KRISHNA%20CHARAN/Downloads/voice%20cloning_v_1.0/selftest.html)
- **Root Cause:** Presenting at a live hackathon with varying venue Wi-Fi / firewall rules creates risk if CDN assets or microphone permissions are blocked.
- **Fix:** Built a dedicated `/selftest` diagnostic dashboard running automated checks for HTTPS context, AudioContext support, WebAssembly SIMD, WebGPU, CDN reachability, model initialization, and synthetic test-vector inference.
