FROM node:25.2.1-alpine3.23

# Set environment variable for model directory
ENV CUBISM_MODEL_DIR=/root/workspace/Cubism/Resources
# Install dependencies
RUN apk add \
    python3 py3-pip py3-websockets \
    git
RUN pip3 install --break-system-packages websockets "mcp[cli]"

# Set working directory
WORKDIR /root/workspace/Cubism

###############################################################################
# Define build arguments
ARG CORE_ARCHIVE_DIR="./volume/Core"

ARG GIT_FRAMEWORK_DIR_NAME="Framework"
ARG GIT_FRAMEWORK_REPO="https://github.com/Live2D/CubismWebFramework.git"
ARG GIT_FRAMEWORK_TAG="5-r.5-beta.3"
###############################################################################

# Install Cubism SDK
RUN mkdir Core; \
    git clone --branch ${GIT_FRAMEWORK_TAG} ${GIT_FRAMEWORK_REPO} ${GIT_FRAMEWORK_DIR_NAME};
#   git clone --recursive --branch ${GIT_FRAMEWORK_TAG} ${GIT_FRAMEWORK_REPO} ${GIT_FRAMEWORK_DIR_NAME}

# Copy Core files
COPY ${CORE_ARCHIVE_DIR}/ ./Core

###############################################################################
# Define build arguments
ARG GIT_SAMPLE_DIR_NAME="Samples"
ARG GIT_SAMPLE_REPO="https://github.com/Live2D/CubismWebSamples.git"
ARG GIT_SAMPLE_TAG=""
###############################################################################

# Build Demo on CubismWebSamples
RUN if [ ! -z "${GIT_SAMPLE_DIR_NAME}" ] && [ ! -z "${GIT_SAMPLE_REPO}" ] && [ ! -z "${GIT_SAMPLE_TAG}" ]; then \
        git clone --branch ${GIT_SAMPLE_TAG} ${GIT_SAMPLE_REPO} ${GIT_SAMPLE_DIR_NAME}; \
        rm -rf ${GIT_SAMPLE_DIR_NAME}/Framework; \
        ln -s ./../${GIT_FRAMEWORK_DIR_NAME} ./${GIT_SAMPLE_DIR_NAME}/Framework; \
        rm -rf ${GIT_SAMPLE_DIR_NAME}/Core; \
        ln -s ./../Core ./${GIT_SAMPLE_DIR_NAME}/Core; \
        cd ./${GIT_SAMPLE_DIR_NAME}/Samples/TypeScript/Demo; \
        npm install -g npm && \
        npm install && \
        npm audit fix && \
        npm run build; \
    fi

# Set working directory
WORKDIR /root/workspace/adapter

# Expose WebSocket port
# python3 acting_doll_server.py --host 0.0.0.0 --port 8765
#CMD ["python3", "acting_doll_server.py", "--host", "0.0.0.0", "--port", "8765"]
