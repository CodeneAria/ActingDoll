FROM node:25.2.1-alpine3.23

ARG CORE_ARCHIVE_DIR="./volume/Core"

ARG GIT_FRAMEWORK_REPO="https://github.com/Live2D/CubismWebFramework.git"
ARG GIT_FRAMEWORK_TAG="5-r.5-beta.3"
ARG GIT_FRAMEWORK_DIR_NAME="Framework"

ARG GIT_SAMPLE_REPO="https://github.com/Live2D/CubismWebSamples.git"
ARG GIT_SAMPLE_TAG="5-r.5-beta.3"
ARG GIT_SAMPLE_DIR_NAME="Samples"

# Set environment variable for model directory
ENV CUBISM_MODEL_DIR=/root/workspace/Cubism/Resources

# Install dependencies
RUN apk add python3; \
    apk add py3-pip; \
    apk add py3-websockets; \
    apk add git

# Install Python dependencies for acting_doll
RUN pip3 install --break-system-packages websockets "mcp[cli]"

WORKDIR /root/workspace/Cubism

# Install Cubism SDK
RUN mkdir Core; \
    git clone --branch ${GIT_FRAMEWORK_TAG} ${GIT_FRAMEWORK_REPO} ${GIT_FRAMEWORK_DIR_NAME};
#   git clone --recursive --branch ${GIT_FRAMEWORK_TAG} ${GIT_FRAMEWORK_REPO} ${GIT_FRAMEWORK_DIR_NAME}

# Copy Core files
COPY ${CORE_ARCHIVE_DIR}/ ./Core

# Build Demo on CubismWebSamples
RUN git clone --branch ${GIT_SAMPLE_TAG} ${GIT_SAMPLE_REPO} ${GIT_SAMPLE_DIR_NAME}; \
    rm -rf ${GIT_SAMPLE_DIR_NAME}/Framework; \
    ln -s ./../${GIT_FRAMEWORK_DIR_NAME} ./${GIT_SAMPLE_DIR_NAME}/Framework; \
    rm -rf ${GIT_SAMPLE_DIR_NAME}/Core; \
    ln -s ./../Core ./${GIT_SAMPLE_DIR_NAME}/Core; \
    cd ./${GIT_SAMPLE_DIR_NAME}/Samples/TypeScript/Demo; \
    npm install -g npm && \
    npm install && \
    npm audit fix && \
    npm run build

# Set working directory
WORKDIR /root/workspace/adapter

# Expose WebSocket port
# python3 websocket_server.py --host 0.0.0.0 --port 8765
#CMD ["python3", "websocket_server.py", "--host", "0.0.0.0", "--port", "8765"]
