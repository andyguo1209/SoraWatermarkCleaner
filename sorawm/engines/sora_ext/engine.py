from __future__ import annotations

import os
import shlex
import subprocess
import threading
from pathlib import Path
from typing import Callable, Optional

from loguru import logger

from sorawm.engines.base import WatermarkRemovalEngine


class SoraExtEngine(WatermarkRemovalEngine):
    """第三方仓库适配器（子进程模式）。

    优先保证可用性和与现有 UI 的契约兼容；后续可替换为直接 import 的源码模式。

    环境变量：
    - EXTERNAL_ENGINE_PATH: 外部仓库目录（默认 external/SoraWatermarkCleaner）
    - EXTERNAL_ENGINE_CMD_TEMPLATE: 运行命令模板，包含 {input} {output}
        示例："uv run python example.py --input {input} --output {output}"
    """

    def __init__(self) -> None:
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

    def process_video(
        self,
        input_video_path: Path,
        output_video_path: Path,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        input_video_path = Path(input_video_path)
        output_video_path = Path(output_video_path)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.engine_path.exists():
            raise FileNotFoundError(
                f"External engine path not found: {self.engine_path}. Set EXTERNAL_ENGINE_PATH to the upstream repo path."
            )

        cmd_str = self.cmd_template.format(
            input=str(input_video_path), output=str(output_video_path)
        )
        cmd = shlex.split(cmd_str)

        logger.info(f"Running external engine: {cmd_str}")

        if progress_callback is not None:
            progress_callback(5)

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
            for line in process.stdout:
                # 只在关键阶段推进进度，避免刷屏日志
                if "%" in line and progress_callback is not None:
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


