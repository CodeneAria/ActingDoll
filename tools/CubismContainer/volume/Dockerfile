FROM node:25.2.1-alpine3.23

ARG CORE_ARCHIVE_DIR="./volume/Core"

ARG GIT_FRAMEWORK_REPO="https://github.com/Live2D/CubismWebFramework.git"
ARG GIT_FRAMEWORK_TAG="5-r.4"
ARG GIT_FRAMEWORK_DIR_NAME="Framework"

ARG GIT_SAMPLE_REPO="https://github.com/Live2D/CubismWebSamples.git"
ARG GIT_SAMPLE_TAG="5-r.4"
ARG GIT_SAMPLE_DIR_NAME="Samples"

# Install git
RUN apk add git
WORKDIR /root/workspace/Cubism

RUN mkdir Core

RUN git clone --branch ${GIT_FRAMEWORK_TAG} ${GIT_FRAMEWORK_REPO} ${GIT_FRAMEWORK_DIR_NAME}
#RUN git clone --recursive --branch ${GIT_FRAMEWORK_TAG} ${GIT_FRAMEWORK_REPO} ${GIT_FRAMEWORK_DIR_NAME}
RUN git clone --branch ${GIT_SAMPLE_TAG} ${GIT_SAMPLE_REPO} ${GIT_SAMPLE_DIR_NAME}

# Copy Core files
COPY ${CORE_ARCHIVE_DIR}/ ./${GIT_SAMPLE_DIR_NAME}/Core
COPY ${CORE_ARCHIVE_DIR}/ ./Core
RUN rm -rf ${GIT_SAMPLE_DIR_NAME}/Framework;\
    ln -s /root/workspace/Cubism/${GIT_FRAMEWORK_DIR_NAME} ${GIT_SAMPLE_DIR_NAME}/Framework

# Install dependencies
RUN apk add python3; \
    apk add py3-pip; \
    apk add py3-websockets;

# Install Python dependencies for acting_doll
RUN pip3 install --break-system-packages websockets

# Build TypeScript Demo
WORKDIR /root/workspace/Cubism/${GIT_SAMPLE_DIR_NAME}/Samples/TypeScript/Demo
RUN npm install -g npm && \
    npm install && \
    npm audit fix && \
    npm run build

# Set working directory
WORKDIR /root/workspace/acting_doll

# Set environment variable for model directory
ENV CUBISM_MODEL_DIR=/root/workspace/Cubism/models


# Expose WebSocket port
#EXPOSE 8765
# CMD ["python3", "-m", "websocket_server", "--host", "0.0.0.0"]
# python3 -m websocket_server
