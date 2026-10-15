# Timeless 35mm Reconstruction

> **Production-Ready Adobe Premiere Pro UXP Plugin Suite & Photochemical Emulation Pipeline**

[![Premiere Pro](https://img.shields.io/badge/Adobe%20Premiere%20Pro-2024%20%2F%202025%20(v24%2B)-00005b?logo=adobepremierepro)](https://helpx.adobe.com/premiere-pro.html)
[![UXP Manifest](https://img.shields.io/badge/UXP-Manifest%20v5-eb1000)](https://developer.adobe.com/premiere-pro/uxp/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv)](https://opencv.org/)
[![Cloudflare Pages](https://img.shields.io/badge/Cloudflare%20Pages-Live%20Demo-F38020?logo=cloudflare)](https://timeless-35mm-reconstruction.pages.dev)

---

## 📽️ Overview

**Timeless 35mm Reconstruction** is a professional extension suite for **Adobe Premiere Pro** that converts digital footage into authentic 35mm motion picture film stock. 

The suite bridges modern asynchronous Adobe UXP APIs with an OpenCV & NumPy photochemical processing engine. It accurately simulates:
1. **MTF Lens Falloff:** Radial edge softness emulating vintage spherical and anamorphic glass.
2. **Red Halation Bleed:** Diffuse red halation bloom caused by light reflecting off the anti-halation rem-jet backing layer.
3. **Logarithmic Grain Modulation:** Silver halide crystal clumping weighted parabolically across midtones and shadows.
4. **Photochemical Chemical Balance:** Spectral color shifts for Daylight (5600K Warm) and Tungsten (3200K Cool) negative stocks.

---

## 📂 Suite Architecture

The repository contains the complete extension suite:

```
timeless-35mm-reconstruction/
├── manifest.json       # Adobe UXP v5 manifest (Host: Premiere Pro, Node integration enabled)
├── index.html          # Dark-theme UXP panel UI & interactive canvas emulsion simulator
├── timeless.py         # OpenCV / NumPy 35mm film reconstruction pipeline
├── .gitignore          # Environment and build exclusion rules
└── README.md           # Documentation & guides
```

---

## 🎞️ Cinematic Eras & Camera Modifiers

### Era Profiles
- **1950s - Technicolor Golden Age & Nitrate Stock:** Pronounced optical edge softness, heavy red halation bloom, dense organic silver grain.
- **1960s - Nouvelle Vague & Techniscope 2-Perf:** High-contrast street photography feel with punchy edge bleed.
- **1970s - New Hollywood Gritty Panavision:** Cold shadow undertones with intense practical tungsten flare.
- **1980s - High-Speed 5294/5297 Blockbuster:** Sharper center resolution with high-ISO shadow grain and tight red neon halation.
- **1990s - Kodak EXR & Vision Modern Fine Grain:** T-Grain emulsion with subtle halation and high optical fidelity.

### Camera Modifier Profiles
- **Standard Neutral Camera:** Flat baseline stock response.
- **1950s Mitchell BNC (Bausch & Lomb Baltars):** High radial falloff with vintage bloom.
- **1950s Bell & Howell 2709 (Vintage Cooke Glass):** Strong optical aberration and grain clumping.
- **1960s Arriflex 35 II-C (Schneider Xenon Glass):** Handheld documentary contrast and edge bleed.
- **1970s Panavision Panaflex (C-Series Anamorphic):** Classic horizontal streak and halation diffusion.
- **1980s Arriflex 35 BL-4 (Zeiss Super Speed Mark II):** Controlled tight halation with sharp center focus.
- **1980s Moviecam SuperAmerica (Canon K-35 Glass):** Fast aperture diffusion with moderate grain.
- **1990s Panavision Platinum (Primo Primes):** Ultra-low distortion with minimal spherical aberration.

---

## ⚡ Installation & Premiere Pro Setup

### 1. Requirements
- Adobe Premiere Pro 2024 or 2025 (v24.0+)
- [Adobe UXP Developer Tool (UDT)](https://developer.adobe.com/developer-tool/)
- Python 3.9+ with `opencv-python` and `numpy`:
  ```bash
  pip install opencv-python numpy
  ```

### 2. Loading the Plugin
1. Open the **Adobe UXP Developer Tool**.
2. Click **Add Plugin** and select `manifest.json` from this repository.
3. Launch Adobe Premiere Pro.
4. In UDT, click **Load** on the *Timeless 35mm Reconstruction* card.
5. In Premiere Pro, open **Window > Extensions (or Plugins) > Timeless 35mm Reconstruction**.

### 3. Timeline Workflow
1. In your active sequence, select any video clip on **Track 1**.
2. Choose your **Era**, **Camera Modifier**, and **Chemical Balance** in the panel.
3. Fine-tune sliders with real-time feedback on the **Live Emulsion Viewport**.
4. Click **Reconstruct Selected Clip**.
5. The rendered `_35mm_reconstructed.mp4` video will be written to disk and automatically imported into your Premiere Pro Project Bin.

---

## 💻 Standalone CLI Usage

The core processing engine `timeless.py` can be executed directly from any terminal or automated render queue:

```bash
python timeless.py \
  --input "input_clip.mp4" \
  --output "output_35mm.mp4" \
  --mtf 15 \
  --thresh 205 \
  --h_blur 65 \
  --h_int 0.90 \
  --g_int 0.058 \
  --g_size 1.4 \
  --balance "cool"
```

### CLI Parameters
| Flag | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `--input` | `str` | *required* | Source video path |
| `--output` | `str` | *required* | Destination video path |
| `--mtf` | `int` | `11` | Maximum radial MTF lens blur (pixels) |
| `--thresh` | `int` | `215` | Highlight threshold for halation extraction (0-255) |
| `--h_blur` | `int` | `45` | Halation diffusion kernel blur radius |
| `--h_int` | `float` | `0.6` | Halation red bleed intensity multiplier |
| `--g_int` | `float` | `0.04` | Log-modulated silver grain noise intensity |
| `--g_size` | `float` | `1.2` | Film grain crystal spatial scale factor |
| `--balance` | `str` | `warm` | Chemical balance (`warm` for 5600K / `cool` for 3200K) |

---

## 🌐 Cloudflare Pages Live Demo

Test the interactive interface and visual emulsion simulator online:
👉 **[timeless-35mm-reconstruction.pages.dev](https://timeless-35mm-reconstruction.pages.dev)**

---

## 📄 License
MIT License. Built for professional filmmakers and colorists.
