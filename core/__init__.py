# core/__init__.py
from .database import SessionLocal, engine, get_db, init_db
from .models import Base, Paciente, Agendamento, Profissional, LogAuditoria  # Nome corrigido
from .security import gerar_hash_senha, verificar_senha, sanitizar_input
from .services import PacienteService, AgendamentoService, ProfissionalService
from .reports import gerar_relatorio_financeiro, gerar_relatorio_pacientes

__all__ = [
    'Base', 'Paciente', 'Agendamento', 'Profissional', 'LogAuditoria',  # Nome corrigido
    'SessionLocal', 'engine', 'get_db', 'gerar_hash_senha', 'verificar_senha',
    'sanitizar_input', 'PacienteService', 'AgendamentoService',
    'ProfissionalService', 'gerar_relatorio_financeiro',
    'gerar_relatorio_pacientes', 'init_db'
]