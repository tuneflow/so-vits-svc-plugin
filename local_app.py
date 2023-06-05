from local_plugin import SingingVoiceCloneLocal
from tuneflow_devkit import Runner
from pathlib import Path
import uvicorn
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()

    app = Runner(
        plugin_class_list=[SingingVoiceCloneLocal],
        bundle_file_path=str(Path(__file__).parent.joinpath('bundle_local.json').absolute())).start(
        path_prefix='/plugins/singing-voice-clone-local',
        config={
            "corsConfig":
                {"allowedOrigins": ["https://www.tuneflow.com", "https://tuneflow.com"],
                 "addAllowCredentialsHeader": True}})
    uvicorn.run(app, port=args.port)
