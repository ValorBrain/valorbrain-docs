# Plano — OpenBao, isolamento de CI e remediação de segurança

**Data:** 2026-09-23
**Status:** OpenBao/agents, CI database isolation, P0 auth/authorization corridors, unit secret cleanup, audit rotation, Raft snapshots e suíte Engine verde validados; runner ainda fisicamente no host, remoção dos `.env` fallback e custódia offline do recovery material pendentes
**Escopo:** Engine, SaaS, Ops, runners, Jira e hosts auxiliares

## Objetivo

Centralizar segredos sem revogar ou rotacionar chaves de inferência, GitHub PAT ou Cloudflare; mover o CI para fora do host de produção; corrigir os bloqueadores de autorização/isolamento; e validar Jira sem alterar sua configuração.

## Restrições confirmadas

- Não revogar PATs do GitHub.
- Não rotacionar chaves de inferência.
- Não rotacionar chaves Cloudflare nesta etapa.
- Não trocar pricing nem iniciar self-service; manter `talk-to-us` enquanto a oferta estiver em revisão.
- Não quebrar sessões JWT atuais.
- Não executar migrations ou alterações destrutivas em produção sem gate e rollback.
- Preservar alterações de trabalho já existentes nos quatro repositórios.

## Abordagem

### Fase 0 — baseline e isolamento

- Inventariar units, ambientes, listeners e policies sem imprimir valores.
- Confirmar backup/restore e estado do host destino.
- Manter os valores atuais como fallback durante toda a migração.
- Criar diretório de credenciais e adaptadores de leitura somente após o gate da Fase 1.

### Resultado da Fase 0 (2026-09-23)

- `peace.atrative.com.br` (`vps-valor`) foi validado: Ubuntu 24.04.5, 4 vCPU, 15 GiB RAM, 104 GiB livres, Tailscale e Docker ativos.
- O VPS é compartilhado por CloudPanel, Mailcow, PostgreSQL, SearXNG e o watcher do Engine; o OpenBao precisa ficar isolado, sem socket do Docker, nginx ou porta pública.
- OpenBao/Vault não está instalado; a porta local 8200 está livre e o UFW não a libera.
- `desktop-brj0r2g-1` é WSL2, sem Bun e com systemd/netlink limitado; não será usado como runner persistente sem uma decisão alternativa.
- Testes focados SaaS: 72/72; testes de backup/restore: 75/75; typechecks Engine e SaaS: verdes.
- Backup local do Engine tem dump, sidecar e manifest; nenhum restore drill real foi executado nesta fase.
- Nenhuma instalação, rotação, revogação, reinicialização ou alteração de produção foi feita.

### Resultado da Fase 1A (2026-09-23)

- OpenBao `v2.7.0` foi baixado do release oficial, com checksum SHA-256 e assinatura GPG verificados.
- Binário nativo instalado em `/opt/openbao/bin/bao`; usuário e diretórios dedicados criados.
- Unit `openbao.service` criada com hardening, `MemorySwapMax=0` e escrita restrita a `/var/lib/openbao`.
- Na conclusão da Fase 1A, a unit estava `disabled`/`inactive`, sem config, sem listener na 8200 e sem processo `bao`; essa foi a baseline antes da Fase 1B.
- `systemd-analyze security` reportou exposição 4.2/10 antes da inicialização.

### Resultado da Fase 1B (2026-09-23)

- OpenBao foi inicializado com TLS, Raft single-node, auditoria de arquivo `0600` e AppRole.
- Recovery Shamir 5/3 foi armazenado em `/root/.valorbrain-private/openbao/recovery-2.7.0.json`, modo `600`, sem valores impressos.
- Policies e seis AppRoles foram criadas; CI foi testado com negação `403` para `production`.
- 42 secrets production e 9 secrets staging foram copiados sem rotação; comparação de valores foi integral.
- Agents separados renderizam secrets em `/run` como `0400`; staging, Ops, SaaS e Engine principal passaram cutover com health e process-env gates.
- O timer local de unseal foi habilitado e testado após restart real do OpenBao; todos os serviços permaneceram verdes.
- `.env` foram endurecidos para `0600`; valores antigos e secrets inline de workers/units ainda permanecem como fallback e serão removidos em etapa separada.

### Fase 1 — OpenBao

- Executar OpenBao como binário nativo gerenciado por systemd, em vez de container, porque o Docker do VPS também hospeda Mailcow/CloudPanel.
- Usar usuário dedicado, filesystem e credenciais com permissões restritas, sem montar socket do Docker.
- Listener somente Tailscale; TLS; UI protegida; auditoria habilitada.
- Unseal com chaves offline separadas; nunca storing chaves no repositório.
- Policies separadas para `production`, `staging` e `ci`.
- Paths por ambiente e serviço; nenhum segredo de produção para CI.

### Fase 2 — entrega local

- Usar `systemd LoadCredential`/`LoadCredentialEncrypted` como mecanismo local.
- Criar agente/renovação para buscar valores no OpenBao e materializá-los em `/run/credentials/<unit>`.
- Manter configuração não secreta em env.
- Migrar primeiro secrets estáticos: DB, Stripe, LLM, Telegram, Cloudflare, JWT e chaves de operador.
- Não imprimir valores em logs, status, testes ou documentação.

### Fase 3 — JWT

- Manter a chave JWT atual; ela tem 96 caracteres hexadecimais e não é fraca.
- Se rotação futura for aprovada, gerar nova chave, assinar com a nova e aceitar a anterior por sete dias.
- Testar token antigo e novo antes de desligar a anterior.

### Fase 4 — CI

- Provisionar runner em máquina staging separada, não no host de produção.
- Runner sem acesso ao PostgreSQL de produção e sem `.env` de produção.
- Credenciais CI obtidas do OpenBao por policy efêmera.
- Atualizar labels dos workflows somente após smoke verde.
- Manter rollback para o runner atual até a primeira execução green.

### Fase 5 — correções de segurança

Implementar em commits separados, cada um com teste:

1. autorização REST/MCP para `vbm_`, scopes, audience, identity e visibility;
2. remover join público por `companyId`/role e exigir invite;
3. corrigir purge com verificação global de hashes;
4. remover headers de role/user como autoridade;
5. invalidar/revalidar JWT legado;
6. offboarding completo e revogação de tokens;
7. MFA/filas/Telegram e demais bugs mediums.

### Resultado da Fase 4/5 (2026-09-23)

- O CI deixou de usar `postgres`: o role `ci` é não-superusuário, sem `BYPASSRLS`, não tem `CONNECT` em `valorbrain`/`valorbrain_saas` e só provisiona bancos de teste. O role separado `ci_test_admin` existe apenas para seed/RLS de bancos CI e também não alcança produção.
- `pg_hba.conf` removeu `trust` para superusuário e trocou listeners locais/Tailscale por `scram-sha-256`; o PgBouncer foi sincronizado com os verificadores SCRAM existentes e reiniciado. O health monitor deixou de usar `psql -h localhost` sem peer/senha, eliminando o loop de restart do PostgreSQL.
- Templates schema-only sem dados (`valorbrain_ci_template` e `valorbrain_saas_ci_template`) foram criados; os workflows não copiam nem consultam bancos de produção. Runner continua no host de produção, portanto a segregação física de rede/host ainda é pendente.
- Registro público rejeita `companyId`/`role`; JWT legado e sessão são revalidados contra usuário ativo; claims de tenant/role não viram autoridade sem credencial apropriada.
- `vbm_` REST agora exige audience/escopo; `read` não muta, exporta nem cria credenciais. O worker de embed não executa mais cleanup global de hashes.
- Offboarding de usuário revoga somente tokens MCP/API ligados ao usuário; offboarding de company revoga tokens do tenant, suspende o tenant no Engine e só então marca a empresa/usuários inativos em transação.
- Cutover Engine/SaaS foi reiniciado com health gate; Engine `ok`, SaaS `ok` com database/engine/workers `true`, Agents e workers principais ativos. Testes focados e typechecks passaram.
- Continuidade verificada sem rotação: hashes de `JWT_SECRET`, `JWT_SECRET_PREVIOUS` e `AUTH_SECRET` conferem entre Agent e fallback; uma sessão JWT legada de usuário ativo retornou `200`, enquanto usuário desativado foi recusado com `401`. Nenhum token foi revogado nesta etapa; nenhuma credencial existente foi rotacionada.
- A suíte Engine completa foi executada com o role de seed isolado: 4059 passaram, 68 foram ignorados e 41 falharam/7 erros; os restantes majoritariamente em baselines de subprocessos, schema drift, contrato OpenClaw e testes de concorrência; não houve escrita em produção. Esses itens permanecem tracked como dívida de CI, sem ocultar o resultado.
- Após o endurecimento de autenticação, os jobs de anomalia, hybrid sync, ROI e triagem de feedback foram executados novamente com sucesso; coverage/family-drift continuam sendo alarmes nonzero por design, não serviços quebrados. Jobs cross-tenant de ROI/family usam peer authentication sem senha administrativa no processo.
- O endurecimento do PgBouncer expôs credenciais TCP antigas em apps vizinhos que antes dependiam de `trust`. Twenty CRM foi reconectado reutilizando a senha já existente do app no role `supabase_admin`; Manifest passou a usar o role dedicado `manifest_app`; CRM bridge ganhou o role de leitura `crm_bridge` e uma `CRM_DATABASE_URL` em arquivo root-only. Todos os três ficaram ativos e o PgBouncer ficou sem falhas de autenticação recentes.
- Segredos inline foram removidos de 33 unit files: 5 units com drop-in OpenBao tiveram as cópias inline retiradas, e 28 units passaram a ler `/etc/valorbrain/units/<unit>.env` (modo `0600`, root). Os arquivos foram validados contra os backups e nenhum valor foi impresso; os processos atuais não foram reiniciados, então a mudança vale a partir do próximo start.
- Templates systemd versionados no Engine/SaaS não contêm mais credenciais reais: deltax passou a usar peer authentication (`User=postgres`, socket Unix), kg-drift idem, e os demais passaram a referenciar os arquivos root-only ou o drop-in OpenBao.
- O audit log do OpenBao em `peace.atrative.com.br` foi rotacionado com `logrotate` (`copytruncate`, 30 rotações, compressão): caiu de ~4,2 GB para ~113 MB. Um snapshot Raft diário foi criado em `/var/backups/openbao` (root-only, 14 cópias) e testado com sucesso.
- A causa da explosão do audit log era o loop de `auth/token/renew-self`: as policies dos AppRoles não concediam `update` nesse path, então os quatro agents renovavam em retry contínuo. As policies `vb-*-read` receberam `auth/token/renew-self` e `auth/token/lookup-self`; após o restart, as renovações passaram a ocorrer em intervalo normal e o audit log caiu para ~149 KB.
- A suíte Engine completa (`tests/unit` + `tests/integration`) rodou verde no banco CI isolado: **4258 pass, 0 fail, 0 error, 43 skip** (`suite: PASS`). Foram corrigidos os grants de schema, a expectativa de triggers do schema drift, o canary de superfície, as permissões de `billing_events`, o isolamento do teste de rerank e os fixtures de conflito alinhados ao ADR-030. Typecheck Engine e SaaS verdes; teste unitário do Jira passou.
- A suíte SaaS completa rodou verde no banco CI `valorbrain_saas_ci` com o role `ci`: **896 pass, 0 fail**. Foram corrigidos o teardown de `audit_logs` (trigger de cadeia), duas chaves i18n órfãs e os grants do app role no banco de teste. O template CI do SaaS precisa manter o role `ci` como owner dos objetos para o teardown funcionar.
- A causa dos failures de conflito/conversational resolution foi identificada e corrigida no fixture: os testes semeavam o mesmo `authority` com `as_of` diferentes, e `isTemporalHistoryPair` (ADR-030) classificava o par como histórico temporal. Os fixtures agora usam autoridade mais alta no fato mais antigo, e ambos os arquivos passam 10/10 isoladamente.
- Débitos remanescentes: runner CI ainda no host de produção; `.env` de fallback ainda contêm valores; e a custódia offline do recovery material ainda depende de decisão humana.
- O isolamento lógico do runner foi verificado: o usuário `ci` não tem sudo, não lê `/opt/valorbrain/.env`, `/www/valorbrain-saas/.env` nem `/run/openbao-agent/*`, e recebe `permission denied for database "valorbrain"` no PostgreSQL de produção. A separação física de host/rede continua sendo o débito principal da Fase 4.
- O job de compressão deltax foi movido para peer authentication e executou com sucesso; o KG drift detector passou a autenticar por peer e o backfill idempotente de 36 triplos do tenant principal zerou o alarme (`Drift sample: 0/30`). O backfill foi estendido a todos os 19 tenants: 915 triplos faltantes foram gravados, sem duplicação.

### Fase 6 — Jira

- Não alterar credenciais.
- Executar testes unitários do syncer.
- Fazer smoke read-only ou dry-run com a configuração existente.
- Confirmar `/search/jql`, paginação, timezone e webhook.
- Tratar as falhas históricas como baseline anterior à correção de 31/08.

### Fase 7 — pricing

- Não alterar pricing, checkout ou entitlement nesta fase.
- Manter `talk-to-us` e registrar a oferta como pendente de decisão humana.
- Só criar migração de pricing depois de decisão explícita.

## S.U.P.E.R

- **S:**_simples — uma frente: segurança/segredos e release.
- **U:** parcial — OpenBao → credential local → serviço; sem fluxo reverso de secrets para prompts/logs.
- **P:**_sim — policies e paths por ambiente antes dos adaptadores.
- **E:** parcial — systemd/OpenBao são específicos do host; CI terá adapter separado.
- **R:** sim — secret source e delivery layer devem ser substituíveis.

**Resultado:** 2 débitos técnicos documentados; prosseguir com gates e sem mudanças sem aprovação.

## Riscos e rollback

- OpenBao indisponível: manter fallback estático temporário, mas nunca silenciosamente.
- Policy errada: testar com tokens sem privilégio antes de liberar apps.
- Credential rotation: aceitar chave anterior; não remover fallback antes do smoke.
- Runner novo: não desligar runner antigo até dois workflows green.
- Correção de auth: cambios em camadas, testes de regressão e feature flag quando possível.
- Jira: rollback para último commit; não tocar em configuração do conector.

## Testes mínimos antes de cada promote

- OpenBao init/unseal/auth/policy em ambiente descartável.
- Leitura de credential por systemd e falha explícita quando ausente.
- Secrets não aparecem em `systemctl show`, `/proc`, logs ou build artifact.
- CI não consegue conectar ao banco de produção.
- JWT: token existente, token com chave anterior e token novo.
- Auth: registro, invite, token read/write, purge cross-tenant, visibility spoofing.
- SaaS RLS, RLS do Engine, webhook signature e readiness.
- Jira: syncer unitário, endpoint `/search/jql`, paginação e dry-run.
- Engine: typecheck, suíte focal, schema drift e MCP surface canary.
- SaaS: typecheck, unit, lint, build e smoke de rotas.
- Ops: typecheck, lint sem artefato rollback e HTTP gate.

## Decisões pendentes

1. Host do OpenBao: `vps-valor`, `desktop-brj0r2g-1` ou outro.
2. Máquina destino do CI: a mesma do staging ou `vps-valor`.
3. Se a política permite que o runner CI leia somente paths `ci/*` e nunca `production/*`.
