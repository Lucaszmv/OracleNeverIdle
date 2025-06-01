import os
import psutil
import time
import speedtest
from multiprocessing import Process
import gc

# Função para simular carga de CPU, executada por cada processo filho
def cpu_load_task():
    """Simula uma carga de trabalho na CPU."""
    try:
        # Loop computacional para consumir CPU.
        # Ajuste o range para aumentar/diminuir a intensidade da carga.
        c = 0
        for _ in range(10**7): # Este loop é uma forma de manter a CPU ocupada
            c += 1
    except Exception:
        # Em um cenário real, logar o erro seria importante.
        pass

def run_speed_test():
    """Executa o teste de velocidade e imprime os resultados."""
    try:
        s = speedtest.Speedtest(secure=True)
        s.get_best_server()
        s.download(threads=None)
        s.upload(threads=None)
        results = s.results.dict()
        download_mbps = results["download"] / 1_000_000
        upload_mbps = results["upload"] / 1_000_000
        # Formato de lista para o resultado do speedtest
        print(f"    Status: Teste concluído. Download {download_mbps:.1f} Mbps, Upload {upload_mbps:.1f} Mbps.")
    except speedtest.ConfigRetrievalError as e:
        print(f"    Status: Falha ao buscar configuração do teste ({e}).")
    except Exception as e:
        print(f"    Status: Falha ao executar teste de velocidade ({e}).")

def main():
    # Constantes de configuração
    CPU_USAGE_TARGET = 0.30  # 30% de uso da CPU
    MEMORY_USAGE_TARGET = 0.30  # 30% de uso da Memória
    EXECUTION_INTERVAL_SECONDS = 30 * 60  # 30 minutos

    pid_info = f"(PID: {os.getpid()})"
    print(f"Script 'Never Idle' em ação! {pid_info}")
    print(f"   Configurações: Manter ~{CPU_USAGE_TARGET*100:.0f}% da CPU e ~{MEMORY_USAGE_TARGET*100:.0f}% da Memória ocupadas.")
    print(f"   Verificações a cada: {EXECUTION_INTERVAL_SECONDS // 60} minutos.")
    
    allocated_memory_chunks = []

    while True:
        # Mensagem de início de ciclo mais limpa
        print(f"\n--- Verificando atividade da VPS (Ciclo de {EXECUTION_INTERVAL_SECONDS // 60} min) ---")
        current_process = psutil.Process(os.getpid())

        # 1. Uso de Memória
        print("1. Memória RAM:")
        total_mem_bytes = psutil.virtual_memory().total
        target_mem_bytes = int(total_mem_bytes * MEMORY_USAGE_TARGET)

        allocated_memory_chunks.clear()
        gc.collect()

        chunk_size = 1024 * 1024  # 1 MB
        try:
            while current_process.memory_info().rss < target_mem_bytes:
                allocated_memory_chunks.append(bytearray(chunk_size))
                if len(allocated_memory_chunks) * chunk_size > total_mem_bytes: 
                    print("    Alerta: Limite de segurança na alocação de memória atingido.")
                    break
        except MemoryError:
            print("    Alerta: Erro de memória durante alocação. Meta pode não ter sido atingida.")
        
        mem_info_after_alloc = current_process.memory_info()
        print(f"   Alvo: ~{MEMORY_USAGE_TARGET*100:.0f}% da RAM total.")
        print(f"   Uso Atual: {mem_info_after_alloc.rss / (1024*1024):.1f} MB de ~{target_mem_bytes / (1024*1024):.1f} MB (alvo estimado).")

        # 2. Uso de CPU
        print("\n2. Processador (CPU):")
        cpu_cores = psutil.cpu_count(logical=True)
        target_cpu_processes_float = cpu_cores * CPU_USAGE_TARGET
        target_cpu_processes = max(1, int(round(target_cpu_processes_float))) if target_cpu_processes_float > 0 else 0
        
        print(f"   Alvo: Ativar ~{CPU_USAGE_TARGET*100:.0f}% da capacidade.")
        if target_cpu_processes > 0:
            print(f"   Ação: Utilizando {target_cpu_processes} de {cpu_cores} processadores para simular carga.")
        else:
            print("   Ação: Nenhuma carga de CPU adicional (alvo de 0% ou nenhum core disponível).")

        active_processes = []
        if target_cpu_processes > 0:
            for _ in range(target_cpu_processes):
                p = Process(target=cpu_load_task)
                active_processes.append(p)
                p.start()
        
        # 3. Teste de Rede
        print("\n3. Conexão de Rede:")
        run_speed_test()

        # Gerenciamento dos processos de CPU (sem prints excessivos)
        if active_processes:
            for p in active_processes:
                p.join(timeout=15)
                if p.is_alive():
                    # Mensagem de erro específica se um processo não terminar
                    print(f"    Alerta CPU: Processo {p.pid} não finalizou como esperado e foi terminado.")
                    p.terminate()
                    p.join()
        
        print(f"\n--- Fim da verificação. Próximo ciclo em {EXECUTION_INTERVAL_SECONDS // 60} minutos. ---")
        time.sleep(EXECUTION_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScript interrompido pelo usuário.")
    except Exception as e:
        print(f"Erro inesperado na execução principal: {e}") 