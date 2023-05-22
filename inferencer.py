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

cached_models = {}

cuda = []
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        cuda.append("cuda:{}".format(i))
f = open(Path(__file__).parent.joinpath('models.json'), "r")
MODE_INVENTORY = json.load(f)
f.close()


def load_model_func(model_id):
    global cached_models
    if model_id in cached_models:
        print('Using cached model')
        return cached_models[model_id]["model"], cached_models[model_id]["spk"]
    matched_model_specs = [m for m in MODE_INVENTORY if m["id"] == model_id]
    if len(matched_model_specs) == 0:
        raise ValueError(f"Model id not found: {model_id}")
    if len(matched_model_specs) > 1:
        raise ValueError(f"Multiple models with the same id: {model_id}")

    model_spec = matched_model_specs[0]
    config_path = str(Path(__file__).parent.joinpath('checkpoints').joinpath(
        model_spec["dir"]).joinpath(model_spec["config"]))
    with open(config_path, 'r') as f:
        config = json.load(f)
    spk_dict = config["spk"]
    ckpt_path = str(Path(__file__).parent.joinpath('checkpoints').joinpath(
        model_spec["dir"]).joinpath(model_spec["model"]))
    cluster_path = str(Path(__file__).parent.joinpath('checkpoints').joinpath(
        model_spec["dir"]).joinpath(model_spec["cluster"])) if "cluster" in model_spec else None
    cluster_name = model_spec["cluster_name"] if "cluster_name" in model_spec else "no_clu"
    model_branch = model_spec["model_branch"] if "model_branch" in model_spec else "v1"
    hifigan_enhance = model_spec["hifigan_enhance"] if "hifigan_enhance" in model_spec else False
    if cluster_name == "no_clu" and model_branch == "v1":
        model = Svc(ckpt_path, config_path,
                    nsf_hifigan_enhance=hifigan_enhance)
    elif cluster_name == "no_clu" and model_branch == "Vec768-Layer12":
        model = Svc_768l12(ckpt_path, config_path,
                           nsf_hifigan_enhance=hifigan_enhance)
    elif cluster_name != "no_clu" and cluster_path is not None and model_branch == "v1":
        model = Svc(ckpt_path, config_path,
                    cluster_model_path=cluster_path, nsf_hifigan_enhance=hifigan_enhance)
    elif cluster_path is not None:
        model = Svc_768l12(
            ckpt_path, config_path, cluster_model_path=cluster_path, nsf_hifigan_enhance=hifigan_enhance)
    else:
        raise ValueError("Invalid model config")
    spk_list = list(spk_dict.keys())
    spk = spk_list[0]
    cached_models[model_id] = {
        "model": model,
        "spk": spk,
    }
    return model, spk


def audio_from_bytes(file_bytes, crop_min=0, crop_max=100):
    try:
        input_file = BytesIO(file_bytes)
        input_file.seek(0)
        audio = AudioSegment.from_file(input_file)
    except FileNotFoundError as e:
        msg = (
            f"Cannot load audio"
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


def vc_fn(model_id, input_audio_bytes, vc_transform, auto_f0, cluster_ratio, slice_db, noise_scale, pad_seconds, cl_num, lg_num, lgr_num, F0_mean_pooling, enhancer_adaptive_key, cr_threshold):
    model, sid = load_model_func(model_id)
    try:
        if input_audio_bytes is None:
            return "You need to upload an audio", None
        if model is None:
            return "You need to upload an model", None
        sampling_rate, audio = audio_from_bytes(input_audio_bytes)
        audio = (audio / np.iinfo(audio.dtype).max).astype(np.float32)
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio.transpose(1, 0))
        temp_file = tempfile.NamedTemporaryFile(delete=True, suffix='.wav')
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
