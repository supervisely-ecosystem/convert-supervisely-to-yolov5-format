<div align="center" markdown>
<img src="https://i.imgur.com/QO4GtA1.png"/>

# From supervisely to Yolo5 format


<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Preparation">Preparation</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#How-To-Use">How To Use</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/convert-supervisely-to-yolov5-format)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/convert-supervisely-to-yolov5-format&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/convert-supervisely-to-yolov5-format&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/convert-supervisely-to-yolov5-format&counter=runs&label=runs&123)](https://supervise.ly)

</div>

## Overview

Transform project to YOLO v5 format and prepares download tar archive.

**YOLO v5 [format](https://github.com/ultralytics/yolov5/wiki/Train-Custom-Data)** you can find here.

**Supervisely [format](https://docs.supervise.ly/data-organization/00_ann_format_navi)** you can find here.




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



