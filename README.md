# so-vits-SVC Plugin for TuneFlow

[简体中文](./README.zh.md) | [English](./README.md)

## Clone Repo

```bash
git clone https://github.com/tuneflow/so-vits-svc-plugin.git
```

## Installation

It is recommended to install through python virtual environments, so that these dependencies won't conflict with your existing pip packages.

```bash
pip install -r requirements.txt
```

In addition, you need `ffmpeg` to convert non-wave audio files to wave for the model to process. To install `ffmpeg`, follow the instruction [here (windows)](https://phoenixnap.com/kb/ffmpeg-windows) or [here (ubuntu)](https://phoenixnap.com/kb/install-ffmpeg-ubuntu) or [here (macOS)](https://phoenixnap.com/kb/ffmpeg-mac).

## Run the Plugin

Once you installed the dependencies and prepared the models, you can start running the plugin using:

```bash
python local_plugin.py
```

You should see something like this in your console log:

```bash
============= Plugin Info =============
Provider ID: andantei
Provider Name: Andantei
Plugin ID: singing-voice-clone-local
Plugin Name: Singing Voice Clone (Local)
Plugin Description: Sing a vocal clip with a new voice
=======================================
```

Next, start TuneFlow Desktop, if you don't have it already, download from the homepage [https://tuneflow.com](https://tuneflow.com).

Create an empty song, or open an existing song.

Once the project is loaded, switch to the TuneFlow Plugin Library, at the top right corner, click on the "Load a local plugin in debug mode" button. If everything is setup correctly our plugin should load successfully and show up in the plugin inventory.

![Load local debug plugin](./images/load_plugin_en.jpg)

To run the plugin, right click on a vocal clip, in the run plugins menu, select this plugin.
