# “闪卡”开放工具

[English](README.md)

本仓库提供可独立安装的制卡 Skill、文稿说明、打包校验脚本和示例。闪卡 App 本体源码不在这里。

| Skill | 交付内容 | 能力 |
| --- | --- | --- |
| [`generate-twinkling-pack`](skills/generate-twinkling-pack/) | 多卡 `.winkmd`；有附件则 ZIP | 问答、挖空、选择题、层级分类、星标、折叠提示、跳过朗读、普通图片和录音 |
| [`generate-twinkling-word-pack`](skills/generate-twinkling-word-pack/) | 旧格式 `.wink` 单词卡或卡包 | 原生单词模板、读音、释义、例句与分类；本次不变 |

新版笔记 Skill 需要支持 `.winkmd` 导入的闪卡版本。旧 `.wink` 仍能导入 App；旧 Skill 版本保留在已有发布中。新版新建卡只交付普通图片，改已有文稿时可以保留其 `.rimg`，不再制作新的图片挖空。

## 安装与使用

从 [Releases](https://github.com/mindstormygit/wink-flashcard-tools/releases) 下载需要的 Skill ZIP，解压完整目录到 AI 工具的 Skills 目录。Codex 默认位置为 `~/.codex/skills/generate-twinkling-pack/` 或 `~/.codex/skills/generate-twinkling-word-pack/`。不要只复制 SKILL.md；更新后新建会话以重新发现 Skill。

```text
使用 $generate-twinkling-pack，把这份 PDF 制成约 40 张闪卡。
按目录建立层级分类，重要卡加星；翻译跳过朗读，提示默认折叠。
生成并校验 .winkmd，有图片或录音则交付 ZIP。
```

`category: ["医学","循环系统"]` 表示“医学 → 循环系统”这一条路径，每卡归最末一级。导入时可选已有普通包或新建包，无分类的卡保留在无分类。卡包名只预填新包名称；分类颜色只用于新建分类，填空偏好只用于新建卡包，不改已有设置。

```text
使用 $generate-twinkling-word-pack，从这份英语资料挑选 40 个重要词汇，
根据原文写读音、中文释义、例句和翻译，生成并校验 .wink 单词卡包。
```

纯文字 `.winkmd` 可从“文件”App 直接用闪卡打开。带 `media/` 的普通 ZIP 从闪卡内“导入闪卡文件”选择。流程见[笔记 Skill](skills/generate-twinkling-pack/SKILL.md)，写法以[方言规范](skills/generate-twinkling-pack/references/wink-spec-markdown-format.md)为准。规范在打包时从闪卡 App 仓库原样复制，只在 App 仓库修改。Python 脚本只用标准库；校验封装、附件和 App 严格导入会拒收的写法，App 负责完整正文语义。

## 发布包与检查

```bash
python3 -m unittest discover -s tests -v
python3 scripts/package_skills.py --app-repo ../iOS/TwinklingCard
```

打包先从 App 仓库（`--app-repo` 或环境变量 `WINK_APP_REPO`）复制方言规范和拒收／接受样例，再在 `dist/` 生成两套可独立分发的 ZIP。推送发布标签会触发现有 GitHub Actions；本地打包不发布。

AI 生成内容需要结合原资料核对，只处理有权使用的材料。网页、OCR、模型推理和媒体获取由用户选择的 AI 环境提供；打包、校验在本地完成。

[闪卡官网](https://card.detailsoft.cn/) · [App Store](https://apps.apple.com/cn/app/id1515687192) · [格式索引](docs/wink-format.md)

MIT License，见 [LICENSE](LICENSE)。
