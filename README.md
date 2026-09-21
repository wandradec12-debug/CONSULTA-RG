# Consulta RG • Estoque — versão online

Sistema completo para:
- login de administrador;
- importação diária de Excel/CSV;
- substituição da base ativa;
- consulta de RG pelo celular;
- leitura de QR Code pela câmera;
- indicação da posição de estoque;
- histórico das importações;
- indicadores básicos;
- registro das consultas.

## 1. Testar no computador
Requisitos: Docker Desktop.

```bash
docker compose up --build
```

Abra `http://localhost:8000`.

Usuário padrão: `admin`
Senha padrão: `admin123`

**Troque a senha antes de disponibilizar na internet.**

## 2. Estrutura da planilha
O sistema reconhece automaticamente nomes próximos a:
- RG (obrigatório)
- Posição (obrigatório)
- Produto
- Lote
- Validade
- Quantidade
- Status

RG deve ser tratado como texto para preservar zeros à esquerda.

## 3. Publicação
A aplicação foi preparada em container. Pode ser publicada em um provedor de cloud que aceite Docker e PostgreSQL. Na publicação, configure:
- DATABASE_URL
- SECRET_KEY
- ADMIN_USER
- ADMIN_PASSWORD

Também é necessário HTTPS para uso confiável da câmera do celular.

## 4. Próxima evolução recomendada
Para uma operação de CD, a próxima etapa é adicionar:
1. usuários separados (Administrador / Operador);
2. QR Code também na etiqueta da posição;
3. confirmação de posição física;
4. registro de divergência RG x posição;
5. dashboard de acuracidade;
6. exportação de divergências;
7. trilha de auditoria;
8. versionamento das bases em vez de apagar a anterior;
9. integração com WMS/ERP, se disponível;
10. domínio interno e controle de acesso conforme política de TI da empresa.
