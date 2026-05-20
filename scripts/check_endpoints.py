import requests

urls = [
    'http://127.0.0.1:5000/',
    'http://127.0.0.1:5000/api/productos',
    'http://127.0.0.1:5000/api/categorias',
]

for u in urls:
    try:
        r = requests.get(u, timeout=5)
        print('URL:', u)
        print('Status:', r.status_code)
        body = r.text
        print('Body:', body[:2000])
        print('----')
    except Exception as e:
        print('URL:', u)
        print('Error:', e)
        print('----')
