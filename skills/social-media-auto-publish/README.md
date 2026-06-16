# social-media-auto-publish package

This folder stores the packaged Codex skill `social-media-auto-publish`.

## Files

- `README.md`: this package note
- `restore.sh`: restore the full skill package from base64 archive
- `social-media-auto-publish.tar.gz.base64`: full packaged skill archive
- `social-media-auto-publish.sha256`: SHA-256 checksum for the restored tar.gz

## Restore

```bash
mkdir -p /tmp/social-media-auto-publish-restore
cd /tmp/social-media-auto-publish-restore
curl -L -o social-media-auto-publish.tar.gz.base64 \
  https://raw.githubusercontent.com/784697524-ux/chengke/main/skills/social-media-auto-publish/social-media-auto-publish.tar.gz.base64
curl -L -o social-media-auto-publish.sha256 \
  https://raw.githubusercontent.com/784697524-ux/chengke/main/skills/social-media-auto-publish/social-media-auto-publish.sha256
curl -L -o restore.sh \
  https://raw.githubusercontent.com/784697524-ux/chengke/main/skills/social-media-auto-publish/restore.sh
bash restore.sh
```

The restored directory contains:

```text
social-media-auto-publish/
  SKILL.md
  README.md
  bin/sau
  install.sh
  scripts/
  skills/
  references/
  patches/
```

Runtime state is not included: cookies, logs, QR images, browser profiles, and virtual environments.
