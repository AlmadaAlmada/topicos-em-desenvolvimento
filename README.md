# HelpDesk Inteligente

Sistema web de gestão de chamados de suporte com apoio de IA, desenvolvido para a disciplina
Tópicos Especiais em Desenvolvimento de Software (Grupo G1, fase de Concepção).

## Funcionalidades

| # | Funcionalidade | Usa IA? | Técnica |
|---|----------------|---------|---------|
| 1 | Cadastro e autenticação de usuários | Não | PBKDF2-SHA256 + JWT, perfis (solicitante, técnico, admin) |
| 2 | Abertura e acompanhamento de chamados | Não | CRUD, histórico, comentários, SLA por prioridade |
| 3 | Classificação e priorização automática | **Sim** | TF-IDF + Regressão Logística; regras de piso de prioridade; triagem humana se confiança < 45% |
| 4 | Atribuição de chamados a técnicos | Não | Regra: especialista da categoria com menor carga |
| 5 | Base de conhecimento com sugestão de soluções | **Sim** (busca) | Similaridade de cosseno TF-IDF sobre artigos revisados |
| 6 | Painel de indicadores | Não | Agregações SQL; inclui acurácia da IA em produção |

Também inclui: retreino do modelo com chamados revisados por técnicos, versionamento e rollback de modelos.

## Como executar

Pré-requisitos: Python 3.9+ e Node.js 18+.

### Backend (porta 8000)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Na primeira execução o banco SQLite (`helpdesk.db`) é criado, o modelo é treinado e os dados de demonstração são carregados.
Documentação interativa da API: http://localhost:8000/docs

### Frontend (porta 5173)

```bash
cd frontend
npm install
npm run dev
```

Acesse http://localhost:5173.

### Contas de demonstração (senha `senha123`)

| Perfil | E-mail |
|--------|--------|
| Administrador | admin@helpdesk.com |
| Técnicos | ana@ (Rede), bruno@ (Hardware), carla@ (Software), diego@ (Acesso/E-mail), elisa@ (Impressora) — domínio `helpdesk.com` |
| Solicitantes | fernanda@empresa.com, gustavo@empresa.com, helena@empresa.com |

## Testes e avaliação do modelo

```bash
cd backend
python -m pytest tests            # 17 testes de API e regras
python -m scripts.evaluate_model  # compara técnicas de classificação (validação cruzada)
```

## Estrutura

```
backend/
  app/
    ai/            classificador, regras de prioridade, recomendador, dados de treino
    routers/       auth, tickets, kb, dashboard, ai_admin
    models.py      modelo de dados (SQLAlchemy)
    services.py    regras de negócio sem IA (atribuição, SLA)
  scripts/         avaliação comparativa do modelo
  tests/
frontend/
  src/pages/       Login, Cadastro, Chamados, Abrir chamado, Detalhe, Base, Painel, Administração
docs/
  screenshots/     telas do sistema
  Relatorio_Fase_Concepcao_G1.docx
```

## Variáveis de ambiente (produção)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `HELPDESK_SECRET_KEY` | chave de desenvolvimento | **Obrigatório trocar** em produção |
| `HELPDESK_DATABASE_URL` | SQLite local | ex.: `postgresql://...` |
| `HELPDESK_AI_THRESHOLD` | 0.45 | Confiança mínima para aplicar a classificação |
| `HELPDESK_KB_THRESHOLD` | 0.12 | Similaridade mínima para sugerir artigo |
| `HELPDESK_SEED_HISTORY` | 1 | 0 para não gerar histórico fictício |
