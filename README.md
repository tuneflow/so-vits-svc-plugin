# so-vits-SVC Plugin for TuneFlow

[简体中文](./README.zh.md) | [English](./README.md)

## Clone Repo

```bash
git clone https://github.com/tuneflow/so-vits-svc-plugin.git
```

## Installation

### (Option 1) Download Pre-Built Release

You can also download a prebuilt package with all dependencies included, from the below links:

[Download for Windows](https://plugin-dist.tuneflow.com/plugins/svc/binary/win-x64-1.0.0.zip)

[Download for macOS (Coming Soon)](#)

### (Option 2) Build from Source

It is recommended to install through python virtual environments, so that these dependencies won't conflict with your existing pip packages.

```bash
pip install -r requirements.txt
```

In addition, you need `ffmpeg` to convert non-wave audio files to wave for the model to process. To install `ffmpeg`, follow the instruction [here (windows)](https://phoenixnap.com/kb/ffmpeg-windows) or [here (ubuntu)](https://phoenixnap.com/kb/install-ffmpeg-ubuntu) or [here (macOS)](https://phoenixnap.com/kb/ffmpeg-mac).


Lastly, you need to use `pyinstaller` to bundle your app into an .exe file that can be called by the TuneFlow Desktop app.

## (Optional) Automatically Load Models

If you want the plugin to load models on start up, you can optionally place your model file(.pth) and config file(config.json) under `checkpoints` folder.

The folder structure would look like this:

```
-- <root folder of the project>
    -- ......
    -- checkpoints
        -- G_XXX.pth
        -- config.json
    -- ......
```

## Run the Plugin

Start TuneFlow Desktop, if you don't have it already, download from the homepage [https://tuneflow.com](https://tuneflow.com).

Create an empty song, or open an existing song.

Once the project is loaded, right click on an audio clip and run the "Smart Vocal Changer (Local Beta)" plugin. When it is running for the first time, you need to locate the plugin folder and hit the load plugin button.

Then, you can run the plugin as how you would use it like any other plugins. Note that the plugin needs some time to start running at its first run, please be patient while waiting.
