from __future__ import annotations

from tuneflow_py import TuneflowPlugin, Song, ParamDescriptor, WidgetType, TrackType, InjectSource, TuneflowPluginTriggerData, ClipAudioDataInjectData
from typing import Any
import traceback
from inferencer import vc_fn_model, load_custom_model_func
from utils import trim_audio
from pathlib import Path


class SingingVoiceCloneLocal(TuneflowPlugin):
    @staticmethod
    def provider_id():
        return "andantei"

    @staticmethod
    def plugin_id():
        return "singing-voice-clone-local"

    @staticmethod
    def params(song: Song) -> dict[str, ParamDescriptor]:
        # Check if there is any .pth file in the checkpoints folder.
        checkpoints_folder = Path(__file__).parent.joinpath("checkpoints")
        checkpoint_path = None
        config_path = None
        if checkpoints_folder.exists():
            # Find all files under checkpoints_folder, non-recursively.
            checkpoints = [file for file in checkpoints_folder.iterdir() if file.is_file() and file.suffix == ".pth"]
            if len(checkpoints) > 0:
                checkpoint_path = str(checkpoints[0])
                config_file_path = Path(__file__).parent.joinpath('checkpoints').joinpath("config.json")
                if config_file_path.exists():
                    config_path = str(config_file_path)

        return {
            "clipAudioData": {
                "displayName": {
                    "zh": '音频',
                    "en": 'Audio',
                },
                "defaultValue": None,
                "widget": {
                    "type": WidgetType.NoWidget.value,
                },
                "hidden": True,
                "injectFrom": {
                    "type": InjectSource.ClipAudioData.value,
                    "options": {
                        "clips": "selectedAudioClips"
                    }
                }
            },
            "modelFile": {
                "displayName": {
                    "zh": '模型文件 (.pth)',
                    "en": 'Model File (.pth)',
                },
                "defaultValue": checkpoint_path,
                "widget": {
                    "type": WidgetType.FileSelector.value,
                    "config": {
                        "allowedExtensions": ["pth"],
                        "selectLocalFile": True
                    }
                },
            },
            "configFile": {
                "displayName": {
                    "zh": '配置文件 (config.json)',
                    "en": 'Config File (config.json)',
                },
                "defaultValue": config_path,
                "widget": {
                    "type": WidgetType.FileSelector.value,
                    "config": {
                        "allowedExtensions": ["json"],
                        "selectLocalFile": True
                    }
                },
            },
            "pitchOffset": {
                "displayName": {
                    "zh": '变调',
                    "en": 'Pitch Offset',
                },
                "description": {
                    "zh": '半音为单位，+12为升一个八度，-12为降一个八度',
                    "en": 'Pitch offset in semitones, +12 for one octave up, -12 for one octave down',
                },
                "defaultValue": 0,
                "widget": {
                    "type": WidgetType.Slider.value,
                    "config": {
                        "minValue": -12,
                        "maxValue": 12,
                        "step": 1,
                    }
                },
            },
            "f0MeanPooling": {
                "displayName": {
                    "zh": 'f0均值滤波',
                    "en": 'f0 mean pooling',
                },
                "description": {
                    "zh": '开启后可能帮助改善哑音',
                    "en": 'May improve muted audio in some cases',
                },
                "defaultValue": False,
                "widget": {
                    "type": WidgetType.Switch.value,
                    "config": {
                    }
                },
            },
            "f0Threshold": {
                "displayName": {
                    "zh": 'f0过滤阈值',
                    "en": 'f0 filter threshold',
                },
                "description": {
                    "zh": '值越大，哑音概率可能越小，同时可能导致音高不准',
                    "en": 'Larger value may reduce the probability of muted audio, but may also cause pitch inaccuracy',
                },
                "defaultValue": 0.05,
                "widget": {
                    "type": WidgetType.Slider.value,
                    "config": {
                        "minValue": 0,
                        "maxValue": 1,
                        "step": 0.01,
                    }
                },
            },
        }

    @staticmethod
    def run(song: Song, params: dict[str, Any]):
        pitchOffset: int = params["pitchOffset"]
        f0MeanPooling: bool = params["f0MeanPooling"]
        f0Threshold: float = params["f0Threshold"]
        model_file: str = params["modelFile"]
        config_file: str = params["configFile"]
        trigger: TuneflowPluginTriggerData = params["trigger"]
        trigger_entity_id = trigger["entities"][0]  # type:ignore
        track = song.get_track_by_id(
            trigger_entity_id["trackId"])  # type:ignore
        if track is None:
            raise Exception("Cannot find track")
        clip = track.get_clip_by_id(trigger_entity_id["clipId"])  # type:ignore
        if clip is None:
            raise Exception("Cannot find clip")
        clip_audio_data_list: ClipAudioDataInjectData = params["clipAudioData"]

        try:
            model, spk = load_custom_model_func(config_path=config_file, ckpt_path=model_file)
            result = vc_fn_model(
                model, spk, trim_audio(clip_audio_data_list[0]["audioData"]["data"],
                                       song, clip),
                vc_transform=pitchOffset, auto_f0=False, cluster_ratio=0, slice_db=-40, noise_scale=0.4,
                pad_seconds=0.5, cl_num=0, lg_num=0, lgr_num=0.75, F0_mean_pooling=f0MeanPooling,
                enhancer_adaptive_key=0, cr_threshold=f0Threshold)
            if not result:
                raise Exception("Failed to generate audio")
            status, generated_data = result
            if status != "Success" or generated_data is None:
                raise Exception("Failed to generate audio")
            sample_rate, generated_audio_data = generated_data
            generated_audio_data.seek(0)
            new_track = song.create_track(
                TrackType.AUDIO_TRACK, index=song.get_track_index(track.get_id())+1)  # type:ignore
            new_track.create_audio_clip(clip_start_tick=clip.get_clip_start_tick(), audio_clip_data={
                "audio_data": {
                    "data": generated_audio_data.read(),
                    "format": "mp3",
                },
                "duration": clip.get_duration(),
                "start_tick": clip.get_clip_start_tick(),
            }, clip_end_tick=clip.get_clip_end_tick(), insert_clip=True)
        except Exception as e:
            print(traceback.format_exc())
            raise e