FROM node:25.2.1-alpine3.23

###############################################################################
# Set environment variable for model directory
ENV CUBISM_MODEL_DIR=/root/workspace/Cubism/Resources
# Install dependencies
RUN apk add \
    python3 py3-pip py3-websockets \
    git
RUN pip3 install --break-system-packages websockets "mcp[cli]"

###############################################################################
# Set working directory
WORKDIR /root/workspace

###############################################################################
# Copy Core files
ARG ADAPTER_DIR="./volume/temp_adapter"
COPY ${ADAPTER_DIR} ./
RUN mkdir -p /root/workspace/adapter/allowed

###############################################################################
# unzip SDK archive
ARG SDK_ARCHIVE="CubismSDK*"
#RUN unzip -q ${SDK_ARCHIVE}.zip && rm ${SDK_ARCHIVE}.zip && mv ${SDK_ARCHIVE} Cubism
RUN unzip -q ${SDK_ARCHIVE}.zip \
    && mkdir -p ./adapter/Cubism/Resources \
    && cp -r ./Resources ./adapter/Cubism/ \
    && cp -r ./${SDK_ARCHIVE}/Framework/ ./adapter/Cubism/ \
    && cp -r ./${SDK_ARCHIVE}/Core/ ./adapter/Cubism/ \
    && cp -r ./${SDK_ARCHIVE}/Samples/Resources/ ./adapter/Cubism/Sample/ \
    && rm -rf ${SDK_ARCHIVE}

###############################################################################
# Build pipelines for production
RUN cd ./adapter/server \
    && rm -rf dist/ build/ *.egg-info/ \
    && pip install --break-system-packages --root-user-action=ignore --upgrade ./ \
    && update-model

###############################################################################
# Build pipelines for production
RUN cd ./adapter/acting_doll \
    && npm install -g npm && npm audit fix;
RUN cd ./adapter/acting_doll \
    && npm run build:prod

###############################################################################
RUN echo -e "Created: $(date)\nCubismSDKForWEB: ${SDK_ARCHIVE}\nDEV: false" > ./adapter/__version__

###############################################################################
# Set working directory
WORKDIR /root/workspace/adapter

# Expose WebSocket port
ENTRYPOINT ["/bin/sh", "start.sh" ]
