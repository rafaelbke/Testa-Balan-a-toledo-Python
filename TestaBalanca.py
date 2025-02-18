import serial
import time
import threading
import tkinter as tk

# Configurações de teste
PORTAS = [f"COM{i}" for i in range(1, 11)]
BAUDRATES = [2400, 9600]
COMANDO_PEDIR_PESO = b'\x05'

# Variáveis globais
porta_encontrada = None
baudrate_encontrado = None
executando = False  


def log_mensagem(mensagem, cor="black"):
    """Adiciona mensagens no log com a cor especificada."""
    txt_log.tag_configure("verde", foreground="green", font=("Arial", 10, "bold"))
    txt_log.insert(tk.END, mensagem + "\n", "verde" if cor == "green" else None)
    txt_log.see(tk.END)
    root.update_idletasks()


def detectar_balança():
    """Tenta encontrar a balança testando portas e baudrates."""
    global porta_encontrada, baudrate_encontrado

    log_mensagem("🔍 Procurando balança...")

    for porta in PORTAS:
        for baudrate in BAUDRATES:
            try:
                with serial.Serial(porta, baudrate, timeout=1) as ser:
                    mensagem = f"Tentando {porta} a {baudrate} bps..."
                    log_mensagem(mensagem)

                    ser.write(COMANDO_PEDIR_PESO)
                    ser.flush()
                    time.sleep(0.5)

                    dados = ser.read(7).decode(errors='ignore').strip()

                    if dados and len(dados) >= 3:
                        mensagem = f"✅ Balança encontrada na {porta} a {baudrate} bps!"
                        log_mensagem(mensagem, "green")
                        porta_encontrada, baudrate_encontrado = porta, baudrate
                        return True  
            except serial.SerialException:
                log_mensagem(f"⚠️ Erro ao acessar {porta}. Continuando...")

    log_mensagem("❌ Nenhuma balança encontrada.")
    return False


def iniciar_teste():
    """Inicia a busca pela balança em uma thread separada."""
    btn_iniciar["state"] = "disabled"
    btn_parar["state"] = "normal"
    lbl_peso["text"] = "Peso: ---"
    txt_log.delete(1.0, tk.END)
    lbl_status["text"] = "Procurando balança..."

    def thread_teste():
        encontrado = detectar_balança()
        if encontrado:
            lbl_status["text"] = f"Balança: {porta_encontrada} ({baudrate_encontrado} bps)"
            iniciar_leitura_automatica()
        else:
            lbl_status["text"] = "Nenhuma balança encontrada."
            btn_iniciar["state"] = "normal"
            btn_parar["state"] = "disabled"

    threading.Thread(target=thread_teste, daemon=True).start()


def iniciar_leitura_automatica():
    """Inicia a leitura do peso automaticamente após encontrar a balança."""
    global executando
    executando = True
    tempo_inicio = time.time()

    def thread_leitura():
        global executando
        try:
            with serial.Serial(porta_encontrada, baudrate_encontrado, timeout=1) as ser:
                while executando:
                    if time.time() - tempo_inicio > 30:
                        break

                    ser.write(COMANDO_PEDIR_PESO)
                    ser.flush()
                    time.sleep(0.5)

                    dados = ser.read(7).decode(errors='ignore').strip()
                    peso = dados[1:-1] if dados and len(dados) >= 3 else "---"
                    
                    mensagem = f"⚖️ Peso: {peso} g"
                    lbl_peso["text"] = mensagem
                    log_mensagem(mensagem)

        except serial.SerialException as e:
            log_mensagem(f"❌ Erro na comunicação: {e}")

        parar_leitura()

    threading.Thread(target=thread_leitura, daemon=True).start()


def parar_leitura():
    """Para a leitura do peso."""
    global executando
    executando = False
    lbl_peso["text"] = "Peso: ---"
    btn_iniciar["state"] = "normal"
    btn_parar["state"] = "disabled"


def ler_peso_manual():
    """Lê o peso manualmente a qualquer momento."""
    if porta_encontrada and baudrate_encontrado:
        try:
            with serial.Serial(porta_encontrada, baudrate_encontrado, timeout=1) as ser:
                ser.write(COMANDO_PEDIR_PESO)
                ser.flush()
                time.sleep(0.5)

                dados = ser.read(7).decode(errors='ignore').strip()
                peso = dados[1:-1] if dados and len(dados) >= 3 else "---"
                
                mensagem = f"⚖️ Peso Manual: {peso} g"
                lbl_peso["text"] = mensagem
                log_mensagem(mensagem)
        except serial.SerialException as e:
            log_mensagem(f"❌ Erro na comunicação: {e}")
    else:
        log_mensagem("⚠️ Nenhuma balança detectada.")


# Criar interface
root = tk.Tk()
root.title("R.Dorneles Leitor de Balança Toledo")
root.geometry("500x400")

# Elementos da interface
lbl_status = tk.Label(root, text="Clique em 'Iniciar Teste' para detectar a balança.", font=("Arial", 12))
lbl_status.pack(pady=10)

# Mensagem para mostrar quando encontrar a balança
lbl_balança_encontrada = tk.Label(root, text="", font=("Arial", 12, "bold"), fg="green")
lbl_balança_encontrada.pack(pady=5)

btn_iniciar = tk.Button(root, text="Iniciar Teste", font=("Arial", 12), command=iniciar_teste)
btn_iniciar.pack(pady=5)

btn_parar = tk.Button(root, text="Parar Teste", font=("Arial", 12), state="disabled", command=parar_leitura)
btn_parar.pack(pady=5)

btn_ler_manual = tk.Button(root, text="Ler Peso Manual", font=("Arial", 12), command=ler_peso_manual)
btn_ler_manual.pack(pady=5)

lbl_peso = tk.Label(root, text="Peso: ---", font=("Arial", 14, "bold"))
lbl_peso.pack(pady=10)

txt_log = tk.Text(root, height=10, width=60, wrap="word")
txt_log.pack(pady=10)

# Iniciar interface
root.mainloop()
