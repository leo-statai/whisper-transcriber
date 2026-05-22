#!/usr/bin/env bash
set -euo pipefail

echo "==> Adicionando chave GPG do NVIDIA Container Toolkit..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

echo "==> Adicionando repositório apt..."
curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null

echo "==> apt update..."
sudo apt-get update -qq

echo "==> Instalando nvidia-container-toolkit..."
sudo apt-get install -y nvidia-container-toolkit

echo "==> Configurando runtime do Docker..."
sudo nvidia-ctk runtime configure --runtime=docker

echo "==> Reiniciando Docker..."
sudo systemctl restart docker

echo
echo "OK. Verificando GPU dentro de um container:"
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi | head -15
