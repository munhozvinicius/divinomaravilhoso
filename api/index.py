#!/usr/bin/env python3
"""
Vercel serverless function for Divino Maravilhoso API.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import server module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path is set
from urllib.parse import urlparse, parse_qs
import json
from http import HTTPStatus

# Import database functions
from server import (
    get_events, get_products, get_social_links,
    get_top_tracks, get_setlist_tracks, get_recent_comments,
    format_event, generate_story_card, DB_POOL, init_db
)

# Initialize database on module load
try:
    init_db()
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")


def handler(request, context):
    """
    Main Vercel serverless handler.

    Args:
        request: Vercel request object with properties: url, method, headers, body
        context: Vercel context object

    Returns:
        dict: Response with statusCode, headers, and body
    """
    try:
        # Get request details
        url = request.get('url', '/')
        method = request.get('method', 'GET')

        # Parse URL
        parsed = urlparse(url)
        path = parsed.path
        path_parts = path.strip('/').split('/')

        # Set CORS headers
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        }

        # Handle OPTIONS for CORS
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }

        # GET requests
        if method == 'GET':
            # Events API
            if path == '/api/events':
                events = get_events()
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(events)
                }

            # Products API
            if path == '/api/products':
                products = get_products()
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(products)
                }

            # Social links API
            if path == '/api/social':
                links = get_social_links()
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(links)
                }

            # Top tracks API
            if path == '/api/setlist/top':
                top_tracks = get_top_tracks()
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(top_tracks)
                }

            # Setlist tracks API
            if path == '/api/setlist/tracks':
                tracks = get_setlist_tracks()
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(tracks)
                }

            # Comments API
            if path.startswith('/api/setlist/comments'):
                query = parse_qs(parsed.query)
                limit = int(query.get('limit', ['20'])[0])
                comments = get_recent_comments(limit=limit)
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(comments)
                }

            # Story card generation
            if len(path_parts) >= 4 and path_parts[0] == 'api' and path_parts[1] == 'events' and path_parts[3] == 'story-card.png':
                try:
                    event_id = int(path_parts[2])
                except ValueError:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': 'ID inválido'})
                    }

                with DB_POOL.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute('SELECT * FROM events WHERE id = %s;', (event_id,))
                        event = cur.fetchone()

                if not event:
                    return {
                        'statusCode': 404,
                        'headers': headers,
                        'body': json.dumps({'error': 'Evento não encontrado'})
                    }

                event_dict = format_event(event)
                img_bytes = generate_story_card(event_dict)

                return {
                    'statusCode': 200,
                    'headers': {
                        **headers,
                        'Content-Type': 'image/png'
                    },
                    'body': img_bytes,
                    'isBase64Encoded': True
                }

        # POST requests
        if method == 'POST':
            # Parse body
            body_str = request.get('body', '{}')
            if isinstance(body_str, str):
                body = json.loads(body_str) if body_str else {}
            else:
                body = body_str

            # Vote endpoint
            if path == '/api/setlist/vote':
                track_name = body.get('track_name', '').strip()
                contributor = body.get('contributor_name', '').strip()

                if not track_name:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': 'track_name é obrigatório'})
                    }

                with DB_POOL.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            'INSERT INTO setlist_votes (track_name, contributor_name) VALUES (%s, %s);',
                            (track_name, contributor or None)
                        )

                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps({'track': track_name, 'status': 'ok'})
                }

            # Comment endpoint
            if path == '/api/setlist/comment':
                idea = body.get('idea', '').strip()
                contributor = body.get('contributor_name', '').strip()

                if not idea:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': 'idea é obrigatório'})
                    }

                with DB_POOL.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            'INSERT INTO setlist_comments (idea, contributor_name) VALUES (%s, %s);',
                            (idea, contributor or None)
                        )

                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps({'status': 'ok'})
                }

            # Newsletter endpoint
            if path == '/api/newsletter':
                email = body.get('email', '').strip()

                if not email or '@' not in email:
                    return {
                        'statusCode': 400,
                        'headers': headers,
                        'body': json.dumps({'error': 'E-mail inválido'})
                    }

                with DB_POOL.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            'INSERT INTO newsletter_signups (email) VALUES (%s) ON CONFLICT (email) DO NOTHING;',
                            (email,)
                        )

                return {
                    'statusCode': 201,
                    'headers': headers,
                    'body': json.dumps({'status': 'ok'})
                }

            # Orders endpoint
            if path == '/api/orders':
                # Handle order creation
                # (implementation from server.py handle_create_order)
                return {
                    'statusCode': 501,
                    'headers': headers,
                    'body': json.dumps({'error': 'Orders endpoint not yet implemented'})
                }

        # 404 for unknown endpoints
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Endpoint não encontrado', 'path': path})
        }

    except Exception as e:
        # Error handling
        print(f"Error in handler: {e}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }
