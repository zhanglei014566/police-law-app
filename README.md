# 执法辅助工具

面向公安民警的执法辅助应用，支持关键词搜索法条。

## 功能特性

- 🔍 关键词搜索法条
- 📚 包含4部法律、806条法条
  - 治安管理处罚法（134条）
  - 公安机关办理行政案件程序规定（239条）
  - 公安机关办理刑事案件程序规定（183条）
  - 刑事诉讼法（250条）
- 📱 安卓APP支持

## 下载APK

在 [Releases](../../releases) 页面下载最新的 APK 文件。

## 本地运行

### 桌面版（Tkinter）
```bash
python main_tkinter.py
```

### 桌面版（Kivy）
```bash
pip install kivy
python main_kivy.py
```

### 网页版
```bash
python generate_html.py
# 生成 laws_search.html，用浏览器打开即可
```

## 构建 APK

本项目使用 GitHub Actions 自动构建 APK。推送代码到 main 分支后会自动触发构建。

## 技术栈

- Python 3.10+
- Kivy（安卓打包）
- SQLite（法条存储）
- Buildozer（安卓打包工具）
- GitHub Actions（CI/CD）
