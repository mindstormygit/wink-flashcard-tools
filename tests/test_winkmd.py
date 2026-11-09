import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/generate-twinkling-pack"
sys.path.insert(0, str(SKILL / "scripts"))
sys.path.insert(0, str(REPO / "scripts"))
from build_winkmd import build
from validate_winkmd import InputError, parse, validate
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
        self.assertEqual(out.read_text(), text)
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
                     "{{note=a\\}b}}原文{{/note}}", "$x^2^y$", "{{ruby64=abc}}字{{/ruby}}", "价格从 $5 涨到 $10",
                     "{{mute}}跨两行\\\n同一段{{/mute}}"):
            with self.subTest(body=body):
                self.assertEqual(parse(body + "\n\n<!-- back -->\n\n背面")["cards"], 1)

    def test_leading_rule_is_not_a_header(self):
        self.assertEqual(parse("---\nNote: 正文\n\n<!-- back -->\n\n背面")["cards"], 1)
        with self.assertRaises(InputError):
            parse("---\nwink_md_version: 2\npack_name: 未闭合")

if __name__ == '__main__':
    unittest.main()
