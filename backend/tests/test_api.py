from conftest import login


# ---------- 1. Cadastro e autenticação ----------

def test_register_and_login(client):
    r = client.post("/api/auth/register", json={"name": "Novo Usuário", "email": "Novo@Teste.com", "password": "abc12345"})
    assert r.status_code == 201
    assert r.json()["user"]["role"] == "solicitante"
    assert r.json()["user"]["email"] == "novo@teste.com"
    headers = login(client, "novo@teste.com", "abc12345")
    assert client.get("/api/auth/me", headers=headers).json()["name"] == "Novo Usuário"


def test_duplicate_email_and_wrong_password(client):
    r = client.post("/api/auth/register", json={"name": "X", "email": "admin@helpdesk.com", "password": "abc12345"})
    assert r.status_code in (409, 422)
    r = client.post("/api/auth/login", json={"email": "admin@helpdesk.com", "password": "errada"})
    assert r.status_code == 401


def test_protected_routes(client, requester):
    assert client.get("/api/tickets").status_code == 401
    assert client.get("/api/dashboard", headers=requester).status_code == 403
    assert client.post("/api/ai/retrain", headers=requester).status_code == 403


# ---------- 2/3/4. Abertura, classificação e atribuição ----------

def test_create_ticket_is_classified_and_assigned(client, requester):
    r = client.post("/api/tickets", headers=requester, json={
        "title": "Impressora não imprime",
        "description": "Mando imprimir e o documento fica parado na fila da impressora do setor.",
    })
    assert r.status_code == 201, r.text
    t = r.json()
    assert t["ai_category"] == "Impressora"
    assert t["category"] == "Impressora"
    assert t["status"] == "Aberto"
    assert t["assignee"]["name"].startswith("Elisa")  # especialista em impressora
    assert t["sla_due_at"] is not None
    assert any("IA" in c["body"] for c in t["comments"])
    assert t["suggestions"], "deveria sugerir artigo da base de conhecimento"
    assert t["suggestions"][0]["category"] == "Impressora"


def test_security_rule_raises_priority(client, requester):
    r = client.post("/api/tickets", headers=requester, json={
        "title": "Arquivos estranhos",
        "description": "Apareceu uma mensagem de ransomware pedindo pagamento e os arquivos não abrem.",
    })
    t = r.json()
    assert t["priority"] == "Crítica"


def test_low_confidence_goes_to_triage(client, requester, tech):
    r = client.post("/api/tickets", headers=requester, json={
        "title": "Ajuda por favor", "description": "Está acontecendo uma coisa esquisita aqui comigo.",
    })
    t = r.json()
    assert t["status"] == "Triagem"
    assert t["category"] is None and t["assignee"] is None
    # Técnico faz a triagem: define categoria -> sai da triagem
    r = client.patch(f"/api/tickets/{t['id']}", headers=tech, json={"category": "Software", "priority": "Média"})
    assert r.json()["status"] == "Aberto"
    assert r.json()["classification_reviewed"] is True
    r = client.post(f"/api/tickets/{t['id']}/auto-assign", headers=tech)
    assert r.json()["assignee"]["name"].startswith("Carla")


def test_assignment_balances_load(client, requester):
    names = []
    for i in range(2):
        r = client.post("/api/tickets", headers=requester, json={
            "title": f"Sem internet no computador {i}",
            "description": "O computador está sem acesso à internet, aparece sem conexão.",
        })
        names.append(r.json()["assignee"]["name"] if r.json()["assignee"] else None)
    assert all(n and n.startswith("Ana") for n in names)  # única especialista em Rede


def test_requester_permissions_and_resolution_flow(client, requester, tech):
    t = client.post("/api/tickets", headers=requester, json={
        "title": "Outlook não abre", "description": "O Outlook fica carregando o perfil e não abre.",
    }).json()
    # solicitante não pode mudar categoria
    assert client.patch(f"/api/tickets/{t['id']}", headers=requester, json={"category": "Rede"}).status_code == 403
    # não pode resolver sem solução
    assert client.patch(f"/api/tickets/{t['id']}", headers=tech, json={"status": "Resolvido"}).status_code == 400
    r = client.patch(f"/api/tickets/{t['id']}", headers=tech,
                     json={"resolution": "Perfil recriado.", "status": "Resolvido"})
    assert r.json()["resolved_at"] is not None
    r = client.patch(f"/api/tickets/{t['id']}", headers=requester, json={"status": "Fechado"})
    assert r.json()["status"] == "Fechado"


def test_requester_sees_only_own_tickets(client, requester):
    other = login(client, "gustavo@empresa.com")
    client.post("/api/tickets", headers=other, json={"title": "Mouse parou", "description": "O mouse sem fio parou de funcionar."})
    mine = client.get("/api/tickets", headers=requester).json()
    assert all(t["requester"]["name"] == "Fernanda Souza" for t in mine)


# ---------- 5. Base de conhecimento ----------

def test_kb_suggestions_and_crud(client, requester, tech):
    r = client.get("/api/ai/suggestions", params={"q": "esqueci minha senha"}, headers=requester)
    assert r.status_code == 200 and r.json()
    assert "senha" in r.json()[0]["title"].lower()

    art = client.post("/api/kb", headers=tech, json={
        "title": "Projetor da sala 3 sem imagem", "category": "Hardware",
        "problem": "O projetor da sala de reunião 3 não mostra imagem do notebook.",
        "solution": "Use o cabo HDMI azul e pressione Win+P > Duplicar.",
    })
    assert art.status_code == 201
    # Novo artigo passa a ser sugerido imediatamente (índice atualizado)
    r = client.get("/api/ai/suggestions", params={"q": "projetor sala reunião sem imagem"}, headers=requester)
    assert r.json()[0]["id"] == art.json()["id"]
    assert client.post("/api/kb", headers=requester, json={
        "title": "xxxxx", "problem": "xxxxxxxxxxxx", "solution": "xxxxxxxxxxxx"}).status_code == 403


def test_self_resolved_counts_as_deflection(client, requester, tech):
    arts = client.get("/api/kb", headers=requester).json()
    r = client.post("/api/tickets/self-resolved", headers=requester,
                    json={"title": "Senha", "description": "", "kb_article_id": arts[0]["id"]})
    assert r.status_code == 201 and r.json()["self_resolved"] is True
    d = client.get("/api/dashboard", headers=tech).json()
    assert d["totals"]["deflected_by_kb"] >= 1


# ---------- 6. Painel e ciclo de vida da IA ----------

def test_dashboard(client, tech):
    d = client.get("/api/dashboard", headers=tech).json()
    assert d["totals"]["tickets"] >= 5
    assert set(d["by_category"]) == {"Hardware", "Software", "Rede", "Acesso", "E-mail", "Impressora"}
    assert d["ai"]["reviewed"] >= 1
    assert len(d["daily"]) == 30


def test_retrain_uses_reviewed_tickets_and_rollback(client, admin):
    before = client.get("/api/ai/models", headers=admin).json()
    r = client.post("/api/ai/retrain", headers=admin)
    assert r.status_code == 200
    new = r.json()
    assert new["samples_from_tickets"] >= 1
    assert new["active"] is True
    r = client.post(f"/api/ai/models/{before[0]['version']}/activate", headers=admin)
    assert r.status_code == 200 and r.json()["active"] is True
