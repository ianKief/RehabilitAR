import os
from pyngrok import ngrok
from src.web import create_app
app = create_app()
if __name__ == "__main__":
    # Evitamos que ngrok se abra dos veces debido al "reloader" automático de Flask
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        
        token = os.environ.get("NGROK_AUTHTOKEN")
        if token:
            ngrok.set_auth_token(token)
        
        puerto = 5000
        public_url = ngrok.connect(puerto).public_url
        print(f" * Túnel ngrok activo: {public_url} -> http://127.0.0.1:{puerto}")
        
        os.environ["URL_NGROK"] = public_url

    app.run(debug=True, port=5000)