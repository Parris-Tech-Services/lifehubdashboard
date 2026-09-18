from pathlib import Path
import importlib.util
import sys


def load_module():
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "update_welltory_summary.py"
    spec = importlib.util.spec_from_file_location("update_welltory_summary", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    sample = Path(__file__).parent / "sample_welltory_small.csv"
    if not sample.exists():
        print("Sample CSV missing", file=sys.stderr)
        sys.exit(2)
    module = load_module()
    out = module.summarise_csv(sample)
    assert out["measurementCount"] == 3
    assert out["stressAverage"] == 20.0
    assert out["energyAverage"] == 60.0
    assert out["focusAverage"] == 80.0
    assert out["latestMeasurement"] == "2025-12-11T20:42:45"
    print("OK: summariser smoke test passed")


if __name__ == "__main__":
    main()
