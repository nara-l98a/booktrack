import json, tempfile, unittest
from pathlib import Path
from booktrack.app import main, load, save

class BooktrackTests(unittest.TestCase):
    def setUp(self): self.t=tempfile.TemporaryDirectory(); self.path=Path(self.t.name)/"books.json"
    def tearDown(self): self.t.cleanup()
    def run_cli(self,*args): return main(["--data",str(self.path),*args])
    def test_add_persists_and_lists(self):
        self.run_cli("add","测试书","作者甲","--pages","200","--status","在读")
        b=load(self.path)["books"][0]; self.assertEqual(b["title"],"测试书"); self.assertEqual(b["pages"],200)
    def test_update_auto_completes(self):
        self.run_cli("add","书","甲","--pages","10"); self.run_cli("update","1","--page","10"); self.assertEqual(load(self.path)["books"][0]["status"],"已读")
    def test_invalid_page_rejected_without_write(self):
        self.run_cli("add","书","甲","--pages","10")
        with self.assertRaises(SystemExit): self.run_cli("update","1","--page","11")
        self.assertEqual(load(self.path)["books"][0]["current_page"],0)
    def test_filter_and_stats_data(self):
        self.run_cli("add","书","甲","--pages","100","--status","在读","--rating","4"); self.run_cli("add","完","乙","--pages","50","--status","已读","--rating","5")
        self.assertEqual(len([b for b in load(self.path)["books"] if b["status"]=="已读"]),1)
    def test_atomic_save_roundtrip(self):
        save(self.path,{"version":1,"books":[]}); self.assertEqual(load(self.path)["version"],1)
    def test_sample_refuses_to_overwrite_existing_data(self):
        original={"version":1,"books":[]};save(self.path,original)
        with self.assertRaises(SystemExit): self.run_cli("sample")
        self.assertEqual(load(self.path),original)
    def test_blank_book_fields_and_empty_update_are_rejected(self):
        with self.assertRaises(SystemExit): self.run_cli("add"," ","作者","--pages","10")
        self.run_cli("add","书","作者","--pages","10")
        with self.assertRaises(SystemExit): self.run_cli("update","1")
        self.assertEqual(load(self.path)["books"][0]["current_page"],0)

    def test_malformed_book_data_is_rejected_before_commands_run(self):
        self.path.write_text(json.dumps({"version": 1, "books": [{"id": 1, "title": "书", "author": "作者", "pages": 10, "current_page": 11, "status": "在读", "rating": None, "notes": "", "added": "2024-01-01"}]}), encoding="utf-8")
        with self.assertRaises(ValueError): load(self.path)

    def test_duplicate_book_ids_are_rejected(self):
        book = {"id": 1, "title": "书", "author": "作者", "pages": 10, "current_page": 0, "status": "想读", "rating": None, "notes": "", "added": "2024-01-01"}
        self.path.write_text(json.dumps({"version": 1, "books": [book, {**book, "title": "另一本"}]}), encoding="utf-8")
        with self.assertRaises(ValueError): load(self.path)

if __name__ == "__main__": unittest.main()
