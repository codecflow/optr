FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    git curl ca-certificates \
    build-essential pkg-config meson ninja-build cmake \
    python3 python3-dev python3-venv \
    python3-gi python3-gi-cairo gir1.2-gstreamer-1.0 \
    libgirepository-2.0-dev libglib2.0-dev libcairo2-dev libffi-dev \
    gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav \
    libegl1 libgles2 libgl1-mesa-dri libgbm1 libosmesa6 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

ENV MUJOCO_GL=egl

WORKDIR /workspace
