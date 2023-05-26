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
import glob
from pathlib import Path
import re

cached_models = {}

# by default it we will choose the model with the highest steps
def get_max_steps_file(path):
    max_steps = -1
    max_steps_file = None
    file_pattern = re.compile(r'G_(\d+)\.pth$')

    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file():
                match = file_pattern.search(entry.name)
                if match:
                    steps = int(match.group(1))
                    if steps > max_steps:
                        max_steps = steps
                        max_steps_file = entry.name
    return max_steps_file

def get_directories(path):
    directories = []
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_dir() and get_max_steps_file(str(Path(path).joinpath(entry.name))):
                directories.append(entry.name)
    return directories


# If you just want the filenames, not the entire path
MODE_INVENTORY = get_directories(str(Path(__file__).parent.joinpath('models'))) # store the file name

cuda = []
if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        cuda.append("cuda:{}".format(i))

def load_model_func(model_name):
    global cached_models
    if model_name in cached_models:
        print('Using cached model')
        return cached_models[model_name]["model"], cached_models[model_name]["spk"]
    matched_model_specs = [m for m in MODE_INVENTORY if m == model_name]
    if len(matched_model_specs) == 0:
        raise ValueError(f"Model id not found: {model_name}")

    model_dir = str(Path(__file__).parent.joinpath("models").joinpath(matched_model_specs[0]))
    config_path = str(Path(model_dir).joinpath("config.json"))
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except:
        raise ValueError(f"config file not found or format incorrect under {model_dir}")
    spk_dict = config["spk"]
    
    model_spec = config["model_spec"] if "model_spec" in config else {}
    

    # fill in the parameters
    # fetch model if there is a model in there
    checkpoint_name = model_spec["model_name"] if "model_name" in model_spec else get_max_steps_file(model_dir)
    if checkpoint_name is None:
        raise ValueError(f"No model found under: {str(model_dir)}")
    ckpt_path = str(Path(model_dir).joinpath(checkpoint_name))
    
    # load other training parameters
    cluster_path = str(Path(__file__).parent.joinpath("models").joinpath(model_spec["cluster_name"])) if "cluster_name" in model_spec else "no_clu"
    model_branch = model_spec["model_branch"] if "model_branch" in model_spec else "v1"
    hifigan_enhance = model_spec["hifigan_enhance"] if "hifigan_enhance" in model_spec else False
    
    if cluster_path == "no_clu" and model_branch == "v1":
        model = Svc(ckpt_path, config_path,
                    nsf_hifigan_enhance=hifigan_enhance)
    elif cluster_path == "no_clu" and model_branch == "Vec768-Layer12":
        model = Svc_768l12(ckpt_path, config_path,
                           nsf_hifigan_enhance=hifigan_enhance)
    elif cluster_path != "no_clu" and cluster_path is not None and model_branch == "v1":
        model = Svc(ckpt_path, config_path,
                    cluster_model_path=cluster_path, nsf_hifigan_enhance=hifigan_enhance)
    elif cluster_path is not None:
        model = Svc_768l12(
            ckpt_path, config_path, cluster_model_path=cluster_path, nsf_hifigan_enhance=hifigan_enhance)
    else:
        raise ValueError("Invalid model config")
    spk_list = list(spk_dict.keys())
    spk = spk_list[0]
    cached_models[model_name] = {
        "model": model,
        "spk": spk,
    }
    return model, spk


def audio_from_file(filename, crop_min=0, crop_max=100):
    try:
        print(f"filename is :{filename}")
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


def vc_fn(model_id, input_audio_path, vc_transform, auto_f0, cluster_ratio, slice_db, noise_scale, pad_seconds, cl_num, lg_num, lgr_num, F0_mean_pooling, enhancer_adaptive_key, cr_threshold):
    model, sid = load_model_func(model_id)
    try:
        if input_audio_path is None:
            return "You need to upload an audio", None
        if model is None:
            return "You need to upload an model", None
        sampling_rate, audio = audio_from_file(input_audio_path)
        audio = (audio / np.iinfo(audio.dtype).max).astype(np.float32)
        if len(audio.shape) > 1:
            audio = librosa.to_mono(audio.transpose(1, 0))
        temp_file = tempfile.NamedTemporaryFile(delete=True, suffix='.wav')
        temp_path = temp_file.name
        
        fd, temp_path = tempfile.mkstemp(suffix='.wav')
        soundfile.write(temp_path, audio, sampling_rate, format="wav")
        # try:
        #     _audio = model.slice_inference(temp_path, sid, vc_transform, slice_db, cluster_ratio, auto_f0, noise_scale,
        #                                    pad_seconds, cl_num, lg_num, lgr_num, F0_mean_pooling, enhancer_adaptive_key, cr_threshold)
        # except Exception as e:
        #     traceback.print_exc()
        #     raise e
        #     return 'errors', None
        # finally:
        #     temp_file.close()
        #     model.clear_empty()
        _audio = model.slice_inference(temp_path, sid, vc_transform, slice_db, cluster_ratio, auto_f0, noise_scale,
                                            pad_seconds, cl_num, lg_num, lgr_num, F0_mean_pooling, enhancer_adaptive_key, cr_threshold)
        output_file = BytesIO()
        soundfile.write(output_file, _audio, model.target_sample, format="mp3")
        return "Success", (model.target_sample, output_file)
    except Exception as e:
        traceback.print_exc()
        raise e
