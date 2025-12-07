# 🚀 ExifLensSetter.py (Standalone Exif Writer)

## 📝 概要

本アプリは、**オールドレンズなど電子接点を持たないレンズのExif情報（レンズ名、F値など）をJpegなどの写真ファイル一括で書き込むための簡易ツール**です。

コードは基本的にすべてGoogle Geminiを使用して作成しました。

動作確認はWindows11でのみ行っています。

* GUI操作
* ドラッグ＆ドロップ対応。
* レンズ情報の**プリセット保存**機能。

## 🛠️ インストールと準備

### 1. 必須ツール

このアプリケーションの動作には、**Python3.6以上**と**ExifTool**が別途必須です。

* Python3.6以上を別途インストールして下さい。
* ExifToolをダウンロードし、**exiftool.exe**をpathが通ったフォルダか**ExifLensSetter.py**と同じフォルダに配置して下さい。

### 2. 必要なPythonライブラリ

以下のライブラリを事前にインストールして下さい。

* **customtkinter**
* **tkinterdnd2**

```
py -m pip install customtkinter tkinterdnd2
```

## 🖥️ 実行方法

**ExifLensSetter.py**をダブルクリックするか、コマンドから実行して下さい。

```
py ExifLensSetter.py
```

## 📄ライセンス

本コード ExifLensSetter.py は、MITライセンスのもとで公開されます。

Copyright (c) 2025 QQK / QuunQuickKick

本コードは、以下のライブラリを利用しています。

* customtkinter, tkinterdnd2: MIT License
* ExifTool (外部ツール): Artistic License 1.0 に基づいて配布されています。
