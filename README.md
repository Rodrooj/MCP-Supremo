# 🐧 Agente MCP para administração local do Arch Linux

Este projeto demonstra uma arquitetura local de Model Context Protocol (MCP) que conecta um cliente LLM (Google GenAI) a ferramentas de administração do sistema. O cliente pode elaborar planos de comandos e solicitar a confirmação do usuário antes de executá-los.

> **Aviso de segurança:** a confirmação descrita neste README ocorre no cliente `mcp_agent.py`. O servidor `mcp_server.py` ainda expõe uma ferramenta que executa comandos shell e não aplica uma autorização independente no próprio servidor. A pequena blacklist existente não é uma barreira de segurança confiável. Considere o servidor um processo privilegiado: não o exponha a clientes não confiáveis e não execute o projeto em máquinas com dados ou credenciais que você não esteja disposto a arriscar. Consulte a [Issue #1](https://github.com/Rodrooj/MCP-Supremo/issues/1) para o trabalho de segurança pendente.

## Recursos descritos pelo cliente

- Planejamento de etapas para tarefas de administração do Arch Linux.
- Execução sequencial de comandos com interrupção no cliente quando uma etapa falha.
- Tratamento de entrada interativa para comandos que precisam de stdin.
- Integração com a API Google GenAI a partir de `GEMINI_API_KEY`.

Esses comportamentos do cliente não restringem chamadas diretas à ferramenta de shell exposta pelo servidor.

## Arquitetura

O projeto tem dois processos que se comunicam por stdio:

1. **Servidor (`mcp_server.py`)**: expõe `execute_command`, executa o comando informado via shell e devolve stdout, stderr e exit code. O servidor executa com os privilégios do usuário que o iniciou.
2. **Cliente/agente (`mcp_agent.py`)**: usa Google GenAI para planejar tarefas, mantém o contexto da sessão e apresenta o fluxo de aprovação ao usuário.

## Pré-requisitos

- Arch Linux ou distribuição compatível.
- Python 3.10 ou superior.
- Uma chave Google GenAI válida.
- Ferramentas locais usadas pelos comandos propostos, como `sudo`, `pacman` e `systemctl`, conforme a tarefa.

## Instalação

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

O arquivo `requirements.txt` contém dependências externas. `asyncio` faz parte da biblioteca padrão do Python e não precisa ser instalado com pip.

## Configuração

Defina a chave do Google GenAI no ambiente em que o cliente será executado:

```sh
export GEMINI_API_KEY="sua_chave"
```

Evite versionar chaves, senhas ou tokens em arquivos do repositório.

## Uso

Com o ambiente virtual ativado e a chave configurada:

```sh
python mcp_agent.py
```

Leia cada comando antes de aprovar um plano. Não interprete a revisão do plano no cliente como isolamento ou autorização no servidor; essa proteção ainda precisa ser implementada no servidor.

## Limitações e próximos passos

- A ferramenta do servidor executa shell arbitrário e a blacklist não substitui uma política de autorização.
- Os privilégios do processo servidor definem o alcance das operações; execute com privilégios mínimos.
- A saída e os erros dos comandos podem conter dados sensíveis; evite passar segredos em comandos ou publicá-los em logs.
- A política server-side, a validação de entradas, os limites de execução/timeout e testes de autorização estão pendentes na [Issue #1](https://github.com/Rodrooj/MCP-Supremo/issues/1).

Esta documentação descreve as limitações atuais; ela não representa a implementação do controle de acesso.
