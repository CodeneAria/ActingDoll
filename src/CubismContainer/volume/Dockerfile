FROM node:25.2.1-alpine3.23

###############################################################################
# Set environment variable for model directory
ENV CUBISM_MODEL_DIR=/root/workspace/adapter/Cubism/Resources
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
    && cp -r ./Resources/* ./adapter/Cubism/Resources/ \
    && cp -r ./${SDK_ARCHIVE}/Framework/ ./adapter/Cubism/ \
    && cp -r ./${SDK_ARCHIVE}/Core/ ./adapter/Cubism/ \
    && cp -r ./${SDK_ARCHIVE}/Samples/Resources/ ./adapter/Cubism/Sample/ \
    && rm -rf ${SDK_ARCHIVE}

###############################################################################
# Build pipelines for production
RUN cd ./adapter/server \
    && rm -rf dist/ build/ *.egg-info/ \
    && pip install --break-system-packages --root-user-action=ignore --upgrade ./
RUN cd ./adapter/acting_doll \
    && npm install -g npm && npm audit fix;

###############################################################################
RUN echo -e "Created: $(date)\nCubismSDKForWEB: ${SDK_ARCHIVE}\nDEV: false" > ./adapter/__version__

###############################################################################
# Build pipelines for production
ARG MOC3_SCALE=1.4
ARG MOC3_HORIZONTAL=0.4
ARG MOC3_VERTICAL=-0.4
ARG MOC3_CUSTOM_MOTION=false

RUN if [ "${MOC3_CUSTOM_MOTION}" = "true" ]; then \
    update-model --horizontal ${MOC3_HORIZONTAL} --vertical ${MOC3_VERTICAL} --scale ${MOC3_SCALE} --custom; \
else \
    update-model --horizontal ${MOC3_HORIZONTAL} --vertical ${MOC3_VERTICAL} --scale ${MOC3_SCALE}; \
fi
RUN cd ./adapter/acting_doll && npm run build:prod

###############################################################################
# Set working directory
WORKDIR /root/workspace/adapter

# Expose WebSocket port
ENTRYPOINT ["/bin/sh", "start.sh" ]
