from plugin import SingingVoiceClone
from tuneflow_devkit import Debugger
from pathlib import Path

if __name__ == "__main__":
    Debugger(plugin_class=SingingVoiceClone, bundle_file_path=str(
        Path(__file__).parent.joinpath('bundle.json').absolute())).start()
