# Divino Maravilhoso - Site oficial da banda

Projeto web inspirado na estética tropical urbana do material fornecido para apresentar a banda Divino Maravilhoso, divulgar agenda, playlist e oferecer uma loja com fluxo de pedidos para merch.

## Como executar

```bash
python3 server.py
```

O servidor inicia em `http://localhost:8000` servindo os arquivos estáticos e as APIs REST que alimentam o front-end.

## Estrutura

- `public/` – Site estático (HTML, CSS e JavaScript).
- `server.py` – Servidor HTTP com API e banco de dados SQLite.
- `data/divino.db` – Banco de dados com tabelas para agenda, produtos, pedidos, newsletter e redes sociais.

## API

### `GET /api/events`
Lista todos os eventos cadastrados com título, data, cidade, local, status e links de ingresso.

### `GET /api/products`
Lista os itens de merchandise, retornando preço, categoria, estoque e se é lançamento.

### `GET /api/social`
Retorna as redes sociais oficiais da banda.

### `POST /api/orders`
Recebe um pedido da loja (`customer` + `items`) e grava no banco. Calcula total a partir dos produtos cadastrados.

### `POST /api/newsletter`
Cadastro simples de e-mail na base de newsletter.

## Banco de dados

O arquivo SQLite é criado automaticamente na primeira execução com dados iniciais de:

- Agenda com datas confirmadas e em negociação
- Catálogo de boné, camiseta, adesivos e bandeira
- Links sociais para Instagram, YouTube, Spotify e e-mail

A partir dessas tabelas é possível evoluir para um painel administrativo e integrar meios de pagamento.

## Customização visual

O layout utiliza gradientes, mosaicos e tipografia condensada para ecoar o design original. O CSS foi construído para ser responsivo e destacar as seções principais da banda.
