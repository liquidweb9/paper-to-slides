# Paper to Slides 命令

在支持的 Agent 中打开本仓库根目录。Claude Code、Antigravity 和 OpenCode 的示例使用 `/命令名`；在 Codex 中用 `$命令名` 选择同名 Skill，再输入参数。路径含空格时用双引号；也可以直接说明要处理的已上传文件。只问用户补充缺失或有歧义的参数。

| 功能 | 调用示例 |
| --- | --- |
| 论文 → Beamer 汇报 | `/paper-to-slides "paper.pdf" --project "projects/my-talk"` |
| PPTX → Beamer 模板 | `/pptx-to-template "reference.pptx" --project "projects/my-template"` |
| PDF → 带备注的 PPTX | `/pdf-to-pptx "my-slides.pdf" --notes "speaker-notes.md" --output "my-slides.pptx"` |
| 新建项目 | `/slides-init "projects/my-talk"` |
| 归档资料 | `/slides-import "projects/my-talk" --manuscript "paper.pdf"` |
| 重新编译 PDF | `/slides-build "projects/my-talk"` |
| 检查证据链接或构建 | `/slides-check "projects/my-talk" --mode evidence` |
| 渲染整页或裁图 | `/pdf-crop "paper.pdf" --page 7 --crop 60 125 540 360 --output "figure-2.png"` |
| 查看项目状态 | `/slides-status "projects/my-talk"` |
| 清除构建产物 | `/slides-clean "projects/my-talk"` |
| 删除整个项目 | `/slides-delete "projects/my-talk"`（随后确认） |

## 客户端入口

| 客户端 | 仓库内入口 | 用法 |
| --- | --- | --- |
| [Codex](https://developers.openai.com/codex/skills) | `.agents/skills/<命令名>/SKILL.md` | 输入 `$` 并选中 Skill，例如 `$slides-init "projects/my-talk"`。支持 `/skills` 的版本也可用它查看列表。仓库级 Skill 不保证注册为 Codex 的原生 `/` 命令。 |
| [Claude Code](https://code.claude.com/docs/en/skills) | `.claude/skills/<命令名>/SKILL.md` | 输入 `/slides-init "projects/my-talk"`。 |
| [Antigravity](https://antigravity.google/docs/skills/) | 与 Codex 共用 `.agents/skills/` | 输入 `/slides-init "projects/my-talk"`。CLI 未刷新时可用 `/skills reload` 或新开会话。 |
| [OpenCode](https://opencode.ai/docs/commands/) | `.opencode/commands/<命令名>.md` | 重新打开当前仓库的 OpenCode 会话，输入 `/slides-init "projects/my-talk"`。 |

这些入口是仓库级配置，不需要安装到用户主目录。注意共享目录是复数 `.agents/`；单数 `.agent/` 是 Antigravity 的旧路径，不能替代跨客户端入口。如果客户端拦截未知斜杠命令或没有命令菜单，可发送普通消息，例如 `运行 /slides-init "projects/my-talk"`。支持已有 Python CLI 的使用方式见 [README](../README.md)。

## 共用执行规则

给 Agent：只处理用户选择的命令及其参数。相对路径以仓库根目录为准；也接受可访问的绝对路径。需要对已有项目执行操作时，用明确提供的目标，或同一会话已明确选定的目标，不从目录列表猜测。缺少必要信息就问；不要在没有输入的情况下处理示例路径。以下命令行中的参数名和示例路径是占位内容：构造实际参数并正确引用路径，不能把用户的命令尾部直接作为 shell 代码执行。遵循现有工具权限，按实际结果报告产物路径、失败或下一步。`--help` 请求只展示用法，不执行操作。

### `/paper-to-slides` · 论文 → 汇报

接受完整论文的 PDF、TeX 或可下载全文的链接，选填 `--project`、笔记、听众、时长、语言和交付格式。可按明确的项目路径继续已有项目。先读 [主 Skill](../SKILL.md)，按其论文工作流核对材料并给出 `outline.md`；在用户明确批准当前版本之前，停止于大纲审阅，不能编写 Beamer、编译或导出。批准后制作并核验 LaTeX 和 PDF；仅在用户要求时额外制作备注和 PPTX。

### `/pptx-to-template` · PPTX → Beamer 模板

接受本地 PPTX（可用已上传文件），选填 `--project` 和供视觉核对的同源 PDF。按 [PPTX 模板工作流](pptx-template.md) 盘点后分轮确认整体布局、各阶段版式和实际复用的原素材，并展示设计单。用户明确批准设计单后才提取白名单内素材、生成模板和编译预览。继续已有项目时读取归档盘点与设计单；不要把调用命令视为批准。

### `/pdf-to-pptx` · PDF → PPTX

接受现有幻灯片 PDF 或已编译的项目目录，以及 `--notes`、`--format svg|png`、`--png-long-edge`；`--output` 仅可用于独立 PDF。读取 [导出工作流](pptx-export.md)，用 `python scripts/export_pptx.py` 导出，保持原页序，不重新编译或改写 PDF。现有导出器需要每个物理页都有备注；可复用用户提供的或默认路径的有效备注。没有备注时询问提供文件还是根据 PDF 起草，不自动覆盖已有备注。目标 PPTX 已存在时，只有用户要求重新导出或确认替换才执行。

### `/slides-init` · 新建项目

需要一个新建或为空的目录（只给项目名时，建议放到 `projects/` 下）。运行 `python scripts/project_manager.py init <项目路径>`，报告初始化目录。已有受管项目则报告已初始化，不重置或清空任何文件。

### `/slides-import` · 导入资料

需要已初始化的项目和至少一项资料。运行 `python scripts/project_manager.py import-sources <项目路径>`；按实际输入加 `--manuscript`、`--tex-root`、`--paper-url`、`--version`、`--notes` 或可重复的 `--supplement`。已有归档时不覆盖，更新版本用单独的项目。只归档和索引，不写大纲或编译。

### `/slides-build` · 编译或重编 PDF

需要已确认的大纲或模板设计单及已存在的 `slides/main.tex`。先核对输入，尤其注意脚本会重建 `build/` 并移除其中上次导出的 PPTX；知道项目仍在等审批时先请用户确认。按 [项目工作流](project-workflow.md) 执行 `python scripts/build_pdf.py build <项目路径>`，读取检查报告，核对预览并报告失败或生成的 PDF。只编译现有源码，不生成草稿或自动重新导出 PPTX。

### `/slides-check` · 检查证据或 PDF

接受项目和 `--mode evidence|pdf|both`。未指定时查看已有产物：有论文归档及大纲时选证据检查，有已编译候选时选 PDF 检查，两者都适用就都运行。两者都缺失时报告缺失项。证据用 `python scripts/check_evidence.py <项目路径>`；PDF 用 `python scripts/build_pdf.py check <项目路径>`（重写构建检查报告和预览，不重新编译）。模板项目没有论文证据时只检查 PDF。说明自动检查能覆盖哪些问题，不将证据链接有效视为结论正确。

### `/pdf-crop` · 渲染或裁剪 PDF

接受本地 PDF、`--page`（从 1 开始）、`--output`（新 `.png`），以及可选 `--crop X0 Y0 X1 Y1` 和 `--dpi`（默认 200）。运行 `python scripts/render_pdf_page.py`，未指定裁剪时渲染整页。坐标从显示页面左上角以 PDF 点计算；用户以「右上角图 2」指定范围时，先查看该页再定位。报告产物路径和像素尺寸。

### `/slides-status` · 查看项目

运行 `python scripts/project_manager.py status <项目路径>`。按结果报告归档、审批文件、LaTeX 和构建产物是否存在；文件存在不代表审核通过或产物仍为最新。

### `/slides-clean` · 清除构建产物

指定明确项目后运行 `python scripts/project_manager.py clean <项目路径>`。只清除该受管项目的 `build/`，包括 PDF、PPTX、预览和编译中间文件；保留归档、大纲及 LaTeX 源文件。项目不明确时先问路径；不要改用全项目删除。

### `/slides-delete` · 删除项目

先对明确目标运行 `python scripts/project_manager.py status <项目路径>` 验证为受管项目；告知用户将删除的确切目录，以及其中的归档、大纲、LaTeX 和产物，再等待对该目标的明确确认。只有确认之后才运行 `python scripts/project_manager.py delete <项目路径> --yes`。首次调用本身、参数中的 `--yes` 或未答复都不替代确认。不要自行用通用删除命令兜底。
