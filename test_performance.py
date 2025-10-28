"""
性能测试脚本

用法：
    python test_performance.py <video_path>
    
示例：
    python test_performance.py resources/puppies.mp4
"""

import sys
import time
from pathlib import Path

from loguru import logger

from sorawm.core import SoraWM


def test_performance(video_path: str):
    """测试视频处理性能"""
    
    video_path = Path(video_path)
    if not video_path.exists():
        logger.error(f"视频文件不存在: {video_path}")
        return
    
    # 输出文件路径
    output_path = Path("output") / f"test_performance_{video_path.stem}.mp4"
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    logger.info("=" * 60)
    logger.info("🚀 开始性能测试")
    logger.info(f"📹 输入视频: {video_path}")
    logger.info(f"📁 输出路径: {output_path}")
    logger.info("=" * 60)
    
    # 初始化处理器
    logger.info("初始化模型...")
    init_start = time.time()
    sora_wm = SoraWM()
    init_time = time.time() - init_start
    logger.info(f"✅ 模型初始化完成，耗时: {init_time:.2f}秒")
    
    # 显示当前配置
    logger.info("\n当前优化配置:")
    logger.info(f"  - 编码预设: {sora_wm.ffmpeg_preset}")
    logger.info(f"  - 硬件加速: {sora_wm.enable_hardware_encoding}")
    logger.info(f"  - 批处理大小: {sora_wm.batch_size}")
    logger.info(f"  - 检测间隔: {sora_wm.detection_interval}帧")
    logger.info(f"  - 单次遍历: {sora_wm.enable_single_pass}")
    logger.info("")
    
    # 运行处理
    logger.info("开始处理视频...")
    process_start = time.time()
    
    try:
        sora_wm.run(video_path, output_path)
        process_time = time.time() - process_start
        
        logger.info("=" * 60)
        logger.info("✅ 处理完成！")
        logger.info(f"⏱️  总耗时: {process_time:.2f}秒 ({process_time/60:.2f}分钟)")
        logger.info(f"📊 模型初始化: {init_time:.2f}秒")
        logger.info(f"📊 视频处理: {process_time:.2f}秒")
        logger.info(f"📁 输出文件: {output_path}")
        logger.info("=" * 60)
        
        # 计算处理速度
        from sorawm.utils.video_utils import VideoLoader
        loader = VideoLoader(video_path)
        video_duration = loader.total_frames / loader.fps
        speed_ratio = video_duration / process_time
        
        logger.info(f"\n📈 性能统计:")
        logger.info(f"  - 视频时长: {video_duration:.1f}秒")
        logger.info(f"  - 处理时间: {process_time:.1f}秒")
        logger.info(f"  - 处理速度: {speed_ratio:.2f}x (1秒视频需要{1/speed_ratio:.2f}秒处理)")
        
        if speed_ratio >= 0.5:
            logger.info(f"  - ✅ 性能优秀！接近实时处理")
        elif speed_ratio >= 0.1:
            logger.info(f"  - ✅ 性能良好")
        else:
            logger.info(f"  - ⚠️ 性能一般，建议检查配置或硬件")
        
        # 估算不同长度视频的处理时间
        logger.info(f"\n⏱️ 处理时间估算:")
        for duration in [30, 60, 120, 300]:
            estimated = duration / speed_ratio
            logger.info(f"  - {duration}秒视频: 约{estimated:.1f}秒 ({estimated/60:.1f}分钟)")
        
    except Exception as e:
        logger.error(f"❌ 处理失败: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n❌ 错误: 请提供视频文件路径")
        print("\n可用的测试视频:")
        resources = Path("resources")
        if resources.exists():
            for video in resources.glob("*.mp4"):
                print(f"  - {video}")
        sys.exit(1)
    
    video_path = sys.argv[1]
    test_performance(video_path)


if __name__ == "__main__":
    main()

