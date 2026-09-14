#!/usr/bin/env bash
#
# Prepares a fresh Ubuntu 24.04 EC2 instance to run the app. Run once,
# over SSH, as the default ubuntu user:
#
#   curl -fsSL https://raw.githubusercontent.com/<owner>/adaptive-quiz/main/scripts/server-setup.sh | bash
#
# Installs Docker from Docker's own repository (Ubuntu's package lags
# behind and its compose plugin predates the !reset override syntax the
# production overlay uses), adds a swap file so building the frontend
# image on 2 GB of memory does not get killed, and clones the repo.
#
# Safe to re-run: every step checks whether it has already happened.

set -euo pipefail

readonly REPO_URL="${REPO_URL:-https://github.com/Auroaruora/adaptive-quiz.git}"
readonly CHECKOUT="$HOME/adaptive-quiz"
readonly SWAP_FILE=/swapfile
readonly SWAP_SIZE=2G

log() {
  echo "==> $*"
}

install_docker() {
  if command -v docker >/dev/null; then
    log "docker already installed: $(docker --version)"
    return
  fi
  log "installing docker"
  curl -fsSL https://get.docker.com | sudo sh
  # Lets the ubuntu user run docker without sudo. Takes effect on the
  # next login, which is why the script says so at the end.
  sudo usermod -aG docker "$USER"
}

add_swap() {
  if [[ -f "$SWAP_FILE" ]]; then
    log "swap already present"
    return
  fi
  log "adding ${SWAP_SIZE} swap"
  sudo fallocate -l "$SWAP_SIZE" "$SWAP_FILE"
  sudo chmod 600 "$SWAP_FILE"
  sudo mkswap "$SWAP_FILE"
  sudo swapon "$SWAP_FILE"
  echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab >/dev/null
}

clone_repo() {
  if [[ -d "$CHECKOUT/.git" ]]; then
    log "repo already cloned at $CHECKOUT"
    return
  fi
  log "cloning $REPO_URL"
  git clone "$REPO_URL" "$CHECKOUT"
}

main() {
  sudo apt-get update -q
  sudo apt-get install -y -q git curl
  install_docker
  add_swap
  clone_repo
  cat <<MSG

Done. Next:
  1. log out and back in so the docker group applies
  2. write $CHECKOUT/.env (see docs/deploy.md for the keys)
  3. run $CHECKOUT/scripts/deploy.sh
MSG
}

main "$@"
