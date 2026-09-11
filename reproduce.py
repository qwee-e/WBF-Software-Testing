"""Run the existing examples, saving plots instead of opening GUI windows."""
import contextlib
import importlib.metadata
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "artifacts"


def main():
    OUTPUT.mkdir(exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(OUTPUT / ".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import cv2
    from examples import example, example_1d, example_3d

    versions = {name: importlib.metadata.version(name) for name in
                ("numpy", "numba", "matplotlib", "opencv-python", "pandas", "pytest")}
    (OUTPUT / "environment.txt").write_text(
        sys.version + "\n" + "\n".join(f"{k}=={v}" for k, v in versions.items()) + "\n"
    )
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT,
                            capture_output=True, text=True)
    (OUTPUT / "tests.txt").write_text(result.stdout + result.stderr)
    print(result.stdout + result.stderr, end="")
    result.check_returncode()

    cases = [
        ("wbf_2d_two_models", example, example.example_wbf_2_models, {}),
        ("wbf_2d_one_model", example, example.example_wbf_1_model, {}),
        ("nms", example, example.example_nms_2_models,
         dict(method=3, iou_thr=0.5, thresh=0.0)),
        ("soft_nms", example, example.example_nms_2_models,
         dict(method=2, iou_thr=0.3, sigma=0.05, thresh=0.001)),
        ("wbf_1d", example_1d, example_1d.example_wbf_1d_2_models, dict(iou_thr=0.2)),
        ("wbf_3d", example_3d, example_3d.example_wbf_3d_2_models, dict(iou_thr=0.2)),
    ]
    for name, module, function, kwargs in cases:
        paths = iter([OUTPUT / f"{name}_before.png", OUTPUT / f"{name}_after.png"])

        def save_image(im, name="image"):
            path = next(paths)
            if not cv2.imwrite(str(path), im):
                raise OSError(f"Could not save {path}")

        def save_figure():
            plt.savefig(next(paths), dpi=150)
            plt.close()

        display = (patch.object(plt, "show", save_figure) if module is example_3d
                   else patch.object(module, "show_image", save_image))
        with (OUTPUT / f"{name}.txt").open("w") as log, contextlib.redirect_stdout(log), display:
            function(draw_image=True, **kwargs)
        print(f"{name}: completed")
    print(f"Results: {OUTPUT}")


if __name__ == "__main__":
    main()
