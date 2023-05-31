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
try:
    f = open(Path(__file__).parent.joinpath('models.json'), "r")
    MODEL_INVENTORY = json.load(f)
    f.close()
except Exception as e:
    traceback.print_exc()
    MODEL_INVENTORY = []

def get_custom_model_id(config_path, spk):
    return f'{config_path}__{spk}'

def load_model_func(model_id):
    global cached_models
    if model_id in cached_models:
        print('Using cached model')
        return cached_models[model_id]["model"], cached_models[model_id]["spk"]
    matched_model_specs = [m for m in MODEL_INVENTORY if m["id"] == model_id]
    if len(matched_model_specs) == 0:
        raise ValueError(f"Model id not found: {model_id}")
    if len(matched_model_specs) > 1:
        raise ValueError(f"Multiple models with the same id: {model_id}")

    model_spec = matched_model_specs[0]
    config_path = str(Path(__file__).parent.joinpath('checkpoints').joinpath(
        model_spec["dir"]).joinpath(model_spec["config"]))
    ckpt_path = str(Path(__file__).parent.joinpath('checkpoints').joinpath(
        model_spec["dir"]).joinpath(model_spec["model"]))
    cluster_path = str(Path(__file__).parent.joinpath('checkpoints').joinpath(
        model_spec["dir"]).joinpath(model_spec["cluster"])) if "cluster" in model_spec else None
    cluster_name = model_spec["cluster_name"] if "cluster_name" in model_spec else "no_clu"
    model_branch = model_spec["model_branch"] if "model_branch" in model_spec else "v1"
    hifigan_enhance = model_spec["hifigan_enhance"] if "hifigan_enhance" in model_spec else False
    model, spk = _load_model_do_func(model_id, config_path, ckpt_path, cluster_path, cluster_name, model_branch, hifigan_enhance)
    return model, spk

def load_custom_model_func(config_path, ckpt_path, cluster_path=None, cluster_name="no_clu", model_branch="v1", hifigan_enhance=False):
    global cached_models
    with open(config_path, 'r') as f:
        config = json.load(f)
    spk_dict = config["spk"]
    spk_list = list(spk_dict.keys())
    spk = spk_list[0]
    model_id = get_custom_model_id(config_path, spk)
    if model_id in cached_models:
        print('Using cached model')
        return cached_models[model_id]["model"], cached_models[model_id]["spk"]
    return _load_model_do_func(model_id, config_path, ckpt_path, cluster_path, cluster_name, model_branch, hifigan_enhance)

def _load_model_do_func(model_id, config_path, ckpt_path, cluster_path=None, cluster_name="no_clu", model_branch="v1", hifigan_enhance=False):
    with open(config_path, 'r') as f:
        config = json.load(f)
    spk_dict = config["spk"]
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


def vc_fn(
        model_id, input_audio_bytes, vc_transform, auto_f0, cluster_ratio, slice_db, noise_scale, pad_seconds, cl_num,
        lg_num, lgr_num, F0_mean_pooling, enhancer_adaptive_key, cr_threshold):
    model, sid = load_model_func(model_id)
    return vc_fn_model(
        model, sid, input_audio_bytes=input_audio_bytes, vc_transform=vc_transform, auto_f0=auto_f0,
        cluster_ratio=cluster_ratio, slice_db=slice_db, noise_scale=noise_scale, pad_seconds=pad_seconds, cl_num=cl_num,
        lg_num=lg_num, lgr_num=lgr_num, F0_mean_pooling=F0_mean_pooling, enhancer_adaptive_key=enhancer_adaptive_key,
        cr_threshold=cr_threshold)


def vc_fn_model(
        model, sid, input_audio_bytes, vc_transform, auto_f0, cluster_ratio, slice_db, noise_scale, pad_seconds, cl_num,
        lg_num, lgr_num, F0_mean_pooling, enhancer_adaptive_key, cr_threshold):
    try:
        if input_audio_bytes is None:
            return "You need to upload an audio", None
        if model is None:
            return "You need to upload an model", None
        sampling_rate, audio = audio_from_bytes(input_audio_bytes)
        audio = (audio / np.iinfo(audio.dtype).max).astype(np.float32)
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio.transpose(1, 0))
        fd, temp_path = tempfile.mkstemp(suffix='.wav')
        soundfile.write(temp_path, audio, sampling_rate, format="wav")
        try:
            _audio = model.slice_inference(
                temp_path, sid, vc_transform, slice_db, cluster_ratio, auto_f0, noise_scale, pad_seconds, cl_num,
                lg_num, lgr_num, F0_mean_pooling, enhancer_adaptive_key, cr_threshold)
        except Exception as e:
            print(e)
            return 'errors', None
        finally:
            try:
                os.close(fd)
                os.unlink(temp_path)
            except Exception as e:
                print(e)
            model.clear_empty()
        output_file = BytesIO()
        soundfile.write(output_file, _audio, model.target_sample, format="mp3")
        return "Success", (model.target_sample, output_file)
    except Exception as e:
        traceback.print_exc()
        return "Error", None
