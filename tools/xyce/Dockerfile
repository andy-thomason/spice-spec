# Serial Xyce 7.10 built from the release tags on GitHub, following Xyce's own
# INSTALL.md (CMake build). Only official sources: the Ubuntu base image,
# Xyce/Xyce, trilinos/Trilinos, DrTimothyAldenDavis/SuiteSparse.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential gfortran cmake bison flex libfl-dev libfftw3-dev \
      libblas-dev liblapack-dev curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build

# SuiteSparse (AMD and its config library only), needed by Trilinos.
RUN curl -fsSL -o ss.tgz https://github.com/DrTimothyAldenDavis/SuiteSparse/archive/refs/tags/v7.8.3.tar.gz \
 && sha256sum ss.tgz && mkdir ss && tar xzf ss.tgz -C ss --strip-components=1 \
 && cmake -S ss -B ss-build -D CMAKE_BUILD_TYPE=Release -D CMAKE_INSTALL_PREFIX=/opt/suitesparse \
      -D SUITESPARSE_ENABLE_PROJECTS="suitesparse_config;amd" \
 && cmake --build ss-build -j 16 -t install && rm -rf ss ss-build ss.tgz
ENV LD_LIBRARY_PATH=/opt/suitesparse/lib

# Xyce release tag (its source is only used to build it).
RUN curl -fsSL -o xyce.tgz https://github.com/Xyce/Xyce/archive/refs/tags/Release-7.10.0.tar.gz \
 && sha256sum xyce.tgz && mkdir xyce && tar xzf xyce.tgz -C xyce --strip-components=1 && rm xyce.tgz

# Trilinos 14.4.0, serial, with the options Xyce ships for it.
RUN curl -fsSL -o tri.tgz https://github.com/trilinos/Trilinos/archive/refs/tags/trilinos-release-14-4-0.tar.gz \
 && sha256sum tri.tgz && mkdir tri && tar xzf tri.tgz -C tri --strip-components=1 && rm tri.tgz
RUN mkdir tri-build && cd tri-build \
 && cmake -C /build/xyce/cmake/trilinos/trilinos-base.cmake \
      -D CMAKE_BUILD_TYPE=Release -D CMAKE_INSTALL_PREFIX=/opt/trilinos \
      -D AMD_LIBRARY_DIRS=/opt/suitesparse/lib -D AMD_INCLUDE_DIRS=/opt/suitesparse/include/suitesparse \
      /build/tri \
 && cmake --build . -j 24 -t install \
 && cd .. && rm -rf tri tri-build

# Xyce itself.
RUN mkdir xyce-build && cd xyce-build \
 && cmake -D CMAKE_BUILD_TYPE=Release -D CMAKE_INSTALL_PREFIX=/opt/xyce -D Trilinos_ROOT=/opt/trilinos /build/xyce \
 && cmake --build . -j 8 -t install \
 && cd .. && rm -rf xyce xyce-build

ENV PATH=/opt/xyce/bin:$PATH
ENV XYCE_NO_TRACKING=1
WORKDIR /work
