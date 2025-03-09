import os
import random
import numpy as np
import librosa

def extract_features(audio: np.ndarray, sample_rate: int, n_mfcc: int = 20, n_mels: int = 40, 
                     n_fft: int = 1024, hop_length: int = 512) -> np.ndarray:
    """
    Extract audio features for doorbell detection.
    
    Args:
        audio: Audio signal.
        sample_rate: Sample rate of audio signal.
        n_mfcc: Number of MFCC coefficients.
        n_mels: Number of Mel bands.
        n_fft: FFT window size.
        hop_length: Number of samples between consecutive frames.
        
    Returns:
        feature_vector: Combined feature vector.
    """
    mel_spec = librosa.feature.melspectrogram(y=audio, sr=sample_rate, n_mels=n_mels, 
                                              n_fft=n_fft, hop_length=hop_length)
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    mfcc = librosa.feature.mfcc(S=mel_spec_db, n_mfcc=n_mfcc, sr=sample_rate)
    mfcc_delta = librosa.feature.delta(mfcc)
    spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sample_rate, n_bands=6, fmin=100.0)
    spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate, n_fft=n_fft, 
                                                          hop_length=hop_length)
    feature_vector = np.concatenate([
        np.mean(mel_spec_db, axis=1), np.std(mel_spec_db, axis=1),
        np.mean(mfcc, axis=1), np.std(mfcc, axis=1),
        np.mean(mfcc_delta, axis=1), np.std(mfcc_delta, axis=1),
        np.mean(spectral_contrast, axis=1), np.std(spectral_contrast, axis=1),
        [np.mean(spectral_centroid), np.std(spectral_centroid)]
    ])
    return feature_vector

def get_segments(audio: np.ndarray, segment_samples: int, hop_samples: int) -> list:
    """
    Extract all valid segments from an audio signal.
    
    Args:
        audio: Audio signal.
        segment_samples: Length of each segment (in samples).
        hop_samples: Hop length between segments (in samples).
        
    Returns:
        segments: List of audio segments.
    """
    segments = []
    for i in range(0, len(audio) - segment_samples + 1, hop_samples):
        segment = audio[i:i + segment_samples]
        if len(segment) == segment_samples:
            segments.append(segment)
    return segments

def apply_augmentations(segment: np.ndarray, sr: int, segment_samples: int, 
                        aug_config: dict) -> list:
    """
    Generate augmented versions of a given audio segment.
    
    Args:
        segment: Original audio segment.
        sr: Sample rate.
        segment_samples: Length of segment in samples.
        aug_config: Dictionary with augmentation parameters.
        
    Returns:
        List of augmented audio segments.
    """
    augmented = []
    pitch_factor = np.random.uniform(aug_config["pitch_min"], aug_config["pitch_max"])
    augmented.append(librosa.effects.pitch_shift(segment, sr=sr, n_steps=pitch_factor))
    stretch_factor = np.random.uniform(aug_config["stretch_min"], aug_config["stretch_max"])
    y_stretched = librosa.effects.time_stretch(segment, rate=stretch_factor)
    if len(y_stretched) < segment_samples:
        y_stretched = np.pad(y_stretched, (0, segment_samples - len(y_stretched)))
    else:
        y_stretched = y_stretched[:segment_samples]
    augmented.append(y_stretched)
    noise_factor = np.random.uniform(aug_config["noise_min"], aug_config["noise_max"])
    augmented.append(segment + noise_factor * np.random.randn(len(segment)))
    volume_factor = np.random.uniform(aug_config["volume_min"], aug_config["volume_max"])
    augmented.append(segment * volume_factor)
    return augmented

def get_random_background_segment(audio_dirs: list, sample_rate: int, segment_samples: int, 
                                  doorbell_path: str = None) -> np.ndarray:
    """
    Returns a random background segment from the given directories.
    
    Args:
        audio_dirs: List of directories containing background audio files.
        sample_rate: Sample rate.
        segment_samples: Required segment length (in samples).
        doorbell_path: Path to the doorbell file to exclude.
        
    Returns:
        A background segment or None if not found.
    """
    candidates = []
    for directory in audio_dirs:
        for fname in os.listdir(directory):
            file_path = os.path.join(directory, fname)
            if (doorbell_path is None or os.path.abspath(file_path) != os.path.abspath(doorbell_path)) and \
               fname.endswith(('.wav', '.mp3', '.ogg')):
                candidates.append(file_path)
    if not candidates:
        return None
    chosen = random.choice(candidates)
    try:
        y, _ = librosa.load(chosen, sr=sample_rate)
        if len(y) < segment_samples:
            return None
        start = np.random.randint(0, len(y) - segment_samples + 1)
        return y[start:start + segment_samples]
    except Exception as e:
        print(f"Error loading {chosen}: {e}")
        return None

def generate_mixed_examples(doorbell_segments: list, background_segments: list, sample_rate: int,
                            n_mfcc: int, n_mels: int, n_fft: int, hop_length: int,
                            mix_ratio_range: tuple, max_mixed_samples: int = None) -> (list, int):
    """
    Generate mixed positive examples by mixing doorbell segments with background segments.
    
    Args:
        doorbell_segments: List of doorbell audio segments.
        background_segments: List of background audio segments reserved for mixing.
        sample_rate: Sample rate.
        n_mfcc, n_mels, n_fft, hop_length: Parameters for feature extraction.
        mix_ratio_range: Tuple with minimum and maximum mixing ratio.
        max_mixed_samples: Maximum number of mixed examples to generate.
        
    Returns:
        mixed_features: List of feature vectors from mixed examples.
        mixed_count: Number of mixed examples generated.
    """
    mixed_features = []
    mixed_count = 0
    if not doorbell_segments:
        print("Warning: No doorbell segments available for mixing.")
        return mixed_features, mixed_count
    if not background_segments:
        print("Warning: No background segments available for mixing.")
        return mixed_features, mixed_count
    max_iterations = 1000
    iterations = 0
    while (max_mixed_samples is None or mixed_count < max_mixed_samples) and iterations < max_iterations:
        bg_segment = random.choice(background_segments)
        db_seg = random.choice(doorbell_segments)
        mix_ratio = np.random.uniform(*mix_ratio_range)
        mixed = librosa.util.normalize(db_seg + mix_ratio * bg_segment)
        feat = extract_features(mixed, sample_rate, n_mfcc, n_mels, n_fft, hop_length)
        mixed_features.append(feat)
        mixed_count += 1
        iterations += 1
    return mixed_features, mixed_count

def process_dataset(doorbell_path: str, audio_dirs: list, sample_rate: int = 16000, 
                    segment_duration: float = 1.0, hop_duration: float = 0.5, n_mfcc: int = 20, 
                    n_mels: int = 40, n_fft: int = 1024, hop_length: int = 512, augment: bool = True, 
                    mix_background: bool = True, mix_ratio_range: tuple = (0.1, 0.5), 
                    max_background_samples: int = 1000, max_mixed_samples: int = None,
                    background_mix_split: float = 0.5) -> (np.ndarray, np.ndarray):
    """
    Process audio dataset to extract features for doorbell detection.
    
    For doorbell audio, segments are extracted and, if augment is True, multiple augmented
    versions are generated and averaged (producing one robust example per segment). In addition,
    if mix_background is True, doorbell segments are mixed with random background segments
    (reserved exclusively for mixing) to simulate noisy environments.
    
    For background audio, the number of negatives is limited by max_background_samples.
    The background segments are divided into two subsets: one for negatives and one for mixing,
    controlled by 'background_mix_split' (e.g., 0.5 means 50% for negatives and 50% for mixing).
    
    Returns:
        features: Array of feature vectors.
        labels: Array of binary labels (1 for doorbell, 0 for background).
    """
    features, labels = [], []
    segment_samples = int(sample_rate * segment_duration)
    hop_samples = int(sample_rate * hop_duration)
    
    if not os.path.exists(doorbell_path):
        raise ValueError(f"Doorbell file '{doorbell_path}' does not exist.")
    
    print(f"Processing doorbell sample: {doorbell_path}")
    y_doorbell, sr = librosa.load(doorbell_path, sr=sample_rate)
    doorbell_segments = get_segments(y_doorbell, segment_samples, hop_samples)
    
    if not doorbell_segments:
        raise ValueError("No valid doorbell segments were extracted.")
    
    # Augmentation configuration
    aug_config = {
        "pitch_min": -1,
        "pitch_max": 1,
        "stretch_min": 0.8,
        "stretch_max": 1.2,
        "noise_min": 0.01,
        "noise_max": 0.1,
        "volume_min": 0.5,
        "volume_max": 1.5
    }
    
    # Process doorbell segments: extract features (averaging augmentations if enabled)
    for segment in doorbell_segments:
        base_feat = extract_features(segment, sr, n_mfcc, n_mels, n_fft, hop_length)
        if augment:
            aug_segs = apply_augmentations(segment, sr, segment_samples, aug_config)
            aug_feats = [extract_features(a, sr, n_mfcc, n_mels, n_fft, hop_length) for a in aug_segs]
            seg_feat = np.mean([base_feat] + aug_feats, axis=0)
        else:
            seg_feat = base_feat
        features.append(seg_feat)
        labels.append(1)
    
    # Gather all background segments from audio_dirs (without asigning them como negatives aún)
    all_bg_segments = []
    for directory in audio_dirs:
        for fname in os.listdir(directory):
            file_path = os.path.join(directory, fname)
            if os.path.abspath(file_path) == os.path.abspath(doorbell_path):
                continue
            if os.path.isfile(file_path) and file_path.endswith(('.wav', '.mp3', '.ogg')):
                try:
                    y_bg, sr = librosa.load(file_path, sr=sample_rate)
                    bg_segs = get_segments(y_bg, segment_samples, hop_samples)
                    all_bg_segments.extend(bg_segs)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
    
    # Limit total background segments
    if max_background_samples is not None:
        all_bg_segments = all_bg_segments[:max_background_samples]
    
    # Split background segments into two groups:
    # one for negatives and one for mixing
    random.shuffle(all_bg_segments)
    split_index = int(len(all_bg_segments) * background_mix_split)
    bg_for_negatives = all_bg_segments[split_index:]  # Resto para negativos
    bg_for_mixing = all_bg_segments[:split_index]       # Reservados para mezclas
    
    # Process negatives: add features from bg_for_negatives
    for seg in bg_for_negatives:
        feat = extract_features(seg, sr, n_mfcc, n_mels, n_fft, hop_length)
        features.append(feat)
        labels.append(0)
    
    # Generate mixed examples: mix doorbell segments with background segments for mixing
    if mix_background:
        mixed_feats, mixed_count = generate_mixed_examples(
            doorbell_segments, bg_for_mixing, sample_rate, n_mfcc, n_mels, n_fft, hop_length, 
            mix_ratio_range, max_mixed_samples
        )
        for feat in mixed_feats:
            features.append(feat)
            labels.append(1)
    
    total_positives = sum(1 for l in labels if l == 1)
    total_negatives = len(labels) - total_positives
    print(f"Dataset: {total_positives} positives, {total_negatives} negatives. Ratio 1:{total_negatives/total_positives:.1f}")
    return np.array(features), np.array(labels)
