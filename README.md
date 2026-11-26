# Paper to Slides

**简体中文** · [English](README.en.md)

把研究论文整理成适合组会、论文讨论班或 Journal Club 的技术汇报。可以从论文制作 Beamer 幻灯片、从参考 PPTX 定制可复用的 LaTeX 模板，或把现有幻灯片 PDF 导出为带演讲者备注的 PowerPoint。[查看默认 16:9 Beamer 模板预览](template/template.pdf)

## 快速开始：在 Agent 中使用

在支持的客户端中打开**本仓库根目录**，无需将命令安装到用户主目录。在 Claude Code、Antigravity 和 OpenCode 使用下表中的 `/命令名`；在 Codex 输入 `$` 并选择同名 Skill，例如 `$slides-init "projects/my-talk"`。

| 命令 | 示例或用途 |
| --- | --- |
| `/paper-to-slides` | `/paper-to-slides "paper.pdf" --project "projects/my-talk"`：先确认逐页大纲，再制作 LaTeX 和 PDF。 |
| `/pptx-to-template` | `/pptx-to-template "reference.pptx" --project "projects/my-template"`：确认版式与素材后生成模板。 |
| `/pdf-to-pptx` | `/pdf-to-pptx "my-slides.pdf" --notes "speaker-notes.md"`：保留原页序并导出原生备注。 |
| `/slides-init` | `/slides-init "projects/my-talk"`：初始化项目。 |
| `/slides-import` | `/slides-import "projects/my-talk" --manuscript "paper.pdf"`：归档资料。 |
| `/slides-build` | `/slides-build "projects/my-talk"`：重新编译现有 LaTeX。 |
| `/slides-check` | `/slides-check "projects/my-talk" --mode pdf`：检查 PDF 构建；也可用 `evidence` 或 `both`。 |
| `/pdf-crop` | `/pdf-crop "paper.pdf" --page 7 --output "page-07.png"`：渲染整页，或用 `--crop` 裁图。 |
| `/slides-status` | `/slides-status "projects/my-talk"`：查看已有文件和产物。 |
| `/slides-clean` | `/slides-clean "projects/my-talk"`：清理构建产物和失败诊断。 |
| `/slides-delete` | `/slides-delete "projects/my-talk"`：确认后删除整个项目。 |

详见[命令参数与客户端用法](references/agent-commands.md)。也可在仓库根目录运行下文的 Python 命令；逐页大纲、LaTeX 内容和讲稿由汇报者或 Agent 编写。

## 环境准备

| 用途 | 依赖 |
| --- | --- |
| 运行脚本 | Python 3.11 或更新版本 |
| 索引、渲染和检查 PDF | PyMuPDF |
| 从 PPTX 盘点版式、提取确认过的原图 | python-pptx；建议另提供 PowerPoint 导出的 PDF 供视觉核对 |
| 编译 Beamer PDF | `latexmk`、`xelatex`，以及 Beamer、xeCJK、unicode-math 和 TikZ |
| 导出 PPTX | PyMuPDF、python-pptx。默认 SVG 导出另需 Poppler 的 `pdftocairo` |

```sh
python -m pip install pymupdf python-pptx
python --version
latexmk -v
xelatex --version
pdftocairo -v
```

将所需工具放入 `PATH`。如果只把已有 PDF 导出为 PPTX，可以跳过 TeX 环境。模板优先使用 Times New Roman 排版拉丁文字，使用 SimSun（宋体）排版中文正文，使用 SimHei（黑体）排版封面中文。相应字体缺失时，会使用 TeX Gyre Termes 或 Fandol，并在编译日志中记录。

## 从论文开始

### 1. 创建项目并归档资料

把原始 PDF 放在项目工作目录之外，例如仓库根目录的 `paper.pdf`，或在命令中传入其绝对路径。项目路径需要尚未创建或为空。

```sh
python scripts/project_manager.py init "projects/my-talk"
python scripts/project_manager.py import-sources "projects/my-talk" --manuscript "paper.pdf"
python scripts/project_manager.py status "projects/my-talk"
```

`import-sources` 会将资料复制到项目的 `sources/`，原件仍位于传入的路径。它同时记录 SHA-256 并为 PDF 生成逐页文本索引。工作时将 `sources/` 视为只读归档，公式、图表和识别不清的内容以归档 PDF 的页面为准。需要裁图或改写时，将衍生文件写到 `source-review/` 或 `slides/figures/`。

`--manuscript` 还支持直接 PDF URL、arXiv 摘要页、OpenReview forum 链接和本地 TeX 入口。用 `--paper-url` 记录官方入口，`--version` 记录已核对的版本，`--notes` 导入阅读笔记，`--supplement` 可重复传入补充资料。完整 TeX 工程用 `--tex-root` 保留文件间的相对路径。将同一批资料一次导入，需要使用另一版论文时创建独立项目。[资料准备与裁图](references/source-preparation.md)

### 2. 写逐页大纲并核对证据

在项目根目录创建 `outline.md`，记录论文版本、听众、汇报目标，以及每页的页顶章节标题、正文标题、内容和证据位置。主讲按「主要问题 → 论文贡献 → 前置知识 → 论文方案 → 实验 → 总结与讨论」展开。

- 同一章节复用页顶标题，正文标题说明该页的概念、流程步骤或实验比较。论文贡献集中在一页。
- 方案从总流程图开始，后续按图中的步骤展开，将关键公式、推导和例子放到对应步骤。补充技术细节放在正文中用到它的地方。
- 实验先交代数据集、设置、指标和基线，再说明数值及证据适用范围。将来源、作者与会议归属等图表出处记录在大纲或 TeX 注释中，投影保留读图所需的坐标、单位和图例。
- 总结与讨论用一个正文标题和一段文字，先写论文完成了什么、证据支持什么，再写一项可开展的后续工作。

每页使用 `### S01 标题` 这样的唯一 ID，并在对应小节内为报告值、公式和关键结论附上具体位置，例如 `[式 (2)](sources/manuscript/original/paper.pdf#page=3)`。其中 `page` 从 PDF 的第一页开始计数。无实质论断的封面或纯演示页可按[证据指南](references/evidence-review.md)注明例外及原因。

```sh
python scripts/check_evidence.py "projects/my-talk"
```

此命令检查归档指纹、链接和页码范围。数据、公式与结论仍应逐一对照论文。汇报者构造的手算例子要明确标记，并限定由实验支持的结论。使用 Agent 制作新汇报时，须按 [Skill 工作流](SKILL.md) 明确批准大纲后才进入制作。[证据核对与讨论指南](references/evidence-review.md)

### 3. 编译并检查 PDF

将 [`template/template.tex`](template/template.tex) 和 [`template/template.sty`](template/template.sty) 复制到 `slides/`，并将前者命名为 `main.tex`。以核对过的内容替换模板教学页，用相对路径引用本项目中的图和样式。

```sh
python scripts/project_manager.py approve-outline "projects/my-talk" --yes
python scripts/build_pdf.py build "projects/my-talk"
python scripts/build_pdf.py check "projects/my-talk"
```

`build` 通过 `latexmk` 调用 XeLaTeX，检查编译日志和 PDF，并生成逐页预览。通过检查的 PDF 写到 `build/main.pdf`。`check` 复核已编译的文件，并检查 `slides/` 是否在编译后被修改。修改 LaTeX 或图表后，重新执行 `build`。

只在明确批准当前大纲后执行 `approve-outline --yes`；修改大纲后须重新批准。先读 `build/check.json`，再逐页查看 `build/pages/`。公式与图表的裁切、重叠和投影可读性需要结合预览核对。编译或自动检查失败时，查看 `build-failed/check.json` 和可用的日志；上一版 `build/` 保留。成功重建才替换 `build/`，此前导出的 PPTX 需要重新生成。项目模式导出要求构建与当前源码及获批大纲一致；旧项目需记录审批并重建一次。

## 从参考 PPTX 定制模板

使用 `/pptx-to-template`（Codex：`$pptx-to-template`）后，Agent 先盘点实际页码、版式、母版和可选对象，再分轮询问：

1. **整体布局**：页面比例、留白、字体、配色、标题和页脚。
2. **各阶段版式**：封面、方法、实验等阶段用哪些代表页作为参考，示例中保留哪些可替换区域。
3. **素材复用**：逐项选择按样式重建、复用指定原件，或使用占位／省略，并确认原件的使用范围。

确认设计单后才生成 `slides/main.tex`、本地主题和 PDF 预览。选择参考页不会自动复制原页内容。只做模板不需要论文；模板可以脱离原 PPTX 编译。脚本支持提取选中的嵌入式 PNG/JPEG；复杂图表或矢量素材可能需要手工处理。盘点、选择性提取和生成模板的命令见 [PPTX 模板工作流](references/pptx-template.md)。

## 导出带原生备注的 PowerPoint

按最终 PDF 的物理页序编写 UTF-8 的 `speaker-notes.md`。用 `## 1`、`## 2` 等连续标题，每页对应一段或多段讲稿，封面和 Beamer 动画生成的独立 PDF 页也计入。备注写成可直接讲述的话，将论文的精确证据位置留在大纲或 TeX 注释中。

```markdown
## 1
今天讨论一个具体问题：客户端的低秩更新合并时，什么条件下会出现聚合误差？

## 2
先看两组因子分别求平均的步骤。把两个均值相乘后，会出现跨客户端的配对项。
```

**管理项目**。从 `build/main.pdf` 和项目根目录的 `speaker-notes.md` 生成 `build/main.pptx`。

```sh
python scripts/export_pptx.py "projects/my-talk"
```

**已有幻灯片 PDF**。适用于手工调整 LaTeX 并重新生成 PDF 后，也适用于其他来源的幻灯片 PDF。

```sh
python scripts/export_pptx.py "my-slides.pdf" --notes "speaker-notes.md" --output "my-slides.pptx"
```

默认每页嵌入一张 SVG，PDF 中的文字、公式和矢量图形保留为可缩放路径。投影内容是一张图，编辑版式或正文请修改 LaTeX；备注可在 PowerPoint 中编辑。兼容用的备用 PNG 采用无损压缩，默认长边 3840 像素，16:9 页面为 3840 × 2160。纯 PNG 导出可用下面的命令。

```sh
python scripts/export_pptx.py "my-slides.pdf" --notes "speaker-notes.md" --format png --png-long-edge 3840 --output "my-slides-png.pptx"
```

导出脚本会复核页数、图片、位置、SVG 引用及备注在 PPTX 中的对应关系。交付前对照 PDF 放大检查公式和裁图，并在目标查看器里检查放映效果。PDF 页序变化时同步调整备注，再运行导出。只修改备注时，直接重新导出即可。[PPTX 导出指南](references/pptx-export.md)

## 项目目录与清理

```text
projects/my-talk/
├── .paper-to-slides          项目管理标记
├── sources/                  论文、笔记和补充资料的归档及 manifest.json
├── template-source/          模板项目的参考 PPTX 归档和盘点
├── template-spec.json        模板项目可选的生成配置
├── outline.md                逐页大纲和证据位置，或模板设计单
├── speaker-notes.md          逐页演讲者讲稿
├── source-review/            可选的原文核对截图
├── slides/
│   ├── main.tex              Beamer 入口
│   ├── *.sty                本地主题
│   └── figures/             幻灯片用图
└── build/
    ├── main.pdf              通过自动检查的 PDF
    ├── main.pptx             按需导出的 PowerPoint
    ├── check.json            自动检查报告
    ├── compile.log           latexmk 输出
    ├── latex/                编译中间文件和 XeLaTeX 日志
    └── pages/                逐页预览
```

只清理生成产物时运行 `clean`。确定要删除整个本地项目及其资料归档、大纲、幻灯片源码和备注时，再运行 `delete --yes`。

```sh
python scripts/project_manager.py clean "projects/my-talk"
python scripts/project_manager.py delete "projects/my-talk" --yes
```

`projects/` 由 Git 忽略，用于在本机保存论文和汇报产物。需要交付时，可单独分享 PDF、PPTX、备注文件以及含本地图和样式的 LaTeX 源文件。[项目管理与检查流程](references/project-workflow.md)
