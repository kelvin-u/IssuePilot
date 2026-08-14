FROM node:22-bookworm-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends git ripgrep && rm -rf /var/lib/apt/lists/*

CMD ["bash"]
