#!/usr/bin/env python3
"""
Vercel serverless function wrapper for Divino Maravilhoso server.
"""
import sys
from pathlib import Path

# Add parent directory to path to import server module
sys.path.insert(0, str(Path(__file__).parent.parent))

from server import DivinoHandler, init_db
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

# Initialize database on cold start
init_db()

class VercelHandler(BaseHTTPRequestHandler):
    """Wrapper to make DivinoHandler work with Vercel's serverless functions."""

    def __init__(self, *args, **kwargs):
        # Get request from Vercel
        self.vercel_request = kwargs.pop('vercel_request', None)
        super().__init__(*args, **kwargs)

    def setup(self):
        """Override setup to use Vercel's request/response."""
        pass

# Main handler function for Vercel
def handler(request, response):
    """
    Main entry point for Vercel serverless function.

    Args:
        request: Vercel request object
        response: Vercel response object
    """
    import io
    from http import HTTPStatus
    from server import (
        get_events, get_products, get_social_links,
        get_top_tracks, get_setlist_tracks, get_recent_comments,
        format_event, generate_story_card, DB_POOL
    )

    # Parse the request path
    path = request.path if hasattr(request, 'path') else '/'
    method = request.method if hasattr(request, 'method') else 'GET'

    # Set CORS headers
    response.setHeader('Access-Control-Allow-Origin', '*')
    response.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    response.setHeader('Access-Control-Allow-Headers', 'Content-Type')

    # Handle OPTIONS for CORS
    if method == 'OPTIONS':
        response.status(200).end()
        return

    # Handle GET requests
    if method == 'GET':
        parsed = urlparse(path)
        path_parts = parsed.path.strip('/').split('/')

        # API Routes
        if parsed.path == '/api/events':
            events = get_events()
            response.status(200).json(events)
            return

        if parsed.path == '/api/products':
            products = get_products()
            response.status(200).json(products)
            return

        if parsed.path == '/api/social':
            links = get_social_links()
            response.status(200).json(links)
            return

        if parsed.path == '/api/setlist/top':
            top_tracks = get_top_tracks()
            response.status(200).json(top_tracks)
            return

        if parsed.path == '/api/setlist/tracks':
            tracks = get_setlist_tracks()
            response.status(200).json(tracks)
            return

        if parsed.path.startswith('/api/setlist/comments'):
            query = parse_qs(parsed.query)
            limit = int(query.get('limit', ['20'])[0])
            comments = get_recent_comments(limit=limit)
            response.status(200).json(comments)
            return

        # Story card generation
        if len(path_parts) == 4 and path_parts[0] == 'api' and path_parts[1] == 'events' and path_parts[3] == 'story-card.png':
            try:
                event_id = int(path_parts[2])
            except ValueError:
                response.status(400).send('ID inválido')
                return

            with DB_POOL.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT * FROM events WHERE id = %s;', (event_id,))
                    event = cur.fetchone()

            if not event:
                response.status(404).send('Evento não encontrado')
                return

            event_dict = format_event(event)
            img_bytes = generate_story_card(event_dict)
            response.setHeader('Content-Type', 'image/png')
            response.status(200).send(img_bytes)
            return

        # Serve static files - redirect to public directory
        response.status(404).send('Not found')
        return

    # Handle POST requests
    if method == 'POST':
        body = request.body if hasattr(request, 'body') else {}

        if path == '/api/setlist/vote':
            # Handle vote
            track_name = body.get('track_name', '').strip()
            contributor = body.get('contributor_name', '').strip()

            if not track_name:
                response.status(400).json({'error': 'track_name é obrigatório'})
                return

            with DB_POOL.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO setlist_votes (track_name, contributor_name) VALUES (%s, %s);',
                        (track_name, contributor or None)
                    )

            response.status(201).json({'track': track_name, 'status': 'ok'})
            return

        if path == '/api/setlist/comment':
            # Handle comment
            idea = body.get('idea', '').strip()
            contributor = body.get('contributor_name', '').strip()

            if not idea:
                response.status(400).json({'error': 'idea é obrigatório'})
                return

            with DB_POOL.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO setlist_comments (idea, contributor_name) VALUES (%s, %s);',
                        (idea, contributor or None)
                    )

            response.status(201).json({'status': 'ok'})
            return

        if path == '/api/newsletter':
            # Handle newsletter signup
            email = body.get('email', '').strip()

            if not email or '@' not in email:
                response.status(400).json({'error': 'E-mail inválido'})
                return

            with DB_POOL.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        'INSERT INTO newsletter_signups (email) VALUES (%s) ON CONFLICT (email) DO NOTHING;',
                        (email,)
                    )

            response.status(201).json({'status': 'ok'})
            return

        response.status(404).json({'error': 'Endpoint não encontrado'})
        return

    response.status(405).send('Method not allowed')
