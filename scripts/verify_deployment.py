"""Record deployment evidence using stdlib HTTP; never print credentials."""
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def http(url, payload=None):
    request = Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                      headers={'Content-Type': 'application/json'} if payload is not None else {})
    with urlopen(request, timeout=300 if payload else 15) as response:
        body = response.read().decode()
        return response.status, json.loads(body) if response.headers.get_content_type() == 'application/json' else body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend-url', default='http://127.0.0.1:7860')
    parser.add_argument('--frontend-url', default='http://127.0.0.1:8501')
    parser.add_argument('--include-generation', action='store_true', help='Uses paid generator and judge API calls')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = {'codespace_name': os.getenv('CODESPACE_NAME'),
              'backend_url_tested': args.backend_url, 'frontend_url_tested': args.frontend_url,
              'generation_tested': args.include_generation,
              'forwarded_browser_urls_verified': False}
    try:
        code, health = http(args.backend_url.rstrip('/') + '/')
        if code != 200 or health.get('status') != 'ready' or health.get('vectors', 0) < 1:
            raise ValueError('Backend health response is not ready')
        report['backend_health'] = health
        report['frontend_health_status'], _ = http(args.frontend_url.rstrip('/') + '/_stcore/health')
        code, retrieved = http(args.backend_url.rstrip('/') + '/v1/relevant_chunks',
                               {'query': 'What are the cancellation rules for an Advance Purchase booking?', 'k': 3})
        if code != 200 or len(retrieved.get('relevant_chunks', [])) != 3:
            raise ValueError('Retrieval did not return three source excerpts')
        report['retrieval_http_status'] = code
        report['retrieved_chunks'] = len(retrieved['relevant_chunks'])
        if args.include_generation:
            catalog = json.loads((root / 'backend_files/reference_catalog.json').read_text())
            code, answer = http(args.backend_url.rstrip('/') + '/v1/answer_with_relevant_chunks',
                                {'query': catalog[0]['question'], 'k': 3})
            if not answer.get('answer') or not answer.get('reference_available') or answer.get('composite_score') is None:
                raise ValueError('Approved-reference answer or its scoring is incomplete')
            report['answer_http_status'] = code
            report['answer_route'] = answer['route']
            report['answer_composite'] = answer['composite_score']
            report['answer_and_sources'] = answer
        report['checks_passed'] = True
    except (HTTPError, URLError, ValueError, KeyError) as exc:
        report['checks_passed'] = False
        report['error_type'] = type(exc).__name__
        if isinstance(exc, HTTPError):
            report['http_status'] = exc.code
        print('Deployment check failed. Inspect services/logs; private forwarded URLs require browser sign-in.')
    output = root / 'outputs/deployment_verification.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2))
    print(json.dumps({key: value for key, value in report.items() if key != 'answer_and_sources'}, indent=2))
    if not report['checks_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
