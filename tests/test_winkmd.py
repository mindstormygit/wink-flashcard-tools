import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/generate-twinkling-pack"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(REPO / "scripts"))
from build_winkmd import GENERATOR, build, stamp
from build_word_wink import (
    InputError as WordInputError,
    build_artifact as build_word_artifact,
    load_source as load_word_source,
    main as build_word_main,
    write_wink,
)
from validate_winkmd import InputError, parse, validate
from validate_word_wink import validate_word_wink
import package_skills


class DialectSpecTests(unittest.TestCase):
    """The spec and its samples are copied from the App repository by scripts/package_skills.py."""

    def test_shared_samples_match_the_app(self):
        samples = json.loads(package_skills.SKILL_SAMPLES.read_text(encoding="utf-8"))
        wrap = lambda body: f"---\nwink_md_version: 2\n---\n\n{body}\n\n<!-- back -->\n\n答案\n"
        for sample in samples["must_reject"]:
            with self.subTest(reject=sample["name"]), self.assertRaises(InputError):
                parse(wrap(sample["body"]))
        for sample in samples["must_accept"]:
            with self.subTest(accept=sample["name"]):
                self.assertEqual(parse(wrap(sample["body"]))["cards"], 1)
        for sample in samples["headerless_files"]:
            with self.subTest(headerless=sample["name"]):
                info = parse(sample["text"])
                self.assertEqual(info["cards"], 1)
                self.assertNotIn("pack_name", info.get("header", {}))

    def test_copies_match_the_app_repository(self):
        app = package_skills.DEFAULT_APP_REPO
        if not (app / package_skills.APP_SPEC).is_file():
            self.skipTest(f"App repository not found at {app}; set WINK_APP_REPO")
        copy = package_skills.SKILL_SPEC.read_text(encoding="utf-8")
        self.assertTrue(copy.startswith(package_skills.GENERATED_MARK))
        source = (app / package_skills.APP_SPEC).read_text(encoding="utf-8")
        self.assertEqual(package_skills.strip_generated_header(copy), package_skills.skill_spec_body(source),
                         "Skill spec is stale; rerun scripts/package_skills.py")
        self.assertEqual(package_skills.SKILL_SAMPLES.read_bytes(), (app / package_skills.APP_SAMPLES).read_bytes())


class WinkmdDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.media = self.root / "media"
        self.media.mkdir()
    def tearDown(self):
        self.temp.cleanup()
    def manuscript(self, body):
        path = self.root / "draft.winkmd"
        path.write_text(body, encoding="utf-8")
        return path
    def test_plain_delivery_preserves_unicode_and_metadata(self):
        text = '---\nwink_md_version: 2\npack_name: 医学\n---\n<!-- meta\n{"category":["医学","循环"],"starred":true}\n-->\n问题\n<!-- back -->\n答案'
        source = self.manuscript(text)
        out = self.root / "result.winkmd"
        info = build(source, out)
        self.assertEqual(info["cards"], 1)
        stamped = text.replace("pack_name: 医学\n", f"pack_name: 医学\ngenerator: {GENERATOR}\n")
        self.assertEqual(out.read_text(encoding="utf-8"), stamped)
    def test_generator_is_stamped_once_and_matches_the_changelog(self):
        changelog = (SKILL / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        latest = next(line for line in changelog if line.startswith("## "))
        self.assertTrue(latest.startswith(f"## {GENERATOR.split()[-1]} "), latest)
        # No header: one is added. Old generator line: replaced, not duplicated. Leading divider: stays body text.
        self.assertEqual(stamp("正文"), f"---\nwink_md_version: 2\ngenerator: {GENERATOR}\n---\n\n正文")
        self.assertEqual(stamp("---\ngenerator: old 1.0\n---\n正文").count("generator:"), 1)
        self.assertTrue(stamp("---\nNote: 正文").endswith("---\nNote: 正文"))
        self.assertEqual(parse(stamp("---\nNote: 正文"))["header"]["generator"], GENERATOR)
    def test_archive_has_one_root_manuscript_and_one_file_for_repeated_references(self):
        (self.media / "image.png").write_bytes((SKILL / "examples/media/sample.png").read_bytes())
        source = self.manuscript('![一](att:image.png)\n<!-- back -->\n![二](att:image.png)')
        out = self.root / "result.zip"
        build(source, out)
        with zipfile.ZipFile(out) as archive:
            self.assertEqual(archive.namelist(), ["draft.winkmd", "media/image.png"])
        self.assertEqual(len(validate(out)["references"]), 2)
    def test_missing_media_fails_before_output_exists(self):
        out = self.root / "result.zip"
        with self.assertRaisesRegex(InputError, "missing"):
            build(self.manuscript('![图](att:missing.png)'), out)
        self.assertFalse(out.exists())
    def test_oversized_audio_and_unsafe_references_fail(self):
        (self.media / "large.wav").write_bytes(b'\0' * (10 * 1024 * 1024 + 1))
        for ref in ('large.wav', '../outside.png', 'x/y.png', 'drm.m4p'):
            with self.assertRaises(InputError):
                validate(self.manuscript(f'![录音](att:{ref})'))
    def test_unknown_body_markers_and_missing_version_are_supported(self):
        self.assertEqual(parse('{{future}}正文{{/future}}')["cards"], 1)
        with self.assertRaises(InputError):
            parse('---\nwink_md_version: 9\n---\n正文')
    def test_code_examples_do_not_split_cards_or_require_media(self):
        result = parse('```\n<!-- card -->\n![示例](att:absent.png)\n```\n<!-- card -->\n第二张')
        self.assertEqual(result["cards"], 2)
        self.assertEqual(result["references"], [])
    def test_bad_metadata_and_unclosed_blocks_are_rejected(self):
        for text in ('<!-- meta\n{"category":"x"}\n-->\n正文', '<!-- meta\n{"starred":1}\n-->\n正文', '<!-- meta\n{}', ':::choice\n题干\n- [x] 是', '<details>\n<summary>提示</summary>\n内容', '{{c1::旧写法}}'):
            with self.subTest(text=text), self.assertRaises((InputError, ValueError)):
                parse(text)
    def test_existing_output_is_not_overwritten(self):
        output = self.root / 'output.winkmd'
        output.write_text('保留原件')
        with self.assertRaises(FileExistsError):
            build(self.manuscript('新内容'), output)
        self.assertEqual(output.read_text(), '保留原件')
    def test_zip_with_multiple_manuscripts_or_traversal_is_rejected(self):
        for entries in ({'a.winkmd':'a','b.winkmd':'b'}, {'a.winkmd':'a','../escape':'bad'}):
            archive = self.root / 'bad.zip'
            with zipfile.ZipFile(archive, 'w') as z:
                for name, content in entries.items(): z.writestr(name,content)
            with self.assertRaises(InputError): validate(archive)
    def test_all_shipped_examples_validate(self):
        for name in ('example-pack.winkmd','example-card.winkmd','example-media.winkmd','example-media.zip'):
            with self.subTest(example=name): validate(SKILL / 'examples' / name)


    def test_strict_rejections_match_the_app(self):
        for body in ("参考文献[1]", "漢字[かんじ]", "x^2^", "{{mute}}没闭合", "{{mute}}{{u}}错序{{/mute}}{{/u}}", "{{c1::答案}}"):
            with self.subTest(body=body), self.assertRaises(InputError):
                parse(body + "\n\n<!-- back -->\n\n背面")
        for body in ("详见[说明](https://example.com)", "参考文献\\[1\\]", "{{mute}}{{u}}嵌套{{/u}}{{/mute}}",
                     "{{note=a\\}b}}原文{{/note}}", "$x^2^y$", "价格从 $5 涨到 $10",
                     "{{mute}}跨两行\\\n同一段{{/mute}}"):
            with self.subTest(body=body):
                self.assertEqual(parse(body + "\n\n<!-- back -->\n\n背面")["cards"], 1)

    def test_leading_rule_is_not_a_header(self):
        self.assertEqual(parse("---\nNote: 正文\n\n<!-- back -->\n\n背面")["cards"], 1)
        with self.assertRaises(InputError):
            parse("---\nwink_md_version: 2\npack_name: 未闭合")

    def test_card_and_back_separators_after_code_and_math(self):
        for marker in ("<!-- card -->", "<!-- back -->"):
            for before, after in (
                ("```code```", "second"),
                ("$$\nx$$", "$$y\n$$"),
                ("$$\nx$$", "$$\ny$$"),
            ):
                with self.subTest(before=before, marker=marker, after=after), self.assertRaises(InputError):
                    parse(f"first\n{before}\n\n{marker}\n\n{after}")

        for safe in ("`code`", "$$x$$", "$$\nx\n$$", "```\n<!-- card -->\n```"):
            with self.subTest(safe=safe):
                self.assertEqual(parse(f"{safe}\n\n<!-- back -->\nanswer\n\n<!-- card -->\nsecond")["cards"], 2)

    def test_nested_choice_items(self):
        for body in (
            "1. prompt\n   - [x] nested",
            "Q\n- [x] A\n  - child\n- [ ] B",
            "Q\n- [x] A\n    1. child\n- [ ] B",
        ):
            with self.subTest(body=body), self.assertRaises(InputError):
                parse(f":::choice\n{body}\n:::")
        for prompt in ("1. step\n   - detail", "- step\n  1. detail"):
            with self.subTest(prompt=prompt):
                self.assertEqual(parse(f":::choice\n{prompt}\n\n- [x] A\n- [ ] B\n:::")["cards"], 1)

    def test_choice_header_attributes_and_inline_explanation(self):
        for body in (
            ":::choice{shuffle=false}\n哪项正确？\n- [ ] 甲\n- [x] 以上都是\n:::explanation\n解析内容。\n:::",
            ":::choice{#q1 shuffle=true}\n哪项正确？\n- [x] 甲\n- [ ] 乙\n:::",
            ":::choice{shuffle=false #q1}\n交换顺序\n- [x] 甲\n- [ ] 乙\n:::",
            ":::choice{#q1\tshuffle=true}\n制表符分隔\n- [x] 甲\n- [ ] 乙\n:::",
            ":::choice\n缩进闭题\n- [x] 甲\n- [ ] 乙\n  :::",
            "前文段落\n\n  :::choice{shuffle=maybe}\n中段缩进开题不是选择题，只是普通段落",
            ":::choice 不是选择题，只是普通段落",
            "$$\n:::choice{shuffle=maybe}\n$$",
            ":::choice\n题干\n$$\nx\n$$\n- [x] 甲\n- [ ] 乙\n:::",
            ":::choice\n```code```\n- [x] 甲\n- [ ] 乙\n:::",
            ":::choice\n- 题干条目\n- [x] 甲\n- [ ] 乙\n:::",
            ":::choice\n题干\n- [x] 甲\n- [ ] 乙\n:::explanation\n:::choice{bogus}\n:::explanation\n第二个标记是普通文字\n:::\n\n<!-- back -->\n\n背面补充",
            ":::choice\n题干带代码：\n```\n:::explanation\n:::\n```\n- [x] 甲\n- [ ] 乙\n:::explanation\n```\n:::\n```\n真解析\n:::",
            "> {{mute}}甲\\\n> 乙{{/mute}}",
            "<DETAILS>\n<summary>大写折叠块</summary>\n\n正文\n\n</DETAILS>",
            "<details-extra>相似前缀不是折叠块</details-extra>",
        ):
            with self.subTest(valid=body):
                self.assertEqual(parse(body)["cards"], 1)
        self.assertEqual(
            parse(":::choice\n题干\n$$\nx\n$$\n- [x] 甲\n:::\n\n<!-- back -->\n\n背面\n\n<!-- card -->\n\n第二张")["cards"],
            2,
        )
        for body in (
            ":::choice{shuffle=maybe}\n题干\n- [x] 甲\n:::",
            "  :::choice{shuffle=maybe}\n题干\n- [x] 甲\n:::",
            "<!-- meta\n{}\n-->\n  :::choice{shuffle=maybe}\n题干\n- [x] 甲\n:::",
            ":::choice{shuffle=true shuffle=false}\n题干\n- [x] 甲\n:::",
            ":::choice{#q1 #q2}\n题干\n- [x] 甲\n:::",
            ":::choice{#a!b}\n题干\n- [x] 甲\n:::",
            ":::choice{}\n题干\n- [x] 甲\n:::",
            ":::choice{foo=bar}\n题干\n- [x] 甲\n:::",
            ":::choice{shuffle=false\n题干\n- [x] 甲\n:::",
            ":::choice\n$$\n:::explanation\nx\n$$\n- [x] 甲\n:::",
            ":::choice\n题干\n$$\nx$$\n- [x] 甲\n:::",
            ":::choice\n- [x] 只有选项没有题干\n:::",
            ":::choice\n题干\n- [x] 甲\n# 紧接标题\n:::",
            ":::choice\n- 题干列表\n  - [x] 嵌套选项不算顶层\n:::",
            ":::choice\n题干\n- [x] {{mute}}选项一\n- [ ] 选项二{{/mute}}\n:::",
            ":::choice\n题干\n:::explanation\n解析不能在选项前\n- [x] 甲\n:::",
            ":::choice\n题干\n- [x] 甲\n\n选项后的普通段落\n:::explanation\n解析\n:::",
            ":::choice\n题干\n- [x] 甲\n- 非选项普通列表项\n:::explanation\n解析\n:::",
            ":::choice\n题干\n- [x] {{mute}}跨区未闭合\n:::explanation\n这里关{{/mute}}\n:::",
            ":::choice\n题干\n- [x] 甲\n:::explanation\n<details>\n<summary>提示</summary>\n\n不允许\n\n</details>\n:::",
            ":::choice\n题干\n- [x] 甲\n:::explanation\n<DETAILS>\n<summary>大写提示</summary>\n\n不允许\n\n</DETAILS>\n:::",
            "<details>\n<summary>提示</summary>\n\n:::choice\n题干\n- [x] 甲\n:::\n\n</details>",
            "<details>\n<summary>{{mute}}标题</summary>\n正文{{/mute}}\n</details>",
        ):
            with self.subTest(invalid=body), self.assertRaises(InputError):
                parse(body)


class SkillPackagingTests(unittest.TestCase):
    def test_release_archive_contains_both_workflows_and_valid_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = package_skills.write_archive("generate-twinkling-pack", Path(tmp))
            with zipfile.ZipFile(archive_path) as archive:
                names = set(archive.namelist())
                for required in (
                    "generate-twinkling-pack/SKILL.md",
                    "generate-twinkling-pack/agents/openai.yaml",
                    "generate-twinkling-pack/references/note-workflow.md",
                    "generate-twinkling-pack/references/word-workflow.md",
                    "generate-twinkling-pack/scripts/build_winkmd.py",
                    "generate-twinkling-pack/scripts/validate_winkmd.py",
                    "generate-twinkling-pack/scripts/build_word_wink.py",
                    "generate-twinkling-pack/scripts/validate_word_wink.py",
                ):
                    self.assertIn(required, names)
                skill_md = archive.read("generate-twinkling-pack/SKILL.md").decode("utf-8")
                openai_yaml = archive.read("generate-twinkling-pack/agents/openai.yaml").decode("utf-8")
            self.assertTrue(skill_md.startswith("---\n"))
            if shutil.which("ruby"):
                script = (
                    'require "yaml"; '
                    'text = STDIN.read; '
                    'm = text.match(/\\A---\\n(.*?)\\n---\\n/m) or abort("missing frontmatter"); '
                    'data = YAML.safe_load(m[1]); '
                    'abort("bad name") unless data["name"] == "generate-twinkling-pack"; '
                    'abort("bad desc") unless data["description"].is_a?(String) && !data["description"].strip.empty?'
                )
                result = subprocess.run(["ruby", "-e", script], input=skill_md, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                openai_check = subprocess.run(
                    ["ruby", "-ryaml", "-e", 'd = YAML.safe_load(STDIN.read); abort("bad") unless d["interface"].is_a?(Hash)'],
                    input=openai_yaml,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(openai_check.returncode, 0, openai_check.stderr)


class WordWinkDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write_json(self, name, payload):
        path = self.root / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_shipped_word_examples_validate(self):
        for name, expected_product in (
            ("example-word-pack.wink", "pack"),
            ("example-word-card.wink", "card"),
        ):
            with self.subTest(example=name):
                summary = validate_word_wink(SKILL / "examples" / name)
                self.assertEqual(summary["product"], expected_product)

    def test_word_json_examples_build_and_validate(self):
        cases = (
            ("example-words.json", "auto", "pack"),
            ("example-word-card.json", "auto", "card"),
            ("example-word-card.json", "card", "card"),
            ("example-one-word-pack.json", "pack", "pack"),
        )
        for name, mode, expected_product in cases:
            with self.subTest(source=name, mode=mode):
                source = load_word_source(SKILL / "examples" / name, mode)
                self.assertEqual(source["product"], expected_product)
                out = self.root / f"{Path(name).stem}-{mode}.wink"
                write_wink(build_word_artifact(source, source["product"]), out)
                summary = validate_word_wink(out)
                self.assertEqual(summary["product"], expected_product)

    def test_cli_explicit_standalone_word_card(self):
        out = self.root / "cli-card.wink"
        rc = build_word_main([str(SKILL / "examples/example-word-card.json"), str(out), "--product", "card"])
        self.assertEqual(rc, 0)
        summary = validate_word_wink(out)
        self.assertEqual(summary["product"], "card")
        self.assertEqual(summary["word"], "resilient")

    def test_invalid_word_inputs_are_rejected(self):
        bad_cases = (
            ("multi-word-forced-card", "card", {"langCode": "en", "words": [{"word": "a", "definition": "甲"}, {"word": "b", "definition": "乙"}]}),
            ("card-with-name", "card", {"name": "不应有包名", "langCode": "en", "words": [{"word": "a", "definition": "甲"}]}),
            ("card-with-tags", "card", {"langCode": "en", "tags": [{"id": "t1", "name": "分类"}], "words": [{"word": "a", "definition": "甲"}]}),
            ("card-with-word-tag", "card", {"langCode": "en", "words": [{"word": "a", "definition": "甲", "tag": "t1"}]}),
            ("unsupported-lang", "auto", {"langCode": "ru", "words": [{"word": "мир", "definition": "世界"}]}),
            ("mismatched-template", "card", {"langCode": "en", "words": [{"word": "apple", "definition": "苹果", "extras": [{"label": "假名", "content": "あ", "templateKey": "ja.kana"}]}]}),
        )
        for name, mode, payload in bad_cases:
            with self.subTest(case=name), self.assertRaises(WordInputError):
                load_word_source(self.write_json(f"{name}.json", payload), mode)

    def test_write_wink_race_preserves_existing_file(self):
        out = self.root / "race.wink"
        out.write_bytes(b"winner-content")
        source = load_word_source(SKILL / "examples/example-word-card.json", "card")
        artifact = build_word_artifact(source, "card")
        with mock.patch.object(Path, "exists", return_value=False):
            with self.assertRaises(FileExistsError):
                write_wink(artifact, out)
        self.assertTrue(out.exists())
        self.assertEqual(out.read_bytes(), b"winner-content")

if __name__ == '__main__':
    unittest.main()
