FROM node:22.23.2-bookworm-slim AS node
FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git gh openssh-client gnupg minisign dpkg-dev openjdk-17-jre-headless apksigner ca-certificates && rm -rf /var/lib/apt/lists/*
COPY release/automation/requirements.txt /opt/gchat/requirements.txt
RUN pip install --no-cache-dir -r /opt/gchat/requirements.txt
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && npm install --global @tauri-apps/cli@2.11.4
COPY scripts /opt/gchat/scripts
COPY release/automation /opt/gchat/automation
RUN useradd --uid 10001 --create-home release
USER 10001
ENV PYTHONUNBUFFERED=1 TMPDIR=/state/tmp GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=/opt/gchat/automation/git-askpass GNUPGHOME=/state/gnupg TAURI_SIGNING_PRIVATE_KEY_PATH=/keys/updater.key GCHAT_RELEASE_PASSPHRASE_FILE=/keys/linux.password
ENTRYPOINT ["python3","/opt/gchat/automation/start"]
CMD ["--state","/state","--config","/config/controller.json"]
