import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent

# 加载 .env 环境变量，若存在则覆盖默认配置
env_path = ROOT / ".env"
load_dotenv(dotenv_path=env_path, override=False)


RESOURCES_DIR = ROOT / "resources"
WATER_MARK_TEMPLATE_IMAGE_PATH = RESOURCES_DIR / "watermark_template.png"

WATER_MARK_DETECT_YOLO_WEIGHTS = RESOURCES_DIR / "best.pt"

OUTPUT_DIR = ROOT / "output"

OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


DEFAULT_WATERMARK_REMOVE_MODEL = "lama"

WORKING_DIR = ROOT / "working_dir"
WORKING_DIR.mkdir(exist_ok=True, parents=True)

LOGS_PATH = ROOT / "logs"
LOGS_PATH.mkdir(exist_ok=True, parents=True)

DATA_PATH = ROOT / "data"
DATA_PATH.mkdir(exist_ok=True, parents=True)

SQLITE_PATH = DATA_PATH / "db.sqlite3"


# ============= 性能优化配置 =============
# FFmpeg编码预设：faster(速度优先) / medium(平衡) / slow(质量优先)
FFMPEG_PRESET = "faster"

# 是否启用硬件加速编码（需要硬件支持）
ENABLE_HARDWARE_ENCODING = True

# 批处理大小：同时处理的帧数（越大GPU利用率越高，但内存占用也越大）
BATCH_SIZE = 8

# 跳帧检测间隔：每N帧检测一次水印（1=每帧检测，3=每3帧检测一次）
DETECTION_INTERVAL = 3

# 是否启用单次遍历优化（边检测边处理，避免重复解码）
ENABLE_SINGLE_PASS = True

# 是否只处理水印区域（而不是整帧），大幅提升性能
PROCESS_REGION_ONLY = True

# 处理区域的边距（像素），增加边距可以让过渡更自然
REGION_MARGIN = 30

# 检测失败后继续使用上一个bbox的最大帧数（0=无限制，一直使用最后的bbox）
MAX_FRAMES_WITHOUT_DETECTION = 0  # 0表示无限制，推荐设置


# ============= 清理参数（取消等级档位，直接参数化） =============
# 模板匹配阈值（如使用模板检测时）
TEMPLATE_THRESHOLD = float(os.getenv("TEMPLATE_THRESHOLD", "0.5"))

# 检测间隔与区域边距沿用上方基础配置（可通过环境变量覆盖 BATCH/INTERVAL/MARGIN 本身）



# 数据库类型配置
DATABASE_TYPE = "sqlite"  # 强制使用 sqlite

# ============= 验证码配置 =============
# 万能验证码（写死，用于开发和测试）
UNIVERSAL_VERIFICATION_CODE = os.getenv("UNIVERSAL_VERIFICATION_CODE", "888888")

# 是否启用验证码验证
VERIFICATION_CODE_ENABLED = os.getenv("VERIFICATION_CODE_ENABLED", "true").lower() == "true"
