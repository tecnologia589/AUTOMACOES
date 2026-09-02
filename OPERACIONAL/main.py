"""
=============================================================================
  SQUAD OPERACIONAL - CORBELINO ADVOGADOS ASSOCIADOS
=============================================================================

  Fluxo operacional do escritorio:
  1. Consultar processos ativos e suas fases
  2. Listar tarefas pendentes por responsavel
  3. Gerar pecas juridicas automaticamente (razoes finais, replicas, etc)
  4. Criar tarefas no ADVBOX com prazos
  5. Monitorar prazos fatais
  6. Gerar peticao inicial a partir de pasta de documentos

  Uso:
    cd "AUTOMACOES CORBELINO_ADVOGADOS" && python OPERACIONAL/main.py tarefas
    cd "AUTOMACOES CORBELINO_ADVOGADOS" && python OPERACIONAL/main.py processos
    cd "AUTOMACOES CORBELINO_ADVOGADOS" && python OPERACIONAL/main.py prazos
    cd "AUTOMACOES CORBELINO_ADVOGADOS" && python OPERACIONAL/main.py gerar-peca <lawsuit_id>
    cd "AUTOMACOES CORBELINO_ADVOGADOS" && python OPERACIONAL/main.py gerar-peticao "C:\\pasta_do_cliente"

  Equipe / usuarios ADVBOX:
    Os IDs de usuario ADVBOX sao lidos de variaveis de ambiente (config/.env),
    nunca hardcoded. Preencha-os no onboarding do escritorio:
      ADVBOX_USER_RESPONSAVEL  -> ID do advogado responsavel (campo 'from' das tarefas)
      ADVBOX_USER_OPERACIONAL  -> ID de quem recebe tarefas operacionais
      ADVBOX_USER_FINANCEIRO   -> ID do financeiro
    Opcionalmente, ADVBOX_USERS_MAP pode mapear "ID:NOME,ID:NOME" para exibicao.
=============================================================================
"""
import sys, os, io, json, argparse
from datetime import datetime, timedelta
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'INTEGRACOES'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

import requests
from advbox_integration import (
    carregar_settings, _request as advbox_request,
    buscar_cliente, buscar_processo, listar_transacoes
)
from google_integration import autenticar_google


ADVBOX_BASE = 'https://app.advbox.com.br/api/v1'

# IDs de usuario ADVBOX - lidos do ambiente, nunca hardcoded.
# Preencha no config/.env no onboarding do escritorio.
USER_RESPONSAVEL_ID = os.getenv('ADVBOX_USER_RESPONSAVEL', '')
USER_OPERACIONAL_ID = os.getenv('ADVBOX_USER_OPERACIONAL', '')
USER_FINANCEIRO_ID = os.getenv('ADVBOX_USER_FINANCEIRO', '')

# Campo 'from' das tarefas /posts: por padrao, o responsavel do escritorio.
USUARIO_PADRAO_TAREFAS_ID = os.getenv('ADVBOX_USER_FROM', '') or USER_RESPONSAVEL_ID


def _carregar_users_map():
    """
    Mapa {id(int): NOME} para exibicao e filtro por usuario.
    Fonte: variavel de ambiente ADVBOX_USERS_MAP no formato "ID:NOME,ID:NOME".
    Sem hardcode de nomes de equipe; vazio por padrao.
    """
    raw = os.getenv('ADVBOX_USERS_MAP', '')
    mapa = {}
    for par in raw.split(','):
        par = par.strip()
        if not par or ':' not in par:
            continue
        uid, nome = par.split(':', 1)
        uid = uid.strip()
        nome = nome.strip()
        if uid.isdigit() and nome:
            mapa[int(uid)] = nome.upper()
    return mapa


USERS = _carregar_users_map()


def _headers():
    token = os.getenv('ADVBOX_API_TOKEN', '')
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'CORBELINO_ADVOGADOS-Advocacia/1.0',
    }


# ============================================================
# COMANDO: tarefas - Lista tarefas pendentes
# ============================================================

def cmd_tarefas(args):
    print('=' * 80)
    print('  TAREFAS PENDENTES - CORBELINO ADVOGADOS ASSOCIADOS')
    print('=' * 80)

    params = {'limit': 100}
    if args.dias:
        inicio = datetime.now() - timedelta(days=30)
        fim = datetime.now() + timedelta(days=int(args.dias))
        params['date_start'] = inicio.strftime('%Y-%m-%d')
        params['date_end'] = fim.strftime('%Y-%m-%d')
    else:
        params['date_start'] = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        params['date_end'] = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

    if args.usuario:
        for uid, nome in USERS.items():
            if args.usuario.upper() in nome:
                params['user_id'] = uid
                break

    r = requests.get(f'{ADVBOX_BASE}/posts', headers=_headers(), params=params, timeout=15)
    data = r.json()
    todas = data.get('data', [])

    # Filtrar pendentes
    pendentes = [t for t in todas if any(not u.get('completed') for u in t.get('users', []))]

    # Agrupar por responsavel
    por_resp = defaultdict(list)
    for t in pendentes:
        for u in t.get('users', []):
            if not u.get('completed'):
                nome = u.get('name', 'SEM RESPONSAVEL')
                por_resp[nome].append(t)

    print(f'\n  Total pendentes: {len(pendentes)}')

    for resp in sorted(por_resp.keys()):
        tarefas = por_resp[resp]
        print(f'\n  --- {resp} ({len(tarefas)} tarefas) ---')
        for t in sorted(tarefas, key=lambda x: x.get('date_deadline') or x.get('date', '') or '9'):
            lawsuit = t.get('lawsuit', {}) or {}
            cli = ''
            if lawsuit.get('customers'):
                cli = lawsuit['customers'][0].get('name', '')
            num = lawsuit.get('process_number') or 'S/N'
            prazo = t.get('date_deadline', '')
            prazo_str = f' | PRAZO: {prazo[:10]}' if prazo else ''
            urg = ' [URGENTE]' if any(u.get('urgent') for u in t.get('users', [])) else ''
            imp = ' [IMPORTANTE]' if any(u.get('important') for u in t.get('users', [])) else ''
            notes = (t.get('notes') or '')[:50]
            print(f'    {t.get("date","")[:10]} | {t.get("task","")[:25]:25} | {cli[:25]:25}{urg}{imp}{prazo_str}')
            if notes:
                print(f'      {notes}')


# ============================================================
# COMANDO: processos - Lista processos ativos
# ============================================================

def cmd_processos(args):
    print('=' * 80)
    print('  PROCESSOS ATIVOS - CORBELINO ADVOGADOS ASSOCIADOS')
    print('=' * 80)

    data = advbox_request('GET', '/lawsuits', params={'limit': 1000})
    todos = data.get('data', [])
    ativos = [p for p in todos if 'ARQUIV' not in (p.get('stage') or '').upper()
              and 'RENUNCI' not in (p.get('stage') or '').upper()]

    if args.responsavel:
        ativos = [p for p in ativos if args.responsavel.upper() in (p.get('responsible') or '').upper()]

    por_fase = defaultdict(list)
    for p in ativos:
        por_fase[p.get('stage') or 'SEM FASE'].append(p)

    print(f'\n  Total ativos: {len(ativos)}')

    for fase in sorted(por_fase.keys()):
        procs = por_fase[fase]
        print(f'\n  [{fase}] - {len(procs)} processo(s)')
        for p in sorted(procs, key=lambda x: x.get('created_at', ''), reverse=True):
            cli = p.get('customers', [{}])[0].get('name', '') if p.get('customers') else ''
            num = p.get('process_number') or 'S/N'
            resp = p.get('responsible', '')[:15]
            print(f'    {num[:35]:35} | {cli[:28]:28} | {resp}')


# ============================================================
# COMANDO: prazos - Lista prazos fatais proximos
# ============================================================

def cmd_prazos(args):
    print('=' * 80)
    print('  PRAZOS FATAIS - PROXIMOS 14 DIAS')
    print('=' * 80)

    inicio = datetime.now()
    fim = inicio + timedelta(days=14)

    r = requests.get(f'{ADVBOX_BASE}/posts', headers=_headers(), params={
        'deadline_start': inicio.strftime('%Y-%m-%d'),
        'deadline_end': fim.strftime('%Y-%m-%d'),
        'limit': 100
    }, timeout=15)
    data = r.json()
    tarefas = data.get('data', [])

    pendentes = [t for t in tarefas if any(not u.get('completed') for u in t.get('users', []))]
    pendentes.sort(key=lambda x: x.get('date_deadline') or '9999')

    print(f'\n  Prazos encontrados: {len(pendentes)}')

    for t in pendentes:
        lawsuit = t.get('lawsuit', {}) or {}
        cli = ''
        if lawsuit.get('customers'):
            cli = lawsuit['customers'][0].get('name', '')
        prazo = (t.get('date_deadline') or '')[:10]
        resps = [u.get('name', '')[:20] for u in t.get('users', []) if not u.get('completed')]
        urg = ' [URGENTE]' if any(u.get('urgent') for u in t.get('users', [])) else ''
        notes = (t.get('notes') or '')[:60]

        dias_rest = (datetime.strptime(prazo, '%Y-%m-%d') - datetime.now()).days if prazo else '?'

        print(f'\n  PRAZO: {prazo} ({dias_rest} dias) {urg}')
        print(f'    {t.get("task","")[:30]} | {cli[:30]}')
        print(f'    Responsavel: {", ".join(resps)}')
        if notes:
            print(f'    {notes}')


# ============================================================
# COMANDO: criar-tarefa - Cria tarefa no ADVBOX
# ============================================================

def cmd_criar_tarefa(args):
    print('Criando tarefa no ADVBOX...')

    # Buscar task_id pelo nome
    settings = carregar_settings()
    task_types = settings.get('tasks', [])
    task_id = None
    for tt in task_types:
        if args.tipo.upper() in tt.get('task', '').upper():
            task_id = tt['id']
            break
    if not task_id:
        print(f'Tipo de tarefa "{args.tipo}" nao encontrado.')
        print('Tipos disponiveis:')
        for tt in task_types[:20]:
            print(f'  {tt["task"]}')
        return

    # Buscar user_id do destinatario
    guest_id = None
    for uid, nome in USERS.items():
        if args.para.upper() in nome:
            guest_id = uid
            break
    if not guest_id:
        print(f'Usuario "{args.para}" nao encontrado.')
        print('Configure o mapa de usuarios em ADVBOX_USERS_MAP no config/.env')
        return

    if not USUARIO_PADRAO_TAREFAS_ID:
        print('ERRO: ADVBOX_USER_FROM/ADVBOX_USER_RESPONSAVEL nao configurado no config/.env')
        return

    payload = {
        'lawsuits_id': int(args.processo),
        'start_date': args.data or datetime.now().strftime('%Y-%m-%d'),
        'from': int(USUARIO_PADRAO_TAREFAS_ID),
        'guests': [guest_id],
        'tasks_id': task_id,
        'comments': args.mensagem or '',
    }
    if args.prazo:
        payload['date_deadline'] = args.prazo
    if args.urgente:
        payload['urgent'] = True
        payload['important'] = True

    print(f'  Processo: {args.processo}')
    print(f'  Tipo: {args.tipo}')
    print(f'  Para: {args.para} (ID: {guest_id})')
    print(f'  Mensagem: {(args.mensagem or "")[:50]}')

    resp = input('\n  Confirma? (s/N): ').strip().lower()
    if resp != 's':
        print('  Cancelado.')
        return

    r = requests.post(f'{ADVBOX_BASE}/posts', headers=_headers(), json=payload, timeout=15)
    if r.status_code == 200:
        data = r.json()
        print(f'  Tarefa criada! ID: {data.get("posts_id")}')
    else:
        print(f'  Erro: {r.status_code} | {r.text[:100]}')


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='Squad Operacional - Corbelino Advogados Associados')
    subparsers = parser.add_subparsers(dest='comando')

    # tarefas
    p_tarefas = subparsers.add_parser('tarefas', help='Listar tarefas pendentes')
    p_tarefas.add_argument('--usuario', '-u', help='Filtrar por usuario (use o nome configurado em ADVBOX_USERS_MAP)')
    p_tarefas.add_argument('--dias', '-d', help='Dias a frente (default: 14)')

    # processos
    p_procs = subparsers.add_parser('processos', help='Listar processos ativos')
    p_procs.add_argument('--responsavel', '-r', help='Filtrar por responsavel')

    # prazos
    p_prazos = subparsers.add_parser('prazos', help='Listar prazos fatais proximos')

    # baixar-docs
    p_baixar = subparsers.add_parser('baixar-docs', help='Baixar docs do Drive para gerar peticao')
    p_baixar.add_argument('cliente', nargs='?', help='Nome do cliente (busca em RECLAMANTE no Drive)')
    p_baixar.add_argument('--id', dest='pasta_id', help='ID da pasta do cliente no Google Drive')
    p_baixar.add_argument('--saida', '-o', help='Arquivo de saida')

    # subir-peticao
    p_subir = subparsers.add_parser('subir-peticao', help='Subir peticao formatada para o Drive')
    p_subir.add_argument('cliente', nargs='?', help='Nome do cliente')
    p_subir.add_argument('--id', dest='pasta_id', help='ID da pasta do cliente no Google Drive')
    p_subir.add_argument('--arquivo', '-a', required=True, help='Arquivo .txt com a peticao')

    # protocolo
    p_proto = subparsers.add_parser('protocolo', help='Gerar protocolo de entrega/recebimento de documentos')
    p_proto.add_argument('processo', nargs='?', help='ID do processo no ADVBOX')
    p_proto.add_argument('--cliente', '-c', help='Nome do cliente')
    p_proto.add_argument('--tipo', '-t', required=True, choices=['entrega', 'recebimento'])
    p_proto.add_argument('--docs', '-d', required=True, help='Documentos separados por virgula')
    p_proto.add_argument('--obs', '-o', help='Observacoes')
    p_proto.add_argument('--drive', action='store_true', help='Subir para o Drive')
    p_proto.add_argument('--advbox', action='store_true', help='Registrar publicacao no ADVBOX')

    # criar-tarefa
    p_criar = subparsers.add_parser('criar-tarefa', help='Criar tarefa no ADVBOX')
    p_criar.add_argument('processo', help='ID do processo no ADVBOX')
    p_criar.add_argument('tipo', help='Tipo da tarefa (ex: ACOMPANHAMENTO)')
    p_criar.add_argument('para', help='Responsavel (nome configurado em ADVBOX_USERS_MAP)')
    p_criar.add_argument('--mensagem', '-m', help='Comentario da tarefa')
    p_criar.add_argument('--prazo', '-p', help='Prazo fatal (YYYY-MM-DD)')
    p_criar.add_argument('--data', help='Data da tarefa (default: hoje)')
    p_criar.add_argument('--urgente', action='store_true', help='Marcar como urgente')

    args = parser.parse_args()

    if args.comando == 'tarefas':
        cmd_tarefas(args)
    elif args.comando == 'processos':
        cmd_processos(args)
    elif args.comando == 'prazos':
        cmd_prazos(args)
    elif args.comando == 'baixar-docs':
        from gerar_peticao import cmd_baixar
        cmd_baixar(args)
    elif args.comando == 'subir-peticao':
        from gerar_peticao import cmd_subir
        cmd_subir(args)
    elif args.comando == 'protocolo':
        from protocolo_entrega import executar_protocolo
        executar_protocolo(args)
    elif args.comando == 'criar-tarefa':
        cmd_criar_tarefa(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
