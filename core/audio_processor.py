import os
import time
import math
import numpy as np
import librosa
import soundfile as sf

# 在导入 pydub 前设置环境变量
from core.utils import get_ffmpeg_path, get_ffprobe_path


# 关键步骤：提前设置 FFmpeg 路径
def _setup_ffmpeg_early():
    ffmpeg_path = get_ffmpeg_path()
    ffprobe_path = get_ffprobe_path()
    if os.path.exists(ffmpeg_path) and os.path.exists(ffprobe_path):
        # 直接设置环境变量（覆盖默认行为）
        os.environ["PATH"] += os.pathsep + os.path.dirname(ffmpeg_path)
        os.environ["FFMPEG_PATH"] = ffmpeg_path
        os.environ["FFPROBE_PATH"] = ffprobe_path


_setup_ffmpeg_early()

# 现在再导入 pydub
from pydub import AudioSegment
from pydub.effects import speedup
import tempfile


class AudioProcessor:
    def __init__(self):
        self.setup_ffmpeg_paths()

        # 音频处理参数优化
        self.default_sample_rate = 44100  # 高质量采样率
        self.processing_sample_rate = 44100  # 处理时使用的采样率
        self.output_bitrate = "320k"  # 高质量输出比特率
        self.quality_preset = "high"  # 质量预设

    def setup_ffmpeg_paths(self):
        """设置FFmpeg路径（兼容性保障）"""
        ffmpeg_path = get_ffmpeg_path()
        ffprobe_path = get_ffprobe_path()
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffprobe = ffprobe_path

    def process_audio(self, file_path, speed, volume, pitch, log_callback):
        """处理音频文件 - 优化版本"""
        # 如果参数都是默认值，跳过处理
        if speed == 100 and volume == 100 and pitch == 100:
            return file_path

        log_callback(f"开始高质量音频处理: 语速={speed}%, 音量={volume}%, 音程={pitch}%")

        try:
            # 确保FFmpeg路径正确设置
            self.setup_ffmpeg_paths()

            # 优化的处理策略：优先使用 librosa 进行高质量处理
            if self._has_librosa():
                return self.process_with_librosa_optimized(file_path, speed, volume, pitch, log_callback)
            else:
                log_callback("Librosa未安装，使用优化的pydub处理")
                return self.process_with_pydub_optimized(file_path, speed, volume, pitch, log_callback)

        except Exception as e:
            log_callback(f"音频处理失败: {str(e)}")
            return file_path

    def _has_librosa(self):
        """检查是否有librosa库"""
        try:
            import librosa
            return True
        except ImportError:
            return False

    def process_with_librosa_optimized(self, file_path, speed, volume, pitch, log_callback):
        """使用librosa进行优化的高质量音频处理"""
        try:
            log_callback("使用Librosa进行高质量处理...")

            # 使用更高质量的音频加载参数
            y, sr = librosa.load(file_path, sr=self.processing_sample_rate, mono=False)

            # 如果是立体声，分别处理左右声道
            if y.ndim > 1:
                processed_channels = []
                for channel in range(y.shape[0]):
                    channel_data = y[channel]
                    processed_channel = self._process_single_channel_librosa(
                        channel_data, sr, speed, volume, pitch, log_callback
                    )
                    processed_channels.append(processed_channel)
                processed_audio = np.vstack(processed_channels)
            else:
                processed_audio = self._process_single_channel_librosa(
                    y, sr, speed, volume, pitch, log_callback
                )

            # 保存为高质量临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name

            # 使用32位浮点保存，保持最高质量
            sf.write(temp_path, processed_audio.T if processed_audio.ndim > 1 else processed_audio,
                     sr, subtype='FLOAT')

            # 转换为最终格式
            self._convert_to_final_format(temp_path, file_path, log_callback)

            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass

            log_callback("Librosa高质量处理完成")
            return file_path

        except Exception as e:
            log_callback(f"Librosa处理失败: {str(e)}，回退到pydub")
            return self.process_with_pydub_optimized(file_path, speed, volume, pitch, log_callback)

    def _process_single_channel_librosa(self, audio_data, sr, speed, volume, pitch, log_callback):
        """使用librosa处理单声道音频"""
        processed = audio_data.copy()

        # 1. 音程调整（使用高质量算法）
        if pitch != 100:
            pitch_factor = pitch / 100.0
            semitones = 12 * math.log2(pitch_factor)

            # 使用更高质量的音程调整算法
            processed = librosa.effects.pitch_shift(
                processed, sr=sr, n_steps=semitones,
                bins_per_octave=24,  # 更高精度
                res_type='kaiser_best'  # 高质量重采样
            )
            log_callback(f"音程调整完成: {pitch}% ({semitones:.2f} 半音)")

        # 2. 语速调整（保持音程的时间拉伸）
        if speed != 100:
            speed_factor = speed / 100.0
            rate_factor = 1.0 / speed_factor  # 速度快则拉伸因子小

            # 使用高质量的时间拉伸算法
            processed = librosa.effects.time_stretch(
                processed, rate=rate_factor,
                hop_length=512,  # 更小的hop length提高质量
                res_type='kaiser_best'
            )
            log_callback(f"语速调整完成: {speed}%")

        # 3. 音量调整（带动态范围保护）
        if volume != 100:
            volume_factor = volume / 100.0
            processed = processed * volume_factor

            # 防止削波，使用软限制
            if np.max(np.abs(processed)) > 0.95:
                processed = self._apply_soft_limiter(processed, threshold=0.95)
                log_callback("应用软限制器防止削波")

            log_callback(f"音量调整完成: {volume}%")

        # 4. 音频质量增强
        processed = self._enhance_audio_quality(processed, sr, log_callback)

        return processed

    def _apply_soft_limiter(self, audio, threshold=0.95, ratio=0.1):
        """应用软限制器防止削波"""
        abs_audio = np.abs(audio)
        mask = abs_audio > threshold

        # 对超过阈值的部分应用软限制
        excess = abs_audio[mask] - threshold
        limited_excess = threshold + excess * ratio

        # 应用限制，保持原始符号
        audio[mask] = np.sign(audio[mask]) * limited_excess

        return audio

    def _enhance_audio_quality(self, audio, sr, log_callback):
        """音频质量增强"""
        try:
            # 轻微的去噪处理
            if len(audio) > sr:  # 只对长于1秒的音频进行处理
                # 使用spectral gating进行轻微去噪
                stft = librosa.stft(audio, hop_length=512)
                magnitude = np.abs(stft)

                # 计算谱门限
                spectral_mean = np.mean(magnitude, axis=1, keepdims=True)
                gate_threshold = 0.1 * spectral_mean

                # 应用温和的门限
                gated_magnitude = np.where(magnitude > gate_threshold,
                                           magnitude, magnitude * 0.5)

                # 重构音频
                phase = np.angle(stft)
                enhanced_stft = gated_magnitude * np.exp(1j * phase)
                audio = librosa.istft(enhanced_stft, hop_length=512)

                log_callback("应用音频增强处理")
        except:
            pass  # 增强失败不影响主流程

        return audio

    def process_with_pydub_optimized(self, file_path, speed, volume, pitch, log_callback):
        """使用pydub的优化处理方法"""
        try:
            log_callback("使用优化的pydub处理...")

            # 使用更高质量的加载参数
            audio = AudioSegment.from_file(file_path, format="mp3")

            # 转换为更高质量的格式进行处理
            audio = audio.set_frame_rate(self.processing_sample_rate)
            audio = audio.set_sample_width(4)  # 32位

            # 处理顺序优化：先调整音程，再调整语速，最后调整音量

            # 1. 音程调整（改进的算法）
            if pitch != 100:
                audio = self.adjust_pitch_enhanced(audio, pitch, log_callback)

            # 2. 语速调整
            if speed != 100:
                speed_factor = speed / 100.0
                audio = speedup(audio, playback_speed=speed_factor, chunk_size=150, crossfade=25)
                log_callback(f"语速调整完成: {speed}%")

            # 3. 音量调整（改进的动态范围处理）
            if volume != 100:
                audio = self.adjust_volume_enhanced(audio, volume, log_callback)

            # 4. 音频后处理
            audio = self.post_process_audio(audio, log_callback)

            # 保存处理后的文件
            processed_path = file_path.replace(".mp3", "_processed.mp3")

            # 使用高质量编码参数
            audio.export(processed_path, format="mp3",
                         bitrate=self.output_bitrate,
                         codec="libmp3lame",
                         parameters=[
                             "-q:a", "0",  # 最高质量
                             "-joint_stereo", "1",
                             "-reservoir", "1"
                         ])

            # 替换原始文件
            os.remove(file_path)
            os.rename(processed_path, file_path)

            log_callback("优化的pydub处理完成")
            return file_path

        except Exception as e:
            log_callback(f"优化pydub处理失败: {str(e)}")
            raise e

    def adjust_pitch_enhanced(self, audio, pitch, log_callback):
        """增强的音程调整算法"""
        pitch_factor = pitch / 100.0

        # 使用更平滑的音程调整策略
        if 0.8 <= pitch_factor <= 1.25:
            # 小幅度调整使用直接方法
            new_sample_rate = int(audio.frame_rate * pitch_factor)
            pitched_audio = audio._spawn(
                audio.raw_data,
                overrides={'frame_rate': new_sample_rate}
            )
            result = pitched_audio.set_frame_rate(audio.frame_rate)

        elif pitch_factor < 0.8:
            # 大幅度降调使用分步处理
            steps = max(2, int(-math.log2(pitch_factor) * 2))
            step_factor = pitch_factor ** (1 / steps)
            result = audio

            for i in range(steps):
                new_rate = int(result.frame_rate * step_factor)
                result = result._spawn(
                    result.raw_data,
                    overrides={'frame_rate': new_rate}
                ).set_frame_rate(result.frame_rate)

        else:  # pitch_factor > 1.25
            # 大幅度升调使用分步处理
            steps = max(2, int(math.log2(pitch_factor) * 2))
            step_factor = pitch_factor ** (1 / steps)
            result = audio

            for i in range(steps):
                new_rate = int(result.frame_rate * step_factor)
                result = result._spawn(
                    result.raw_data,
                    overrides={'frame_rate': new_rate}
                ).set_frame_rate(result.frame_rate)

        log_callback(f"音程调整完成: {pitch}%")
        return result

    def adjust_volume_enhanced(self, audio, volume, log_callback):
        """增强的音量调整，带动态范围压缩"""
        volume_factor = volume / 100.0

        if volume_factor > 1.0:
            # 放大音量时使用软限制
            db_change = 20 * math.log10(volume_factor)

            # 分步增益以避免过度失真
            if db_change > 6:  # 超过6dB分步处理
                steps = int(db_change / 6) + 1
                step_gain = db_change / steps
                result = audio

                for _ in range(steps):
                    result = result.apply_gain(step_gain)
                    # 应用软限制
                    if step_gain > 3:
                        result = result.compress_dynamic_range(threshold=-12.0, ratio=4.0)
            else:
                result = audio.apply_gain(db_change)

        else:
            # 减小音量
            db_change = 20 * math.log10(max(volume_factor, 0.01))
            result = audio.apply_gain(db_change)

        log_callback(f"音量调整完成: {volume}%")
        return result

    def post_process_audio(self, audio, log_callback):
        """音频后处理：轻微增强"""
        try:
            # 应用轻微的动态范围优化
            if audio.max_possible_amplitude > 0:
                # 标准化但保留动态范围
                normalized = audio.normalize(headroom=1.0)  # 保留1dB头空间

                # 轻微的EQ增强（如果需要）
                # 这里可以添加更多的后处理逻辑

                log_callback("应用音频后处理")
                return normalized
        except:
            pass

        return audio

    def _convert_to_final_format(self, temp_path, output_path, log_callback):
        """转换为最终格式"""
        try:
            # 加载临时文件
            audio = AudioSegment.from_wav(temp_path)

            # 应用最后的质量优化
            audio = audio.set_frame_rate(self.default_sample_rate)

            # 保存处理后的文件
            processed_path = output_path.replace(".mp3", "_processed.mp3")

            # 使用最高质量参数导出
            audio.export(processed_path, format="mp3",
                         bitrate=self.output_bitrate,
                         codec="libmp3lame",
                         parameters=[
                             "-q:a", "0",  # VBR最高质量
                             "-joint_stereo", "1",
                             "-reservoir", "1",
                             "-b:a", "320k"  # 确保比特率
                         ])

            # 替换原始文件
            os.remove(output_path)
            os.rename(processed_path, output_path)

            log_callback("音频格式转换完成")

        except Exception as e:
            log_callback(f"格式转换失败: {str(e)}")
            raise e

    # 为了向后兼容，保留原始方法
    def process_pitch_with_librosa(self, file_path, speed, volume, pitch, log_callback):
        """兼容性方法，调用优化版本"""
        return self.process_with_librosa_optimized(file_path, speed, volume, pitch, log_callback)

    def process_with_pydub(self, file_path, speed, volume, pitch, log_callback):
        """兼容性方法，调用优化版本"""
        return self.process_with_pydub_optimized(file_path, speed, volume, pitch, log_callback)

    def adjust_pitch(self, audio, pitch):
        """兼容性方法，调用增强版本"""
        return self.adjust_pitch_enhanced(audio, pitch, lambda msg: None)