<div align="center" markdown>

# From supervisely to Yolo5 format


<p align="center">

  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/remote-import)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/remote-import&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/remote-import&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/remote-import&counter=runs&label=runs&123)](https://supervise.ly)

</div>

## Overview

Transform project to YOLO v5 format and prepares download tar archive.

**YOLO v5 format** contain:

Configuration file(config_file_name.yaml) that defines:
1) a path to a directory of training images,
2) the same for our validation images, 
3) the number of classes, 
4) a list of class names

Example:

train: /alex_data/sl/images/train/

val: /alex_data/sl/images/val/

nc: 2

names: ['lemon', 'kiwi']

Structure of train and val images and labels according to the example below:
<img src="https://user-images.githubusercontent.com/26833433/83666389-bab4d980-a581-11ea-898b-b25471d37b83.jpg"/>

YOLOv5 locates label for each image

Example:

coco/images/train2017/000000109622.jpg  # image,

coco/labels/train2017/000000109622.txt  # label.


Structure of label file:
1) One row per object
2) Each row is class x_center y_center width height format.
3) Box coordinates must be in normalized xywh format (from 0 - 1).
4) Class numbers are zero-indexed (start from 0).

<img src="https://user-images.githubusercontent.com/26833433/91506361-c7965000-e886-11ea-8291-c72b98c25eec.jpg"/>

The label file corresponding to the above image contains 2 persons (class 0) and a tie (class 27):
<img src="https://user-images.githubusercontent.com/26833433/98809572-0bc4d580-241e-11eb-844e-eee756f878c2.png"/>


## Preparation

Download or create project in supervisely format you want to convert.

## How To Run 
**Step 1**: Add app to your team from Ecosystem if it is not there.

**Step 2**: Go to `Plugins & Apps` section in current team. And press `Run` button in front of application.

**Note**: Running procedure is simialr for almost all apps that are started from context menu. Example steps with screenshots are [here in how-to-run section](https://github.com/supervisely-ecosystem/merge-classes#how-to-run). 


## How to use

1. Check project you want to convert to yolo5 format.

2. Click three point on project and choise "Download as" option.

3. In popup menu choise "Convert Supervisely into YOLO v5 format".

<img src="https://i.imgur.com/ZTYhihF.png"/>

4. Open "files" menu. Here in directory "yolov5_format" you can find tar archive with project in YOLOv5 format.

<img src="https://i.imgur.com/pu9snon.png"/>



