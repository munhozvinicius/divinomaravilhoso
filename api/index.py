"""
Vercel serverless API for Divino Maravilhoso
"""
import os
import json
import unicodedata
from datetime import date, datetime
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, List

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# Database configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://neondb_owner:npg_EunfT2mh0Sci@ep-calm-sky-aczofamt-pooler.sa-east-1.aws.neon.tech/Divino%20?sslmode=require&channel_binding=require'
)

# Initialize connection pool
DB_POOL = None
try:
    DB_POOL = ConnectionPool(
        conninfo=DATABASE_URL,
        min_size=1,
        max_size=6,
        kwargs={'autocommit': True, 'row_factory': dict_row}
    )
except Exception as e:
    print(f"Error initializing DB pool: {e}")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize('NFKD', value or '')
    without_accents = ''.join(ch for ch in normalized if not unicodedata.combining(ch))
    cleaned = ''.join(ch if ch.isalnum() else '-' for ch in without_accents.lower())
    collapsed = '-'.join(filter(None, cleaned.split('-')))
    return collapsed or 'track'


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
    if not DB_POOL:
        return []
    try:
        with DB_POOL.connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM events ORDER BY date_iso ASC;')
                rows = cur.fetchall()
        return [format_event(row) for row in rows]
    except Exception as e:
        print(f"Error getting events: {e}")
        return []


def get_products() -> List[Dict[str, Any]]:
    if not DB_POOL:
        return []
    try:
        with DB_POOL.connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM products ORDER BY is_new DESC, name ASC;')
                rows = cur.fetchall()
        return [format_product(row) for row in rows]
    except Exception as e:
        print(f"Error getting products: {e}")
        return []


def get_social_links() -> List[Dict[str, Any]]:
    if not DB_POOL:
        return []
    try:
        with DB_POOL.connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT label, url, platform FROM social_links ORDER BY id ASC;')
                rows = cur.fetchall()
        return rows
    except Exception as e:
        print(f"Error getting social links: {e}")
        return []


def get_setlist_tracks() -> List[Dict[str, Any]]:
    if not DB_POOL:
        return []
    try:
        with DB_POOL.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT track_name, slug, position FROM setlist_tracks ORDER BY position ASC NULLS LAST, track_name ASC;'
                )
                rows = cur.fetchall()
        return rows
    except Exception as e:
        print(f"Error getting setlist tracks: {e}")
        return []


def get_top_tracks() -> List[Dict[str, Any]]:
    if not DB_POOL:
        return []
    try:
        with DB_POOL.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''
                    SELECT
                      t.track_name,
                      COALESCE(COUNT(v.id), 0) AS votos,
                      MAX(v.created_at) AS last_vote,
                      MIN(t.position) AS pos
                    FROM setlist_tracks t
                    LEFT JOIN setlist_votes v ON v.track_name = t.track_name
                    GROUP BY t.track_name
                    ORDER BY votos DESC, last_vote DESC NULLS LAST, pos ASC
                    LIMIT 10;
                    '''
                )
                rows = cur.fetchall()
        return rows
    except Exception as e:
        print(f"Error getting top tracks: {e}")
        return []


def get_recent_comments(limit: int = 20) -> List[Dict[str, Any]]:
    if not DB_POOL:
        return []
    try:
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
    except Exception as e:
        print(f"Error getting comments: {e}")
        return []


def handler(event, context):
    """Main Vercel handler"""
    try:
        # Extract request info from Vercel event
        http_method = event.get('httpMethod') or event.get('method', 'GET')
        path = event.get('path') or event.get('rawPath', '/')
        query_params = event.get('queryStringParameters') or {}
        headers_out = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        }

        # Handle OPTIONS for CORS
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers_out,
                'body': ''
            }

        # GET requests
        if http_method == 'GET':
            if path == '/api/events':
                return {
                    'statusCode': 200,
                    'headers': headers_out,
                    'body': json.dumps(get_events())
                }

            if path == '/api/products':
                return {
                    'statusCode': 200,
                    'headers': headers_out,
                    'body': json.dumps(get_products())
                }

            if path == '/api/social':
                return {
                    'statusCode': 200,
                    'headers': headers_out,
                    'body': json.dumps(get_social_links())
                }

            if path == '/api/setlist/top':
                return {
                    'statusCode': 200,
                    'headers': headers_out,
                    'body': json.dumps(get_top_tracks())
                }

            if path == '/api/setlist/tracks':
                return {
                    'statusCode': 200,
                    'headers': headers_out,
                    'body': json.dumps(get_setlist_tracks())
                }

            if path == '/api/setlist/comments':
                limit = int(query_params.get('limit', 20))
                return {
                    'statusCode': 200,
                    'headers': headers_out,
                    'body': json.dumps(get_recent_comments(limit=limit))
                }

        # POST requests
        if http_method == 'POST':
            if not DB_POOL:
                return {
                    'statusCode': 500,
                    'headers': headers_out,
                    'body': json.dumps({'error': 'Database not available'})
                }

            body_str = event.get('body', '{}')
            body = json.loads(body_str) if body_str else {}

            if path == '/api/setlist/vote':
                track_name = body.get('track_name', '').strip()
                contributor = body.get('contributor_name', '').strip()

                if not track_name:
                    return {
                        'statusCode': 400,
                        'headers': headers_out,
                        'body': json.dumps({'error': 'track_name é obrigatório'})
                    }

                try:
                    with DB_POOL.connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                'INSERT INTO setlist_votes (track_name, contributor_name) VALUES (%s, %s);',
                                (track_name, contributor or None)
                            )
                    return {
                        'statusCode': 201,
                        'headers': headers_out,
                        'body': json.dumps({'track': track_name, 'status': 'ok'})
                    }
                except Exception as e:
                    print(f"Error recording vote: {e}")
                    return {
                        'statusCode': 500,
                        'headers': headers_out,
                        'body': json.dumps({'error': str(e)})
                    }

            if path == '/api/setlist/comment':
                idea = body.get('idea', '').strip()
                contributor = body.get('contributor_name', '').strip()

                if not idea:
                    return {
                        'statusCode': 400,
                        'headers': headers_out,
                        'body': json.dumps({'error': 'idea é obrigatório'})
                    }

                try:
                    with DB_POOL.connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                'INSERT INTO setlist_comments (idea, contributor_name) VALUES (%s, %s);',
                                (idea, contributor or None)
                            )
                    return {
                        'statusCode': 201,
                        'headers': headers_out,
                        'body': json.dumps({'status': 'ok'})
                    }
                except Exception as e:
                    print(f"Error recording comment: {e}")
                    return {
                        'statusCode': 500,
                        'headers': headers_out,
                        'body': json.dumps({'error': str(e)})
                    }

            if path == '/api/newsletter':
                email = body.get('email', '').strip()

                if not email or '@' not in email:
                    return {
                        'statusCode': 400,
                        'headers': headers_out,
                        'body': json.dumps({'error': 'E-mail inválido'})
                    }

                try:
                    with DB_POOL.connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                'INSERT INTO newsletter_subscribers (email) VALUES (%s) ON CONFLICT (email) DO NOTHING;',
                                (email,)
                            )
                    return {
                        'statusCode': 201,
                        'headers': headers_out,
                        'body': json.dumps({'status': 'ok'})
                    }
                except Exception as e:
                    print(f"Error recording newsletter signup: {e}")
                    return {
                        'statusCode': 500,
                        'headers': headers_out,
                        'body': json.dumps({'error': str(e)})
                    }

        # 404 for unknown endpoints
        return {
            'statusCode': 404,
            'headers': headers_out,
            'body': json.dumps({'error': 'Endpoint não encontrado', 'path': path})
        }

    except Exception as e:
        print(f"Error in handler: {e}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e), 'type': type(e).__name__})
        }
