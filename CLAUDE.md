# CLAUDE.md

Orientações para assistentes de código (Claude / LLMs) atuarem com segurança e alinhamento no projeto.

## 1. Visão Geral do Sistema
Backend (FastAPI) para:
- Gestão de usuários, atendentes (caregivers), times e funções.
- Exposição de APIs REST consumidas por outros sistemas (principalmente o `go-realtime-event-system`).
- Persistência principal: PostgreSQL (SQLAlchemy ORM). (MongoDB opcional se existir camada NoSQL).
- Rastreabilidade: created_by, updated_by, user_ip, timestamps.
- Meta: 100% de cobertura de testes (linhas e branches).
- Arquitetura orientada a SOLID: separação clara entre Models, Schemas, CRUD, Services e Routers.

## 2. Objetivos Principais
1. Servir como fonte de verdade de identidade e perfil operacional.
2. Oferecer contratos REST estáveis para consumidores externos.
3. Facilitar evolução incremental com mínima quebra.
4. Centralizar regras de negócio em Services desacoplados.

## 3. Estrutura de Pastas (Resumo Funcional)

Raiz:
- `backendeldery/` código principal da aplicação.
- `go-realtime-event-system/` (link simbólico SOMENTE LEITURA; consumidor das APIs).
- `alembic/` migrações SQL.
- `backendeldery/tests/` testes (pytest + MagicMock/AsyncMock).
- `scripts/` utilidades / automação.
- `modelos/` diagramas / documentação extra (quando presente).
- Infra: `docker-compose.yml`, `Dockerfile`, `alembic.ini`, `init.sql`, `pyproject.toml`, `.env.example`.

Dentro de `backendeldery/`:
- `main.py` montagem FastAPI / inclusão de routers.
- `config.py` leitura de variáveis de ambiente.
- `database.py` engine / sessão (async ou sync).
- `models.py` modelos ORM (User, Attendant, Team, Function, Specialty ...).
- `schemas.py` Pydantic (Create / Update / Response).
- `crud/` camada de persistência isolada (users, attendant, team, function, base).
- `services/` orquestração e lógica composta (ex: `attendantUpdateService.py`).
- `routers/` endpoints HTTP (por domínio).
- `validators/` validações específicas (ex: `cpf_validator.py`).
- `utils.py`, `process_audit_logs.py` utilidades e jobs (se aplicável).

Testes:
- Exemplos: `test_attendant_Update_Service.py` (atualização e orquestração).
- Estratégia: mocks focados na sessão / dependências externas.

## 4. Integração Externa: go-realtime-event-system
- Natureza: CLIENTE das APIs do backend.
- O link simbólico existe para inspecionar padrões de consumo (rotas, payloads, status codes).
- Proibido: import direto de módulos desse sistema no backend.
- Toda integração acontece via HTTP (contrato OpenAPI/JSON).
- Antes de mudar um contrato, inspecionar o consumo (ver seção 21).

## 5. Domínio (Models Principais)
- User: identidade base (credenciais / dados de contato).
- Attendant: extensão do usuário com atributos profissionais (formação, experiência, endereço).
- Team: agrupamento lógico.
- Function: papel/cargo (role).
- Specialty (quando implementado): categorização profissional.
- Auditoria padronizada em todas as entidades mutáveis.

## 6. Schemas (Pydantic)
- Create* / Update* / *Response separados para cada entidade.
- Não expor hash de senha ou campos sensíveis.
- Validadores especializados (CPF, email, enums).
- Evoluções: adicionar campos é compatível; remover exige versão.

## 7. Camada CRUD
- Responsabilidade: operações diretas de banco (create/get/list/update/delete).
- Evitar SQL bruto; preferir construções ORM.
- Erros de integridade tratados e convertidos em exceções de domínio ou retornos neutros para o Service decidir.
- Para novos CRUDs: herdar de base (se existir) preservando padrões (session injetada, commits controlados).

## 8. Services
- Agregam múltiplos CRUDs.
- Implementam regras compostas (ex: sincronizar teams/functions/specialties de Attendant).
- Ponto ideal para:
  - Emissão futura de eventos.
  - Validações cross-entity.
  - Versionamento de comportamento.

## 9. Routers
- Endpoints organizados por domínio.
- Tipagem de entrada/saída via Schemas.
- Convertem exceções internas em HTTPException padronizada.
- NÃO conter lógica de negócio pesada.

## 10. Fluxo Exemplo (Atualização de Atendente)
1. Router recebe payload AttendantUpdate.
2. Service recupera entidade (404 se não existir).
3. Atualiza campos primitivos (exceto relacionamentos).
4. Manipula relacionamentos em métodos dedicados (_add_team_associations, _set_function_association, etc).
5. Persiste e retorna schema de resposta.

## 11. Validações
- CPF: `validators/cpf_validator.py`.
- Email / formatos: Pydantic.
- Enums: validar strings normalizadas.
- Consistência: preferir lançar exceções de domínio convertidas em HTTP 4xx.

## 12. Padrões SOLID
- SRP: CRUD ≠ Service ≠ Router.
- OCP: Extensões via novas classes, sem alterar código estável.
- LSP: Subtipos (ex: Attendant derivado de base User logicamente) mantêm contratos.
- ISP: Interfaces enxutas (evitar acoplamento de métodos raramente usados).
- DIP: Services dependem de abstrações (instâncias CRUD injetadas).

## 13. Convenções Gerais
- Auditoria: created_by, updated_by, user_ip sempre atualizados.
- Logging (se presente): sem prints; evitar log de dados sensíveis.
- Nomes claros, evitar abreviações desnecessárias.
- Datas em UTC ISO 8601.

## 14. Erros / HTTP
- 404: entidade não encontrada.
- 409: conflitos (unique violation) se aplicável.
- 422: validação Pydantic.
- Estrutura de erro estável: {"detail": "mensagem"}.

## 15. Segurança / Sensibilidade
- Não logar CPF completo em nível debug/info.
- `.env` não versionado.
- Sanitizar saída de dados confidenciais.
- Restringir campos de autenticação a escopos adequados.

## 16. Estratégia de Testes
- Pytest + MagicMock / AsyncMock.
- Níveis:
  - Unit (CRUD isolado, Services com mocks).
  - Contract/API (respostas e status codes).
  - Branch coverage (erros e caminhos alternativos).
- Meta: 100% cobertura (usar relatório para fechar lacunas).
- Nome: `test_<contexto>_<cenário>`.

## 17. Estratégia de Mock
- Banco: AsyncMock para sessão (execute / commit / refresh).
- Preferir objetos reais simples a mocks para entidades (ex: instanciar Attendant).
- Relacionamentos Many-to-Many: validar tamanho/IDs manipulado.

## 18. Qualidade
- Lint: ruff.
- (Opcional futuro) mypy para tipagem estática.
- Refactors pequenos + testes imediatos.
- Cada mudança de schema → avaliar migração (Alembic).

## 19. Observações sobre o Link Simbólico
- Uso exclusivo: leitura/inspeção de consumo.
- Nunca copiar código source para dentro do backend.
- Documentar diferenças ao alterar contratos.

## 20. Diretrizes para Geração Automática (LLM)
FAZER:
- Reusar estruturas existentes.
- Manter auditoria e padrões de nomenclatura.
- Gerar testes para novas lógicas.
NÃO FAZER:
- Remover campos/rotas sem análise de impacto.
- Introduzir dependências não justificadas.
- Duplicar lógica de Services em Routers ou CRUDs.

## 21. Mudanças de Contrato de API (Processo Rigoroso)
Quando solicitado alterar rota, payload, query params, status code ou formato de resposta:

1. Classificação:
   - Adição (compatível)
   - Modificação (potencialmente breaking)
   - Remoção (breaking)
   - Renomeação (breaking)

2. Inspeção no consumidor (`go-realtime-event-system`):
   - grep -R '"/attendants"' go-realtime-event-system
   - grep -R '"attendant_id"' go-realtime-event-system
   - Procurar:
     - Caminhos: /users, /attendants/{id}, /teams...
     - Métodos HTTP: GET/POST/PUT/PATCH/DELETE
     - Uso de campos JSON (dot notation, destructuring, obj["campo"])
     - Códigos de status esperados (ex: if resp.status == 201)

3. Mapear Dependências:
   - Listar arquivos e trechos onde a rota/campo aparece.
   - Identificar suposições fortes (ex: campo obrigatório, enum exato).

4. Gerar Diff Planejado:
   - Antes: estrutura atual (listar chaves).
   - Depois: nova estrutura.
   - Sinalizar: REMOVIDO, TIPO ALTERADO, ENUM REDUZIDO.

5. Definir Estratégia:
   - Compatível: implementar diretamente.
   - Breaking: versionar (/v2) ou campo novo + deprecated para campo antigo.

6. Testes de Contrato:
   - Ajustar/Adicionar testes em backendeldery/tests/ validando:
     - Estrutura JSON.
     - Códigos de status.
     - Campos obrigatórios / opcionais.

7. Checklist (ver seção 24):
   - Impacto revisado
   - Testes atualizados
   - OpenAPI/documentação atualizada
   - Plano de deprecação se necessário

## 22. Politica de Deprecação
- Novos campos: adicionar sem remover antigos; marcar (documentar) como deprecated.
- Remoção: apenas após confirmação (grep sem usos) + versão nova da rota ou ciclo de release definido.
- Rotas renomeadas: manter rota antiga retornando header Warning ou campo meta.deprecated.

## 23. Modelo de Resposta da IA para Pedido de Alteração
Exemplo:
Solicitação: Remover campo 'formacao' de AttendantResponse.
Análise:
- Campo usado? grep -R '"formacao"' go-realtime-event-system → encontrado em X arquivos.
- Classificação: breaking.
Plano:
- Manter campo em /v1 (deprecated).
- Criar /v2/attendants sem 'formacao'.
- Adicionar aviso no README.
Ações:
- Atualizar schemas (v2).
- Tests: adicionar test_attendant_response_v2_sem_formacao.
- Atualizar OpenAPI.
Risco: médio.
Confirmação solicitada antes de aplicar.

## 24. Checklist Geral para PR
- [ ] Alteração de contrato classificada (adição / breaking)
- [ ] grep no go-realtime-event-system sem usos órfãos (ou plano de migração)
- [ ] Testes novos/atualizados (100% cobertura preservada)
- [ ] Lint ok
- [ ] Migração Alembic (se schema DB mudou)
- [ ] Documentação (README / OpenAPI / CLAUDE.md) atualizada
- [ ] Estratégia de deprecação (se necessário)
- [ ] Sem import direto de código externo
- [ ] Logs não expõem dados sensíveis

## 25. Exemplos de Comandos Úteis (Mac)
- Buscar rota: grep -R '"/attendants"' go-realtime-event-system
- Buscar campo JSON: grep -R '"nivel_experiencia"' go-realtime-event-system
- Contar ocorrências: grep -R '"function_names"' go-realtime-event-system | wc -l

## 26. Evoluções Futuras Sugeridas
- Script diff OpenAPI automatizado.
- Testes de contrato consumidores (mock client) internos.
- Emissão de eventos (webhook ou fila) encapsulados em Services.
- Auditoria completa (histórico versionado de mudanças por entidade).

## 27. Regras para Modificação de Arquivos Críticos
Antes de alterar:
- models.py
- schemas.py
- CRUDs (users, attendant, team, function)
- services/*
Confirmar impacto: banco (migração?), APIs públicas, testes dependentes.

## 28. Diretrizes de Performance
- Paginação para list endpoints quando volume crescer.
- Indexes adequados (Alembic) para campos usados em filtros.
- Evitar N+1: usar selectin/joinedload quando necessário.

## 29. Observação sobre Teste Exemplo (AttendantUpdateService)
Arquivo: backendeldery/tests/test_attendant_Update_Service.py
Coberturas:
- Sucesso update_user
- Sucesso get_attendant
- Not found get_attendant
- Atualização de campos primitivos Attendant
- Ignorar campos de relacionamento em update direto
Expandir:
- Testar caminhos de erro de validação
- Testar atualização parcial (sem todos os campos)
- Testar manipulação de relacionamentos (teams/functions/specialties) via métodos específicos.

## 30. Ações que a IA DEVE Tomar Perante Pedidos Ambíguos
- Solicitar clarificação de qual rota/campo.
- Propor plano incremental (primeiro adicionar, depois deprecar).
- Sugerir testes que evidenciem compatibilidade.

## 31. Ações que a IA NÃO DEVE Tomar
- Deletar campos sem inspeção prévia.
- Introduzir versão nova sem necessidade.
- Mesclar múltiplas mudanças de contrato em um único PR sem justificativa.