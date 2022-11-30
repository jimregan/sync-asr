from sync_asr.vtt_input import VTTCaption, VTTInput
import os


can_run = True
try:
    import webvtt
except ImportError:
    can_run = False


TEST_DIR = os.path.dirname(os.path.abspath(__file__))


def test_vtt_caption():
    pass


def test_vtt_input():
    pass