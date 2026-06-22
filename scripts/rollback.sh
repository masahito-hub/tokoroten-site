#!/bin/bash
set -e
TAG="${1:-baseline-2026-06}"
echo "Rolling back to $TAG..."
git checkout "$TAG" -- theme/
./scripts/deploy.sh
echo "Rollback to $TAG complete."
