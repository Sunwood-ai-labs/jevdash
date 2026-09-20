"""FFmpeg-based lossless/high-quality MP4 video recorder for Pygame."""

import os
import subprocess
import pygame


class VideoRecorder:
    """Streams Pygame frames into an FFmpeg stdin pipe to generate crisp MP4 videos."""

    def __init__(self, output_path: str, width: int, height: int, fps: int = 60):
        self.output_path = output_path
        self.width = width
        self.height = height
        self.fps = fps
        self.process = None
        self.frame_count = 0

        # Ensure destination directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if exists
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "rgb24",
            "-r", str(fps),
            "-i", "-",  # Read from stdin
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-crf", "20",  # High quality
            "-movflags", "+faststart",  # Web/preview friendly
            output_path
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            print(f"[VideoRecorder] Warning: Failed to start FFmpeg: {e}")
            self.process = None

    def record_frame(self, surface: pygame.Surface):
        """Captures the current Pygame surface and writes raw bytes to FFmpeg stdin."""
        if not self.process or not self.process.stdin:
            return

        try:
            # Convert surface to raw 24-bit RGB byte buffer
            raw_bytes = pygame.image.tobytes(surface, "RGB")
            self.process.stdin.write(raw_bytes)
            self.frame_count += 1
        except Exception as e:
            print(f"[VideoRecorder] Error writing frame: {e}")
            self.close()

    def close(self):
        """Closes the FFmpeg stdin pipe and finishes encoding the MP4 file."""
        if self.process:
            try:
                if self.process.stdin:
                    self.process.stdin.close()
                self.process.wait(timeout=10)
            except Exception as e:
                print(f"[VideoRecorder] Error closing FFmpeg: {e}")
                self.process.kill()
            finally:
                self.process = None
                print(f"[VideoRecorder] Video saved: {self.output_path} ({self.frame_count} frames)")
