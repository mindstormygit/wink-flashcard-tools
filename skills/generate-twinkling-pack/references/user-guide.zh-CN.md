# 闪卡生成 Skill 使用帮助

## 能做什么

这个 Skill 让 Codex 把资料整理成可直接导入“闪卡”App 的 `.wink` 独立卡片或闪卡卡包，支持：

- PDF、扫描版 PDF、网页 URL、图片、Markdown、纯文本和常见文档；
- 单张正反面笔记卡、单选题或多选题，也可把它们混合放在同一个卡包；
- 加粗、高亮、文字颜色、上下标、链接等富文本；
- 普通图片附件；
- “闪卡”App 原生 `.rimg` 图片挖空；
- 按目录或主题建立层级 Tag；
- 未加密的 `.wink` 输出。

扫描版 PDF 需要当前 Codex 环境具备 OCR 能力；网页和远程图片需要能够访问网络。

## 安装给 Codex

分享时保留完整的 `generate-twinkling-pack` 目录，不要只发送 `SKILL.md`。接收者需要把整个目录放入 Codex 的个人 Skills 目录：

```text
~/.codex/skills/generate-twinkling-pack/
```

如果设置了 `CODEX_HOME`，则放入：

```text
$CODEX_HOME/skills/generate-twinkling-pack/
```

最终应当能看到下面的结构：

```text
generate-twinkling-pack/
├── SKILL.md
├── LICENSE
├── CHANGELOG.md
├── agents/
├── examples/
├── references/
└── scripts/
```

安装后新建一个 Codex 任务，使 Skill 重新被发现。不要形成多套一层的路径，例如：

```text
generate-twinkling-pack/generate-twinkling-pack/SKILL.md
```

## 最短用法

把资料附加到 Codex，然后直接说：

```text
使用 $generate-twinkling-pack，把这个 PDF 制作成约 100 张适合复习的 .wink 卡片。
按 PDF 大纲建立 Tag，提炼重点并适当挖空；重要图表使用“闪卡”App 原生图片挖空。
```

只需要一张卡片并导入现有卡包时，明确要求“独立卡片”：

```text
使用 $generate-twinkling-pack，把下面的知识点制作成一张 .wink 独立笔记卡。
不要生成卡包；完成后校验文件。
```

独立卡片不包含卡包名或 Tag。导入时，“闪卡”App 会让用户选择目标卡包。多张卡片应生成卡包。

如果提示词只说“生成闪卡”或“制作卡片”，没有明确要求独立卡片还是卡包，Skill 会在内容完成后按数量选择：最终 1 张导出独立卡片，2 张及以上导出卡包。明确要求卡包时，即使只有 1 张也不会自动改成独立卡片。

如果不确定怎么提要求，可以先说：

```text
使用 $generate-twinkling-pack。先分析我提供的资料，并告诉我建议的卡片数量、
Tag 结构，以及文字卡和图片挖空卡的比例；确认后再生成卡包。
```

想混合不同题型时，可以直接指定数量或比例：

```text
使用 $generate-twinkling-pack，把这份资料生成 40 张复习卡：
25 张笔记卡、10 张单选题、5 张多选题。
选择题要有可信的干扰项和简短解析，所有卡片共用按章节建立的层级 Tag。
```

## 常用提示词

### PDF 教材

```text
使用 $generate-twinkling-pack 处理这个 PDF。
按照目录建立层级 Tag，生成约 80 张卡片。
每张卡只考查一个知识点；重点概念使用文字挖空，
重要结构图使用原生 .rimg 图片挖空，并在答案中保留页码。
```

### 扫描版 PDF

```text
使用 $generate-twinkling-pack 处理这个扫描版 PDF。
先 OCR 并检查目录与页码，只使用能够可靠识别的内容。
按章节生成约 50 张卡片，无法辨认的文字不要猜测。
```

### 网页

```text
使用 $generate-twinkling-pack 分析这个 URL：
https://example.com/article

提炼约 15 张复习卡，建立少量主题 Tag；
保留真正有助于理解的配图，并对图中的关键标签制作原生图片挖空。
```

### 指定章节

```text
使用 $generate-twinkling-pack，只处理这个 PDF 的第 6 章。
生成 20 张文字卡和 10 张图片挖空卡，Tag 按本章小节建立。
```

### 笔记卡与选择题混合

```text
使用 $generate-twinkling-pack 分析这份资料，制作约 30 张卡片。
需要主动回忆或解释机制的知识点做成笔记卡；
容易混淆的概念做成单选题或多选题，并给出简短解析。
不要用格式暗示正确答案，干扰项必须可信且有资料依据。
```

### 仅生成预览方案

```text
使用 $generate-twinkling-pack 分析这份资料，但先不要生成卡包。
先给我卡片数量、Tag 大纲、5 张示例卡和建议使用的图片列表。
```

## 交付结果

Codex 应当交付一个经过验证的 `.wink` 文件，并先说明它是独立卡片还是卡包。

- 卡片数量；
- 笔记卡、单选题和多选题各自的数量；
- 选择题的选项总数；
- 富文本 span 数量；
- 图片附件数量；
- 原生 RichImage 和图片挖空数量；
- 卡包产品的 Tag 数量及已分配 Tag 的卡片数量。

图片挖空必须是原生 `.rimg`，不能用前后两张 PNG 或把色块直接画进 PNG 来模拟。

当前版本的选择题支持问题、选项和解析中的文字富文本，但不支持在选择题内放图片；需要图片或图片挖空时使用同一卡包中的笔记卡。

## 常见问题

### Codex 找不到 Skill

检查以下项目：

1. 目录名是 `generate-twinkling-pack`；
2. `SKILL.md` 位于该目录第一层；
3. 分享包中的 `scripts` 和 `references` 没有丢失；
4. 安装后新建了 Codex 任务；
5. 提示词明确写了 `$generate-twinkling-pack`。

### 能否只发一个 `SKILL.md`

不能。生成器、校验器和格式说明都在配套目录中，必须分享完整目录。

### 是否需要“闪卡”App 源码

使用 Skill 生成卡片或卡包不需要“闪卡”App 源码，但需要 Python 3。PDF 解析、OCR、网页读取和图片裁剪能力由运行该 Skill 的 Codex 环境提供。

### 可以先检查再生成吗

可以。让 Codex 先输出建议的卡片数量、Tag 大纲和示例卡，确认后再生成 `.wink`。

### 笔记卡和选择题能否共用 Tag

可以。两种卡片可以在同一个卡包中任意混排，也可以引用同一套层级 Tag。
