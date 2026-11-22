# “闪卡”开放工具

[English](README.md)

本仓库提供统一的“闪卡（WinkNotes）”制卡 Skill、文稿说明、打包校验脚本和示例。闪卡 App 本体源码不在这里。

## 统一 Skill：[`generate-twinkling-pack`](skills/generate-twinkling-pack/)

| 卡片类型 | 交付内容 | 能力 |
| --- | --- | --- |
| 笔记与选择题 | 多卡 `.winkmd`；有附件则 ZIP | 问答、挖空、选择题（单选／多选、单题 `shuffle` 开关、题内 `:::explanation` 解析）、层级分类、星标、折叠提示、跳过朗读、表格、公式、普通图片和录音 |
| 原生单词卡 | 旧格式 `.wink` 独立单词卡或单语种单词卡包 | 原生 `WordDocument` 模板（英／日／韩／德／法／西／葡／意）、读音、中文释义、例句、语言字段与层级分类 |

**兼容性与分包说明**：
- `.winkmd` 导入的正式版目标为闪卡 **3.0**（**2.21.0** 公测版也支持 `.winkmd`，其中单题 `shuffle` 覆盖与题内 `:::explanation` 按具体构建判断；更早的 v2 构建请用裸 `:::choice` 并把单题解析写在 `<!-- back -->`，旧端无法表达单题洗牌覆盖）。
- `.wink` 单词文件兼容已有版本；旧版独立笔记／单词 Skill 保留在已有发布中。
- 笔记卡和原生单词卡在闪卡内分属不同卡包：每种受支持的词汇语言各交付一份 `.wink`，只有同时要求笔记或选择题时再额外交付一份 `.winkmd`（或媒体 ZIP）。新版笔记新建卡只交付普通图片，改已有文稿时可保留其 `.rimg`，不再制作新的图片挖空。

## 安装与升级

从 [Releases](https://github.com/mindstormygit/wink-flashcard-tools/releases) 下载 `generate-twinkling-pack.zip`，解压完整目录到 AI 工具的 Skills 目录。Codex 默认位置为 `~/.codex/skills/generate-twinkling-pack/`。保留 `scripts/`、`references/`、`agents/` 等全部文件，不要只复制 `SKILL.md`；更新后新建会话以重新发现 Skill。

如果以前单独安装过 `generate-twinkling-word-pack`，请按以下顺序升级：
1. 解压安装完整的新版 `generate-twinkling-pack/` 目录。
2. 把保存的 `$generate-twinkling-word-pack` 提示词、自动化任务或写死的脚本路径更新为 `$generate-twinkling-pack` / `generate-twinkling-pack/`。
3. 移出旧的 `generate-twinkling-word-pack/` 目录，避免工具同时发现两个词卡入口。
4. 新建会话，用一个词卡请求验证入口工作正常。

```text
使用 $generate-twinkling-pack，把这份 PDF 制成约 40 张闪卡。
混合问答与选择题（选择题附题内解析），按目录建立层级分类，重要卡加星；
翻译跳过朗读，提示默认折叠，生成并校验 .winkmd（有图片或录音则交付 ZIP）。
```

`category: ["医学","循环系统"]` 表示“医学 → 循环系统”这一条路径，每卡归最末一级。导入时可选已有普通包或新建包，无分类的卡保留在无分类。卡包名只预填新包名称；分类颜色只用于新建分类，填空偏好只用于新建卡包，不改已有设置。

```text
使用 $generate-twinkling-pack，从这份英语资料挑选 40 个重要词汇，
根据原文写读音、中文释义、例句和翻译，生成并校验 .wink 单词卡包。
```

纯文字 `.winkmd` 与 `.wink` 可从“文件”App 直接用闪卡打开；带 `media/` 的普通 ZIP 从闪卡内「导入 → 闪卡文件」选择。路由见 [SKILL.md](skills/generate-twinkling-pack/SKILL.md)，两条分支流程分别见 [note-workflow.md](skills/generate-twinkling-pack/references/note-workflow.md) 与 [word-workflow.md](skills/generate-twinkling-pack/references/word-workflow.md)，`.winkmd` 写法以[方言规范](skills/generate-twinkling-pack/references/wink-spec-markdown-format.md)为准。规范由维护者从闪卡 App 仓库原样复制，只在 App 仓库修改。Python 脚本只用标准库；校验封装、附件、单词 JSON 结构与 App 严格导入会拒收的写法，App 负责完整正文语义。

## 发布包与检查

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package_skills.py
```

无参数运行会直接按仓库内已提交的规范副本打包到 `dist/generate-twinkling-pack.zip`。持有闪卡 App 本地仓库的维护者可运行 `python3 scripts/package_skills.py --app-repo ../iOS/TwinklingCard`（或设置 `WINK_APP_REPO`）先同步方言规范与拒收／接受样例再打包。推送发布标签会触发现有 GitHub Actions；本地打包不发布。

AI 生成内容需要结合原资料核对，只处理有权使用的材料。网页、OCR、模型推理和媒体获取由用户选择的 AI 环境提供；打包、校验在本地完成。

[闪卡官网](https://card.detailsoft.cn/) · [App Store](https://apps.apple.com/cn/app/id1515687192) · [格式索引](docs/wink-format.md)

MIT License，见 [LICENSE](LICENSE)。
