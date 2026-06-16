#!/usr/bin/env bash
set -euo pipefail

archive="social-media-auto-publish.tar.gz"
base64_file="$archive.base64"
checksum_file="social-media-auto-publish.sha256"

if [ ! -f "$base64_file" ]; then
  echo "missing $base64_file" >&2
  exit 1
fi

base64 --decode "$base64_file" > "$archive"

if [ -f "$checksum_file" ]; then
  expected="$(cat "$checksum_file" | tr -d '[:space:]')"
  actual="$(shasum -a 256 "$archive" | awk '{print $1}')"
  if [ "$expected" != "$actual" ]; then
    echo "checksum mismatch" >&2
    echo "expected: $expected" >&2
    echo "actual:   $actual" >&2
    exit 1
  fi
fi

tar -xzf "$archive"
echo "Restored: $(pwd)/social-media-auto-publish"
