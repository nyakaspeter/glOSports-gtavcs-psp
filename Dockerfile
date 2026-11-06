# syntax=docker/dockerfile:1
# Build environment for vice-city-stories-recomp (GTA Vice City Stories, PSP
# static recompilation) on goodluckOS: armhf cross-compiler, SDL2, FFmpeg 7.
# Debian trixie: its FFmpeg 7.1 matches the headers upstream vendors (the
# console's glibc is 2.44, newer than trixie's 2.41).
# The source is mounted from upstream/ by build.sh, so rebuilds are incremental.
FROM debian:trixie

RUN dpkg --add-architecture armhf && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates cmake ninja-build pkg-config file g++ patchelf \
        crossbuild-essential-armhf \
        libsdl2-dev:armhf \
        libavcodec-dev:armhf libavformat-dev:armhf libavutil-dev:armhf \
        libswresample-dev:armhf libswscale-dev:armhf \
        libegl-dev:armhf libgles-dev:armhf && \
    rm -rf /var/lib/apt/lists/*

ENV PKG_CONFIG_PATH=/usr/lib/arm-linux-gnueabihf/pkgconfig
ENV PKG_CONFIG_LIBDIR=/usr/lib/arm-linux-gnueabihf/pkgconfig
ENV PKG_CONFIG_ALLOW_CROSS=1
