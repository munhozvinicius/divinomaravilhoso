# Divino Maravilhoso — Plataforma oficial

Experiência web premium para a banda Divino Maravilhoso com visual neon translúcido, agenda interativa, votação de setlist,
playlist Spotify e base preparada para loja de merch.

## Requisitos

- Python 3.10+
- Dependências Python:
  - [psycopg](https://www.psycopg.org/)
  - [psycopg-pool](https://www.psycopg.org/psycopg3/docs/api/pool.html)
  - [Pillow](https://pillow.readthedocs.io/)

Instale-as rapidamente com:

```bash
python3 -m pip install psycopg[binary] psycopg-pool pillow
```

## Banco de dados

O projeto utiliza PostgreSQL hospedado na Neon com a seguinte URL padrão:

```
postgresql://neondb_owner:npg_EunfT2mh0Sci@ep-calm-sky-aczofamt-pooler.sa-east-1.aws.neon.tech/Divino%20?sslmode=require&channel_binding=require
```

Defina `DATABASE_URL` caso queira apontar para outra instância.

Na inicialização o servidor garante as tabelas:

- `events`, `products`, `orders`, `newsletter_subscribers`, `social_links`
- `setlist_tracks`, `setlist_votes` e `setlist_comments` para votação e mural de sugestões

Os eventos são semeados com as datas fornecidas, preservando Instagram dos bares e status de cada show.

## Executando o servidor

```bash
python3 server.py
```

O servidor sobe em `http://localhost:8000`, servindo o front-end (pasta `public/`) e a API.

### Endpoints principais

- `GET /api/events` — agenda completa com links de Instagram
- `GET /api/events/:id/story-card.png` — gera arte em PNG estilo lambe-lambe para stories
- `GET /api/setlist/tracks` — catálogo oficial de faixas liberadas para voto
- `GET /api/setlist/top` — Top 10 músicas mais votadas (combina votos com catálogo oficial)
- `GET /api/setlist/comments` — últimas sugestões neon
- `POST /api/setlist/vote` — registra voto na música favorita
- `POST /api/setlist/comment` — envia sugestão de faixa/mashup
- `POST /api/newsletter` — lista de espera da loja
- `POST /api/orders` — fluxo de pedidos para futuros drops de merch

### Configurando o front-end em produção

- O script `public/scripts/runtime.js` permite apontar o front-end para um backend remoto setando `apiBase`:
  - defina `data-api-base="https://seu-backend"` no elemento `<body>` ou
  - adicione `?apiBase=https://seu-backend` na URL (valor é salvo em `localStorage`).
- Caso a API esteja offline, a agenda e a votação utilizam dados demonstrativos e exibem um aviso translúcido informando que o backend precisa ser habilitado.
- Assim que o servidor estiver respondendo, os avisos desaparecem automaticamente e os botões de lambe-lambe passam a apontar para o endpoint real.

## Front-end

- Tema dark premium com cartões translúcidos, gradientes rosa/verde/ciano inspirados no Spotify
- Hero destacando nome da banda, formação e manifesto ao vivo
- Seção “Sobre” com cards baseados no conteúdo fornecido pelo cliente
- Agenda com botões para Instagram do local, ingressos e download do cartaz lambe-lambe
- Área participativa com votação em tempo real da setlist, mural de comentários e Top 10 atualizado
- Playlist oficial com CTA de pré-save, Instagram destacado e contato direto via e-mail/WhatsApp

Tudo foi construído pensando em responsividade e expansão futura da loja oficial.

## Verificando a integração com o Neon

Use o script `tools/neon_healthcheck.py` para garantir que o banco gerenciado
na Neon está acessível e semeado com os dados iniciais que o site espera.

1. Crie/ative um ambiente virtual.
2. Instale as dependências necessárias (`psycopg[binary]`, `psycopg-pool`,
   `pillow`).
3. Execute `python3 tools/neon_healthcheck.py`.

Se alguma dependência não puder ser instalada (por exemplo, bloqueio de acesso
ao PyPI retornando *403 Forbidden*), o script informará o erro e a ação
necessária: liberar o download dos pacotes ou fornecer os wheels manualmente
para completar o teste de integração.
