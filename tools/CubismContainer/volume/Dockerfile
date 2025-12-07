FROM node:25.2.1-alpine3.23

ARG SDK_GIT_REPO="https://github.com/Live2D/CubismWebSamples.git"
ARG SDK_GIT_TAG="5-r.4"
ARG CORE_ARCHIVE_DIR="./volume/Core"

RUN apk add git
WORKDIR /root/work

RUN git clone --recursive --branch ${SDK_GIT_TAG} ${SDK_GIT_REPO} CubismSdkForWeb

COPY ${CORE_ARCHIVE_DIR}/ ./CubismSdkForWeb/Core

WORKDIR /root/work/CubismSdkForWeb/Samples/TypeScript/Demo
RUN npm install -g npm && \
    npm install && \
    npm run build
