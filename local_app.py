from local_plugin import SingingVoiceCloneLocal
from tuneflow_devkit import Runner
from pathlib import Path
import uvicorn

if __name__ == "__main__":
    app = Runner(
        plugin_class_list=[SingingVoiceCloneLocal],
        bundle_file_path=str(Path(__file__).parent.joinpath('bundle_local.json').absolute())).start(
        path_prefix='/plugins/singing-voice-clone-local',
        config={
            "corsConfig":
                {"allowedOrigins": ["https://www.tuneflow.com", "https://tuneflow.com", "https://staging.tuneflow.com", "http://127.0.0.1:5173"],
                 "addAllowCredentialsHeader": True}})
    uvicorn.run(app)