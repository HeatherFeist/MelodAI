# Voice agent integration plan

## 1. Use DiffSinger as the singing engine
- Keep this repository as the synthesis backend.
- Expose a simple API or CLI entry point that accepts:
  - text/lyrics
  - voice bank path
  - optional speaker name
  - output path

## 2. Replace or swap voices
- To use your own voice, train or fine-tune a DiffSinger-compatible voice bank.
- In practice this means:
  - preparing a dataset of your singing audio and labels
  - training a new voice bank in the DiffSinger/OpenUtau ecosystem
  - pointing the backend to that trained model directory

## 3. Connect to MelodAI-style app flow
Recommended flow:
1. User enters a prompt or lyrics.
2. App sends text + style + voice selection to the backend.
3. Backend generates vocals with DiffSinger.
4. Backend mixes vocals with instrumental track and returns audio.

## 4. Suggested first milestone
Build a minimal API endpoint that can:
- accept a prompt and voice bank path
- generate a WAV file
- return the file location or URL

## 5. Suggested later milestones
- add style controls (tempo, pitch, emotion)
- add voice swapping for multiple singers
- add a training pipeline for custom voice banks
