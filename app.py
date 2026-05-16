#!/usr/bin/env python3
"""
RPOFlip Backend — Flask API for PDF to Image conversion
Uses PyMuPDF (fitz) instead of pdf2image — NO Poppler required!
"""
import os
import uuid
import shutil
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF — NO external dependencies!

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / 'rpoflip_sessions'
UPLOAD_FOLDER.mkdir(exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_PAGES = 100
DEFAULT_DPI = 600

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


def get_session_path(session_id: str) -> Path:
    """Get path for a session folder."""
    return UPLOAD_FOLDER / session_id


def cleanup_session(session_id: str):
    """Remove session folder and all its contents."""
    session_path = get_session_path(session_id)
    if session_path.exists():
        shutil.rmtree(session_path, ignore_errors=True)


@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Upload a PDF file and return a session ID."""
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files allowed'}), 400

    session_id = str(uuid.uuid4())
    session_path = get_session_path(session_id)
    session_path.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(file.filename)
    pdf_path = session_path / 'original.pdf'
    file.save(str(pdf_path))

    return jsonify({
        'session_id': session_id,
        'filename': filename,
        'size': os.path.getsize(str(pdf_path))
    }), 200


@app.route('/api/convert', methods=['POST'])
def convert_pdf():
    """Convert uploaded PDF to images using PyMuPDF (NO Poppler needed)."""
    data = request.get_json()
    if not data or 'session_id' not in data:
        return jsonify({'error': 'Missing session_id'}), 400

    session_id = data['session_id']
    dpi = data.get('dpi', DEFAULT_DPI)
    max_pages = data.get('max_pages', MAX_PAGES)

    # Clamp DPI to reasonable range (prevent abuse)
    dpi = max(72, min(dpi, 800))

    session_path = get_session_path(session_id)
    pdf_path = session_path / 'original.pdf'

    if not pdf_path.exists():
        return jsonify({'error': 'Session not found or expired'}), 404

    images_path = session_path / 'images'
    images_path.mkdir(exist_ok=True)

    try:
        # Open PDF with PyMuPDF — NO Poppler needed!
        doc = fitz.open(str(pdf_path))
        total_pages = min(len(doc), max_pages)

        # Calculate zoom based on DPI (72 is PDF default)
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        for i in range(total_pages):
            page = doc[i]
            # Render page to pixmap
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            # Save as PNG
            output_path = images_path / f'page_{i+1:04d}.png'
            pix.save(str(output_path))

        doc.close()

        return jsonify({
            'session_id': session_id,
            'total_pages': total_pages,
            'dpi': dpi,
            'format': 'png',
            'zoom_hint': dpi / DEFAULT_DPI
        }), 200

    except Exception as e:
        cleanup_session(session_id)
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500


@app.route('/api/page/<int:page_num>', methods=['GET'])
def get_page(page_num):
    """Get a specific page image by session ID and page number."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id parameter'}), 400

    session_path = get_session_path(session_id)
    image_path = session_path / 'images' / f'page_{page_num:04d}.png'

    if not image_path.exists():
        return jsonify({'error': 'Page not found'}), 404

    return send_file(str(image_path), mimetype='image/png')


@app.route('/api/download', methods=['GET'])
def download_pdf():
    """Download the original PDF file."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id parameter'}), 400

    session_path = get_session_path(session_id)
    pdf_path = session_path / 'original.pdf'

    if not pdf_path.exists():
        return jsonify({'error': 'File not found'}), 404

    return send_file(str(pdf_path), mimetype='application/pdf', as_attachment=True)


@app.route('/api/delete', methods=['POST'])
def delete_session():
    """Delete a session and all its files."""
    data = request.get_json()
    if not data or 'session_id' not in data:
        return jsonify({'error': 'Missing session_id'}), 400

    session_id = data['session_id']
    cleanup_session(session_id)

    return jsonify({'success': True}), 200


@app.route('/api/text/<int:page_num>', methods=['GET'])
def get_page_text(page_num):
    """Extract text and tables from a specific page as HTML."""
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'error': 'Missing session_id parameter'}), 400

    session_path = get_session_path(session_id)
    pdf_path = session_path / 'original.pdf'

    if not pdf_path.exists():
        return jsonify({'error': 'Session not found'}), 404

    try:
        doc = fitz.open(str(pdf_path))
        if page_num < 1 or page_num > len(doc):
            doc.close()
            return jsonify({'error': 'Page number out of range'}), 404

        page = doc[page_num - 1]
        html_content = page.get_text("html")

        doc.close()

        css = """body{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:16px;line-height:1.7;color:#1a1a2e;max-width:800px;margin:0 auto;padding:40px;background:#fff}p{margin:0 0 1em 0}h1,h2,h3,h4{color:#0a0a0f;margin-top:1.5em;margin-bottom:0.5em;font-weight:600}h1{font-size:1.8em}h2{font-size:1.5em}h3{font-size:1.2em}table{border-collapse:collapse;width:100%;margin:1em 0;font-size:14px}th,td{border:1px solid #ddd;padding:10px 12px;text-align:left}th{background:#f8f8fa;font-weight:600;color:#0a0a0f}tr:nth-child(even){background:#fafafa}blockquote{border-left:3px solid #7c3aed;margin:1em 0;padding-left:1em;color:#444}ul,ol{margin:1em 0;padding-left:2em}li{margin:0.3em 0}strong{color:#0a0a0f}"""

        full_html = '<!DOCTYPE html><html><head><meta charset="UTF-8"><style>' + css + '</style></head><body>' + html_content + '</body></html>'

        return full_html, 200, {'Content-Type': 'text/html; charset=utf-8'}

    except Exception as e:
        return jsonify({'error': f'Text extraction failed: {str(e)}'}), 500


@app.route('/api/builtin', methods=['GET'])
def get_builtin_pdfs():
    """Return list of PDFs from the pdfs/ folder."""
    pdfs_folder = Path(__file__).parent / 'pdfs'
    if not pdfs_folder.exists():
        return jsonify({'files': []}), 200

    files = []
    for pdf_path in sorted(pdfs_folder.glob('*.pdf')):
        stat = pdf_path.stat()
        files.append({
            'id': pdf_path.stem,
            'name': pdf_path.name,
            'size': stat.st_size,
            'path': f'/pdfs/{pdf_path.name}'
        })

    return jsonify({'files': files}), 200


@app.route('/pdfs/<path:filename>')
def serve_pdf(filename):
    """Serve a PDF file from the pdfs folder."""
    pdfs_folder = Path(__file__).parent / 'pdfs'
    return send_from_directory(str(pdfs_folder), filename)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok'}), 200


@app.route('/')
def serve_frontend():
    """Serve the frontend HTML file."""
    return send_from_directory('.', 'index.html')


if __name__ == '__main__':
    print(f"RPOFlip Backend starting...")
    print(f"PDF engine: PyMuPDF (NO Poppler required!)")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Max file size: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB")
    print(f"Max pages per PDF: {MAX_PAGES}")
    print(f"Default DPI: {DEFAULT_DPI}")
    print()
    print("API Endpoints:")
    print("  POST /api/upload    — Upload PDF")
    print("  POST /api/convert   — Convert to images (PyMuPDF)")
    print("  GET  /api/page/<n>  — Get page image")
    print("  GET  /api/download  — Download original PDF")
    print("  POST /api/delete    — Delete session")
    print("  GET  /api/builtin   — List built-in PDFs")
    print("  GET  /api/health    — Health check")
    print()
    print("Open http://127.0.0.1:5000 in your browser")
    print()

    app.run(host='0.0.0.0', port=5000, debug=True)
