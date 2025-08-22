"""GStreamer element factory functions organized by category."""

# Core functionality
from .base import create

# Application interface elements
from .app import AppSink, AppSrc, appsink, appsrc

# Network streaming elements
from .network import (
    RTMPSink,
    RTPSource,
    SHMSink,
    SHMSource,
    UDPSink,
    UDPSource,
    rtmpsink,
    rtmpsrc,
    shmsink,
    shmsrc,
    udpsink,
    udpsrc,
)

# Encoding/decoding elements
from .encoding import (
    AVDecH264, AVDecH265, AVDecVP8, AVDecVP9,
    DecodeBin, X264Enc, X265Enc, VP8Enc, VP9Enc,
    AACEnc, OpusEnc, VorbisEnc, AACDec, OpusDec, VorbisDec,
    avdec_h264, avdec_h265, avdec_vp8, avdec_vp9,
    decodebin, x264enc, x265enc, vp8enc, vp9enc,
    aacenc, opusenc, vorbisenc, aacdec, opusdec, vorbisdec,
)

# Parser elements
from .parsing import (
    H264Parse, H265Parse, AACParse, VP8Parse, VP9Parse,
    AC3Parse, MPEGAudioParse, RawAudioParse, RawVideoParse,
    h264parse, h265parse, aacparse, vp8parse, vp9parse,
    ac3parse, mpegaudioparse, rawaudioparse, rawvideoparse,
)

# Video processing elements
from .processing import (
    AudioConvert, AudioMixer, AudioPanorama, AudioResample,
    CapsFilter, Compositor, Identity, Level, Queue, Tee,
    Valve, VideoBox, VideoConvert, VideoCrop, VideoFlip,
    VideoRate, VideoScale, Volume,
    audioconvert, audiomixer, audiopanorama, audioresample,
    capsfilter, compositor, identity, level, queue, tee,
    valve, videobox, videoconvert, videocrop, videoflip,
    videorate, videoscale, volume,
)

# Muxing and payload elements
from .muxing import (
    AVIMux, FLVMux, MatroskaMux, MP4Mux, MPEGTSMux, OggMux, WebMMux,
    RTPH264Depay, RTPH264Pay, RTPH265Depay, RTPH265Pay,
    RTPVP8Depay, RTPVP8Pay, RTPVP9Depay, RTPVP9Pay,
    avimux, flvmux, matroskamux, mp4mux, mpegtsmux, oggmux, webmmux,
    payloader, rtph264depay, rtph265depay, rtph265pay,
    rtpvp8depay, rtpvp8pay, rtpvp9depay, rtpvp9pay,
)

# File I/O elements
from .file import FileSink, FileSource, filesink, filesrc

# Test elements
from .test import VideoTestSource, videotestsrc

__all__ = [
    # Core
    "create",
    # App elements
    "appsrc", "appsink", "AppSrc", "AppSink",
    # Network elements
    "shmsink", "shmsrc", "udpsink", "udpsrc", "rtmpsink", "rtmpsrc",
    "SHMSink", "SHMSource", "UDPSink", "UDPSource", "RTMPSink", "RTPSource",
    # Encoding/decoding elements
    "x264enc", "x265enc", "vp8enc", "vp9enc", "decodebin",
    "avdec_h264", "avdec_h265", "avdec_vp8", "avdec_vp9",
    "aacenc", "opusenc", "vorbisenc", "aacdec", "opusdec", "vorbisdec",
    "X264Enc", "X265Enc", "VP8Enc", "VP9Enc", "DecodeBin",
    "AVDecH264", "AVDecH265", "AVDecVP8", "AVDecVP9",
    "AACEnc", "OpusEnc", "VorbisEnc", "AACDec", "OpusDec", "VorbisDec",
    # Parser elements
    "h264parse", "h265parse", "aacparse", "vp8parse", "vp9parse",
    "ac3parse", "mpegaudioparse", "rawaudioparse", "rawvideoparse",
    "H264Parse", "H265Parse", "AACParse", "VP8Parse", "VP9Parse",
    "AC3Parse", "MPEGAudioParse", "RawAudioParse", "RawVideoParse",
    # Processing elements
    "queue", "capsfilter", "videoconvert", "videoscale", "videorate", "tee",
    "audioconvert", "audioresample", "audiopanorama", "audiomixer",
    "identity", "valve", "videoflip", "videocrop", "videobox",
    "compositor", "volume", "level",
    "Queue", "CapsFilter", "VideoConvert", "VideoScale", "VideoRate", "Tee",
    "AudioConvert", "AudioResample", "AudioPanorama", "AudioMixer",
    "Identity", "Valve", "VideoFlip", "VideoCrop", "VideoBox",
    "Compositor", "Volume", "Level",
    # Muxing elements
    "flvmux", "mp4mux", "qtmux", "matroskamux", "mpegtsmux", "avimux", "webmmux", "oggmux",
    "payloader", "rtph264depay", "rtph265pay", "rtph265depay",
    "rtpvp8pay", "rtpvp8depay", "rtpvp9pay", "rtpvp9depay",
    "FLVMux", "MP4Mux", "QtMux", "MatroskaMux", "MPEGTSMux", "AVIMux", "WebMMux", "OggMux",
    "RTPH264Pay", "RTPH264Depay", "RTPH265Pay", "RTPH265Depay",
    "RTPVP8Pay", "RTPVP8Depay", "RTPVP9Pay", "RTPVP9Depay",
    # File elements
    "filesrc", "filesink", "FileSource", "FileSink",
    # Test elements
    "videotestsrc", "VideoTestSource",
]
