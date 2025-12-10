from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional


class WatermarkRemovalEngine(ABC):
    """抽象引擎接口：隐藏底层实现差异，统一对外能力。

    最小契约：支持视频处理。必要时可扩展图片处理接口。
    """

    @abstractmethod
    def process_video(
        self,
        input_video_path: Path,
        output_video_path: Path,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        ...

    # 兼容现有调用口径（worker/core 调用 run），默认委托到 process_video
    def run(
        self,
        input_video_path: Path,
        output_video_path: Path,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        self.process_video(input_video_path, output_video_path, progress_callback)


