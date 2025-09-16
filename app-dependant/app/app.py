import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# La URL del servicio del que dependemos.
# Se obtiene de una variable de entorno para mayor flexibilidad.
# El valor por defecto apunta al servicio interno de la app estable.
dependency_url = os.environ.get('DEPENDENCY_URL', 'http://app-stable.app-demo.svc.cluster.local')

@app.route('/')
def check_dependency():
    try:
        # Hacemos una petición GET a la app-demo
        response = requests.get(dependency_url, timeout=5)

        # Verificamos que la respuesta sea exitosa (código 2xx)
        if response.status_code >= 200 and response.status_code < 300:
            return jsonify({
                "status": "OK",
                "message": "La aplicación dependiente funciona correctamente.",
                "dependency_check": f"Conexión exitosa con {dependency_url}",
                "dependency_status_code": response.status_code
            }), 200
        else:
            # Si app-demo responde con un error
            return jsonify({
                "status": "ERROR",
                "message": "La aplicación dependiente funciona, pero la dependencia ha fallado.",
                "dependency_check": f"Error al conectar con {dependency_url}",
                "dependency_status_code": response.status_code
            }), 503  # 503 Service Unavailable

    except requests.exceptions.RequestException as e:
        # Si no se puede conectar con app-demo
        return jsonify({
            "status": "ERROR",
            "message": "La aplicación dependiente funciona, pero la dependencia es inalcanzable.",
            "dependency_check": f"No se pudo resolver o conectar con {dependency_url}",
            "error_details": str(e)
        }), 503 # 503 Service Unavailable

if __name__ == '__main__':
    # El servidor escucha en todas las interfaces en el puerto 5000
    app.run(host='0.0.0.0', port=5000)