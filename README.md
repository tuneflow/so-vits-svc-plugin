# so-vits-SVC Plugin for TuneFlow

[简体中文](./README.zh.md) | [English](./README.md)

## Installation

It is recommended to install through python virtual environments, so that these dependencies won't conflict with your existing pip packages.

```bash
pip install -r requirements.txt
```

## Prepare Models

Models are placed under the `checkpoints` folder, here is an example folder structure:

```
-- svc-plugin
    ......
    -- checkpoints
        -- my_model_1
            -- config.json
            -- G_20000.pth
            -- kmeans_1000.pt
        -- another_model
            -- another_config.json
            -- G_40000.pth
            -- kmeans_10000.pt
        -- third_model
            -- some_config.json
            -- G_30000.pth
    ......
```

Once you placed the models, create a `models.json` file under the plugin root directory. The json file contains a list of model specs, each entry contains the following fields:

- `id` model id, any unique string you like
- `name` to be displayed in the UI
- `dir` model folder name, under `checkpoints` folder
- `config` config file path, relative to the model folder.
- `model` model file path, relative to the model folder.
- `cluster` (Optional) cluster file path relative to the model folder. (Ignore if there is no cluster file)
- `cluster_name` (Optional) cluster name (something like kmeans_10000.pt) (Ignore if there is no cluster file or you don't want to enable cluster)
- `model_branch` (Optional) model branch name (Using "v1" if nothing is provided)
- `hifigan_enhance` (Optional) whether to enable hifigan to enhance the model, suitable for small datasets (Using false if nothing is provided)

For the structure above, we should have a `models.json` like this:

```json
[
    {
        "id": "model_1",
        "name": "Pop Star",
        "dir": "my_model_1",
        "config": "config.json",
        "model": "G_20000.pth",
        "cluster": "kmeans_1000.pt"
    },
    {
        "id": "model_2",
        "name": "Rock Singer",
        "dir": "another_model",
        "config": "another_config.json",
        "model": "G_40000.pth",
        "cluster": "kmeans_10000.pt"
    },
    {
        "id": "model_3",
        "name": "Jazz Voice",
        "dir": "third_model",
        "config": "some_config.json",
        "model": "G_30000.pth"
    }
]
```
and the directory structure becomes like this:

```
-- svc-plugin
    ......
    -- models.json
    -- checkpoints
        -- my_model_1
            -- config.json
            -- G_20000.pth
            -- kmeans_1000.pt
        -- another_model
            -- another_config.json
            -- G_40000.pth
            -- kmeans_10000.pt
        -- third_model
            -- some_config.json
            -- G_30000.pth
    ......
```

## Run the Plugin

Once you installed the dependencies and prepared the models, you can start running the plugin using:

```bash
python debug.py
```

You should see something like this in your console log:

```bash
============= Plugin Info =============
Provider ID: andantei
Provider Name: Andantei
Plugin ID: singing-voice-clone
Plugin Name: Singing Voice Clone
Plugin Description: Sing a vocal clip with a new voice
=======================================
```

Next, start TuneFlow Desktop, if you don't have it already, download from the homepage [https://tuneflow.com](https://tuneflow.com).

Create an empty song, or open an existing song.

Once the project is loaded, switch to the TuneFlow Plugin Library, at the top right corner, click on the "Load a local plugin in debug mode" button. If everything is setup correctly our plugin should load successfully and show up in the plugin inventory.

![Load local debug plugin](./images/load_plugin_en.jpg)

To run the plugin, right click on a vocal clip, in the run plugins menu, select this plugin.
