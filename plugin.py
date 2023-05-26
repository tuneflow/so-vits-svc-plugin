from __future__ import annotations

from tuneflow_py import TuneflowPlugin, Song, Clip, ParamDescriptor, WidgetType, TrackType, InjectSource, TuneflowPluginTriggerData, ClipAudioDataInjectData
from typing import Any
import tempfile
import traceback
from inferencer import vc_fn, MODE_INVENTORY
from io import BytesIO
from pydub import AudioSegment
import os

class SingingVoiceClone(TuneflowPlugin):
    @staticmethod
    def provider_id():
        return "andantei, dreamflyfreya"

    @staticmethod
    def plugin_id():
        return "singing-voice-clone_local"

    @staticmethod
    def params(song: Song) -> dict[str, ParamDescriptor]:
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
            "voiceLine": {
                "displayName": {
                    "zh": '声线',
                    "en": 'Voice Line',
                },
                "defaultValue": 'yz',
                "widget": {
                    "type": WidgetType.Select.value,
                    "config": {
                        "options": [
                            {
                                "label": spec,
                                "value": spec
                            } for spec in MODE_INVENTORY
                        ]
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
        voiceLine: str = params['voiceLine']
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

        tmp_file = tempfile.NamedTemporaryFile(
            delete=True, suffix=clip_audio_data_list[0]["audioData"]["format"])
        tmp_file.write(SingingVoiceClone._trim_audio(
            clip_audio_data_list[0]["audioData"]["data"], song, clip))


        fd, path = tempfile.mkstemp(suffix=clip_audio_data_list[0]["audioData"]["format"])

        try:
            with os.fdopen(fd, 'wb') as tmp_file:
                tmp_file.write(SingingVoiceClone._trim_audio(
                    clip_audio_data_list[0]["audioData"]["data"], song, clip))
            result = vc_fn(voiceLine, path, vc_transform=pitchOffset, auto_f0=False, cluster_ratio=0, slice_db=-40,
                           noise_scale=0.4, pad_seconds=0.5, cl_num=0, lg_num=0, lgr_num=0.75, F0_mean_pooling=f0MeanPooling, enhancer_adaptive_key=0, cr_threshold=f0Threshold)
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
            os.remove(path)
            raise e
        os.remove(path)

    @staticmethod
    def _trim_audio(audio_bytes: bytes, song: Song, clip: Clip):
        clip_start_time = song.tick_to_seconds(clip.get_clip_start_tick())
        clip_end_time = song.tick_to_seconds(clip.get_clip_end_tick())
        audio_start_time = song.tick_to_seconds(clip.get_audio_start_tick()) # type:ignore
        in_bytes_io = BytesIO(audio_bytes)
        dub = AudioSegment.from_file(in_bytes_io)
        trimmed_dub = dub[(clip_start_time - audio_start_time)
                          * 1000:(clip_end_time - audio_start_time)*1000]
        output = BytesIO()
        trimmed_dub.export(output, format="wav")
        output.seek(0)
        return output.read()
