import csv
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(module_name: str, filename: str):
    script = ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stats = load_script("update_dashboard_stats", "update_dashboard_stats.py")
welltory = load_script("update_welltory_summary", "update_welltory_summary.py")
recent_files = load_script("generate_recent_files", "generate_recent_files.py")


class DashboardStatsTests(unittest.TestCase):
    def test_downloads_backlog_counts_only_files_at_least_24_hours_old(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            feed_path = Path(temp_dir) / "downloads-feed.json"
            feed_path.write_text(
                json.dumps(
                    {
                        "files": [
                            {"name": "fresh.txt", "ageHours": 23.9},
                            {"name": "boundary.txt", "ageHours": 24},
                            {"name": "old.txt", "ageHours": "48"},
                            {"name": "missing-age.txt"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(stats.compute_downloads_backlog(feed_path), 2)

    def test_weekly_inbox_trend_uses_latest_snapshot_and_tracks_direction(self):
        history = [
            {"timestamp": "2026-08-24T09:00:00+00:00", "stats": {"inboxCount": 5}},
            {"timestamp": "2026-08-24T18:00:00+00:00", "stats": {"inboxCount": 7}},
            {"timestamp": "2026-08-31T09:00:00+00:00", "stats": {"inboxCount": 4}},
            {"timestamp": "2026-09-07T09:00:00+00:00", "stats": {"inboxCount": 6}},
        ]

        trend = stats.build_weekly_inbox_trend(history)

        self.assertEqual([entry["count"] for entry in trend], [7, 4, 6])
        self.assertEqual(trend[1]["cleared"], 3)
        self.assertEqual(trend[2]["added"], 2)


class WelltorySummaryTests(unittest.TestCase):
    def test_csv_summary_normalises_headers_and_averages_measurements(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "WELLTORY_MEASUREMENT_DATA_EXPORT_test.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["Date", "Stress (HRV)", "Energy (HRV)", "Focus"])
                writer.writerow(["2026-09-15T10:00:00", "20", "60", "80"])
                writer.writerow(["2026-09-14T10:00:00", "40", "80", "60"])

            summary = welltory.summarise_csv(csv_path)

            self.assertEqual(summary["sourceFile"], csv_path.name)
            self.assertEqual(summary["latestMeasurement"], "2026-09-15T10:00:00")
            self.assertEqual(summary["measurementCount"], 2)
            self.assertEqual(summary["stressAverage"], 30.0)
            self.assertEqual(summary["energyAverage"], 70.0)
            self.assertEqual(summary["focusAverage"], 70.0)

    def test_deltas_are_numeric_and_do_not_mutate_inputs(self):
        current = {"stressAverage": 35, "energyAverage": 75, "focusAverage": 60, "measurementCount": 12}
        previous = {"stressAverage": 40, "energyAverage": 70, "focusAverage": 65, "measurementCount": 10}

        deltas = welltory.compute_deltas(current, previous)

        self.assertEqual(deltas, {"stress": -5.0, "energy": 5.0, "focus": -5.0, "measurementCount": 2.0})
        self.assertEqual(current["stressAverage"], 35)
        self.assertEqual(previous["stressAverage"], 40)


class RecentFilesTests(unittest.TestCase):
    def test_recent_files_are_sorted_and_generated_indexes_are_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            inbox = temp_root / "Inbox"
            inbox.mkdir()
            older = inbox / "older.txt"
            newer = inbox / "newer.txt"
            generated_index = inbox / "index.html"
            ds_store = inbox / ".DS_Store"
            older.write_text("old", encoding="utf-8")
            newer.write_text("new", encoding="utf-8")
            generated_index.write_text("generated", encoding="utf-8")
            ds_store.write_text("metadata", encoding="utf-8")
            os.utime(older, (1_700_000_000, 1_700_000_000))
            os.utime(newer, (1_800_000_000, 1_800_000_000))

            original_root = recent_files.ROOT
            recent_files.ROOT = temp_root
            try:
                result = recent_files.list_recent("Inbox")
            finally:
                recent_files.ROOT = original_root

            self.assertEqual([entry["path"] for entry in result], ["Inbox/newer.txt", "Inbox/older.txt"])
            self.assertTrue(all("modified" in entry and "ageDays" in entry for entry in result))


if __name__ == "__main__":
    unittest.main()
