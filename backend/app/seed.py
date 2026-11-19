"""Dados de demonstração: usuários, base de conhecimento e histórico de chamados."""
import random
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .ai.classifier import classifier
from .models import Comment, KBArticle, Ticket, User
from .security import hash_password

DEMO_PASSWORD = "senha123"

USERS = [
    ("Administrador", "admin@helpdesk.com", "admin", None, "TI"),
    ("Ana Técnica (Rede)", "ana@helpdesk.com", "tecnico", "Rede", "TI"),
    ("Bruno Técnico (Hardware)", "bruno@helpdesk.com", "tecnico", "Hardware", "TI"),
    ("Carla Técnica (Software)", "carla@helpdesk.com", "tecnico", "Software", "TI"),
    ("Diego Técnico (Acesso/E-mail)", "diego@helpdesk.com", "tecnico", "Acesso", "TI"),
    ("Elisa Técnica (Impressora)", "elisa@helpdesk.com", "tecnico", "Impressora", "TI"),
    ("Fernanda Souza", "fernanda@empresa.com", "solicitante", None, "Financeiro"),
    ("Gustavo Lima", "gustavo@empresa.com", "solicitante", None, "Comercial"),
    ("Helena Costa", "helena@empresa.com", "solicitante", None, "RH"),
]

KB = [
    ("Como redefinir a senha de rede", "Acesso",
     "Esqueci a senha do computador ou da rede e não consigo fazer login.",
     "1. Acesse o portal https://senha.empresa.local a partir de qualquer computador ou celular.\n2. Informe seu usuário e responda às perguntas de segurança.\n3. Defina a nova senha (mínimo 10 caracteres).\n4. Aguarde 5 minutos e faça login com a nova senha."),
    ("Conta bloqueada por tentativas de senha", "Acesso",
     "Usuário bloqueado após errar a senha várias vezes.",
     "O desbloqueio automático ocorre após 15 minutos. Se precisar antes, use o portal de senha (opção Desbloquear conta) ou ligue no ramal 4000."),
    ("Configurar o MFA em um celular novo", "Acesso",
     "Troquei de celular e não recebo o código de verificação do autenticador em dois fatores.",
     "1. Acesse https://mfa.empresa.local em um computador já autenticado.\n2. Remova o dispositivo antigo.\n3. Clique em Adicionar método e leia o QR Code com o app autenticador.\nSem acesso a nenhum dispositivo: abra chamado para validação de identidade."),
    ("Wi-Fi conectado sem internet", "Rede",
     "O notebook conecta no Wi-Fi mas aparece sem internet ou a conexão cai.",
     "1. Esqueça a rede e conecte novamente.\n2. Execute no prompt: ipconfig /release e ipconfig /renew.\n3. Reinicie o notebook.\n4. Se persistir, teste outro ponto de acesso; se só a sua máquina falha, abra chamado."),
    ("VPN com erro de tempo esgotado", "Rede",
     "A VPN não conecta em home office, dá erro de tempo esgotado.",
     "1. Verifique se a sua internet doméstica funciona.\n2. Feche o cliente VPN e abra novamente como administrador.\n3. Confirme o servidor vpn.empresa.com.br.\n4. Desative temporariamente outras VPNs ou antivírus de terceiros."),
    ("Unidade de rede mapeada não abre", "Rede",
     "Não consigo acessar a pasta de rede mapeada, aparece caminho não encontrado.",
     "1. Confirme que está conectado à rede da empresa ou à VPN.\n2. Abra o Explorador, clique com o botão direito na unidade e escolha Desconectar.\n3. Mapeie novamente: \\\\arquivos\\setor.\n4. Se der acesso negado, solicite permissão ao gestor da pasta."),
    ("Outlook não abre ou fica carregando o perfil", "E-mail",
     "O Outlook fica travado em carregando perfil e não abre.",
     "1. Feche o Outlook pelo Gerenciador de Tarefas.\n2. Abra com outlook.exe /safe (Win+R).\n3. Se abrir, desative suplementos em Arquivo > Opções > Suplementos.\n4. Persistindo, recrie o perfil em Painel de Controle > Email."),
    ("Caixa de e-mail cheia", "E-mail",
     "Recebo aviso de caixa de correio cheia e não recebo novas mensagens.",
     "1. Esvazie a pasta Itens Excluídos e Lixo Eletrônico.\n2. Ordene por tamanho e apague anexos grandes antigos.\n3. Ative o Arquivo Morto Online (Arquivo > Ferramentas > Limpeza de caixa de correio)."),
    ("Configurar resposta automática de ausência", "E-mail",
     "Como ativar a resposta automática de férias no e-mail.",
     "No Outlook: Arquivo > Respostas Automáticas > Enviar respostas automáticas. Defina o período e a mensagem para internos e externos."),
    ("Recebi um e-mail suspeito (phishing)", "E-mail",
     "E-mail pedindo senha, link estranho, mensagem suspeita de golpe.",
     "NÃO clique em links nem abra anexos. Use o botão Reportar Phishing do Outlook. Se já clicou e digitou a senha, troque a senha imediatamente e abra chamado com prioridade crítica."),
    ("Impressora não imprime, documento fica na fila", "Impressora",
     "Mando imprimir e o documento fica parado na fila de impressão.",
     "1. Verifique se a impressora está ligada e sem erro no painel.\n2. Abra a fila de impressão e cancele todos os documentos.\n3. Reinicie o serviço Spooler (services.msc > Spooler de Impressão > Reiniciar).\n4. Envie a impressão novamente."),
    ("Papel enroscado na impressora", "Impressora",
     "Papel preso, atolado ou enroscado na impressora.",
     "1. Desligue a impressora.\n2. Abra as tampas indicadas no painel e puxe o papel devagar, no sentido do fluxo.\n3. Verifique se não ficaram pedaços.\n4. Ligue e imprima uma página de teste."),
    ("Instalar impressora do setor", "Impressora",
     "Como instalar a impressora do setor no computador novo.",
     "Win+R > digite \\\\impressao > dê duplo clique na impressora do seu andar. O driver é instalado automaticamente."),
    ("Excel trava ao abrir uma planilha", "Software",
     "O Excel trava ou fecha ao abrir uma planilha específica.",
     "1. Abra o Excel em modo seguro (excel /safe).\n2. Abra a planilha via Arquivo > Abrir > Abrir e Reparar.\n3. Desative suplementos COM.\n4. Se a planilha estiver na rede, copie para a máquina e teste."),
    ("Teams fecha sozinho ou não abre", "Software",
     "O Microsoft Teams fecha logo após abrir ou não carrega.",
     "1. Saia do Teams pela bandeja do sistema.\n2. Apague a pasta %appdata%\\Microsoft\\Teams (cache).\n3. Abra o Teams novamente e faça login.\n4. Alternativa imediata: use teams.microsoft.com no navegador."),
    ("Solicitar instalação de software", "Software",
     "Preciso instalar um programa no computador.",
     "Softwares homologados podem ser instalados pelo Portal da Empresa (Central de Software). Para softwares não homologados, abra chamado com a justificativa e a aprovação do gestor."),
    ("Computador lento", "Hardware",
     "O computador está muito lento, travando ou esquentando.",
     "1. Reinicie o computador (não apenas bloqueie a tela).\n2. Feche abas e programas que não estão em uso.\n3. Verifique espaço em disco (mínimo 10% livre).\n4. Se houver aquecimento ou ruído no ventilador, abra chamado para manutenção."),
    ("Monitor externo sem imagem na docking station", "Hardware",
     "Monitores externos não dão imagem quando conecto o notebook na dock.",
     "1. Desconecte e reconecte o cabo da dock.\n2. Pressione Win+P e escolha Estender.\n3. Atualize o firmware da dock pelo Portal da Empresa.\n4. Teste o monitor direto no notebook para isolar o problema."),
]

HISTORY = [
    ("Não consigo acessar o wifi do 2º andar", "O notebook não encontra a rede corporativa no segundo andar.", "Rede"),
    ("Esqueci minha senha de novo", "Não lembro a senha e o computador não deixa entrar.", "Acesso"),
    ("Impressora do RH sem imprimir", "Os documentos ficam presos na fila da impressora do RH.", "Impressora"),
    ("Outlook travado", "O Outlook não abre desde a atualização de ontem.", "E-mail"),
    ("Planilha de custos travando o Excel", "Sempre que abro a planilha de custos o Excel para de responder.", "Software"),
    ("Notebook superaquecendo", "Meu notebook esquenta muito e desliga sozinho.", "Hardware"),
    ("VPN caindo toda hora", "A VPN desconecta a cada 10 minutos em home office.", "Rede"),
    ("Acesso ao sistema de compras", "Preciso de acesso ao módulo de compras do ERP, já aprovado pelo gestor.", "Acesso"),
    ("Mouse com defeito", "O clique esquerdo do mouse falha.", "Hardware"),
    ("Instalar o Zoom", "Preciso do Zoom instalado para falar com um cliente.", "Software"),
    ("Caixa postal lotada", "Meu e-mail diz que a caixa está cheia.", "E-mail"),
    ("Impressora com papel preso", "Papel atolado na multifuncional da recepção.", "Impressora"),
    ("Sem internet na sala 12", "Nenhum computador da sala 12 tem internet.", "Rede"),
    ("Conta bloqueada", "Minha conta está bloqueada, errei a senha.", "Acesso"),
    ("Teams não abre", "O Teams fecha sozinho quando abro.", "Software"),
    ("Monitor sem imagem", "Conectei na dock e o monitor ficou sem sinal.", "Hardware"),
    ("Recebi e-mail estranho pedindo senha", "Chegou um e-mail dizendo que minha conta vai expirar e pedindo para clicar no link.", "E-mail"),
    ("Toner fraco", "As impressões saem muito claras.", "Impressora"),
    ("Pasta de rede não abre", "A unidade Z: do financeiro diz caminho não encontrado.", "Rede"),
    ("Código do autenticador não chega", "Troquei de celular e o MFA não funciona mais.", "Acesso"),
    ("Erro no sistema de vendas", "O sistema de vendas dá erro ao finalizar o pedido.", "Software"),
    ("Teclado sem funcionar", "O teclado parou totalmente de funcionar.", "Hardware"),
    ("E-mails não chegam do cliente", "As mensagens de um cliente não estão chegando, nem no spam.", "E-mail"),
    ("Instalar impressora nova", "Recebi computador novo e preciso instalar a impressora do setor.", "Impressora"),
    ("Internet muito lenta hoje", "Sites e sistemas web estão muito lentos.", "Rede"),
    ("Permissão de leitura na pasta jurídico", "Preciso ler documentos da pasta do jurídico.", "Acesso"),
    ("Computador lento demais", "Demora 10 minutos para ligar e abrir os programas.", "Hardware"),
    ("Atualizar o navegador", "O Chrome está pedindo atualização e não tenho permissão.", "Software"),
    ("Assinatura de e-mail padrão", "Como coloco a assinatura nova da empresa?", "E-mail"),
    ("Ninguém do setor consegue imprimir", "Todos do setor estão sem conseguir imprimir, a impressora aparece offline.", "Impressora"),
    ("Cabo de rede quebrado", "O conector do cabo de rede quebrou.", "Rede"),
    ("Erro de licença no Office", "O Word diz que o produto não está licenciado.", "Software"),
]


def seed(db: Session, with_history: bool = True) -> None:
    if db.execute(select(User).limit(1)).first():
        return  # já populado
    rng = random.Random(7)
    users = {}
    for name, email, role, specialty, dept in USERS:
        u = User(name=name, email=email, role=role, specialty=specialty, department=dept,
                 password_hash=hash_password(DEMO_PASSWORD))
        db.add(u)
        users[email] = u
    db.flush()

    admin = users["admin@helpdesk.com"]
    for title, cat, problem, solution in KB:
        db.add(KBArticle(title=title, category=cat, problem=problem, solution=solution, author_id=admin.id,
                         times_suggested=rng.randint(3, 30), times_helpful=rng.randint(0, 12)))
    db.flush()

    if not with_history:
        db.commit()
        return

    requesters = [u for u in users.values() if u.role == "solicitante"]
    techs = {u.specialty: u for u in users.values() if u.role == "tecnico"}
    techs["E-mail"] = techs["Acesso"]
    now = datetime.utcnow()
    for i, (title, desc, true_cat) in enumerate(HISTORY):
        c = classifier.classify(title, desc)
        created = now - timedelta(days=rng.randint(0, 27), hours=rng.randint(0, 20), minutes=rng.randint(0, 59))
        t = Ticket(title=title, description=desc, requester_id=rng.choice(requesters).id, created_at=created,
                   ai_category=c.category, ai_category_confidence=c.category_confidence, ai_priority=c.ai_priority,
                   ai_priority_confidence=c.priority_confidence, ai_model_version=c.model_version,
                   priority_rule=c.priority_rule, priority=c.priority, category=true_cat)
        tech = techs[true_cat]
        t.assignee_id = tech.id
        t.assigned_at = created + timedelta(minutes=rng.randint(1, 90))
        roll = rng.random()
        if i >= len(HISTORY) - 6:  # chamados recentes ainda abertos
            t.status = rng.choice(["Aberto", "Em atendimento", "Aguardando usuário"])
            t.classification_reviewed = t.status != "Aberto"
            t.created_at = now - timedelta(hours=rng.randint(1, 30))
            t.assigned_at = t.created_at + timedelta(minutes=10)
        else:
            t.classification_reviewed = True
            t.status = "Fechado" if roll < 0.6 else "Resolvido"
            t.resolved_at = t.assigned_at + timedelta(hours=rng.uniform(0.5, 40))
            t.resolution = "Problema resolvido conforme procedimento padrão da base de conhecimento."
        db.add(t)
        db.flush()
        db.add(Comment(ticket_id=t.id, author_id=t.requester_id, is_system=True, created_at=created,
                       body=f"IA ({c.model_version}) sugeriu categoria '{c.category}' ({c.category_confidence:.0%}) "
                            f"e prioridade '{c.ai_priority}'."))
        if c.category != true_cat and t.classification_reviewed:
            db.add(Comment(ticket_id=t.id, author_id=tech.id, is_system=True, created_at=t.assigned_at,
                           body=f"Classificação ajustada: categoria '{c.category}' → '{true_cat}'."))

    # Alguns casos resolvidos pelo próprio usuário via base de conhecimento.
    arts = db.execute(select(KBArticle)).scalars().all()
    for _ in range(7):
        art = rng.choice(arts)
        when = now - timedelta(days=rng.randint(0, 27))
        db.add(Ticket(title=art.title, description="(resolvido via base de conhecimento)",
                      requester_id=rng.choice(requesters).id, status="Resolvido", category=art.category,
                      priority="Baixa", self_resolved=True, kb_article_used_id=art.id, created_at=when,
                      resolved_at=when + timedelta(minutes=5),
                      resolution=f"Resolvido pelo próprio usuário com o artigo #{art.id}"))
    db.commit()
