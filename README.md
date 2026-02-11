
# 🐧 Agente Autônomo MCP para Arch Linux

Este projeto implementa uma arquitetura local de Model Context Protocol (MCP) que conecta um LLM (Google Gemini) diretamente ao seu sistema Arch Linux. Ele permite que você descreva problemas de alto nível (por exemplo, "Instalar o Docker e configurá-lo para meu usuário") e que o agente planeje, execute e verifique autonomamente os comandos Bash necessários para resolvê-los.

----------

## 🚀 Recursos

- **Resolução Autônoma de Problemas:** O agente não apenas executa comandos; ele analisa a situação, verifica erros e formula um plano.

- **Execução em Lote:** Gera uma lista completa de comandos para uma tarefa e os executa sequencialmente.

- **Manipulação Inteligente de Sudo:** Detecta quando o uso de `sudo` é necessário, solicita sua senha **uma única vez** de forma segura e a armazena em cache durante a sessão. Ele insere automaticamente a senha nos comandos usando `sudo -S`.

- **Segurança em Primeiro Lugar:**

- **Intervenção Humana:** Você visualiza cada comando no plano antes de sua execução.

- **Abortar em Caso de Falha:** Se a etapa 2 falhar, as etapas 3 a 10 são canceladas automaticamente para evitar danos ao sistema.

- **Segurança de Arquivos:** O prompt do sistema instrui o agente a usar `cat` para leitura e `tee` para gravação, evitando erros comuns de permissão de redirecionamento.

- **Tecnologia Gemini:** Utiliza o SDK Google GenAI (Gemini 2.5 Flash) para raciocínio de alta velocidade e baixo custo.

----------

## 🛠️ Arquitetura

O aplicativo consiste em dois processos distintos que se comunicam por meio de entrada/saída padrão (stdio):

1. **O Servidor (`mcp_server.py`):**

- Um ambiente de execução privilegiado.

- Expõe uma única ferramenta: `execute_command`.

- Executa comandos em um subprocesso, capturando STDOUT, STDERR e códigos de saída.

- Suporta injeção de entrada (envio de texto/senhas para os comandos).

2. **O Cliente/Agente (`mcp_agent.py`):**

- Conecta-se à API Gemini para realizar inferências sobre a administração do Arch Linux.

- Mantém o histórico e o contexto da conversa.

- Gerencia a interface do usuário (entrada de dados, aprovação de planos, solicitação de senha).

----------

## 📋 Pré-requisitos

- **SO:** Arch Linux (ou uma distribuição baseada em Arch, como Manjaro/EndeavourOS).

- **Python:** Versão 3.10 ou superior.

- **Chave de API:** Uma chave de API válida do Google Gemini.

- **Ferramentas do sistema:** `sudo`, `pacman`, `systemctl`.

----------


## 📦 Instalação

1. **Clone ou crie a pasta do projeto:**

Bash
```
mkdir arch-mcp-agent
cd arch-mcp-agent
```


2. **Criar um Ambiente Virtual:**

Bash
```
python -m venv venv
source venv/bin/activate
```

3. **Instalar Dependências:**

Bash
```
pip install mcp google-genai asyncio
```

4. **Salvar o Código:**

- Salve o código do servidor como `mcp_server.py`.

- Salve o código do cliente como `mcp_agent.py`.
- 
----------

## 🔑 Configuração

Você precisa definir sua chave da API do Google Gemini como uma variável de ambiente.

**Temporária (Sessão Atual):**

Bash
```
export GEMINI_API_KEY="sua_chave_de_api_real_aqui"
```

**Permanente (Adicione ao  `~/.bashrc` ou `~/.zshrc`):**

Bash
```
echo 'export GEMINI_API_KEY="sua_chave_de_api_real_aqui"' >> ~/.bashrc
source ~/.bashrc
```

----------

## 🖥️ Uso

1. **Ative o Ambiente Virtual** (se ainda não estiver ativo):

Bash
```
source venv/bin/activate
```

2. **Execute o Agente:**

Bash

```
python mcp_agent.py
```

3. **Interaja:**
    
 O agente será inicializado e solicitará que você relate o problema.

**Exemplo:**

> **Problema do Usuário>** Meu horário não está sincronizando. Instale e habilite o NTP.

4. **Revise o Plano:**

O agente gerará um plano:
    
    Plaintext
    ```
    📋 PLANO PROPOSTO:
	1. sudo pacman -S --noconfirm chrony
	2. sudo systemctl start chronyd
	3. sudo systemctl enable chronyd
	4. timedatectl set-ntp true
	5. timedatectl status
    ```
    

6. **Autorização e Autenticação:**

- O agente detecta o uso de `sudo`.

- Ele solicita sua senha **uma vez**: `Digite a senha do sudo (será armazenada em cache para esta sessão):`

- Ele solicita confirmação: `Executar este plano completo? [s/N]:`

7. **Acompanhamento da Execução:**

O agente executa os comandos um por um. Se um comando falhar (por exemplo, pacote não encontrado), a execução é interrompida e o agente pode sugerir uma correção na próxima execução.

----------

## 🛡️ Segurança e Limitações

- **Acesso Sudo:** Esta ferramenta é poderosa. Ela pode modificar arquivos do sistema, instalar pacotes e alterar configurações. **NUNCA** aprove um plano sem ler os comandos.

- **Edição de Arquivos:** O agente usa `sed` e `tee` para editar arquivos. Embora seja instruído a fazer backups, edições complexas (como substituições de expressões regulares) podem, às vezes, falhar. - **Janela de Contexto:** O agente memoriza o histórico da sessão atual. Se a conversa ficar muito longa ou confusa, digite `quit` e reinicie o script para limpar o contexto.

----------

## 🐛 Solução de Problemas

- **"Conexão Fechada" / Arquivo Não Encontrado:**

Certifique-se de que `mcp_server.py` esteja no **mesmo diretório** que `mcp_agent.py`. O script usa detecção de caminho relativo para encontrar o servidor.

- **"Permissão Negada" (Erros de Sudo):**

Se o agente exibir "sudo: um terminal é necessário...", a injeção de senha falhou. Certifique-se de estar usando a versão mais recente de `mcp_agent.py`, que inclui a lógica `sudo -S`.

- **Erros de API:**

Se você vir `Erro de API Gemini`, verifique sua conexão com a internet e confirme se sua `GEMINI_API_KEY` é válida e possui cota restante.
