import cv2
import numpy as np
import argparse
import time
import os
import json

def process_video(input_path, output_path, mtf_blur_max=11, halation_threshold=215, halation_blur=45, halation_intensity=0.6, grain_intensity=0.04, grain_size=1.2, balance="warm", progress_file=None):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open input video: {input_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    # Immediately write initial 0% progress stamp so the UI connects instantly
    if progress_file:
        try:
            with open(progress_file, "w") as pf:
                json.dump({"frame": 0, "total": total_frames, "percent": 0.0, "fps": 0.0, "stage": "Initializing"}, pf)
        except Exception:
            pass

    # Video writer initialization with multi-codec fallbacks
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        cap.release()
        raise RuntimeError("Could not initialize video writer with mp4v, avc1, or XVID codecs.")

    if mtf_blur_max % 2 == 0:
        mtf_blur_max += 1

    # --- PRECOMPUTE OPTICAL DISTORTION MASK ONCE (Massive Speedup) ---
    center_x, center_y = width / 2.0, height / 2.0
    x = np.linspace(0, width - 1, width)
    y = np.linspace(0, height - 1, height)
    xv, yv = np.meshgrid(x, y)
    distances = np.sqrt((xv - center_x)**2 + (yv - center_y)**2)
    max_distance = np.sqrt(center_x**2 + center_y**2)
    normalized_distances = distances / max_distance
    mask_3d = np.expand_dims(normalized_distances, axis=2).astype(np.float32)
    inv_mask_3d = (1.0 - mask_3d).astype(np.float32)

    # --- PRECOMPUTE GRAIN TEXTURE BANK (24 Frames Dynamic Cycling) ---
    grain_bank = []
    noise_h = max(1, int(height / grain_size))
    noise_w = max(1, int(width / grain_size))
    for _ in range(24):
        raw_noise = np.random.normal(0, 1, (noise_h, noise_w, 3)).astype(np.float32)
        if grain_size != 1.0:
            raw_noise = cv2.resize(raw_noise, (width, height), interpolation=cv2.INTER_LINEAR)
        grain_bank.append(raw_noise)

    h_mult = 0.7 if balance == "cool" else 1.0
    h_blur_kernel = (halation_blur | 1, halation_blur | 1)

    frame_count = 0
    start_time = time.time()
    last_progress_time = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        # 1. Optical MTF edge degradation using precomputed mask
        blurred_full = cv2.GaussianBlur(frame, (mtf_blur_max, mtf_blur_max), 0)
        optical_frame = (frame.astype(np.float32) * inv_mask_3d + blurred_full.astype(np.float32) * mask_3d).astype(np.uint8)
        img_float = optical_frame.astype(np.float32) / 255.0

        # 2. Halation isolation & bleed
        gray_frame = cv2.cvtColor(optical_frame, cv2.COLOR_BGR2GRAY)
        _, highlight_mask = cv2.threshold(gray_frame, halation_threshold, 255, cv2.THRESH_BINARY)
        highlight_mask_float = highlight_mask.astype(np.float32) / 255.0
        b_chan, g_chan, r_chan = cv2.split(img_float)

        diffused_red_bleed = cv2.GaussianBlur(r_chan * highlight_mask_float, h_blur_kernel, 0) * (halation_intensity * h_mult)
        r_halation = np.clip(r_chan + diffused_red_bleed, 0.0, 1.0)
        g_halation = np.clip(g_chan + (diffused_red_bleed * 0.15), 0.0, 1.0)
        halation_frame = cv2.merge([b_chan, g_halation, r_halation])

        # 3. Kodak Cineon logarithmic curve & grain application
        log_frame = np.log10(halation_frame * 9.0 + 1.0)
        log_gray = (0.299 * r_halation + 0.587 * g_halation + 0.114 * b_chan)
        grain_modulation = np.expand_dims(np.clip(4.0 * log_gray * (1.0 - log_gray), 0.0, 1.0), axis=2)

        # Retrieve cycling grain pattern
        raw_noise = grain_bank[frame_count % 24]
        processed_grain = raw_noise * (grain_intensity * grain_modulation)
        final_35mm_frame = np.clip(log_frame + processed_grain, 0.0, 1.0)

        # 4. Color balance
        b_fin, g_fin, r_fin = cv2.split(final_35mm_frame)
        if balance == "cool":
            r_fin = np.clip(r_fin * 0.91, 0.0, 1.0)
            b_fin = np.clip(b_fin * 1.06, 0.0, 1.0)
        else:
            r_fin = np.clip(r_fin * 1.02, 0.0, 1.0)

        out_frame = (cv2.merge([b_fin, g_fin, r_fin]) * 255.0).astype(np.uint8)
        out.write(out_frame)

        frame_count += 1

        # Periodic progress emission (every 0.25 seconds or at end)
        now = time.time()
        if progress_file and (now - last_progress_time > 0.25 or frame_count == total_frames):
            last_progress_time = now
            pct = round(min(100.0, (frame_count / total_frames) * 100.0), 1)
            fps_proc = round(frame_count / max(0.001, now - start_time), 1)
            try:
                tmp_prog = progress_file + ".tmp"
                with open(tmp_prog, "w") as pf:
                    json.dump({"frame": frame_count, "total": total_frames, "percent": pct, "fps": fps_proc, "stage": "Rendering"}, pf)
                if os.path.exists(progress_file):
                    os.remove(progress_file)
                os.rename(tmp_prog, progress_file)
            except Exception:
                pass

    cap.release()
    out.release()

    # Final 100% progress stamp
    if progress_file:
        try:
            with open(progress_file, "w") as pf:
                json.dump({"frame": total_frames, "total": total_frames, "percent": 100.0, "fps": 0.0, "stage": "Complete"}, pf)
        except Exception:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Timeless 35mm Reconstruction Engine")
    parser.add_argument("--input", required=True, help="Input video file path")
    parser.add_argument("--output", required=True, help="Output master video file path")
    parser.add_argument("--mtf", type=int, default=11, help="MTF Lens Edge Blur")
    parser.add_argument("--thresh", type=int, default=215, help="Halation Highlight Threshold")
    parser.add_argument("--h_blur", type=int, default=45, help="Halation Radius")
    parser.add_argument("--h_int", type=float, default=0.6, help="Halation Intensity")
    parser.add_argument("--g_int", type=float, default=0.04, help="Film Grain Intensity")
    parser.add_argument("--g_size", type=float, default=1.2, help="Film Grain Size Scale")
    parser.add_argument("--balance", type=str, default="warm", choices=["warm", "cool"], help="Color Temperature Balance")
    parser.add_argument("--progress", type=str, default=None, help="Optional progress JSON file path")
    args = parser.parse_args()

    process_video(
        input_path=args.input,
        output_path=args.output,
        mtf_blur_max=args.mtf,
        halation_threshold=args.thresh,
        halation_blur=args.h_blur,
        halation_intensity=args.h_int,
        grain_intensity=args.g_int,
        grain_size=args.g_size,
        balance=args.balance,
        progress_file=args.progress
    )
