# 📊 Desafio Python Alpha Fitness

Aplicação web completa para o processo seletivo da Rede Alpha Fitness.

## 🚀 Funcionalidades
- Leitura automática de dados de uma planilha Google Sheets
- Exibição dos registros em tabela responsiva
- Atualização automática em tempo real (WebSocket)
- Filtro de pesquisa instantâneo
- Backend Python (FastAPI, APScheduler)
- Frontend ultra-minimalista (HTML, CSS, JS)

## 🏗️ Estrutura do Projeto

├── main.py                # Entry point da aplicação
├── app/
│   ├── main.py            # FastAPI app principal
│   ├── config.py          # Configurações
│   ├── api/               # Rotas e WebSocket
│   ├── models/            # Modelos Pydantic
│   ├── services/          # Serviços (planilha, websocket)
│   └── utils/             # Utilitários (logger, processamento)
├── static/                # Arquivos estáticos (JS, CSS)
├── templates/             # HTML frontend
├── requirements.txt       # Dependências Python
├── Procfile, runtime.txt  # Arquivos de deploy


## ⚙️ Como Executar Localmente
1. Instale as dependências:
   bash
   pip install -r requirements.txt
   
2. Execute a aplicação:
   bash
   python main.py
   
3. Acesse [http://localhost:8000](http://localhost:8000) no navegador

## 🔗 Planilha Google Sheets
- [Planilha Editável](https://docs.google.com/spreadsheets/d/1OO7gDKXv4YJiDfpfrIHaXIa_XUgDhl3rG2FQImQ-ixY/edit?gid=0#gid=0)
- [Planilha CSV (usada pela aplicação)](https://docs.google.com/spreadsheets/d/1OO7gDKXv4YJiDfpfrIHaXIa_XUgDhl3rG2FQImQ-ixY/export?format=csv&gid=0)

## 🧪 Como Testar Atualização em Tempo Real
1. Adicione ou edite dados na planilha Google Sheets
2. Aguarde até 30 segundos (intervalo de atualização)
3. Veja os dados atualizarem automaticamente no site

## 📦 Tecnologias Utilizadas
- Python 3.11+
- FastAPI
- APScheduler
- httpx
- Pydantic
- HTML5, CSS3, JavaScript

## 🏆 Diferenciais
- Arquitetura limpa e profissional
- Código organizado e comentado
- Interface amigável e responsiva
- Logs detalhados para debug

## 👨‍💻 Autor
MaTheus Reis Machado
Desenvolvido para o processo seletivo da Rede Alpha Fitness.
