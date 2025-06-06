#!/bin/bash

# Este script automatiza a instalação completa do OracleNeverIdle como um serviço systemd.
# Ele deve ser executado a partir do seu diretório raiz.
#
# O que ele faz:
# 1. Verifica se está sendo executado com sudo.
# 2. Detecta automaticamente o caminho absoluto do projeto.
# 3. Cria um ambiente virtual Python ('venv') se não existir.
# 4. Instala as dependências do 'requirements.txt' no ambiente virtual.
# 5. Cria o arquivo de serviço systemd com os caminhos corretos.
# 6. Habilita e inicia o serviço.

# --- Verificação de Sudo ---
if [[ $EUID -ne 0 ]]; then
   echo "ERRO: Este script precisa ser executado com sudo." 
   echo "Uso: sudo ./setup_systemd.sh"
   exit 1
fi

echo "✅ Script executado com sudo."

# --- Configuração de Caminhos e Variáveis ---
# Detecta o diretório absoluto onde o script está localizado
WORKING_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
SERVICE_NAME="neveridle"
# Usa o usuário que chamou sudo como o dono do serviço.
# Isso evita problemas de permissão com a pasta do projeto.
SERVICE_USER=${SUDO_USER:-$(whoami)}
VENV_PATH="$WORKING_DIR/venv"
EXEC_START="$VENV_PATH/bin/python3 $WORKING_DIR/NeverIdle.py"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "-------------------------------------------------"
echo "Diretório do projeto detectado: $WORKING_DIR"
echo "O serviço será executado pelo usuário: $SERVICE_USER"
echo "-------------------------------------------------"

# --- Preparação do Ambiente Python ---
echo "🐍 Configurando ambiente virtual Python..."

if [ ! -d "$VENV_PATH" ]; then
    echo "Criando ambiente virtual em '$VENV_PATH'..."
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao criar o ambiente virtual."
        exit 1
    fi
else
    echo "Ambiente virtual já existe."
fi

echo "Instalando dependências do requirements.txt..."
# Instala as dependências como o usuário do serviço para manter as permissões corretas
sudo -u "$SERVICE_USER" "$VENV_PATH/bin/pip" install -r "$WORKING_DIR/requirements.txt"
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao instalar as dependências."
    exit 1
fi
echo "Dependências instaladas."


# --- Criação do Serviço Systemd ---
echo "⚙️ Criando o arquivo de serviço systemd..."

# Usando tee para escrever o arquivo como root
tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Oracle NeverIdle Script to keep the VPS active
After=network.target

[Service]
User=$SERVICE_USER
WorkingDirectory=$WORKING_DIR
ExecStart=$EXEC_START
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF

if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao criar o arquivo de serviço systemd."
    exit 1
fi
echo "Arquivo de serviço criado em '$SERVICE_FILE'."


# --- Ativação do Serviço ---
echo "🚀 Ativando e iniciando o serviço..."
systemctl daemon-reload
systemctl enable "$SERVICE_NAME.service"
systemctl start "$SERVICE_NAME.service"

echo ""
echo "--- Status do Serviço ---"
# Aguarda um pouco para dar tempo ao serviço de iniciar
sleep 2
systemctl status "$SERVICE_NAME.service" --no-pager -l

echo ""
echo "✅ Instalação concluída com sucesso!"
echo "Use 'sudo systemctl status $SERVICE_NAME.service' para verificar a qualquer momento." 