import os

# os.system("wget -P cvec/ https://huggingface.co/spaces/innnky/nanami/resolve/main/checkpoint_best_legacy_500.pt")
import librosa
import numpy as np
import soundfile
from inference.infer_tool import Svc
from inference.infer_tool_768l12 import Svc_768l12
import torch
from pathlib import Path
from io import BytesIO
import tempfile
from pydub import AudioSegment
import json
import traceback

model = None
spk = None
cuda = []
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        cuda.append("cuda:{}".format(i))

model_path = str(Path(__file__).parent.joinpath(
    'checkpoints').joinpath('sunyz').joinpath('G_27200.pth'))
cluster_model_path = str(Path(__file__).parent.joinpath(
    'checkpoints').joinpath('sunyz').joinpath('kmeans_10000.pt'))
config_path = str(Path(__file__).parent.joinpath(
    'checkpoints').joinpath('sunyz').joinpath('config.json'))


def load_model_func(enhance, model_branch):
    global model, cluster_model_path, spk

    with open(config_path, 'r') as f:
        config = json.load(f)
    spk_dict = config["spk"]
    ckpt_path = model_path
    cluster_path = cluster_model_path
    cluster_name = 'kmeans_10000.pt'
    if cluster_name == "no_clu" and model_branch == "v1":
        model = Svc(ckpt_path, config_path, nsf_hifigan_enhance=enhance)
    elif cluster_name == "no_clu" and model_branch == "Vec768-Layer12":
        model = Svc_768l12(ckpt_path, config_path, nsf_hifigan_enhance=enhance)
    elif cluster_name != "no_clu" and model_branch == "v1":
        model = Svc(ckpt_path, config_path,
                    cluster_model_path=cluster_path, nsf_hifigan_enhance=enhance)
    else:
        model = Svc_768l12(
            ckpt_path, config_path, cluster_model_path=cluster_path, nsf_hifigan_enhance=enhance)

    spk_list = list(spk_dict.keys())
    spk = spk_list[0]


load_model_func(enhance=False, model_branch="v1")


def audio_from_file(filename, crop_min=0, crop_max=100):
    try:
        audio = AudioSegment.from_file(filename)
    except FileNotFoundError as e:
        isfile = Path(filename).is_file()
        msg = (
            f"Cannot load audio from file: `{'ffprobe' if isfile else filename}` not found."
            + " Please install `ffmpeg` in your system to use non-WAV audio file formats"
            " and make sure `ffprobe` is in your PATH."
            if isfile
            else ""
        )
        raise RuntimeError(msg) from e
    if crop_min != 0 or crop_max != 100:
        audio_start = len(audio) * crop_min / 100
        audio_end = len(audio) * crop_max / 100
        audio = audio[audio_start:audio_end]
    data = np.array(audio.get_array_of_samples())
    if audio.channels > 1:
        data = data.reshape(-1, audio.channels)
    return audio.frame_rate, data


def vc_fn(input_audio_path, vc_transform, auto_f0, cluster_ratio, slice_db, noise_scale, pad_seconds, cl_num, lg_num, lgr_num, F0_mean_pooling, enhancer_adaptive_key, cr_threshold):
    global model, spk
    sid = spk
    try:
        if input_audio_path is None:
            return "You need to upload an audio", None
        if model is None:
            return "You need to upload an model", None
        sampling_rate, audio = audio_from_file(input_audio_path)
        audio = (audio / np.iinfo(audio.dtype).max).astype(np.float32)
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio.transpose(1, 0))
        temp_file = tempfile.NamedTemporaryFile(delete=True,suffix='.wav')
        temp_path = temp_file.name
        soundfile.write(temp_path, audio, sampling_rate, format="wav")
        try:
            _audio = model.slice_inference(temp_path, sid, vc_transform, slice_db, cluster_ratio, auto_f0, noise_scale,
                                           pad_seconds, cl_num, lg_num, lgr_num, F0_mean_pooling, enhancer_adaptive_key, cr_threshold)
        except Exception as e:
            print(e)
            return 'errors', None
        finally:
            temp_file.close()
            model.clear_empty()
        output_file = BytesIO()
        soundfile.write(output_file, _audio, model.target_sample, format="mp3")
        return "Success", (model.target_sample, output_file)
    except Exception as e:
        traceback.print_exc()
        return "Error", None


def get_model_sample_rate():
    global model
    return model.target_sample
