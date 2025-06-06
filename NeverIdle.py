import os
import psutil
import time
import speedtest
from multiprocessing import Process
import gc
import logging
import logging.handlers
import json # Importar a biblioteca JSON

# --- Carregar Configurações do JSON ---
DEFAULT_CONFIG = {
    "script_settings": {
        "cpu_usage_target_percent": 15,
        "memory_usage_target_percent": 15,
        "execution_interval_minutes": 60
    },
    "logging_settings": {
        "log_filename": "neveridle.log",
        "log_level": "INFO",
        "log_max_mb": 5,
        "log_backup_count": 1
    }
}

CONFIG_FILENAME = 'config.json'

def load_config():
    try:
        with open(CONFIG_FILENAME, 'r', encoding='utf-8') as f:
            config_from_file = json.load(f)
        # Simples merge, priorizando valores do arquivo, mas garantindo que todas as chaves existem.
        # Para uma mesclagem mais profunda e robusta, bibliotecas como deepmerge seriam úteis.
        config = DEFAULT_CONFIG.copy()
        for section, settings in config_from_file.items():
            if section in config:
                config[section].update(settings)
            else:
                config[section] = settings # Adiciona nova seção se não existir no default
        return config
    except FileNotFoundError:
        print(f"AVISO: Arquivo '{CONFIG_FILENAME}' não encontrado. Usando configurações padrão.")
        # Criar config.json com defaults se não existir?
        # with open(CONFIG_FILENAME, 'w', encoding='utf-8') as f_out:
        #     json.dump(DEFAULT_CONFIG, f_out, indent=2)
        return DEFAULT_CONFIG
    except json.JSONDecodeError:
        print(f"AVISO: Erro ao decodificar '{CONFIG_FILENAME}'. Verifique o formato JSON. Usando configurações padrão.")
        return DEFAULT_CONFIG

config = load_config()

# Extrair configurações para variáveis mais fáceis de usar
# Script settings
CPU_USAGE_TARGET = config['script_settings']['cpu_usage_target_percent'] / 100.0
MEMORY_USAGE_TARGET = config['script_settings']['memory_usage_target_percent'] / 100.0
EXECUTION_INTERVAL_SECONDS = config['script_settings']['execution_interval_minutes'] * 60

# Logging settings
LOG_FILENAME = config['logging_settings']['log_filename']
LOG_LEVEL_STR = config['logging_settings']['log_level'].upper()
LOG_MAX_BYTES = config['logging_settings']['log_max_mb'] * 1024 * 1024
LOG_BACKUP_COUNT = config['logging_settings']['log_backup_count']

# Mapear string de nível de log para constante de logging
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)

# --- Configuração do Logger (agora usando valores do config.json) ---
logger = logging.getLogger('NeverIdleLogger')
logger.setLevel(LOG_LEVEL)

file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILENAME, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8'
)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(LOG_LEVEL)

console_formatter = logging.Formatter('%(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)
console_handler.setLevel(LOG_LEVEL) 

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
# --- Fim da Configuração do Logger ---

# Função para simular carga de CPU, executada por cada processo filho
def cpu_load_task():
    """Simula uma carga de trabalho na CPU."""
    try:
        c = 0
        for _ in range(10**7):
            c += 1
    except Exception:
        pass

def run_speed_test():
    """Executa o teste de velocidade e loga os resultados."""
    try:
        s = speedtest.Speedtest(secure=True)
        s.get_best_server()
        s.download(threads=None)
        s.upload(threads=None)
        results = s.results.dict()
        download_mbps = results["download"] / 1_000_000
        upload_mbps = results["upload"] / 1_000_000
        logger.info(f"    Status: Teste concluído. Download {download_mbps:.1f} Mbps, Upload {upload_mbps:.1f} Mbps.")
    except speedtest.ConfigRetrievalError as e:
        logger.error(f"    Status: Falha ao buscar configuração do teste ({e}).")
    except Exception as e:
        logger.error(f"    Status: Falha ao executar teste de velocidade ({e}).")

def main():
    # As constantes de configuração agora são lidas do config.json e atribuídas globalmente

    pid_info = f"(PID: {os.getpid()})"
    logger.info(f"Script 'Never Idle' em ação! {pid_info}")
    # Usa as variáveis globais que foram carregadas do JSON
    logger.info(f"   Configurações: Manter ~{CPU_USAGE_TARGET*100:.0f}% da CPU e ~{MEMORY_USAGE_TARGET*100:.0f}% da Memória ocupadas.")
    logger.info(f"   Verificações a cada: {EXECUTION_INTERVAL_SECONDS // 60} minutos.")
    
    allocated_memory_chunks = []

    while True:
        logger.info(f"\n--- Verificando atividade da VPS (Ciclo de {EXECUTION_INTERVAL_SECONDS // 60} min) ---")
        current_process = psutil.Process(os.getpid())

        # 1. Uso de Memória
        logger.info("1. Memória RAM:")
        total_mem_bytes = psutil.virtual_memory().total
        # MEMORY_USAGE_TARGET já é uma fração (ex: 0.30)
        target_mem_bytes = int(total_mem_bytes * MEMORY_USAGE_TARGET)

        allocated_memory_chunks.clear()
        gc.collect()

        chunk_size = 1024 * 1024
        try:
            while current_process.memory_info().rss < target_mem_bytes:
                allocated_memory_chunks.append(bytearray(chunk_size))
                if len(allocated_memory_chunks) * chunk_size > total_mem_bytes:
                    logger.warning("    Alerta: Limite de segurança na alocação de memória atingido.")
                    break
        except MemoryError:
            logger.warning("    Alerta: Erro de memória durante alocação. Meta pode não ter sido atingida.")
        
        mem_info_after_alloc = current_process.memory_info()
        logger.info(f"   Alvo: ~{MEMORY_USAGE_TARGET*100:.0f}% da RAM total.")
        logger.info(f"   Uso Atual: {mem_info_after_alloc.rss / (1024*1024):.1f} MB de ~{target_mem_bytes / (1024*1024):.1f} MB (alvo estimado).")

        # 2. Uso de CPU
        logger.info("\n2. Processador (CPU):")
        cpu_cores = psutil.cpu_count(logical=True)
        # CPU_USAGE_TARGET já é uma fração (ex: 0.30)
        target_cpu_processes_float = cpu_cores * CPU_USAGE_TARGET
        target_cpu_processes = max(1, int(round(target_cpu_processes_float))) if target_cpu_processes_float > 0 else 0
        
        logger.info(f"   Alvo: Ativar ~{CPU_USAGE_TARGET*100:.0f}% da capacidade.")
        if target_cpu_processes > 0:
            logger.info(f"   Ação: Utilizando {target_cpu_processes} de {cpu_cores} processadores para simular carga.")
        else:
            logger.info("   Ação: Nenhuma carga de CPU adicional (alvo de 0% ou nenhum core disponível).")

        active_processes = []
        if target_cpu_processes > 0:
            for _ in range(target_cpu_processes):
                p = Process(target=cpu_load_task)
                active_processes.append(p)
                p.start()
        
        # 3. Teste de Rede
        logger.info("\n3. Conexão de Rede:")
        run_speed_test()

        if active_processes:
            for p in active_processes:
                p.join(timeout=15)
                if p.is_alive():
                    logger.warning(f"    Alerta CPU: Processo {p.pid} não finalizou como esperado e foi terminado.")
                    p.terminate()
                    p.join()
        
        logger.info(f"\n--- Fim da verificação. Próximo ciclo em {EXECUTION_INTERVAL_SECONDS // 60} minutos. ---")
        time.sleep(EXECUTION_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nScript interrompido pelo usuário.")
    except Exception as e:
        logger.exception(f"Erro inesperado e fatal na execução principal: {e}") 