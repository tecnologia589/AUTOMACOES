# REFERENCIAS — DNA de escrita e pecas-modelo do escritorio

Esta pasta alimenta o motor de geracao de pecas (`peca_escritorio_engine.py`) com o
**estilo proprio do escritorio**. O agente aprende o tom, vocabulario e estrutura a
partir do que voce depositar aqui.

## O que colocar aqui

1. **1 a 2 pecas-modelo PROPRIAS do escritorio** (formato `.txt`).
   - Escolha pecas reais ja protocoladas e bem escritas, que representem o padrao do
     escritorio (ex.: uma peticao inicial e uma contestacao/replica).
   - Remova ou anonimize dados sensiveis de clientes se desejar.
   - Salve como texto puro (`.txt`), UTF-8. O nome do arquivo vira o rotulo da amostra.
   - O motor carrega automaticamente TODOS os `.txt` desta pasta (truncados em ~14k
     caracteres cada) como exemplos de estilo.

2. **`DNA_TOM_ESCRITA.md`** — regras de tom e estilo do escritorio.
   - Ja existe um esqueleto em branco nesta pasta. Preencha cada secao com as
     preferencias do escritorio (conectores favoritos, vocabulario-marca, estrutura
     dos topicos, como tratar as partes, latinismos, etc.).
   - Quanto mais especifico, mais "autoral" fica o resultado.

## Importante

- NAO existem pecas de outros escritorios aqui. Tudo deve ser conteudo PROPRIO do
  escritorio Corbelino Advogados Associados.
- Sem amostras e sem DNA, o motor ainda funciona, mas gera em tom formal-padrao
  (menos personalizado).
- O **timbrado** NAO fica aqui — ele vai em `config/timbrado_modelo.docx`
  (ver `config/timbrado_modelo.LEIA-ME.txt`).
