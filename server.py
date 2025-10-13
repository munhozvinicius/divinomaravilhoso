#!/usr/bin/env python3
import json
import sqlite3
from datetime import datetime
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any, Dict, Iterable, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / 'public'
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DATA_DIR / 'divino.db'


def dict_factory(cursor: sqlite3.Cursor, row: Tuple[Any, ...]) -> Dict[str, Any]:
  return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def init_db() -> sqlite3.Connection:
  DATA_DIR.mkdir(exist_ok=True)
  conn = sqlite3.connect(DB_PATH, check_same_thread=False)
  conn.row_factory = dict_factory
  with conn:
    conn.executescript(
      """
      CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        date_iso TEXT NOT NULL,
        city TEXT NOT NULL,
        venue TEXT NOT NULL,
        status TEXT DEFAULT 'confirmado',
        description TEXT,
        tickets_link TEXT
      );

      CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE,
        description TEXT,
        price_cents INTEGER NOT NULL,
        category TEXT,
        is_new INTEGER DEFAULT 0,
        inventory INTEGER DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        customer_phone TEXT,
        customer_address TEXT,
        payment_method TEXT,
        total_cents INTEGER NOT NULL,
        items_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS newsletter_subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS social_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL,
        url TEXT NOT NULL,
        platform TEXT
      );
      """
    )
  seed_data(conn)
  return conn


def seed_data(conn: sqlite3.Connection) -> None:
  def table_has_rows(table: str) -> bool:
    cursor = conn.execute(f'SELECT COUNT(*) as total FROM {table}')
    return cursor.fetchone()['total'] > 0

  if not table_has_rows('events'):
    events = [
      (
        'Divino no Centro Cultural São Paulo',
        '2024-11-09',
        'São Paulo · SP',
        'Centro Cultural São Paulo',
        'confirmado',
        'Show completo com repertório tropicalista e convidados surpresa.',
        'https://bit.ly/divino-ccsp'
      ),
      (
        'Festival Cores do Brasil',
        '2024-12-14',
        'Rio de Janeiro · RJ',
        'Marina da Glória',
        'confirmado',
        'Palco principal com projeções e participação da DJ Brisa.',
        'https://bit.ly/coresdivino'
      ),
      (
        'Virada Cultural',
        '2025-01-25',
        'Belo Horizonte · MG',
        'Praça da Estação',
        'em negociação',
        'Apresentação ao ar livre com cortejo performático.',
        None
      ),
      (
        'Noite Tropical Independente',
        '2025-02-22',
        'Curitiba · PR',
        'Usina 5',
        'confirmado',
        'Evento especial com cenário imersivo e intervenções visuais.',
        'https://bit.ly/noitetropical'
      ),
      (
        'Tour Nordeste',
        '2025-03-14',
        'Recife · PE',
        'Baile Periférico',
        'em negociação',
        'Mini turnê com workshops e oficinas de percussão.',
        None
      )
    ]
    conn.executemany(
      'INSERT INTO events (title, date_iso, city, venue, status, description, tickets_link) VALUES (?, ?, ?, ?, ?, ?, ?)',
      events
    )

  if not table_has_rows('products'):
    products = [
      (
        'Boné Divino Maravilhoso',
        'bone-divino',
        'Boné aba curva, ajuste traseiro e arte bordada inspirada nos painéis tropicalistas.',
        12990,
        'Bonés',
        1,
        120
      ),
      (
        'Camiseta Manifesto',
        'camiseta-manifesto',
        'Malha premium 100% algodão com estampa frente e verso do manifesto tropical urbano.',
        15990,
        'Camisetas',
        1,
        200
      ),
      (
        'Adesivos Psicodélicos',
        'adesivos-psicodelicos',
        'Kit com 8 adesivos vinílicos resistentes à água com arte exclusiva da turnê.',
        3990,
        'Adesivos',
        0,
        500
      ),
      (
        'Bandeira Palco Livre',
        'bandeira-palco-livre',
        'Bandeira tecido oxford 1,5m × 1m para levantar em festivais e manifestações.',
        8990,
        'Bandeiras',
        0,
        80
      )
    ]
    conn.executemany(
      'INSERT INTO products (name, slug, description, price_cents, category, is_new, inventory) VALUES (?, ?, ?, ?, ?, ?, ?)',
      products
    )

  if not table_has_rows('social_links'):
    links = [
      ('Instagram', 'https://www.instagram.com/divinomaravilhosobr', 'instagram'),
      ('YouTube', 'https://www.youtube.com/@divinomaravilhoso', 'youtube'),
      ('Spotify', 'https://open.spotify.com/artist/3tKDivino', 'spotify'),
      ('Contato por e-mail', 'mailto:contato@divinomaravilhoso.com.br', 'email')
    ]
    conn.executemany(
      'INSERT INTO social_links (label, url, platform) VALUES (?, ?, ?)',
      links
    )


def format_event(row: Dict[str, Any]) -> Dict[str, Any]:
  date_obj = datetime.fromisoformat(row['date_iso'])
  date_label = date_obj.strftime('%d/%m/%Y')
  formatted = dict(row)
  formatted['date_label'] = date_label
  return formatted


def format_product(row: Dict[str, Any]) -> Dict[str, Any]:
  formatted = dict(row)
  formatted['price'] = row['price_cents'] / 100
  formatted['is_new'] = bool(row['is_new'])
  return formatted


def get_events(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
  cursor = conn.execute('SELECT * FROM events ORDER BY date_iso ASC')
  return [format_event(row) for row in cursor.fetchall()]


def get_products(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
  cursor = conn.execute('SELECT * FROM products ORDER BY is_new DESC, name ASC')
  return [format_product(row) for row in cursor.fetchall()]


def get_social_links(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
  cursor = conn.execute('SELECT label, url, platform FROM social_links ORDER BY id ASC')
  return cursor.fetchall()


def calculate_order_total(conn: sqlite3.Connection, items: Iterable[Dict[str, Any]]) -> Tuple[int, List[Dict[str, Any]]]:
  validated_items: List[Dict[str, Any]] = []
  total_cents = 0
  for item in items:
    product_id = item.get('id')
    quantity = int(item.get('quantity', 0))
    if quantity <= 0:
      continue
    product = conn.execute('SELECT id, name, price_cents FROM products WHERE id = ?', (product_id,)).fetchone()
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


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
  daemon_threads = True


class DivinoHandler(SimpleHTTPRequestHandler):
  def __init__(self, *args, **kwargs):
    self.conn = DB_CONN
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
    else:
      self.send_error(HTTPStatus.NOT_FOUND, 'Endpoint não encontrado')

  def handle_api_get(self) -> None:
    if self.path == '/api/events':
      events = get_events(self.conn)
      self._set_json_headers()
      self.wfile.write(json.dumps(events).encode('utf-8'))
    elif self.path == '/api/products':
      products = get_products(self.conn)
      self._set_json_headers()
      self.wfile.write(json.dumps(products).encode('utf-8'))
    elif self.path == '/api/social':
      links = get_social_links(self.conn)
      self._set_json_headers()
      self.wfile.write(json.dumps(links).encode('utf-8'))
    else:
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

    total_cents, validated_items = calculate_order_total(self.conn, items)
    if total_cents == 0 or not validated_items:
      self.send_error(HTTPStatus.BAD_REQUEST, 'Nenhum item válido no pedido')
      return

    with self.conn:
      cursor = self.conn.execute(
        (
          'INSERT INTO orders '
          '(customer_name, customer_email, customer_phone, customer_address, payment_method, total_cents, items_json) '
          'VALUES (?, ?, ?, ?, ?, ?, ?)'
        ),
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
      order_id = cursor.lastrowid

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

    try:
      with self.conn:
        self.conn.execute(
          'INSERT OR IGNORE INTO newsletter_subscribers (email) VALUES (?)',
          (email,)
        )
    except sqlite3.DatabaseError:
      self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, 'Erro ao salvar e-mail')
      return

    self._set_json_headers(HTTPStatus.CREATED)
    self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))


DB_CONN = init_db()


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


if __name__ == '__main__':
  run_server()
