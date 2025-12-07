FROM node:25.2.1-alpine3.23

ARG CORE_ARCHIVE_DIR="./volume/Core"

ARG GIT_FRAMEWORK_REPO="https://github.com/Live2D/CubismWebFramework.git"
ARG GIT_FRAMEWORK_TAG="5-r.4"
ARG GIT_FRAMEWORK_DIR_NAME="Framework"

ARG GIT_SAMPLE_REPO="https://github.com/Live2D/CubismWebSamples.git"
ARG GIT_SAMPLE_TAG="5-r.4"
ARG GIT_SAMPLE_DIR_NAME="CubismSdkForWeb"

# Install git
RUN apk add git
WORKDIR /root/work

RUN mkdir Core

RUN git clone --recursive --branch ${GIT_FRAMEWORK_TAG} ${GIT_FRAMEWORK_REPO} ${GIT_FRAMEWORK_DIR_NAME}
RUN git clone --recursive --branch ${GIT_SAMPLE_TAG} ${GIT_SAMPLE_REPO} ${GIT_SAMPLE_DIR_NAME}

# Copy Core files
COPY ${CORE_ARCHIVE_DIR}/ ./${GIT_SAMPLE_DIR_NAME}/Core
COPY ${CORE_ARCHIVE_DIR}/ ./Core

WORKDIR /root/work/${GIT_SAMPLE_DIR_NAME}/Samples/TypeScript/Demo
RUN npm install -g npm && \
    npm install && \
    npm audit fix && \
    npm run build

WORKDIR /root/work/model
