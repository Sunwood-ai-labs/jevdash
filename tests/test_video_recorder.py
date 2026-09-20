"""Unit test for FFmpeg-based VideoRecorder."""

import os
import pygame
from jev_platformer.ui.video_recorder import VideoRecorder


def test_video_recorder_generates_valid_mp4(tmp_path):
    pygame.init()
    surface = pygame.Surface((320, 240))
    surface.fill((0, 200, 255))

    out_file = str(tmp_path / "test_output.mp4")
    recorder = VideoRecorder(out_file, 320, 240, fps=30)
    assert recorder.process is not None

    for i in range(15):
        # Draw small moving square
        surface.fill((0, 0, 0))
        pygame.draw.rect(surface, (0, 255, 200), (i * 10, 50, 40, 40))
        recorder.record_frame(surface)

    recorder.close()
    pygame.quit()

    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 1000  # Non-trivial MP4 file
