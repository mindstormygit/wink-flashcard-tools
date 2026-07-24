# Wink 闪卡开放工具

[English](README.md)

本仓库开放用于生成 `.wink` 闪卡包的 Skill、格式说明、生成器、校验器和示例。

目前包含两套可以独立安装的 AI 制卡 Skill：

| Skill | 生成内容 | 主要能力 |
| --- | --- | --- |
| [`generate-twinkling-pack`](skills/generate-twinkling-pack/) | 正反面笔记卡、单选题和多选题 | 混合卡包、富文本、层级 Tag、普通图片，以及笔记卡原生矩形图片挖空 |
| [`generate-twinkling-word-pack`](skills/generate-twinkling-word-pack/) | Wink 原生单词卡 | 支持英语、日语、韩语、德语、法语、西班牙语、葡萄牙语和意大利语，可生成读音、中文释义、例句、语言字段和 Tag |

两套 Skill 都使用 Python 3 在本地生成未加密的 `.wink` 文件，并在交付前自动校验。闪卡 App 本体源码不在本仓库的开源范围内。

## 最简单的安装方法

1. 从 [Releases](https://github.com/mindstormygit/wink-flashcard-tools/releases) 下载需要的 Skill 压缩包；
2. 在支持 Skills 的 AI 工具中打开对话；
3. 对 AI 说“请帮我安装这个 Skill”，然后上传压缩包或粘贴下载地址；
4. 安装完成后新建任务，让 AI 重新发现 Skill。

手动安装时必须保留完整目录，不能只复制 `SKILL.md`。Codex 默认位置为：

```text
~/.codex/skills/generate-twinkling-pack/
~/.codex/skills/generate-twinkling-word-pack/
```

其他 AI 工具的安装目录可能不同，请以对应工具的说明为准。

## 笔记卡和选择题用法

```text
使用 $generate-twinkling-pack，把这份 PDF 制作成 30 张笔记卡、
10 道单选题和 5 道多选题。按目录建立 Tag，每张卡只考查一个知识点，
选择题给出可信的干扰项和简短解析，最后生成并校验 .wink 卡包。
```

## 单词卡用法

```text
使用 $generate-twinkling-word-pack 分析这份英语资料，
挑选约 40 个值得学习的单词或固定搭配。
根据原文语境编写简洁的中文释义，每个词添加一个自然例句和翻译，
按小节建立 Tag，最后生成并校验 .wink 单词卡包。
```

## 图片挖空

`generate-twinkling-pack` 支持在笔记卡中生成 Wink 原生矩形 `.rimg` 图片挖空。这属于进阶能力，需要能够理解图片的多模态模型。当前选择题为纯文字，图片和图片挖空用于笔记卡。

## Wink 格式

先阅读 [Wink 格式索引](docs/wink-format.md)。两套 Skill 可以独立分发，因此完整格式细节保存在各自目录中：

- [笔记卡与选择题格式](skills/generate-twinkling-pack/references/wink-format.md)
- [单词卡格式](skills/generate-twinkling-word-pack/references/wink-format.md)

## 生成发布压缩包

```bash
python3 scripts/package_skills.py
```

命令会在 `dist/` 中生成两套可分发 ZIP。推送匹配 `v*` 的 Git 标签时，GitHub Actions 会校验示例，并把两个压缩包和校验值发布到 GitHub Releases。

## 安全和内容质量

- 打包与校验脚本在本地运行；
- PDF 提取、OCR、网页读取和模型推理由用户选择的 AI 环境提供；
- `.wink` 文件未加密，请勿公开含有隐私或敏感内容的卡包；
- AI 生成内容可能出错，重要知识应结合原资料核对；
- 只处理和分发自己有权使用的资料与图片。

## 闪卡 App

- [闪卡官网](https://card.detailsoft.cn/)
- [App Store 下载](https://apps.apple.com/cn/app/id1515687192)

## 许可证

MIT License，详见 [LICENSE](LICENSE)。
