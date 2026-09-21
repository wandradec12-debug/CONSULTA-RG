# CONSULTA RG — Estoque WYMS

Sistema web para consulta de RG e localização de estoque a partir da exportação do WYMS.

## O que esta versão contém

- Login administrativo.
- Importação diária de Excel/CSV.
- Consulta de RG.
- Leitura de QR Code pela câmera do celular.
- Retorno da posição (`LOCALIZAÇÃO`) e principais dados do item.
- Histórico das importações.
- Registro das consultas.
- Endpoint `/health` para monitoramento do Render.
- PostgreSQL para produção.
- Configuração segura de cookie via `COOKIE_SECURE`.

## Publicação no Render

No Web Service:

- Runtime: **Docker**
- Branch: `main`
- Dockerfile Path: `./Dockerfile`
- Root Directory: vazio
- Health Check Path: `/health`

Variáveis de ambiente:

- `DATABASE_URL` = Internal Database URL do PostgreSQL do Render.
- `SECRET_KEY` = gerar pelo botão **Generate**.
- `ADMIN_USER` = usuário administrativo.
- `ADMIN_PASSWORD` = senha definida por você.
- `COOKIE_SECURE` = `true`.

Não coloque senhas, tokens ou exportações reais do WYMS no GitHub.

## Uso

1. Acesse o sistema.
2. Faça login.
3. Importe a exportação WYMS.
4. Consulte o RG digitando o código ou usando a câmera.
5. O sistema apresenta a posição cadastrada no WYMS.

A exportação WYMS deve conter, no mínimo, as colunas `RG` e `LOCALIZAÇÃO`.

## Importante

O arquivo operacional WYMS não faz parte deste pacote. Ele deve ser enviado pela tela de importação do sistema.

## Próxima evolução

- QR Code nas posições físicas.
- Validação RG x posição.
- Registro de divergência.
- Dashboard de acuracidade.
- Trilhas de auditoria.
- Versionamento das bases importadas.
- Usuários e perfis de acesso.
