FROM node:22.23.2-bookworm-slim AS node
FROM ubuntu:24.04@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-pip git gh openssh-client gnupg minisign dpkg-dev openjdk-17-jre-headless apksigner ca-certificates skopeo && rm -rf /var/lib/apt/lists/*
RUN python3 -c "import hashlib,pathlib,urllib.request; data=urllib.request.urlopen('https://dl.k8s.io/release/v1.35.2/bin/linux/amd64/kubectl', timeout=60).read(); assert hashlib.sha256(data).hexdigest() == '924eb50779153f20cb668117d141440b95df2f325a64452d78dff9469145e277'; p=pathlib.Path('/usr/local/bin/kubectl'); p.write_bytes(data); p.chmod(0o755)"
COPY release/automation/requirements.txt /opt/gchat/requirements.txt
RUN python3 -m pip install --break-system-packages --no-cache-dir -r /opt/gchat/requirements.txt
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm && npm install --global @tauri-apps/cli@2.11.4
COPY scripts /opt/gchat/scripts
COPY release /opt/gchat/release
COPY release/automation /opt/gchat/automation
RUN useradd --uid 10001 --create-home release
USER 10001
ARG GCHAT_CONTROLLER_REVISION
ENV GCHAT_CONTROLLER_REVISION=$GCHAT_CONTROLLER_REVISION
ENV PYTHONUNBUFFERED=1 TMPDIR=/state/tmp GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=/opt/gchat/automation/git-askpass GNUPGHOME=/state/gnupg TAURI_SIGNING_PRIVATE_KEY_PATH=/keys/updater.key GCHAT_RELEASE_PASSPHRASE_FILE=/keys/linux.password
ENTRYPOINT ["python3","/opt/gchat/automation/start"]
CMD ["--state","/state","--config","/config/controller.json"]
