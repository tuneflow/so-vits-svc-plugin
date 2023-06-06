# so-vits-SVC TuneFlow 插件

[简体中文](./README.zh.md) | [English](./README.md)

## 下载代码

```bash
git clone https://github.com/tuneflow/so-vits-svc-plugin.git
```

## 安装

### （选项1）使用整合好的压缩包

首先下载安装包：

[Windows下载](https://plugin-dist.tuneflow.com/plugins/svc/binary/win-x64-1.0.0.zip)

[macOS下载(即将推出)](#)

随后解压下载好的安装包，其中的`local_app.exe`即为插件运行程序。

### （选项2）从源代码安装

注意：安装 python 依赖包时推荐使用 virtualenv，这样可以将插件所需依赖与系统其他依赖分离开来。

```bash
pip install -r requirements.txt
```

除此之外，你还需要安装`ffmpeg`来将输入的音频转化成模型接受的输入格式。参考 [这里 (Windows)](https://zhuanlan.zhihu.com/p/118362010)， [这里 (Linux)](https://cloud.tencent.com/developer/article/1711770)，或 [这里 (macOS)](https://www.jianshu.com/p/f6990aee6c7f) 的安装教程。

最后，你需要用pyinstaller将local_app.py打包为local_app.exe，以便TuneFlow桌面版调用。

## (选做) 自动加载模型文件

如果你想每次运行插件时都自动加载模型，你可以把模型和配置文件放到`checkpoints`目录下，这样整个目录结构看起来是这样的：

```
-- <项目根目录>
    -- ......
    -- checkpoints
        -- G_XXX.pth
        -- config.json
    -- ......
```

该方法对于两种安装方式都适用。

## 训练自己的模型

参考 [炼丹百科全书](https://docs.qq.com/doc/DUWdxS1ZaV29vZnlV)，有非常易用的网页版训练界面。

## 运行插件

启动 TuneFlow 桌面版。如果你还没有下载的话，可以从 TuneFlow 首页下载： [https://tuneflow.com](https://tuneflow.com)。

打开桌面版后，我们可以创建一首空白曲目，或者打开一首已有的曲子。

在需要转换的音频片段上右键，在运行插件菜单中选择智能变声器本地版（测试）插件。第一次运行时会让你选择插件目录，这里选择你下载后解压的，或者从头构建的插件目录。

这样，你就可以像任何其他插件一样使用本插件了。注意，插件第一次实际运行的时候需要一定的启动时间，请耐心等待。
