# Deploy do Agente CORBELINO.IA na VPS (Hostinger / Ubuntu)

Guia de deploy do agente operacional (FastAPI, porta **8787**) numa VPS Linux,
rodando como servico **systemd** (start no boot + restart automatico).

> O `.git` de producao e ISOLADO (so a pasta `CORBELINO_ADVOGADOS`). Nenhum segredo
> vai pro GitHub — credenciais sao copiadas a mao via `scp` (Fase 5).

---

## Infraestrutura (a provisionar — onboarding)

> A VPS de producao do Corbelino Advogados Associados AINDA NAO foi provisionada.
> Preencha esta secao quando o deploy for realizado. NUNCA commitar segredos aqui
> (tokens, senhas, `.env`) — apenas infra publica.

- **VPS:** _(provedor / host / IP / distro — ex.: Hostinger, Ubuntu 24.04 LTS)_ — a definir.
- **Acesso SSH:** usuario `deploy` (sudo). Conectar: `ssh deploy@SEU_IP` (com chave autorizada).
- **Projeto na VPS:** `/home/deploy/corbelino-advogados` | virtualenv em `.venv`.
- **Clone do repo privado:** via **deploy key** read-only (`~/.ssh/github_deploy` na VPS).
- **Servico:** systemd `corbelino-agente` (enabled, Restart=always), uvicorn na porta **8787**.
- **Webhook publico:** `http://SEU_IP:8787`
  - Healthcheck (sem auth): `GET /healthcheck`
  - Disparo: `POST /tarefa` com header `Authorization: Bearer <AGENTE_OP_TOKEN>`

### Operacao do dia a dia (apos o deploy)
```bash
# logs em tempo real
journalctl -u corbelino-agente -f
# status / restart
sudo systemctl status corbelino-agente
sudo systemctl restart corbelino-agente
# deploy de nova versao
cd /home/deploy/corbelino-advogados && git pull
source .venv/bin/activate && pip install -r requirements.txt   # so se requirements mudou
sudo systemctl restart corbelino-agente
```

### Pendencias de onboarding (pra funcionar 100%)
Nenhuma credencial foi recebida ainda (ver `docs/ONBOARDING.md`) — preencher
`config/.env` LOCAL primeiro (copiar de `config/.env.example`) e só depois enviar
para a VPS via `scp` (Fase 5): `ANTHROPIC_API_KEY` (essencial p/ gerar pecas),
`ADVBOX_API_TOKEN`, `AGENTE_OP_TOKEN`, `credentials.json` + `oauth_credentials.json`
+ `token.json` (Google Drive), e os tokens `ASAAS` / `ZAPSIGN` / `ATENDE_DIREITO`
(se forem usados). `timbrado_modelo.docx` (assim como o `.env`) NAO vai pro git
(ver `.gitignore`) — precisa ser copiado a parte via `scp`, igual aos demais
segredos (Fase 5).

---

## Pre-requisitos
- VPS Ubuntu 22.04/24.04 com acesso SSH (IP + usuario + senha ou chave).
- Repositorio no GitHub (privado) com o codigo — `pabadvogados-hub/corbelino-advogados`.
- Os arquivos secretos/nao-versionados locais em `config/`:
  `.env`, `credentials.json`, `oauth_credentials.json`, `token.json`,
  `timbrado_modelo.docx` (nenhum deles vai pro git — ver `.gitignore`).

---

## Fase 2 — Subir no GitHub

Repositorio **privado** ja criado: `pabadvogados-hub/corbelino-advogados`. Na pasta
do projeto:

```bash
git remote add origin git@github.com:pabadvogados-hub/corbelino-advogados.git
git push -u origin master
```

(Se usar HTTPS no lugar de SSH: `https://github.com/pabadvogados-hub/corbelino-advogados.git`
e autentique com um Personal Access Token ou `gh auth login`.)

---

## Fase 3 — Preparar a VPS (acesso + usuario)

1. Pegue no hPanel da Hostinger (ou provedor equivalente): **IP publico**, usuario SSH
   (`root`) e senha.
2. Conecte: `ssh root@SEU_IP`
3. (Recomendado) Crie um usuario nao-root para rodar o servico:

```bash
adduser deploy
usermod -aG sudo deploy
# (opcional) liberar login por chave SSH para 'deploy'
su - deploy
```

> Por seguranca, depois desabilite login por senha e use chave SSH. Troque a
> senha de root assim que possivel (ela foi exposta durante o setup).

---

## Fase 4 + 5 — Clonar, provisionar e enviar segredos

Como usuario `deploy`, clone o repo:

```bash
cd ~
git clone git@github.com:pabadvogados-hub/corbelino-advogados.git corbelino-advogados
cd corbelino-advogados
```

Provisione o sistema (Python, venv, tesseract, Chromium do Playwright):

```bash
bash deploy/setup_vps.sh ~/corbelino-advogados
```

**Envie os segredos** a partir da sua maquina **local** (PowerShell/CMD),
NUNCA pelo git:

```powershell
# rode na maquina LOCAL, dentro da pasta CORBELINO_ADVOGADOS
scp config/.env                 deploy@SEU_IP:~/corbelino-advogados/config/.env
scp config/credentials.json     deploy@SEU_IP:~/corbelino-advogados/config/credentials.json
scp config/oauth_credentials.json deploy@SEU_IP:~/corbelino-advogados/config/oauth_credentials.json
scp config/token.json           deploy@SEU_IP:~/corbelino-advogados/config/token.json
scp config/timbrado_modelo.docx deploy@SEU_IP:~/corbelino-advogados/config/timbrado_modelo.docx
```

> O `token.json` (OAuth do Google) e gerado pelo fluxo interativo na maquina
> local. Em VPS sem navegador, basta copiar o token ja gerado; ele se renova
> sozinho pelo refresh_token enquanto valido.

---

## Fase 6 — Servico systemd

```bash
# como deploy (com sudo)
sudo cp deploy/corbelino-agente.service /etc/systemd/system/corbelino-agente.service
# confira User= e os caminhos dentro do arquivo (default: usuario 'deploy', ~/corbelino-advogados)
sudo systemctl daemon-reload
sudo systemctl enable --now corbelino-agente
sudo systemctl status corbelino-agente --no-pager
```

Logs em tempo real:

```bash
journalctl -u corbelino-agente -f
```

---

## Fase 7 — Testar

Healthcheck (na propria VPS):

```bash
curl -s http://127.0.0.1:8787/healthcheck
```

De fora (IP direto) — abra a porta no firewall primeiro:

```bash
sudo ufw allow 8787/tcp     # se o ufw estiver ativo
curl -s http://SEU_IP:8787/healthcheck
```

Disparo de teste (precisa do header com AGENTE_OP_TOKEN do .env):

```bash
curl -s -X POST http://127.0.0.1:8787/tarefa \
  -H "Authorization: Bearer <AGENTE_OP_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"categoria":"...","...":"..."}'
```

---

## Atualizacoes futuras (deploy de nova versao)

```bash
cd ~/corbelino-advogados
git pull
source .venv/bin/activate && pip install -r requirements.txt   # se requirements mudou
sudo systemctl restart corbelino-agente
```

---

## (Opcional, depois) Dominio + HTTPS com Nginx

Quando quiser expor com dominio e SSL (ex.: `agente.corbelinoadvogados.com.br` —
confirmar se o escritorio tem/quer um dominio proprio):

1. Aponte um registro DNS A do dominio para o IP da VPS.
2. Instale Nginx + Certbot, configure proxy reverso para `127.0.0.1:8787`.
3. `sudo certbot --nginx -d agente.SEU_DOMINIO`
4. Feche a porta 8787 externamente (deixe so 80/443 publicas).
