import cv2
import numpy as np
import argparse

def timeless_pipeline(frame, mtf_blur_max=11, halation_threshold=215, halation_blur=45, halation_intensity=0.6, grain_intensity=0.04, grain_size=1.2, balance="warm"):
    h, w, c = frame.shape
    center_x, center_y = w / 2, h / 2
    x = np.linspace(0, w - 1, w)
    y = np.linspace(0, h - 1, h)
    xv, yv = np.meshgrid(x, y)
    distances = np.sqrt((xv - center_x)**2 + (yv - center_y)**2)
    max_distance = np.sqrt(center_x**2 + center_y**2)
    normalized_distances = distances / max_distance
    
    if mtf_blur_max % 2 == 0: mtf_blur_max += 1
    blurred_full = cv2.GaussianBlur(frame, (mtf_blur_max, mtf_blur_max), 0)
    mask_3d = np.expand_dims(normalized_distances, axis=2)
    optical_frame = (frame * (1.0 - mask_3d) + blurred_full * mask_3d).astype(np.uint8)
    img_float = optical_frame.astype(np.float32) / 255.0

    gray_frame = cv2.cvtColor(optical_frame, cv2.COLOR_BGR2GRAY)
    _, highlight_mask = cv2.threshold(gray_frame, halation_threshold, 255, cv2.THRESH_BINARY)
    highlight_mask_float = highlight_mask.astype(np.float32) / 255.0
    b_chan, g_chan, r_chan = cv2.split(img_float)
    
    h_mult = 0.7 if balance == "cool" else 1.0
    red_bleed_layer = diffused_red_bleed = cv2.GaussianBlur(r_chan * highlight_mask_float, (halation_blur | 1, halation_blur | 1), 0) * halation_intensity * h_mult
    green_bleed_layer = diffused_red_bleed * 0.15
    
    r_halation = np.clip(r_chan + red_bleed_layer, 0.0, 1.0)
    g_halation = np.clip(g_chan + green_bleed_layer, 0.0, 1.0)
    halation_frame = cv2.merge([b_chan, g_halation, r_halation])

    log_frame = np.log10(halation_frame * 9.0 + 1.0) / np.log10(10.0)
    log_gray = (0.299 * r_halation + 0.587 * g_halation + 0.114 * b_chan)
    noise_h, noise_w = int(h / grain_size), int(w / grain_size)
    raw_noise = np.random.normal(0, 1, (noise_h, noise_w, c)).astype(np.float32)
    
    if grain_size != 1.0:
        raw_noise = cv2.resize(raw_noise, (w, h), interpolation=cv2.INTER_LINEAR)
        
    grain_modulation = 4.0 * log_gray * (1.0 - log_gray)
    grain_modulation = np.expand_dims(np.clip(grain_modulation, 0.0, 1.0), axis=2)
    processed_grain = raw_noise * grain_intensity * grain_modulation
    final_35mm_frame = np.clip(log_frame + processed_grain, 0.0, 1.0)
    
    b_fin, g_fin, r_fin = cv2.split(final_35mm_frame)
    if balance == "cool":
        r_fin = np.clip(r_fin * 0.91, 0.0, 1.0)
        b_fin = np.clip(b_fin * 1.06, 0.0, 1.0)
    else:
        r_fin = np.clip(r_fin * 1.02, 0.0, 1.0)
        
    final_35mm_frame = cv2.merge([b_fin, g_fin, r_fin])
    return (final_35mm_frame * 255).astype(np.uint8)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mtf", type=int, default=11)
    parser.add_argument("--thresh", type=int, default=215)
    parser.add_argument("--h_blur", type=int, default=45)
    parser.add_argument("--h_int", type=float, default=0.6)
    parser.add_argument("--g_int", type=float, default=0.04)
    parser.add_argument("--g_size", type=float, default=1.2)
    parser.add_argument("--balance", type=str, default="warm")
    args = parser.parse_args()

    cap = cv2.VideoCapture(args.input)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        out_frame = timeless_pipeline(frame, args.mtf, args.thresh, args.h_blur, args.h_int, args.g_int, args.g_size, args.balance)
        out.write(out_frame)
    cap.release()
    out.release()
