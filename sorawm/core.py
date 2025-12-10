from pathlib import Path
from typing import Callable
import platform

import ffmpeg
import numpy as np
from loguru import logger
from tqdm import tqdm

from sorawm.utils.video_utils import VideoLoader
from sorawm.watermark_cleaner import WaterMarkCleaner
from sorawm.watermark_detector import SoraWaterMarkDetector
from sorawm.utils.imputation_utils import (
    find_2d_data_bkps,
    get_interval_average_bbox,
    find_idxs_interval,
)
from sorawm.configs import (
    FFMPEG_PRESET,
    ENABLE_HARDWARE_ENCODING,
    BATCH_SIZE,
    DETECTION_INTERVAL,
    ENABLE_SINGLE_PASS,
    PROCESS_REGION_ONLY,
    REGION_MARGIN,
    MAX_FRAMES_WITHOUT_DETECTION,
    TEMPLATE_THRESHOLD,
)

VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"]


class SoraWM:
    def __init__(self, clean_level: str | None = None):
        self.detector = SoraWaterMarkDetector()
        self.cleaner = WaterMarkCleaner()
        self.ffmpeg_preset = FFMPEG_PRESET
        self.enable_hardware_encoding = ENABLE_HARDWARE_ENCODING
        self.batch_size = BATCH_SIZE
        # 取消等级档位，直接使用参数化配置
        self.template_threshold = float(TEMPLATE_THRESHOLD)
        self.detection_interval = int(DETECTION_INTERVAL)
        self.enable_single_pass = ENABLE_SINGLE_PASS
        self.process_region_only = PROCESS_REGION_ONLY
        self.region_margin = int(REGION_MARGIN)
        self.max_frames_without_detection = MAX_FRAMES_WITHOUT_DETECTION

    def _get_video_codec(self):
        """根据系统和配置选择最佳视频编码器"""
        if not self.enable_hardware_encoding:
            return "libx264"
        
        system = platform.system()
        if system == "Darwin":  # macOS
            return "h264_videotoolbox"
        elif system == "Linux" or system == "Windows":
            # 检查是否有NVIDIA GPU
            try:
                import torch
                if torch.cuda.is_available():
                    return "h264_nvenc"
            except:
                pass
        
        return "libx264"

    def _clean_region(self, frame: np.ndarray, bbox: tuple, width: int, height: int) -> np.ndarray:
        """只清除水印区域（而不是整帧），大幅提升性能
        
        参数:
            frame: 原始帧
            bbox: 水印边界框 (x1, y1, x2, y2)
            width: 视频宽度
            height: 视频高度
            
        返回:
            处理后的帧
        """
        x1, y1, x2, y2 = bbox
        
        # 验证边界框有效性
        if x2 <= x1 or y2 <= y1 or x1 < 0 or y1 < 0 or x2 > width or y2 > height:
            logger.warning(f"Invalid bbox {bbox}, skipping watermark removal")
            return frame
        
        # 计算bbox尺寸，动态调整边距（避免小bbox用大边距导致模糊）
        bbox_w = x2 - x1
        bbox_h = y2 - y1
        bbox_size = max(bbox_w, bbox_h)
        
        # 边距策略：小bbox用小边距，大bbox用大边距，但不超过限制
        if bbox_size < 50:
            margin = min(15, self.region_margin)  # 小bbox用更小边距
        elif bbox_size < 100:
            margin = min(25, self.region_margin)
        else:
            margin = min(35, self.region_margin)  # 最大边距35像素
        
        # 扩展区域（带边距，但限制最大边距避免处理范围过大）
        rx1 = max(0, x1 - margin)
        ry1 = max(0, y1 - margin)
        rx2 = min(width, x2 + margin)
        ry2 = min(height, y2 + margin)
        
        # 确保区域有效
        if rx2 <= rx1 or ry2 <= ry1:
            logger.warning(f"Invalid expanded region from bbox {bbox}, skipping")
            return frame
        
        # 提取区域
        region = frame[ry1:ry2, rx1:rx2].copy()
        
        # 创建区域mask - 精确对应水印位置
        region_mask = np.zeros((ry2 - ry1, rx2 - rx1), dtype=np.uint8)
        # mask相对于region的坐标
        mask_y1 = max(0, y1 - ry1)
        mask_y2 = min(ry2 - ry1, y2 - ry1)
        mask_x1 = max(0, x1 - rx1)
        mask_x2 = min(rx2 - rx1, x2 - rx1)
        
        # 确保mask区域有效
        if mask_x2 > mask_x1 and mask_y2 > mask_y1:
            region_mask[mask_y1:mask_y2, mask_x1:mask_x2] = 255
        else:
            logger.warning(f"Invalid mask region, skipping")
            return frame
        
        # 只处理小区域
        cleaned_region = self.cleaner.clean(region, region_mask)
        
        # 复制回原帧 - 使用原帧copy避免副作用
        result_frame = frame.copy()
        result_frame[ry1:ry2, rx1:rx2] = cleaned_region
        
        return result_frame

    def run_batch(
        self,
        input_video_dir_path: Path,
        output_video_dir_path: Path | None = None,
        progress_callback: Callable[[int], None] | None = None,
    ):
        """批量处理目录中的多个视频文件
        
        参考GitHub官方版本实现
        """
        if output_video_dir_path is None:
            output_video_dir_path = input_video_dir_path.parent / "watermark_removed"
            logger.warning(
                f"output_video_dir_path is not set, using {output_video_dir_path} as output_video_dir_path"
            )
        output_video_dir_path.mkdir(parents=True, exist_ok=True)
        input_video_paths = []
        for ext in VIDEO_EXTENSIONS:
            input_video_paths.extend(input_video_dir_path.rglob(f"*{ext}"))

        video_lengths = len(input_video_paths)
        logger.info(f"Found {video_lengths} video(s) to process")

        for idx, input_video_path in enumerate(
            tqdm(input_video_paths, desc="Processing videos")
        ):
            output_video_path = output_video_dir_path / input_video_path.name
            if progress_callback:

                def batch_progress_callback(single_video_progress: int):
                    overall_progress = int(
                        (idx / video_lengths) * 100 + (single_video_progress / video_lengths)
                    )
                    progress_callback(min(overall_progress, 100))

                self.run(
                    input_video_path, output_video_path, progress_callback=batch_progress_callback
                )
            else:
                self.run(
                    input_video_path, output_video_path, progress_callback=None
                )

    def run(
        self,
        input_video_path: Path,
        output_video_path: Path,
        progress_callback: Callable[[int], None] | None = None,
    ):
        """主处理入口，参考官方版本使用双次遍历模式（更稳定可靠）"""
        logger.info("使用双次遍历模式（官方版本逻辑）")
        return self._run_double_pass(input_video_path, output_video_path, progress_callback)

    def _run_single_pass(
        self,
        input_video_path: Path,
        output_video_path: Path,
        progress_callback: Callable[[int], None] | None = None,
    ):
        """单次遍历优化版本：边检测边清除，避免重复解码
        
        使用批量处理和跳帧检测进一步优化性能
        """
        input_video_loader = VideoLoader(input_video_path)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        width = input_video_loader.width
        height = input_video_loader.height
        fps = input_video_loader.fps
        total_frames = input_video_loader.total_frames

        temp_output_path = output_video_path.parent / f"temp_{output_video_path.name}"
        
        # 使用优化的编码参数
        video_codec = self._get_video_codec()
        output_options = {
            "pix_fmt": "yuv420p",
            "vcodec": video_codec,
        }
        
        # 根据编码器类型设置不同的参数
        if video_codec in ["h264_nvenc", "h264_videotoolbox"]:
            if input_video_loader.original_bitrate:
                output_options["video_bitrate"] = str(
                    int(int(input_video_loader.original_bitrate) * 1.2)
                )
            else:
                output_options["video_bitrate"] = "5M"
            logger.info(f"使用硬件加速编码器: {video_codec}")
        else:
            output_options["preset"] = self.ffmpeg_preset
            if input_video_loader.original_bitrate:
                output_options["video_bitrate"] = str(
                    int(int(input_video_loader.original_bitrate) * 1.2)
                )
            else:
                output_options["crf"] = "23"
            logger.info(f"使用软件编码器: {video_codec}, preset: {self.ffmpeg_preset}")

        process_out = (
            ffmpeg.input(
                "pipe:",
                format="rawvideo",
                pix_fmt="bgr24",
                s=f"{width}x{height}",
                r=fps,
            )
            .output(str(temp_output_path), **output_options)
            .overwrite_output()
            .global_args("-loglevel", "error")
            .run_async(pipe_stdin=True)
        )

        # 批处理缓冲区
        frame_buffer = []
        frame_indices = []
        last_bbox = None
        frames_since_detection = 0
        
        logger.info(
            f"开始单次遍历处理 | "
            f"检测间隔: {self.detection_interval}帧 | "
            f"批处理大小: {self.batch_size} | "
            f"区域处理: {'启用' if self.process_region_only else '禁用'}"
        )
        
        for idx, frame in enumerate(
            tqdm(input_video_loader, total=total_frames, desc="处理视频（单次遍历+批处理）")
        ):
            frame_buffer.append(frame)
            frame_indices.append(idx)
            
            # 当缓冲区满或到达最后一帧时，批量处理
            if len(frame_buffer) >= self.batch_size or idx == total_frames - 1:
                # 批量检测（只检测需要检测的帧）
                frames_to_detect = []
                detect_indices = []
                for i, (buf_idx, buf_frame) in enumerate(zip(frame_indices, frame_buffer)):
                    if buf_idx % self.detection_interval == 0:
                        frames_to_detect.append(buf_frame)
                        detect_indices.append(i)
                
                # 执行批量检测
                if frames_to_detect:
                    detections = self.detector.detect_batch(frames_to_detect)
                    detection_map = dict(zip(detect_indices, detections))
                else:
                    detection_map = {}
                
                # 处理缓冲区中的每一帧
                for i, (buf_idx, buf_frame) in enumerate(zip(frame_indices, frame_buffer)):
                    # 更新bbox - 简化逻辑，确保不漏帧
                    if i in detection_map:
                        detection = detection_map[i]
                        if detection["detected"]:
                            # YOLO检测成功，直接使用（简化验证，只检查基本有效性）
                            detected_bbox = detection["bbox"]
                            x1, y1, x2, y2 = detected_bbox
                            if x2 > x1 and y2 > y1:  # 只做基本检查，避免过度验证
                                last_bbox = detected_bbox
                                frames_since_detection = 0
                            # 如果bbox无效，继续使用上一帧的last_bbox（不更新frames_since_detection）
                        else:
                            # YOLO检测失败，继续使用上一帧的last_bbox
                            frames_since_detection += 1
                    else:
                        # 跳帧检测，继续使用上一帧的last_bbox
                        frames_since_detection += 1
                    
                    # 清除水印 - 核心逻辑：只要last_bbox存在就处理（除非设置了限制）
                    should_clean = last_bbox is not None
                    if self.max_frames_without_detection > 0:
                        should_clean = should_clean and frames_since_detection < self.max_frames_without_detection
                    
                    if should_clean:
                        if self.process_region_only:
                            # 区域处理模式：只处理水印区域（快3-5倍）
                            cleaned_frame = self._clean_region(buf_frame, last_bbox, width, height)
                        else:
                            # 全帧处理模式：处理整帧（传统方式）
                            x1, y1, x2, y2 = last_bbox
                            mask = np.zeros((height, width), dtype=np.uint8)
                            mask[y1:y2, x1:x2] = 255
                            cleaned_frame = self.cleaner.clean(buf_frame, mask)
                    else:
                        cleaned_frame = buf_frame
                    
                    process_out.stdin.write(cleaned_frame.tobytes())
                
                # 清空缓冲区
                frame_buffer = []
                frame_indices = []
            
            # 更新进度 (10% - 95%)
            if progress_callback and idx % 10 == 0:
                progress = 10 + int((idx / total_frames) * 85)
                progress_callback(progress)

        process_out.stdin.close()
        process_out.wait()

        if progress_callback:
            progress_callback(95)

        self.merge_audio_track(input_video_path, temp_output_path, output_video_path)

        if progress_callback:
            progress_callback(99)

    def _run_double_pass(
        self,
        input_video_path: Path,
        output_video_path: Path,
        progress_callback: Callable[[int], None] | None = None,
    ):
        """传统双次遍历版本：第一次检测，第二次清除"""
        input_video_loader = VideoLoader(input_video_path)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        width = input_video_loader.width
        height = input_video_loader.height
        fps = input_video_loader.fps
        total_frames = input_video_loader.total_frames

        temp_output_path = output_video_path.parent / f"temp_{output_video_path.name}"
        
        # 使用优化的编码参数
        video_codec = self._get_video_codec()
        output_options = {
            "pix_fmt": "yuv420p",
            "vcodec": video_codec,
        }
        
        # 根据编码器类型设置不同的参数
        if video_codec in ["h264_nvenc", "h264_videotoolbox"]:
            # 硬件编码器参数
            if input_video_loader.original_bitrate:
                output_options["video_bitrate"] = str(
                    int(int(input_video_loader.original_bitrate) * 1.2)
                )
            else:
                output_options["video_bitrate"] = "5M"  # 默认比特率
            logger.info(f"使用硬件加速编码器: {video_codec}")
        else:
            # 软件编码器参数
            output_options["preset"] = self.ffmpeg_preset
            if input_video_loader.original_bitrate:
                output_options["video_bitrate"] = str(
                    int(int(input_video_loader.original_bitrate) * 1.2)
                )
            else:
                output_options["crf"] = "18"  # 参考官方版本，使用CRF 18保证质量
            logger.info(f"使用软件编码器: {video_codec}, preset: {self.ffmpeg_preset}")

        process_out = (
            ffmpeg.input(
                "pipe:",
                format="rawvideo",
                pix_fmt="bgr24",
                s=f"{width}x{height}",
                r=fps,
            )
            .output(str(temp_output_path), **output_options)
            .overwrite_output()
            .global_args("-loglevel", "error")
            .run_async(pipe_stdin=True)
        )

        frame_bboxes = {}
        detect_missed = []
        bbox_centers = []
        bboxes = []

        logger.debug(
            f"total frames: {total_frames}, fps: {fps}, width: {width}, height: {height}"
        )
        for idx, frame in enumerate(
            tqdm(input_video_loader, total=total_frames, desc="Detect watermarks")
        ):
            # 参考官方版本：简单直接的检测逻辑，不添加复杂的模板匹配
            detection_result = self.detector.detect(frame)
            if detection_result["detected"]:
                frame_bboxes[idx] = {"bbox": detection_result["bbox"]}
                x1, y1, x2, y2 = detection_result["bbox"]
                bbox_centers.append((int((x1 + x2) / 2), int((y1 + y2) / 2)))
                bboxes.append((x1, y1, x2, y2))
            else:
                frame_bboxes[idx] = {"bbox": None}
                detect_missed.append(idx)
                bbox_centers.append(None)
                bboxes.append(None)
            # 10% - 50%
            if progress_callback and idx % 10 == 0:
                progress = 10 + int((idx / total_frames) * 40)
                progress_callback(progress)

        logger.debug(f"detect missed frames: {detect_missed}")
        # logger.debug(f"bbox centers: \n{bbox_centers}")
        if detect_missed:
            # 1. find the bkps of the bbox centers
            bkps = find_2d_data_bkps(bbox_centers)
            # add the start and end position, to form the complete interval boundaries
            bkps_full = [0] + bkps + [total_frames]
            # logger.debug(f"bkps intervals: {bkps_full}")

            # 2. calculate the average bbox of each interval
            interval_bboxes = get_interval_average_bbox(bboxes, bkps_full)
            # logger.debug(f"interval average bboxes: {interval_bboxes}")

            # 3. find the interval index of each missed frame
            missed_intervals = find_idxs_interval(detect_missed, bkps_full)
            # logger.debug(
            #     f"missed frame intervals: {list(zip(detect_missed, missed_intervals))}"
            # )

            # 4. fill the missed frames with the average bbox of the corresponding interval
            for missed_idx, interval_idx in zip(detect_missed, missed_intervals):
                if (
                    interval_idx < len(interval_bboxes)
                    and interval_bboxes[interval_idx] is not None
                ):
                    frame_bboxes[missed_idx]["bbox"] = interval_bboxes[interval_idx]
                    logger.debug(f"Filled missed frame {missed_idx} with bbox:\n"
                    f" {interval_bboxes[interval_idx]}")
                else:
                    # if the interval has no valid bbox, use the previous and next frame to complete (fallback strategy)
                    before = max(missed_idx - 1, 0)
                    after = min(missed_idx + 1, total_frames - 1)
                    before_box = frame_bboxes[before]["bbox"]
                    after_box = frame_bboxes[after]["bbox"]
                    if before_box:
                        frame_bboxes[missed_idx]["bbox"] = before_box
                    elif after_box:
                        frame_bboxes[missed_idx]["bbox"] = after_box
        else:
            del bboxes
            del bbox_centers
            del detect_missed
        
        input_video_loader = VideoLoader(input_video_path)

        for idx, frame in enumerate(tqdm(input_video_loader, total=total_frames, desc="Remove watermarks")):
            # 参考官方版本：支持区域处理模式（如果启用）或全帧处理
            bbox = frame_bboxes[idx]["bbox"]
            if bbox is not None:
                if self.process_region_only:
                    # 区域处理模式：只处理水印区域（快3-5倍）
                    cleaned_frame = self._clean_region(frame, bbox, width, height)
                else:
                    # 全帧处理模式：处理整帧（传统方式，更稳定可靠）
                    x1, y1, x2, y2 = bbox
                    mask = np.zeros((height, width), dtype=np.uint8)
                    mask[y1:y2, x1:x2] = 255
                    cleaned_frame = self.cleaner.clean(frame, mask)
            else:
                cleaned_frame = frame
            process_out.stdin.write(cleaned_frame.tobytes())

            # 50% - 95%
            if progress_callback and idx % 10 == 0:
                progress = 50 + int((idx / total_frames) * 45)
                progress_callback(progress)

        process_out.stdin.close()
        process_out.wait()

        # 95% - 99%
        if progress_callback:
            progress_callback(95)

        self.merge_audio_track(input_video_path, temp_output_path, output_video_path)

        if progress_callback:
            progress_callback(99)

    def merge_audio_track(
        self, input_video_path: Path, temp_output_path: Path, output_video_path: Path
    ):
        logger.info("Merging audio track...")
        video_stream = ffmpeg.input(str(temp_output_path))
        audio_stream = ffmpeg.input(str(input_video_path)).audio

        (
            ffmpeg.output(
                video_stream,
                audio_stream,
                str(output_video_path),
                vcodec="copy",
                acodec="aac",
            )
            .overwrite_output()
            .run(quiet=True)
        )
        # Clean up temporary file
        temp_output_path.unlink()
        logger.info(f"Saved no watermark video with audio at: {output_video_path}")


if __name__ == "__main__":
    from pathlib import Path

    input_video_path = Path(
        "resources/19700121_1645_68e0a027836c8191a50bea3717ea7485.mp4"
    )
    output_video_path = Path("outputs/sora_watermark_removed.mp4")
    sora_wm = SoraWM()
    sora_wm.run(input_video_path, output_video_path)
