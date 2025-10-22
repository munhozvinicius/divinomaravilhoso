# Divino Maravilhoso — Plataforma oficial

Experiência web premium para a banda Divino Maravilhoso com visual neon translúcido, agenda interativa, votação de setlist,
playlist Spotify e base preparada para loja de merch.

## Requisitos

- Python 3.10+
- Dependências Python instaladas via `requirements.txt`:
  - [psycopg](https://www.psycopg.org/)
  - [psycopg-pool](https://www.psycopg.org/psycopg3/docs/api/pool.html)
  - [Pillow](https://pillow.readthedocs.io/)

Instale-as rapidamente com:

```bash
pip install -r requirements.txt
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

## Front-end

- Tema dark premium com cartões translúcidos, gradientes rosa/verde/ciano inspirados no Spotify
- Hero destacando nome da banda, formação e manifesto ao vivo
- Seção “Sobre” com cards baseados no conteúdo fornecido pelo cliente
- Agenda com botões para Instagram do local, ingressos e download do cartaz lambe-lambe
- Área participativa com votação em tempo real da setlist, mural de comentários e Top 10 atualizado
- Playlist oficial com CTA de pré-save, Instagram destacado e contato direto via e-mail/WhatsApp

Tudo foi construído pensando em responsividade e expansão futura da loja oficial.

## Deploy na Vercel

O projeto está configurado para deploy automático na Vercel:

1. **Conecte seu repositório GitHub à Vercel**
2. **Configure a variável de ambiente:**
   - `DATABASE_URL` com a connection string do PostgreSQL (Neon)
3. **Deploy automático:** A Vercel detectará automaticamente o `vercel.json`

### Configuração manual (via CLI):

```bash
# Instale a CLI da Vercel
npm i -g vercel

# Faça login
vercel login

# Configure o projeto
vercel

# Adicione a variável de ambiente
vercel env add DATABASE_URL

# Deploy
vercel --prod
```

### Estrutura para Vercel:
- `/api/index.py` - Serverless functions (API endpoints)
- `/public/` - Arquivos estáticos (HTML, CSS, JS, assets)
- `vercel.json` - Configuração de rotas e builds
- `requirements.txt` - Dependências Python
