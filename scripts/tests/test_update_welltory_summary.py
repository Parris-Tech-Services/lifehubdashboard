from pathlib import Path
import importlib.util


def load_summariser_module():
    # Load the script module directly from the scripts path so tests don't
    # depend on package import paths.
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "update_welltory_summary.py"
    spec = importlib.util.spec_from_file_location("update_welltory_summary", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_summarise_small_sample():
    sample = Path(__file__).parent / "sample_welltory_small.csv"
    assert sample.exists()

    module = load_summariser_module()
    out = module.summarise_csv(sample)

    assert out["measurementCount"] == 3
    # stressAverage should be (10 + 20 + 30) / 3 = 20.0
    assert out["stressAverage"] == 20.0
    assert out["energyAverage"] == 60.0
    assert out["focusAverage"] == 80.0
    # latestMeasurement should be the first row's date
    assert out["latestMeasurement"] == "2025-12-11T20:42:45"
