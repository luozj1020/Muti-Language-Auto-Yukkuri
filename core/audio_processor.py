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
        self.setup_ffmpeg_paths()  # 保留原有设置逻辑（可选）

    def setup_ffmpeg_paths(self):
        """设置FFmpeg路径（兼容性保障）"""
        ffmpeg_path = get_ffmpeg_path()
        ffprobe_path = get_ffprobe_path()
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffprobe = ffprobe_path
        print(f"FFmpeg paths set: {ffmpeg_path}, {ffprobe_path}")

    def process_audio(self, file_path, speed, volume, pitch, log_callback):
        """处理音频文件"""
        # 如果参数都是默认值，跳过处理
        if speed == 100 and volume == 100 and pitch == 100:
            return file_path

        log_callback(f"处理音频: 语速={speed}%, 音量={volume}%, 音程={pitch}%")

        try:
            # 确保FFmpeg路径正确设置
            self.setup_ffmpeg_paths()

            # 添加重试机制
            for attempt in range(3):
                try:
                    # 优先使用librosa处理音程
                    if pitch != 100:
                        return self.process_pitch_with_librosa(file_path, speed, volume, pitch, log_callback)
                    else:
                        return self.process_with_pydub(file_path, speed, volume, pitch, log_callback)
                except Exception as e:
                    if attempt < 2:
                        wait_time = 1 * (attempt + 1)
                        log_callback(f"音频处理失败，重试中 ({attempt + 1}/3): {str(e)}")
                        time.sleep(wait_time)
                    else:
                        raise e
        except Exception as e:
            log_callback(f"音频处理失败: {str(e)}")
            return file_path

    def process_pitch_with_librosa(self, file_path, speed, volume, pitch, log_callback):
        """使用librosa进行高质量音程调整"""
        try:
            # 确保FFmpeg路径正确设置
            self.setup_ffmpeg_paths()

            # 读取音频
            y, sr = librosa.load(file_path, sr=None)

            # 调整音程
            pitch_factor = pitch / 100.0
            semitones = 12 * math.log2(pitch_factor)
            y_shifted = librosa.effects.pitch_shift(y, sr=sr, n_steps=semitones)

            # 调整音量
            if volume != 100:
                volume_factor = volume / 100.0
                y_shifted = y_shifted * volume_factor
                if np.max(np.abs(y_shifted)) > 1.0:
                    y_shifted = y_shifted / np.max(np.abs(y_shifted)) * 0.95

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            sf.write(temp_path, y_shifted, sr)

            # 转换为AudioSegment
            audio = AudioSegment.from_wav(temp_path)

            # 调整语速
            if speed != 100:
                speed_factor = speed / 100.0
                audio = speedup(audio, playback_speed=speed_factor)

            # 保存处理后的文件
            processed_path = file_path.replace(".mp3", "_processed.mp3")

            # 导出音频文件
            audio.export(processed_path, format="mp3", bitrate="192k",
                         codec="libmp3lame", parameters=["-q:a", "2"])

            # 替换原始文件
            os.remove(file_path)
            os.rename(processed_path, file_path)

            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass

            log_callback("高质量音频处理完成")
            return file_path

        except ImportError:
            log_callback("警告: librosa库未安装，使用pydub方法")
            return self.process_with_pydub(file_path, speed, volume, pitch, log_callback)
        except Exception as e:
            log_callback(f"librosa处理失败: {str(e)}，使用pydub方法")
            return self.process_with_pydub(file_path, speed, volume, pitch, log_callback)

    def process_with_pydub(self, file_path, speed, volume, pitch, log_callback):
        """使用pydub处理音频"""
        try:
            # 确保FFmpeg路径正确设置
            self.setup_ffmpeg_paths()

            # 加载音频文件
            audio = AudioSegment.from_file(file_path, format="mp3")

            # 调整语速
            if speed != 100:
                speed_factor = speed / 100.0
                audio = speedup(audio, playback_speed=speed_factor)

            # 调整音量
            if volume != 100:
                volume_factor = volume / 100.0
                db_change = 20 * math.log10(max(volume_factor, 0.01))
                audio = audio.apply_gain(db_change)

            # 调整音高
            if pitch != 100:
                audio = self.adjust_pitch(audio, pitch)

            # 保存处理后的文件
            processed_path = file_path.replace(".mp3", "_processed.mp3")

            # 导出音频文件
            audio.export(processed_path, format="mp3", bitrate="192k",
                         codec="libmp3lame", parameters=["-q:a", "2"])

            # 替换原始文件
            os.remove(file_path)
            os.rename(processed_path, file_path)

            log_callback("pydub音频处理完成")
            return file_path

        except Exception as e:
            log_callback(f"pydub处理失败: {str(e)}")
            raise e

    def adjust_pitch(self, audio, pitch):
        """调整音高"""
        pitch_factor = pitch / 100.0

        # 方法1: 精确的采样率调整
        if 0.5 <= pitch_factor <= 2.0:
            new_sample_rate = int(audio.frame_rate * pitch_factor)
            pitched_audio = audio._spawn(
                audio.raw_data,
                overrides={'frame_rate': new_sample_rate}
            )
            return pitched_audio.set_frame_rate(audio.frame_rate)

        # 方法2: 分段处理极端值
        elif pitch_factor < 0.5:
            steps = max(2, int(-math.log2(pitch_factor)))
            step_factor = pitch_factor ** (1 / steps)
            temp_audio = audio

            for _ in range(steps):
                new_rate = int(temp_audio.frame_rate * step_factor)
                temp_audio = temp_audio._spawn(
                    temp_audio.raw_data,
                    overrides={'frame_rate': new_rate}
                ).set_frame_rate(temp_audio.frame_rate)

            return temp_audio

        else:  # pitch_factor > 2.0
            steps = max(2, int(math.log2(pitch_factor)))
            step_factor = pitch_factor ** (1 / steps)
            temp_audio = audio

            for _ in range(steps):
                new_rate = int(temp_audio.frame_rate * step_factor)
                temp_audio = temp_audio._spawn(
                    temp_audio.raw_data,
                    overrides={'frame_rate': new_rate}
                ).set_frame_rate(temp_audio.frame_rate)

            return temp_audio