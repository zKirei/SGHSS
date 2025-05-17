from core.services import PacienteService
from core.database import SessionLocal, init_db, get_db
from core.security import sanitizar_input, validar_cpf
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import argparse
import subprocess
from rich.console import Console
from pathlib import Path
import uvicorn
import threading

# Configuração do FastAPI
app = FastAPI(title="SGHSS API", description="Sistema de Gestão Hospitalar")
console = Console()
init_db()

# --------------------------------------
# Rotas da API
# --------------------------------------
@app.post("/agendamentos")
def criar_agendamento(dados: dict, db: Session = Depends(get_db)):
    """Cria um novo agendamento de consulta"""
    from core.services import AgendamentoService
    try:
        agendamento = AgendamentoService.agendar_consulta(db, dados)
        return {"mensagem": "Agendamento criado!", "id": agendamento.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro interno")
    


# --------------------------------------
# Funções do Menu Interativo (ATUALIZADAS)
# --------------------------------------
def cadastrar_paciente_manual():
    """Cadastro manual de pacientes via terminal"""
    db = SessionLocal()
    try:
        timestamp = datetime.now().strftime("%H%M%S")
        telefone = f"11999{timestamp[-6:]}"

        # Validação do CPF (agora retorna Tuple[bool, str])
        cpf = console.input("[bold]CPF (apenas números):[/bold] ")
        cpf_valido, msg_cpf = validar_cpf(cpf)
        if not cpf_valido:
            raise ValueError(f"CPF inválido: {msg_cpf}")
        
        # Validação do Nome
        nome = sanitizar_input(console.input("[bold]Nome:[/bold] "))
        
        # Validação da Data de Nascimento (NOVO)
        data_nascimento = console.input("[bold]Data de Nascimento (YYYY-MM-DD):[/bold] ")
        try:
            # Converte e valida o formato
            data_nasc = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
            if data_nasc > datetime.now().date():
                raise ValueError("Data de nascimento não pode ser futura")
        except ValueError as e:
            raise ValueError(f"Data inválida: {str(e)}. Use o formato YYYY-MM-DD")

        # Criação do paciente
        paciente = PacienteService.criar_paciente(
            db,
            {
                "cpf": cpf,
                "nome": nome,
                "telefone": telefone,
                "data_nascimento": data_nasc.isoformat(),  # Data já validada
                "consentimento_lgpd": True
            }
        )
        console.print(f"[bold green]Paciente {paciente.nome} cadastrado![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Erro: {str(e)}[/bold red]")
    finally:
        db.close()

def executar_testes(tipo_teste: str):
    """Executa testes automatizados"""
    data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    diretorio_relatorio = Path("relatorios") / data_hora
    diretorio_relatorio.mkdir(parents=True, exist_ok=True)

    comando = [
        "locust" if tipo_teste == "carga" else "pytest",
        "-f", f"tests/test_{tipo_teste}.py",
        "--headless" if tipo_teste == "carga" else "--self-contained-html",
        f"--html={diretorio_relatorio}/relatorio_{tipo_teste}.html"
    ] if tipo_teste == "carga" else [
        "pytest",
        f"tests/test_{tipo_teste}.py",
        f"--html={diretorio_relatorio}/relatorio_{tipo_teste}.html",
        "--self-contained-html"
    ]

    console.print(f"[bold green]Executando testes de {tipo_teste}...[/bold green]")
    resultado = subprocess.run(comando)
    
    if resultado.returncode == 0:
        console.print(f"[bold green]Sucesso! Relatório em: {diretorio_relatorio}[/bold green]")
    else:
        console.print(f"[bold red]Falha. Verifique o log.[/bold red]")

def menu():
    """Menu interativo principal"""
    while True:
        console.print("\n[bold cyan]SGHSS - Menu Principal[/bold cyan]")
        console.print("1. Cadastrar Paciente (Teste Manual)")
        console.print("2. Executar Testes Funcionais")
        console.print("3. Executar Testes de Segurança")
        console.print("4. Executar Testes de Carga")
        console.print("5. Sair")

        opcao = console.input("\nEscolha uma opção: ")

        if opcao == "1":
            cadastrar_paciente_manual()
        elif opcao in ["2", "3", "4"]:
            tipos = {"2": "functional", "3": "security", "4": "carga"}
            executar_testes(tipos[opcao])
        elif opcao == "5":
            break
        else:
            console.print("[bold red]Opção inválida.[/bold red]")

# --------------------------------------
# Ponto de Entrada Principal
# --------------------------------------
if __name__ == "__main__":
    # Inicia o servidor API em segundo plano
    server_thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "127.0.0.1", "port": 5000, "log_level": "info"},
        daemon=True
    )
    server_thread.start()

    # Inicia o menu interativo
    menu()