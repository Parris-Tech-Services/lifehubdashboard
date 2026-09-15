import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_directory_indexes.py"

spec = importlib.util.spec_from_file_location("generate_directory_indexes", SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load {SCRIPT}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DirectoryIndexRegressionTests(unittest.TestCase):
    def test_generated_timestamp_does_not_make_content_look_changed(self):
        old_html = "<footer>Generated 2026-09-14 09:05 · Run generator</footer>"
        new_html = "<footer>Generated 2026-09-15 11:42 · Run generator</footer>"

        self.assertEqual(module.strip_generated_at(old_html), module.strip_generated_at(new_html))

        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "index.html"
            index_path.write_text(old_html, encoding="utf-8")
            self.assertFalse(module.content_changed(index_path, new_html))

    def test_real_content_change_is_still_detected(self):
        old_html = "<p>Alpha</p><footer>Generated 2026-09-14 09:05</footer>"
        new_html = "<p>Beta</p><footer>Generated 2026-09-15 11:42</footer>"

        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "index.html"
            index_path.write_text(old_html, encoding="utf-8")
            self.assertTrue(module.content_changed(index_path, new_html))


if __name__ == "__main__":
    unittest.main()
