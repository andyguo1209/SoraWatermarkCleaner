import os
import shlex
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional


class ExternalEngineCleaner:
    """Adapter that delegates cleaning to an external engine (upstream repo).

    Configuration via environment variables:
    - EXTERNAL_ENGINE_PATH: directory containing the upstream project (default: external/SoraWatermarkCleaner)
    - EXTERNAL_ENGINE_CMD_TEMPLATE: command template with placeholders {input}, {output}
        default: "uv run python example.py --input {input} --output {output}"

    The command is executed with cwd set to EXTERNAL_ENGINE_PATH.
    """

    def __init__(self, clean_level: Optional[str] = None) -> None:
        # clean_level 已废弃，保留参数仅为兼容旧调用，不再使用
        self.engine_path = Path(
            os.getenv(
                "EXTERNAL_ENGINE_PATH",
                str(Path("external") / "SoraWatermarkCleaner"),
            )
        )
        self.cmd_template = os.getenv(
            "EXTERNAL_ENGINE_CMD_TEMPLATE",
            "uv run python example.py --input {input} --output {output}",
        )

    def run(
        self,
        input_video_path: Path,
        output_video_path: Path,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        input_video_path = Path(input_video_path)
        output_video_path = Path(output_video_path)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        # Best-effort progress notifications
        if progress_callback is not None:
            progress_callback(5)

        # Build command
        cmd_str = self.cmd_template.format(
            input=str(input_video_path), output=str(output_video_path)
        )
        cmd = shlex.split(cmd_str)

        # Run process in external engine path
        if not self.engine_path.exists():
            raise FileNotFoundError(
                f"External engine path not found: {self.engine_path}. Set EXTERNAL_ENGINE_PATH to the upstream repo path."
            )

        # Stream subprocess output to inherit logs while keeping UI responsive
        process = subprocess.Popen(
            cmd,
            cwd=str(self.engine_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        def _drain_stdout():
            assert process.stdout is not None
            for _ in process.stdout:
                # We deliberately do not log here to avoid coupling loggers
                # Users can check upstream logs in the console or add redirection in the template
                if progress_callback is not None:
                    # Nudge progress forward slightly while running
                    progress_callback(50)

        t = threading.Thread(target=_drain_stdout, daemon=True)
        t.start()
        code = process.wait()

        if code != 0:
            raise RuntimeError(
                f"External engine exited with code {code}. Command: {cmd_str}. Check upstream logs."
            )

        if progress_callback is not None:
            progress_callback(100)


def get_cleaner(clean_level: Optional[str] = None):
    """Return the active cleaner implementation.

    If EXTERNAL_ENGINE_PATH exists, use ExternalEngineCleaner; otherwise fall back to local SoraWM.
    """
    engine_path = Path(
        os.getenv(
            "EXTERNAL_ENGINE_PATH",
            str(Path("external") / "SoraWatermarkCleaner"),
        )
    )
    if engine_path.exists():
        try:
            # 优先使用源码级引擎（后续可在此处直接对接第三方python接口）
            from sorawm.engines.sora_ext import SoraExtEngine

            return SoraExtEngine()
        except Exception:
            # 回退到通用子进程适配器
            return ExternalEngineCleaner(clean_level=None)

    # Fallback to local implementation
    from sorawm.core import SoraWM  # deferred import to avoid model load at import time

    return SoraWM(clean_level=None)




