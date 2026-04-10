# FloatSlider - 悬浮图片轮播工具

一个简洁的 Windows 悬浮图片轮播工具，支持高 DPI 显示器、图片自动填充、多种动画效果。

## 功能特性

- **高 DPI 支持** - 完美支持 4K 显示器、150%/125% 等缩放比例，图片显示清晰
- **图片自动填充** - 图片自动填充整个窗口，比例不匹配时自动从中心裁剪
- **窗口自由缩放** - 拖动右下角自由调整窗口大小，图片自动适应
- **置顶悬浮** - 窗口始终保持在其他窗口上方
- **多种动画** - 5 种随机切换动画效果（淡入淡出、左右滑动、上下滑动、缩放）
- **随机/顺序播放** - 支持随机播放和顺序播放两种模式
- **开机自启** - 可设置开机自动启动

## 界面操作

|操作|说明|
|---|---|
|右键菜单|选择图片文件夹、设置轮播间隔、置顶开关、随机/顺序播放、开机自启|
|拖动窗口|鼠标左键拖动窗口|
|缩放窗口|拖动窗口右下角缩放|

## 安装运行

### 方式一：直接运行源码

1.安装 Python 3.8+（建议 Python 3.10 或更高版本）

2.安装依赖：

bash

```bash
pip install -r requirements.txt
```

1.运行程序：

bash

```bash
python FloatSlide.py

```

### 方式二：下载已独立打包的EXE（单文件，体积较大）



### 方式三：使用 PyInstaller 打包成 EXE

#### 步骤 1：安装打包工具

bash

```bash
pip install pyinstaller
```

#### 步骤 2：打包命令

**推荐命令（无控制台窗口）：**

bash

```bash
pyinstaller --onedir --windowed --name "FloatSlider" --icon="app.ico" FloatSlide.py
```

**参数说明：**

|参数|说明|
|---|---|
|`--onedir`|生成文件夹形式的打包（包含多个文件）|
|`--onefile`|生成单个 EXE 文件（体积较大）|
|`--windowed` 或 `-w`|不显示控制台窗口（GUI 程序推荐）|
|`--name`|指定生成的程序名称|
|`--icon`|指定程序图标（可选，需要 .ico 格式）|

#### 步骤 3：运行打包后的程序

打包完成后，EXE 文件位于：

- `dist/FloatSlide/FloatSlide.exe`（使用 `--onedir` 时）
- `dist/FloatSlide.exe`（使用 `--onefile` 时）

双击运行即可。

### 常见打包问题

**Q: 打包后运行提示缺少 DLL？**  
A: 确保在打包电脑上已安装 Visual C++ Redistributable。

**Q: 打包后图标不显示？**  
A: 确保使用 256x256 像素的 .ico 格式图标文件。

**Q: 如何去除命令行窗口？**  
A: 使用 `--windowed` 或 `-w` 参数。

## 目录结构

```
FloatSlide/
├── FloatSlide.py      # 主程序
├── requirements.txt   # Python 依赖
├── README.md          # 说明文档
├── dist/              # 打包输出目录（打包后生成）
└── build/             # 打包临时目录（打包后生成）
```

## 系统要求

- Windows 10/11
- Python 3.8+ 或打包后的 EXE（无需 Python 环境）

## 许可证

MIT License
