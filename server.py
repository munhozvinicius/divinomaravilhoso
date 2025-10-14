#!/usr/bin/env python3
import io
import json
import os
from datetime import date, datetime
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import parse_qs, urlparse

from PIL import Image, ImageDraw, ImageFont
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / 'public'
DATABASE_URL = os.getenv(
  'DATABASE_URL',
  'postgresql://neondb_owner:npg_EunfT2mh0Sci@ep-calm-sky-aczofamt-pooler.sa-east-1.aws.neon.tech/Divino%20?sslmode=require&channel_binding=require'
)

DB_POOL = ConnectionPool(
  conninfo=DATABASE_URL,
  min_size=1,
  max_size=6,
  kwargs={'autocommit': True, 'row_factory': dict_row}
)


def init_db() -> None:
  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS events (
          id SERIAL PRIMARY KEY,
          title TEXT NOT NULL,
          date_iso DATE NOT NULL,
          city TEXT NOT NULL,
          venue TEXT NOT NULL,
          status TEXT DEFAULT 'confirmado',
          description TEXT,
          tickets_link TEXT,
          instagram_url TEXT
        );
        '''
      )
      cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS products (
          id SERIAL PRIMARY KEY,
          name TEXT NOT NULL,
          slug TEXT UNIQUE,
          description TEXT,
          price_cents INTEGER NOT NULL,
          category TEXT,
          is_new BOOLEAN DEFAULT FALSE,
          inventory INTEGER DEFAULT 0
        );
        '''
      )
      cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS orders (
          id SERIAL PRIMARY KEY,
          customer_name TEXT NOT NULL,
          customer_email TEXT NOT NULL,
          customer_phone TEXT,
          customer_address TEXT,
          payment_method TEXT,
          total_cents INTEGER NOT NULL,
          items_json JSONB NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        '''
      )
      cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS newsletter_subscribers (
          id SERIAL PRIMARY KEY,
          email TEXT UNIQUE NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        '''
      )
      cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS social_links (
          id SERIAL PRIMARY KEY,
          label TEXT NOT NULL,
          url TEXT NOT NULL,
          platform TEXT
        );
        '''
      )
      cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS setlist_votes (
          id SERIAL PRIMARY KEY,
          track_name TEXT NOT NULL,
          voter_name TEXT,
          voter_contact TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        '''
      )
      cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS setlist_comments (
          id SERIAL PRIMARY KEY,
          contributor_name TEXT,
          idea TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        '''
      )
  seed_data()


def seed_data() -> None:
  events = [
    (
      'BelzeBeer',
      '2024-10-12',
      'São Paulo · SP',
      'BelzeBeer',
      'confirmado',
      'Estreia da turnê com repertório dançante e jam session após o show.',
      None,
      'https://www.instagram.com/belzebeer/'
    ),
    (
      'La Cancha',
      '2024-10-24',
      'São Paulo · SP',
      'La Cancha',
      'confirmado',
      'Noite latina com grooves tropicais, convidado especial e pista até tarde.',
      None,
      'https://www.instagram.com/lacanchafc/'
    ),
    (
      'São Jorge Bar de Reza',
      '2024-10-26',
      'Santo André · SP',
      'São Jorge Bar de Reza',
      'confirmado',
      'Celebração de sábado com visual psicodélico e coro coletivo nos clássicos.',
      None,
      'https://www.instagram.com/saojorgebardereza/'
    ),
    (
      'Evento Privado',
      '2024-11-21',
      'Local reservado',
      'Evento Corporativo',
      'evento privado',
      'Apresentação exclusiva para convidados com repertório personalizado.',
      None,
      None
    )
  ]

  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      cur.execute('DELETE FROM events;')
      cur.executemany(
        '''
        INSERT INTO events (title, date_iso, city, venue, status, description, tickets_link, instagram_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''',
        events
      )

      cur.execute('SELECT COUNT(*) AS total FROM products;')
      if cur.fetchone()['total'] == 0:
        products = [
          (
            'Boné Divino Maravilhoso',
            'bone-divino',
            'Boné aba curva, ajuste traseiro e arte bordada inspirada nos painéis tropicalistas.',
            12990,
            'Bonés',
            True,
            120
          ),
          (
            'Camiseta Manifesto',
            'camiseta-manifesto',
            'Malha premium 100% algodão com estampa frente e verso do manifesto tropical urbano.',
            15990,
            'Camisetas',
            True,
            200
          ),
          (
            'Adesivos Psicodélicos',
            'adesivos-psicodelicos',
            'Kit com 8 adesivos vinílicos resistentes à água com arte exclusiva da turnê.',
            3990,
            'Adesivos',
            False,
            500
          ),
          (
            'Bandeira Palco Livre',
            'bandeira-palco-livre',
            'Bandeira tecido oxford 1,5m × 1m para levantar em festivais e manifestações.',
            8990,
            'Bandeiras',
            False,
            80
          )
        ]
        cur.executemany(
          '''
          INSERT INTO products (name, slug, description, price_cents, category, is_new, inventory)
          VALUES (%s, %s, %s, %s, %s, %s, %s)
          ''',
          products
        )

      cur.execute('SELECT COUNT(*) AS total FROM social_links;')
      if cur.fetchone()['total'] == 0:
        links = [
          ('Instagram', 'https://www.instagram.com/divinomaravilhosobr', 'instagram'),
          ('YouTube', 'https://www.youtube.com/@divinomaravilhoso', 'youtube'),
          ('Spotify', 'https://open.spotify.com/playlist/4NCPXGyXVz6UM3QVXjFQn3?si=yr7rOCeTQvujWdmVFJQ38A', 'spotify'),
          ('Contato por e-mail', 'mailto:munhoz.vinicius@gmail.com', 'email')
        ]
        cur.executemany(
          'INSERT INTO social_links (label, url, platform) VALUES (%s, %s, %s);',
          links
        )


def format_event(row: Dict[str, Any]) -> Dict[str, Any]:
  raw_date = row['date_iso']
  if isinstance(raw_date, datetime):
    date_obj = raw_date
  elif isinstance(raw_date, date):
    date_obj = datetime.combine(raw_date, datetime.min.time())
  else:
    date_obj = datetime.fromisoformat(str(raw_date))
  formatted = dict(row)
  formatted['date_iso'] = date_obj.date().isoformat()
  formatted['date_label'] = date_obj.strftime('%d/%m/%Y')
  formatted['instagram_url'] = row.get('instagram_url')
  return formatted


def format_product(row: Dict[str, Any]) -> Dict[str, Any]:
  formatted = dict(row)
  formatted['price'] = row['price_cents'] / 100
  formatted['is_new'] = bool(row['is_new'])
  return formatted


def get_events() -> List[Dict[str, Any]]:
  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      cur.execute('SELECT * FROM events ORDER BY date_iso ASC;')
      rows = cur.fetchall()
  return [format_event(row) for row in rows]


def get_products() -> List[Dict[str, Any]]:
  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      cur.execute('SELECT * FROM products ORDER BY is_new DESC, name ASC;')
      rows = cur.fetchall()
  return [format_product(row) for row in rows]


def get_social_links() -> List[Dict[str, Any]]:
  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      cur.execute('SELECT label, url, platform FROM social_links ORDER BY id ASC;')
      rows = cur.fetchall()
  return rows


def get_top_tracks() -> List[Dict[str, Any]]:
  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      cur.execute(
        '''
        SELECT track_name, COUNT(*) AS votos, MAX(created_at) AS last_vote
        FROM setlist_votes
        GROUP BY track_name
        ORDER BY votos DESC, last_vote DESC
        LIMIT 10;
        '''
      )
      rows = cur.fetchall()
  return rows


def get_recent_comments(limit: int = 20) -> List[Dict[str, Any]]:
  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      cur.execute(
        '''
        SELECT contributor_name, idea, created_at
        FROM setlist_comments
        ORDER BY created_at DESC
        LIMIT %s;
        ''',
        (limit,)
      )
      rows = cur.fetchall()
  return rows


def calculate_order_total(items: Iterable[Dict[str, Any]]) -> Tuple[int, List[Dict[str, Any]]]:
  validated_items: List[Dict[str, Any]] = []
  total_cents = 0
  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      for item in items:
        product_id = item.get('id')
        try:
          quantity = int(item.get('quantity', 0))
        except (TypeError, ValueError):
          quantity = 0
        if quantity <= 0:
          continue
        cur.execute('SELECT id, name, price_cents FROM products WHERE id = %s;', (product_id,))
        product = cur.fetchone()
        if not product:
          continue
        subtotal = product['price_cents'] * quantity
        total_cents += subtotal
        validated_items.append({
          'id': product['id'],
          'name': product['name'],
          'price_cents': product['price_cents'],
          'quantity': quantity,
          'subtotal_cents': subtotal
        })
  return total_cents, validated_items


def insert_vote(track_name: str, voter_name: str | None, voter_contact: str | None) -> None:
  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      cur.execute(
        'INSERT INTO setlist_votes (track_name, voter_name, voter_contact) VALUES (%s, %s, %s);',
        (track_name.strip(), voter_name, voter_contact)
      )


def insert_comment(contributor_name: str | None, idea: str) -> None:
  with DB_POOL.connection() as conn:
    with conn.cursor() as cur:
      cur.execute(
        'INSERT INTO setlist_comments (contributor_name, idea) VALUES (%s, %s);',
        (contributor_name, idea)
      )


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
  daemon_threads = True


def load_font(size: int) -> ImageFont.ImageFont:
  font_paths = [
    PUBLIC_DIR / 'assets' / 'fonts' / 'SpaceGrotesk-Bold.ttf',
    PUBLIC_DIR / 'assets' / 'fonts' / 'Manrope-Bold.ttf'
  ]
  for path in font_paths:
    if path.exists():
      try:
        return ImageFont.truetype(str(path), size)
      except OSError:
        continue
  return ImageFont.load_default()


def generate_story_card(event: Dict[str, Any]) -> bytes:
  width, height = 1080, 1920
  base = Image.new('RGBA', (width, height), '#040404')
  overlay = Image.new('RGBA', (width, height))
  overlay_draw = ImageDraw.Draw(overlay)

  neon_colors = [
    (255, 51, 153, 220),
    (64, 224, 208, 200),
    (255, 255, 255, 160)
  ]

  for idx, color in enumerate(neon_colors):
    overlay_draw.ellipse(
      (
        -200 + idx * 180,
        200 + idx * 120,
        width + 200 - idx * 120,
        height - 200 + idx * 90
      ),
      fill=color
    )

  blended = Image.alpha_composite(base, overlay)
  draw = ImageDraw.Draw(blended)

  title_font = load_font(88)
  label_font = load_font(48)
  body_font = load_font(42)

  draw.text((60, 120), 'Agremiação Musical', font=label_font, fill='#f7f8f9')
  draw.text((60, 210), 'DIVINO MARAVILHOSO', font=title_font, fill='#00ffd1')

  date_obj = datetime.fromisoformat(event['date_iso'])
  date_str = date_obj.strftime('%d %b %Y').upper()
  weekday = date_obj.strftime('%A').capitalize()

  draw.text((60, 400), f"{weekday} · {date_str}", font=label_font, fill='#ffffff')
  draw.text((60, 480), event['title'], font=title_font, fill='#ff36a3')
  draw.text((60, 580), event['venue'], font=body_font, fill='#e9fffd')
  draw.text((60, 640), event['city'], font=body_font, fill='#e9fffd')

  draw.rectangle((60, 780, width - 60, 960), outline='#ffffff', width=6)
  draw.text((90, 810), 'Confirme sua presença e marque @divinomaravilhosobr', font=body_font, fill='#ffffff')

  buffer = io.BytesIO()
  blended.convert('RGB').save(buffer, format='PNG')
  return buffer.getvalue()


class DivinoHandler(SimpleHTTPRequestHandler):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

  def _set_json_headers(self, status: HTTPStatus = HTTPStatus.OK) -> None:
    self.send_response(status)
    self.send_header('Content-Type', 'application/json; charset=utf-8')
    self.end_headers()

  def do_GET(self) -> None:
    if self.path.startswith('/api/'):
      self.handle_api_get()
    else:
      super().do_GET()

  def do_POST(self) -> None:
    if self.path == '/api/orders':
      self.handle_create_order()
    elif self.path == '/api/newsletter':
      self.handle_newsletter_signup()
    elif self.path == '/api/setlist/vote':
      self.handle_vote()
    elif self.path == '/api/setlist/comment':
      self.handle_comment()
    else:
      self.send_error(HTTPStatus.NOT_FOUND, 'Endpoint não encontrado')

  def handle_api_get(self) -> None:
    parsed = urlparse(self.path)
    path_parts = parsed.path.strip('/').split('/')

    if parsed.path == '/api/events':
      events = get_events()
      self._set_json_headers()
      self.wfile.write(json.dumps(events).encode('utf-8'))
      return

    if parsed.path == '/api/products':
      products = get_products()
      self._set_json_headers()
      self.wfile.write(json.dumps(products).encode('utf-8'))
      return

    if parsed.path == '/api/social':
      links = get_social_links()
      self._set_json_headers()
      self.wfile.write(json.dumps(links).encode('utf-8'))
      return

    if parsed.path == '/api/setlist/top':
      top_tracks = get_top_tracks()
      self._set_json_headers()
      self.wfile.write(json.dumps(top_tracks).encode('utf-8'))
      return

    if parsed.path == '/api/setlist/comments':
      query = parse_qs(parsed.query)
      limit = int(query.get('limit', ['20'])[0])
      comments = get_recent_comments(limit=limit)
      self._set_json_headers()
      self.wfile.write(json.dumps(comments).encode('utf-8'))
      return

    if len(path_parts) == 4 and path_parts[0] == 'api' and path_parts[1] == 'events' and path_parts[3] == 'story-card.png':
      try:
        event_id = int(path_parts[2])
      except ValueError:
        self.send_error(HTTPStatus.BAD_REQUEST, 'ID inválido')
        return
      with DB_POOL.connection() as conn:
        with conn.cursor() as cur:
          cur.execute('SELECT * FROM events WHERE id = %s;', (event_id,))
          event = cur.fetchone()
      if not event:
        self.send_error(HTTPStatus.NOT_FOUND, 'Evento não encontrado')
        return
      payload = generate_story_card(format_event(event))
      self.send_response(HTTPStatus.OK)
      self.send_header('Content-Type', 'image/png')
      self.send_header('Content-Length', str(len(payload)))
      self.end_headers()
      self.wfile.write(payload)
      return

    self.send_error(HTTPStatus.NOT_FOUND, 'Endpoint não encontrado')

  def handle_create_order(self) -> None:
    length = int(self.headers.get('Content-Length', '0'))
    try:
      payload = json.loads(self.rfile.read(length) or '{}')
    except json.JSONDecodeError:
      self.send_error(HTTPStatus.BAD_REQUEST, 'JSON inválido')
      return

    customer = payload.get('customer') or {}
    items = payload.get('items') or []

    if not customer.get('name') or not customer.get('email'):
      self.send_error(HTTPStatus.BAD_REQUEST, 'Informações do cliente incompletas')
      return

    total_cents, validated_items = calculate_order_total(items)
    if total_cents == 0 or not validated_items:
      self.send_error(HTTPStatus.BAD_REQUEST, 'Nenhum item válido no pedido')
      return

    with DB_POOL.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(
          '''
          INSERT INTO orders (customer_name, customer_email, customer_phone, customer_address, payment_method, total_cents, items_json)
          VALUES (%s, %s, %s, %s, %s, %s, %s)
          RETURNING id;
          ''',
          (
            customer.get('name'),
            customer.get('email'),
            customer.get('phone'),
            customer.get('address'),
            customer.get('payment_method'),
            total_cents,
            json.dumps(validated_items)
          )
        )
        order_id = cur.fetchone()['id']

    self._set_json_headers(HTTPStatus.CREATED)
    self.wfile.write(json.dumps({'order_id': order_id, 'total': total_cents / 100}).encode('utf-8'))

  def handle_newsletter_signup(self) -> None:
    length = int(self.headers.get('Content-Length', '0'))
    try:
      payload = json.loads(self.rfile.read(length) or '{}')
    except json.JSONDecodeError:
      self.send_error(HTTPStatus.BAD_REQUEST, 'JSON inválido')
      return

    email = (payload.get('email') or '').strip()
    if not email:
      self.send_error(HTTPStatus.BAD_REQUEST, 'E-mail é obrigatório')
      return

    with DB_POOL.connection() as conn:
      with conn.cursor() as cur:
        cur.execute(
          'INSERT INTO newsletter_subscribers (email) VALUES (%s) ON CONFLICT (email) DO NOTHING;',
          (email,)
        )

    self._set_json_headers(HTTPStatus.CREATED)
    self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))

  def handle_vote(self) -> None:
    length = int(self.headers.get('Content-Length', '0'))
    try:
      payload = json.loads(self.rfile.read(length) or '{}')
    except json.JSONDecodeError:
      self.send_error(HTTPStatus.BAD_REQUEST, 'JSON inválido')
      return

    track_name = (payload.get('track_name') or '').strip()
    if not track_name:
      self.send_error(HTTPStatus.BAD_REQUEST, 'Escolha uma música')
      return

    voter_name = (payload.get('voter_name') or '').strip() or None
    voter_contact = (payload.get('voter_contact') or '').strip() or None

    insert_vote(track_name, voter_name, voter_contact)

    self._set_json_headers(HTTPStatus.CREATED)
    self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))

  def handle_comment(self) -> None:
    length = int(self.headers.get('Content-Length', '0'))
    try:
      payload = json.loads(self.rfile.read(length) or '{}')
    except json.JSONDecodeError:
      self.send_error(HTTPStatus.BAD_REQUEST, 'JSON inválido')
      return

    idea = (payload.get('idea') or '').strip()
    if not idea:
      self.send_error(HTTPStatus.BAD_REQUEST, 'Conte sua ideia de música')
      return

    contributor_name = (payload.get('contributor_name') or '').strip() or None

    insert_comment(contributor_name, idea)

    self._set_json_headers(HTTPStatus.CREATED)
    self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))


def run_server(port: int = 8000) -> None:
  server_address = ('0.0.0.0', port)
  httpd = ThreadingHTTPServer(server_address, DivinoHandler)
  print(f'🔥 Servidor Divino Maravilhoso ativo em http://localhost:{port}')
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    print('\nEncerrando servidor...')
  finally:
    httpd.server_close()

init_db()


if __name__ == '__main__':
  run_server()
