# so-vits-SVC Plugin for TuneFlow

[简体中文](./README.zh.md) | [English](./README.md)

## Clone Repo

```bash
git clone https://github.com/tuneflow/so-vits-svc-plugin_local.git
```

## Installation

It is recommended to install through python virtual environments, so that these dependencies won't conflict with your existing pip packages.

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements_win.txt # on windows system
```

## Prepare Models

Models should be placed under "models" folder in the following structure as following:

```
-- so-vits-svc-plugin_local
    ......
    -- models
        -- my_model_1
            -- config.json
            -- G_20000.pth
            -- G_40000.pth
            -- kmeans_1000.pt
        -- another_model
            -- config.json
            -- G_40000.pth
            -- kmeans_10000.pt
        -- third_model
            -- config.json
            -- G_30000.pth
    ......
```

Each model has to be accompanied by a json file called `config.json`. Once you placed the models, create a new field called `model_spec` specify the model name, cluster name, and model branch name you are using.
It is by default that the model with HIGHEST STEPS will be choosen if no model name was specified. By default, 

For the structure above, suppose we are choosing `my_model_1`. If we would like to customize the cluster and model branch, we should set the `config.json` under `my_model_1` like this:

```json
[
    ..., 
    "model_spec": {
        "cluster_name": "kmeans_1000.pt",
        "model_branch": "v1"
    }
]
```
In this case, since there is no "model_name" in the json, the mode trained with the highest steps (G_40000.pth) will be choosen. Then, it will choose the cluster name "kmeans_1000.pt" and model branch "v1". 

However, if parameters goes like below, the inferencer will choose model G_20000.pth as specified in the config file.
```json
[
    ..., 
    "model_spec": {
        "cluster_name": "kmeans_1000.pt",
        "model_branch": "v1",
        "model_name": "G_20000.pth"
    }
]
```
## Run the Plugin

Once you installed the dependencies and prepared the models, you can start running the plugin using:

```bash
python debug.py
```

You should see something like this in your console log:

```bash
============= Plugin Info =============
Provider ID: andantei, dreamflyfreya
Provider Name: Andantei, ruijie
Plugin ID: singing-voice-clone_local
Plugin Name: Singing Voice Clone Local
Plugin Description: Sing a vocal clip with a new voice
=======================================
```

Next, start TuneFlow Desktop, if you don't have it already, download from the homepage [https://tuneflow.com](https://tuneflow.com).

Create an empty song, or open an existing song.

Once the project is loaded, switch to the TuneFlow Plugin Library, at the top right corner, click on the "Load a local plugin in debug mode" button. If everything is setup correctly our plugin should load successfully and show up in the plugin inventory.

![Load local debug plugin](./images/load_plugin_en.jpg)

To run the plugin, right click on a vocal clip, in the run plugins menu, select this plugin.
