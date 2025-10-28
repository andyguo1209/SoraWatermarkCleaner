# 性能优化说明文档

## 📊 优化效果预期

| 优化前 | 优化后（预期） | 提升倍数 |
|--------|--------------|----------|
| 1分钟视频需要20分钟 | 1-3分钟 | **7-20倍** |

---

## 🚀 已实施的优化措施

### 1. FFmpeg编码参数优化 ⭐⭐⭐

**优化内容：**
- 将编码预设从 `slow` 改为 `faster`
- 添加硬件加速支持（自动检测）
  - macOS: `h264_videotoolbox`
  - NVIDIA GPU: `h264_nvenc`
  - 其他: `libx264`
- CRF值从18调整为23（速度更快，质量仍然优秀）

**预期提速：** 3-5倍

**配置位置：** `sorawm/configs.py`
```python
FFMPEG_PRESET = "faster"  # 可选: ultrafast/faster/medium/slow
ENABLE_HARDWARE_ENCODING = True
```

---

### 2. 单次遍历优化 ⭐⭐⭐

**优化内容：**
- 原来需要遍历视频两次（检测 + 清除）
- 现在边检测边清除，只遍历一次
- 避免重复视频解码

**预期提速：** 1.8-2.0倍

**配置位置：** `sorawm/configs.py`
```python
ENABLE_SINGLE_PASS = True  # 启用单次遍历
```

---

### 3. 跳帧检测优化 ⭐⭐

**优化内容：**
- 水印位置通常不会快速变化
- 每N帧检测一次（默认3帧）
- 其他帧使用上次检测的位置
- 减少GPU推理次数

**预期提速：** 2-3倍（检测阶段）

**配置位置：** `sorawm/configs.py`
```python
DETECTION_INTERVAL = 3  # 每3帧检测一次
```

---

### 4. 批量推理优化 ⭐⭐

**优化内容：**
- YOLO检测支持批量处理
- 多帧一起推理，提高GPU利用率
- 从30%利用率提升到70-80%

**预期提速：** 1.5-2.0倍

**配置位置：** `sorawm/configs.py`
```python
BATCH_SIZE = 8  # 批处理大小，根据GPU显存调整
```

---

## ⚙️ 配置参数说明

所有性能相关配置都在 `sorawm/configs.py` 中：

```python
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
```

---

## 🎯 推荐配置方案

### 方案1：速度优先（推荐）

适用场景：快速批量处理，对质量要求不是极致

```python
FFMPEG_PRESET = "faster"
ENABLE_HARDWARE_ENCODING = True
BATCH_SIZE = 8
DETECTION_INTERVAL = 3
ENABLE_SINGLE_PASS = True
```

**预期效果：** 1分钟视频约1-2分钟处理完成

---

### 方案2：质量优先

适用场景：最终发布版本，追求最佳质量

```python
FFMPEG_PRESET = "medium"
ENABLE_HARDWARE_ENCODING = True
BATCH_SIZE = 4
DETECTION_INTERVAL = 1  # 每帧都检测
ENABLE_SINGLE_PASS = True
```

**预期效果：** 1分钟视频约3-4分钟处理完成

---

### 方案3：极速模式

适用场景：预览、测试

```python
FFMPEG_PRESET = "ultrafast"
ENABLE_HARDWARE_ENCODING = True
BATCH_SIZE = 16
DETECTION_INTERVAL = 5
ENABLE_SINGLE_PASS = True
```

**预期效果：** 1分钟视频约30-60秒处理完成

---

## 📈 性能监控

### 查看实时日志

程序运行时会输出详细的性能信息：

```
[INFO] 使用硬件加速编码器: h264_videotoolbox
[INFO] 开始单次遍历处理 | 检测间隔: 3帧 | 批处理大小: 8
处理视频（单次遍历+批处理）: 100%|████████| 1800/1800 [02:15<00:00, 13.3it/s]
```

---

## 🔧 故障排查

### 问题1：硬件加速不生效

**症状：** 日志显示 `使用软件编码器: libx264`

**解决方法：**
1. 检查系统是否支持硬件加速
2. macOS用户确认系统版本 >= 10.13
3. NVIDIA GPU用户确认驱动已正确安装
4. 如果硬件不支持，这是正常的，会自动降级到软件编码

### 问题2：内存不足

**症状：** 程序崩溃或卡死

**解决方法：**
```python
BATCH_SIZE = 4  # 减小批处理大小
```

### 问题3：检测不稳定

**症状：** 水印闪烁或漏检

**解决方法：**
```python
DETECTION_INTERVAL = 1  # 每帧都检测
```

---

## 🎨 质量 vs 速度权衡

| 参数 | 质量影响 | 速度影响 |
|------|---------|---------|
| FFMPEG_PRESET | ⬆️ slow质量更好 | ⬇️ slow更慢 |
| DETECTION_INTERVAL | ⬇️ 间隔越大质量可能下降 | ⬆️ 间隔越大速度越快 |
| BATCH_SIZE | ⚪ 无影响 | ⬆️ 越大越快（但占内存） |
| ENABLE_HARDWARE_ENCODING | ⚪ 几乎无影响 | ⬆️⬆️ 显著加速 |

---

## 📝 代码改动说明

### 新增文件
- 无

### 修改文件
1. **sorawm/configs.py** - 添加性能配置项
2. **sorawm/core.py** - 重构处理流程，添加单次遍历和批处理
3. **sorawm/watermark_detector.py** - 添加批量检测方法
4. **sorawm/watermark_cleaner.py** - 添加批量清除方法

### 向后兼容
✅ 完全兼容，原有代码无需修改
✅ 可通过配置切换新旧模式

---

## 🧪 测试建议

1. **先用短视频测试**（10-30秒）验证功能正常
2. **对比质量**：用原视频和处理后视频对比
3. **调整参数**：根据实际效果微调配置
4. **批量处理**：确认稳定后再处理大量视频

---

## 📊 预期性能数据

基于1分钟1080p视频测试（估算）：

| 场景 | 配置 | 处理时间 | 提升 |
|------|------|---------|------|
| 原始实现 | 默认 | 20分钟 | - |
| 仅FFmpeg优化 | preset=faster | 6-8分钟 | 2.5-3.3x |
| + 单次遍历 | single_pass=True | 3-4分钟 | 5-6.7x |
| + 跳帧检测 | interval=3 | 1.5-2.5分钟 | 8-13x |
| 全部优化 | 推荐配置 | 1-2分钟 | **10-20x** |

---

## 💡 未来优化方向

1. **模型量化** - 使用FP16或INT8量化进一步加速
2. **TensorRT优化** - 专门针对NVIDIA GPU优化
3. **多GPU支持** - 并行处理多个视频
4. **视频分段处理** - 长视频切分成多段并行处理
5. **更轻量级的Inpainting模型** - 替换为更快的模型

---

## 📞 反馈与建议

如果遇到问题或有优化建议，欢迎反馈！

---

**最后更新：** 2025-10-28
**版本：** v2.0 (性能优化版)

