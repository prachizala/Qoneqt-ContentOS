# Changes Log - Qoneqt-ContentOS

## Overview
This log documents repository hygiene updates performed on branch `review-fixes`.

## Changes Made
1. **Untracked Binary Audio**:
   - Untracked `test_audio.mp3` from Git tracking using `git rm --cached test_audio.mp3`.
   - Updated `.gitignore` to ignore media binaries: `*.mp3`, `*.mp4`, `*.wav`.
2. **Documentation on Media Assets**:
   - Updated `README.md` with instructions on how to supply local test audio or generate test audio using FFmpeg (`ffmpeg -f lavfi -i "sine=frequency=1000:duration=5" -c:a libmp3lame test_audio.mp3`).
3. **Presentation Asset Review (`PPT.html`)**:
   - Verified `PPT.html`. It is a self-contained HTML presentation deck created for the Hackbriven hackathon evaluation committee.
   - Retained at root because it is directly linked from `README.md`, `CONTRIBUTIONS.md`, and `CHANGELOG_EXPLAINED.md`.
4. **Build & Cache Exclusions**:
   - Confirmed `.gitignore` already comprehensively excludes `.next/`, `node_modules/`, `__pycache__/`, `storage/temp/`, and `storage/exports/`.
5. **License Verification**:
   - Confirmed `LICENSE` is present, valid MIT License authored to Prachi Zala (2026).
6. **Test Verification**:
   - Ran `python -m pytest tests/`: 31 tests passed. 10 video engine / TTS tests failed with `FileNotFoundError` due to absence of local system `ffmpeg` binary on the host environment.

## Manual Steps / History Cleanup (Optional)
To completely purge `test_audio.mp3` from past Git commit history across all branches:
```bash
# Using git filter-repo (recommended tool for history purging)
pip install git-filter-repo
git filter-repo --path test_audio.mp3 --invert-paths
```
*Note: Rewriting git history is destructive. Ensure backups are made before running history rewrites.*
