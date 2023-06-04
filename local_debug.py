from local_plugin import SingingVoiceCloneLocal
from tuneflow_devkit import Debugger
from pathlib import Path

if __name__ == "__main__":
    Debugger(plugin_class=SingingVoiceCloneLocal, bundle_file_path=str(
        Path(__file__).parent.joinpath('bundle_local.json').absolute())).start()
