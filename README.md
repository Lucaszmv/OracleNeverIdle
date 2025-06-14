# 🤖 OracleNeverIdle Script

Este script Python ajuda a manter sua máquina virtual (VPS) "Always Free" da Oracle Cloud (OCI) ativa, simulando o uso de CPU, RAM e rede para evitar a recuperação de recursos por inatividade.

**O que ele faz?** ✨

*   🧠 **Simula Uso de CPU:** Gera uma carga de trabalho para utilizar uma parte da capacidade de processamento da VPS.
*   💾 **Simula Uso de Memória RAM:** Aloca uma porção da memória RAM disponível na VPS.
*   🌐 **Testa a Conexão de Rede:** Executa um teste de velocidade de internet para demonstrar atividade de rede.
*   ⚙️ **Configurável via Arquivo:** Os alvos de uso de CPU, RAM, o intervalo entre as execuções e as configurações de log são ajustáveis através do arquivo `config.json`.

## 1. Configuração do Script

Antes da instalação, você pode ajustar o comportamento do script editando o arquivo `config.json`:

- **`cpu_usage_target_percent`**: Alvo de uso da CPU (%).
- **`memory_usage_target_percent`**: Alvo de uso da RAM (%).
- **`execution_interval_minutes`**: Intervalo entre os ciclos de atividade.
- **`logging_settings`**: Configurações do arquivo de log (`neveridle.log`).

## 2. Instalação Automática (Recomendado)

O script `setup_systemd.sh` instala tudo o que você precisa para rodar o projeto como um serviço, que iniciará com a VPS e será reiniciado automaticamente em caso de falha.

### Pré-requisitos
- Um usuário com permissões `sudo`.
- `python3` e o módulo `venv` do Python instalados. Se não os tiver, instale com (para Debian/Ubuntu):
  ```bash
  sudo apt update && sudo apt install python3 python3-venv -y
  ```

### Passos

1.  **Clone ou baixe os arquivos para uma pasta na sua VPS.**
    ```bash
    # Exemplo com git
    git clone https://github.com/Lucaszmv/OracleNeverIdle.git
    cd OracleNeverIdle
    ```

2.  **Execute o script de instalação com `sudo`.**
    - Dê permissão de execução ao script e rode-o:
      ```bash
      chmod +x setup_systemd.sh
      sudo ./setup_systemd.sh
      ```
    - O script cuidará de criar o ambiente virtual, instalar as dependências e configurar o serviço `systemd`.

## 3. Comandos Úteis

- **Verificar o status do serviço:**
  ```bash
  sudo systemctl status neveridle.service
  ```

- **Acompanhar os logs de atividade em tempo real:**
  ```bash
  tail -f neveridle.log
  ```
- **Parar o serviço:**
  ```bash
  sudo systemctl stop neveridle.service
  ```
- **Reiniciar o serviço:**
  ```bash
  sudo systemctl restart neveridle.service
  ```
- **Desabilitar o início automático com a VPS:**
  ```bash
  sudo systemctl disable neveridle.service
  ```
