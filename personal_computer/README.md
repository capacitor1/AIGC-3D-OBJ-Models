# NXV ATX 程序化 3D 主机模型

一个完全由 Python 脚本生成的 ATX 台式主机模型，包含**开侧板**与**关侧板**两套 OBJ，以及可单独导入的 34 个部件。模型不含贴图，全部使用 MTL 材质与几何细节（冲网、散热鳍片、风扇叶片、线缆、螺丝、发光条等）。

## 交付文件

| 文件 | 说明 |
|---|---|
| `desktop_pc_open.obj` | 开侧板总装，约 7.5 MB，33 个对象组 |
| `desktop_pc_closed.obj` | 关侧板总装，约 7.6 MB，34 个对象组（多 `side_panel_glass`） |
| `desktop_pc.mtl` | 全部材质定义（颜色、透明度、自发光） |
| `components/*.obj` | 34 个独立部件，便于替换/隐藏/单独编辑 |
| `assembly.json` | 装配清单（部件、包围盒、三角面数） |
| `render/*.png` | 6 个角度的 1400×1000 预览图 |
| `render/contact_sheet.png` | 六视图拼版（2100×1122） |
| `render/contact_sheet_preview.jpg` | 拼版压缩预览 |
| `render/viewer.html` | Three.js 实时查看器（支持开/关侧板与视角预设） |
| `shot.js` | 无头浏览器截图脚本 |

## 模型规格

- **单位**：毫米（mm）
- **尺寸**：关侧板约 **235.6 × 479.3 × 465.9 mm**（宽×高×深）；开侧板宽 232 mm
- **三角面**：约 **19 万**（开/关总装略有差异）
- **坐标**：`+Y` 向上，`+Z` 为机箱前面板，`-X` 为可拆卸侧板方向
- **侧板**：`desktop_pc_closed.obj` 中的 `o side_panel_glass` 是独立对象，可直接隐藏/删除得到开侧板状态；`desktop_pc_open.obj` 已省略该对象
- **材质**：无外部贴图；`rgb_cyan`、`rgb_blue`、`rgb_magenta`、`rgb_white`、`rgb_lime` 在 MTL 中带 `Ke` 自发光；`glass` 的 `d=0.26`，部分查看器需开启 alpha blending
- **文字**：全部转换为网格，不依赖系统字体

## 主要部件

- **机箱**：`case_frame`、`right_panel`、`front_panel`、`top_panel`、`rear_panel`、`feet`、`front_io`、`side_panel_glass`
- **主板/CPU**：`motherboard`、`cpu`
- **显卡**：`gpu`、`gpu_support`、`gpu_fan_1..3`
- **散热**：`aio_fan_1..3`、`rear_fan`、`top_fan_1..2`、`aio_pump`、`aio_radiator`、`aio_tube_1..2`
- **电源/存储**：`psu`、`ssd_2_5`、`hdd_3_5`
- **线缆**：`cable_24pin`、`cable_eps`、`cable_gpu`、`cable_sata`、`cable_front_panel`、`cable_aio`

## 重新生成

```bash
cd personal_computer
python assemble.py
```

`assemble.py` 会调用各 `build_*.py`，重新生成 `components/`、`desktop_pc_open.obj`、`desktop_pc_closed.obj`、`desktop_pc.mtl` 与 `assembly.json`。

依赖：

```bash
pip install -r requirements.txt
```

## 预览与截图

启动本地静态服务器（在 `personal_computer` 目录）：

```bash
python -m http.server 8123
```

浏览器打开：

```text
http://127.0.0.1:8123/render/viewer.html?view=frontleft&file=open
```

可用 `view`：`frontleft`、`side`、`top`、`rear`、`gpu`、`low`、`closed`；`file`：`open` 或 `closed`。

无头截图：

```bash
node shot.js frontleft open render/frontleft.png 1400 1000
node shot.js closed closed render/closed.png 1400 1000
```

## 预览图

- `render/frontleft.png` — 开侧板前左 3/4
- `render/side.png` — 开侧板正侧
- `render/top.png` — 顶部双风扇与前面板
- `render/rear.png` — 后部 I/O、显卡挡板、电源
- `render/gpu.png` — 显卡/电源/存储细节
- `render/closed.png` — 关侧板玻璃效果
- `render/contact_sheet.png` — 六视图拼版

## 备注

- 模型面向视觉展示与游戏/影视场景，内部结构为艺术化简化，不是可制造的工程图。
- 若导入器不识别 MTL 的 `Ke`，请手动把 `rgb_*` 材质设为自发光，或使用查看器中的材质转换逻辑。
- 玻璃在部分软件中可能显示为不透明；请将 `glass` 材质设为 alpha blend，或直接隐藏 `side_panel_glass`。
