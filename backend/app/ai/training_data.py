"""Conjunto inicial (semente) de chamados rotulados.

Na fase de concepção não existe histórico real de chamados da organização.
Este conjunto foi construído manualmente pela equipe para permitir o
"arranque a frio" (cold start) do classificador. Conforme o sistema é
usado, chamados com classificação confirmada por técnicos são incorporados
ao treino (ver ai/classifier.py -> retrain).

Critério de rótulo de prioridade:
- Crítica: muitos usuários afetados, serviço essencial parado ou incidente de segurança.
- Alta:    um usuário totalmente impedido de trabalhar.
- Média:   funcionamento degradado, existe contorno.
- Baixa:   solicitação, dúvida ou problema estético.

Formato: (título, descrição, categoria, prioridade)
"""

SEED_TICKETS = [
    # ---------------- Hardware ----------------
    ("Notebook não liga", "Apertei o botão de ligar e nada acontece, nem a luz acende. Já tentei com outro carregador.", "Hardware", "Alta"),
    ("Tela do monitor piscando", "O monitor fica piscando de tempos em tempos, consigo trabalhar mas incomoda bastante.", "Hardware", "Média"),
    ("Teclado com teclas falhando", "Algumas teclas do teclado não funcionam, como a letra A e o espaço.", "Hardware", "Média"),
    ("Mouse sem fio parou", "O mouse sem fio parou de responder, já troquei a pilha.", "Hardware", "Média"),
    ("Computador muito lento e esquentando", "A máquina está esquentando muito e travando, o ventilador faz barulho alto.", "Hardware", "Média"),
    ("Solicito segundo monitor", "Gostaria de solicitar um segundo monitor para minha estação de trabalho.", "Hardware", "Baixa"),
    ("Notebook caiu e a tela quebrou", "Meu notebook caiu da mesa e a tela trincou, não consigo ver nada.", "Hardware", "Alta"),
    ("Headset sem áudio", "O headset não reproduz som nas reuniões, o microfone funciona.", "Hardware", "Média"),
    ("Bateria do notebook não carrega", "A bateria fica em 0% mesmo ligada na tomada, se tirar da tomada desliga.", "Hardware", "Média"),
    ("Computador reiniciando sozinho", "O desktop reinicia sozinho várias vezes por dia, perco o que estava fazendo.", "Hardware", "Alta"),
    ("Troca de teclado por modelo ergonômico", "Solicito troca do teclado por um modelo ergonômico por recomendação médica.", "Hardware", "Baixa"),
    ("Webcam não é reconhecida", "A webcam USB não aparece no Teams nem no gerenciador de dispositivos.", "Hardware", "Média"),
    ("Servidor com disco falhando", "O servidor de arquivos está emitindo alerta de falha no disco RAID, risco de perda de dados de toda a empresa.", "Hardware", "Crítica"),
    ("Tela azul ao iniciar o computador", "O computador mostra tela azul logo que liga e não entra no Windows.", "Hardware", "Alta"),
    ("Cabo do carregador danificado", "O cabo do carregador está descascado perto do conector.", "Hardware", "Média"),
    ("Docking station não reconhece monitores", "Quando conecto o notebook na dock os monitores externos não dão imagem.", "Hardware", "Média"),

    # ---------------- Software ----------------
    ("Excel travando ao abrir planilha", "O Excel trava toda vez que abro a planilha de orçamento, as outras abrem normal.", "Software", "Média"),
    ("Instalar Power BI", "Preciso que instalem o Power BI Desktop na minha máquina para um relatório.", "Software", "Baixa"),
    ("Sistema ERP com erro ao salvar pedido", "Ao salvar pedido de venda no ERP aparece erro de banco de dados e o pedido não é gravado.", "Software", "Alta"),
    ("Licença do Office expirada", "O Word diz que a licença expirou e não deixa editar documentos.", "Software", "Alta"),
    ("Atualização do Windows travada", "A atualização do Windows está parada em 30% há horas.", "Software", "Média"),
    ("Antivírus detectou ameaça", "O antivírus mostrou alerta de vírus encontrado e vários arquivos ficaram com extensão estranha.", "Software", "Crítica"),
    ("Teams não abre", "O Microsoft Teams fecha sozinho logo após abrir, não consigo entrar nas reuniões.", "Software", "Alta"),
    ("Erro ao gerar PDF no sistema financeiro", "O botão de exportar PDF do sistema financeiro dá erro, consigo imprimir pela tela.", "Software", "Média"),
    ("Sistema de folha de pagamento fora do ar", "O sistema de folha está fora do ar para todo o RH no dia de fechamento.", "Software", "Crítica"),
    ("Navegador abrindo propagandas", "O Chrome abre abas de propaganda sozinho e a página inicial mudou.", "Software", "Média"),
    ("Dúvida sobre atalho no Word", "Como faço para criar um sumário automático no Word?", "Software", "Baixa"),
    ("Programa de CAD não inicia", "O AutoCAD mostra erro de DLL ao iniciar, preciso entregar um projeto hoje.", "Software", "Alta"),
    ("Atualizar versão do Adobe Reader", "Solicito atualização do Adobe Reader que está em versão antiga.", "Software", "Baixa"),
    ("CRM muito lento", "O CRM está demorando mais de um minuto para abrir cada cliente.", "Software", "Média"),
    ("Erro de certificado no sistema de notas fiscais", "O sistema de emissão de notas fiscais diz que o certificado digital venceu e nenhuma nota pode ser emitida.", "Software", "Crítica"),
    ("Instalação de software de edição de vídeo", "Peço a instalação de um editor de vídeo para o time de marketing.", "Software", "Baixa"),

    # ---------------- Rede ----------------
    ("Sem internet no computador", "Meu computador está sem acesso à internet, aparece sem conexão no ícone de rede.", "Rede", "Alta"),
    ("Wi-Fi caindo toda hora", "O Wi-Fi da sala de reuniões cai a cada poucos minutos.", "Rede", "Média"),
    ("Internet fora do ar no prédio todo", "Nenhum computador do prédio consegue acessar a internet desde as 9h.", "Rede", "Crítica"),
    ("VPN não conecta", "Trabalhando de casa, a VPN dá erro de tempo esgotado e não consigo acessar os sistemas internos.", "Rede", "Alta"),
    ("Internet lenta", "A internet está bem lenta hoje, sites demoram para carregar.", "Rede", "Média"),
    ("Pasta de rede inacessível", "Não consigo acessar a unidade de rede mapeada Z:, diz caminho não encontrado.", "Rede", "Alta"),
    ("Ponto de rede sem sinal", "O ponto de rede da minha mesa nova não funciona, o cabo não acende.", "Rede", "Média"),
    ("Solicitar acesso ao Wi-Fi de visitantes", "Preciso da senha do Wi-Fi de visitantes para um cliente que virá amanhã.", "Rede", "Baixa"),
    ("Switch do andar desligado", "O switch do terceiro andar desligou e todo o andar ficou sem rede e sem telefone.", "Rede", "Crítica"),
    ("Site interno não abre", "A intranet não carrega, aparece erro de DNS, outros sites funcionam.", "Rede", "Média"),
    ("Liberar site bloqueado pelo firewall", "O firewall está bloqueando o site de um fornecedor que preciso consultar.", "Rede", "Baixa"),
    ("Chamadas de vídeo travando", "As chamadas de vídeo ficam travando e cortando o áudio por causa da conexão.", "Rede", "Média"),
    ("Ataque na rede suspeito", "O firewall registrou muitas tentativas de acesso externo e alguns servidores estão instáveis, suspeita de invasão.", "Rede", "Crítica"),
    ("Cabo de rede para nova estação", "Preciso de um cabo de rede maior para a nova mesa.", "Rede", "Baixa"),
    ("IP duplicado na rede", "Aparece mensagem de conflito de endereço IP e a rede cai.", "Rede", "Média"),
    ("Sem conexão no notebook novo", "O notebook novo não reconhece nenhuma rede Wi-Fi, a placa parece desativada.", "Rede", "Alta"),

    # ---------------- Acesso ----------------
    ("Esqueci minha senha", "Esqueci a senha do computador e não consigo fazer login.", "Acesso", "Alta"),
    ("Usuário bloqueado", "Minha conta foi bloqueada depois de errar a senha várias vezes.", "Acesso", "Alta"),
    ("Acesso à pasta do financeiro", "Solicito permissão de leitura na pasta compartilhada do financeiro, aprovada pelo gestor.", "Acesso", "Baixa"),
    ("Criar usuário para novo colaborador", "Um novo colaborador começa segunda-feira e precisa de usuário de rede, e-mail e acesso ao ERP.", "Acesso", "Média"),
    ("Remover acessos de colaborador desligado", "O colaborador João foi desligado hoje, favor revogar todos os acessos imediatamente.", "Acesso", "Alta"),
    ("Senha expirada no sistema", "O sistema pede para trocar a senha expirada mas dá erro ao salvar a nova.", "Acesso", "Média"),
    ("Autenticação em dois fatores não funciona", "Troquei de celular e não recebo mais o código de verificação do MFA.", "Acesso", "Alta"),
    ("Permissão de administrador local", "Preciso de permissão de administrador para instalar drivers de um equipamento de laboratório.", "Acesso", "Baixa"),
    ("Conta acessada por terceiros", "Recebi aviso de login na minha conta de outro país, acho que roubaram minha senha.", "Acesso", "Crítica"),
    ("Acesso negado ao sistema de RH", "Ao entrar no sistema de RH aparece acesso negado, ontem funcionava.", "Acesso", "Média"),
    ("Alterar perfil de acesso no ERP", "Fui promovido e preciso do perfil de aprovador no ERP.", "Acesso", "Baixa"),
    ("Ninguém consegue logar no domínio", "Todos os usuários estão recebendo erro de relação de confiança ao fazer login, ninguém consegue trabalhar.", "Acesso", "Crítica"),
    ("Desbloquear crachá de acesso ao sistema", "Meu login no sistema de ponto está desativado e não consigo registrar o ponto.", "Acesso", "Média"),
    ("Acesso ao repositório de código", "Solicito acesso ao repositório Git do projeto novo.", "Acesso", "Baixa"),
    ("Login no portal dá erro de credenciais", "Digito usuário e senha corretos no portal e diz credenciais inválidas.", "Acesso", "Média"),
    ("Trocar senha do e-mail e da rede", "Quero trocar minha senha por segurança, como faço?", "Acesso", "Baixa"),

    # ---------------- E-mail ----------------
    ("Caixa de e-mail cheia", "Recebo aviso de que a caixa de correio está cheia e não recebo novas mensagens.", "E-mail", "Média"),
    ("Não consigo enviar e-mails", "Os e-mails ficam na caixa de saída e não são enviados.", "E-mail", "Alta"),
    ("Outlook não abre", "O Outlook fica carregando o perfil e não abre.", "E-mail", "Alta"),
    ("Recebi e-mail suspeito", "Recebi um e-mail pedindo para confirmar minha senha em um link estranho.", "E-mail", "Média"),
    ("Cliquei em link de phishing", "Cliquei em um link de um e-mail falso e digitei minha senha, agora estão saindo e-mails da minha conta para todos os contatos.", "E-mail", "Crítica"),
    ("Criar lista de distribuição", "Solicito a criação de uma lista de e-mail para a equipe comercial.", "E-mail", "Baixa"),
    ("Assinatura de e-mail", "Como configuro a assinatura padrão da empresa no Outlook?", "E-mail", "Baixa"),
    ("E-mail não sincroniza no celular", "Configurei o e-mail no celular mas não sincroniza as mensagens novas.", "E-mail", "Média"),
    ("Servidor de e-mail fora do ar", "Ninguém da empresa consegue enviar nem receber e-mails desde cedo.", "E-mail", "Crítica"),
    ("E-mails indo para o spam", "Os e-mails de um cliente importante estão indo para a pasta de spam.", "E-mail", "Média"),
    ("Recuperar e-mail apagado", "Apaguei sem querer uma pasta de e-mails importantes, é possível recuperar?", "E-mail", "Média"),
    ("Acesso a caixa compartilhada", "Preciso acessar a caixa compartilhada do atendimento pelo Outlook.", "E-mail", "Baixa"),
    ("Anexo grande não envia", "Não consigo enviar um anexo de 40 MB, volta erro de tamanho.", "E-mail", "Baixa"),
    ("Calendário não mostra reuniões", "As reuniões aceitas não aparecem no calendário do Outlook.", "E-mail", "Média"),
    ("Resposta automática de férias", "Como ativo a resposta automática de ausência para minhas férias?", "E-mail", "Baixa"),
    ("E-mail de cliente devolvido", "Mensagens para o domínio de um cliente voltam com erro de entrega.", "E-mail", "Média"),

    # ---------------- Impressora ----------------
    ("Impressora não imprime", "Mando imprimir e o documento fica na fila sem sair nada.", "Impressora", "Média"),
    ("Papel enroscado na impressora", "A impressora do segundo andar está com papel preso e mostra erro.", "Impressora", "Média"),
    ("Toner acabando", "A impressão está saindo clara, o toner deve estar acabando.", "Impressora", "Baixa"),
    ("Instalar impressora no computador", "Preciso instalar a impressora do setor no meu computador novo.", "Impressora", "Baixa"),
    ("Impressora offline", "A impressora aparece como offline para todos do setor.", "Impressora", "Média"),
    ("Scanner não envia para e-mail", "A multifuncional não envia mais os documentos digitalizados para o e-mail.", "Impressora", "Média"),
    ("Impressão saindo manchada", "As folhas saem com manchas pretas e listras.", "Impressora", "Baixa"),
    ("Impressora de etiquetas parada na expedição", "A impressora de etiquetas da expedição parou e nenhum pedido pode ser despachado.", "Impressora", "Crítica"),
    ("Configurar impressão frente e verso", "Como deixo a impressão frente e verso como padrão?", "Impressora", "Baixa"),
    ("Impressora fazendo barulho estranho", "A impressora faz um barulho alto de engrenagem ao puxar o papel.", "Impressora", "Média"),
    ("Driver da impressora com erro", "Ao imprimir aparece erro de driver indisponível.", "Impressora", "Média"),
    ("Impressora fiscal não emite cupom", "A impressora fiscal do caixa não emite cupom e as vendas estão paradas na loja.", "Impressora", "Crítica"),
    ("Solicitar nova impressora para o setor", "O setor cresceu e gostaríamos de uma impressora adicional.", "Impressora", "Baixa"),
    ("Fila de impressão travada", "A fila de impressão travou com um documento que não pode ser cancelado.", "Impressora", "Média"),
    ("Impressora colorida imprimindo só preto", "A impressora colorida só imprime em preto e branco.", "Impressora", "Baixa"),
    ("Preciso imprimir contrato urgente e a impressora não funciona", "Tenho uma assinatura de contrato em 30 minutos e nenhuma impressora imprime.", "Impressora", "Alta"),
]
