# WebPulse

Proyecto de navegación automatizada y pruebas web multiportal con Python,
Playwright, Chromium y Docker Compose. Los workers visitan secciones y artículos,
simulan sesiones de lectura y guardan resultados JSONL.

> Ejecutar únicamente sobre sitios propios o con autorización explícita. Los
> perfiles incluidos apuntan a portales reales. Revisar URLs, concurrencia,
> límites y duración antes de iniciar contenedores.

## Estado del repositorio y ramas

La rama predeterminada `main` contiene este README y `.gitignore`; **no contiene
el worker, un Dockerfile ni un archivo Compose**. No se puede iniciar la
aplicación directamente desde `main`. El código está en estas ramas:

| Rama | Contenido | Directorio de trabajo |
| --- | --- | --- |
| [`release/1.4`](https://github.com/tunonalves/webpulse/tree/release/1.4) | Paquetes headless separados para x86_64 y ARM64 | `x86_64/` o `arm64/` |
| [`release/1.5`](https://github.com/tunonalves/webpulse/tree/release/1.5) | Paquete headful con Xvfb, documentado para x86_64 | Raíz del repositorio |

Los README de esos paquetes aclaran que son reconstrucciones a partir del
estado documentado del proyecto, no copias byte a byte de los directorios
originales. Los límites de recursos son referencias, no resultados de un
benchmark ni una garantía de compatibilidad con cualquier equipo.

## Requisitos

- Git, Bash, Docker Engine y el complemento Docker Compose v2.
- Recursos suficientes para los navegadores y la concurrencia elegida.
- Acceso a la imagen base de Playwright y a las dependencias Python durante la
  construcción. En `release/1.5`, `requirements.txt` fija Playwright 1.61.0 y
  PyYAML 6.0.2.
- Para ARM64, seleccionar el paquete de `release/1.4/arm64` y comprobar la
  compatibilidad de la imagen base con el equipo; no asumir que el paquete
  x86_64 sirve para ambas arquitecturas.

## Preparar una copia de `release/1.5`

```bash
git clone --branch release/1.5 --single-branch git@github.com:tunonalves/webpulse.git
cd webpulse
cp .env.example .env
```

El comando `cp` corresponde a una copia nueva: no sobrescribir un `.env` local
existente. Revisar `.env`, los archivos de `configs/` y `compose.yaml` antes de
seguir. La configuración de usuarios se asigna por portal y permite ajustar
límites de CPU, memoria y memoria compartida.

Validar la configuración sin iniciar la navegación:

```bash
docker compose --profile latecla --profile mardelplata --profile patagonia --profile revistaque --profile cadenario config --quiet
```

Después de autorizar los destinos y ajustar la carga, iniciar y observar:

```bash
./manage.sh up
./manage.sh ps
./manage.sh logs 200
./manage.sh follow
```

`up` habilita los cinco perfiles. La ejecución se mantiene activa; salir de
`follow` no detiene la prueba. Para detener y retirar los contenedores:

```bash
./manage.sh down
```

En `release/1.5`, `stats` e `inspect` consultan contenedores del host, no solo los
de WebPulse. Para una instalación de `release/1.4`, clonar esa rama, entrar en
`arm64/` o `x86_64/` y seguir el README de ese paquete; no mezclar sus archivos
de configuración con los de otra versión.

## Estructura de los paquetes

Estas rutas están en la raíz de `release/1.5` y dentro de cada directorio de
arquitectura de `release/1.4`, no en `main`:

| Ruta | Función |
| --- | --- |
| `worker.py` | Navegación y sesiones de usuarios con Playwright |
| `requirements.txt` | Dependencias Python |
| `Dockerfile` | Imagen de ejecución; la versión 1.5 usa `xvfb-run` |
| `compose.yaml` | Servicios, perfiles, límites y volúmenes |
| `configs/` | Destinos, secciones y tiempos por portal |
| `.env.example` | Plantilla de variables para la configuración local |
| `manage.sh` | Administración de Compose |
| `logs/`, `reports/` | Directorios montados para salidas y reportes |

## Alcance de las comprobaciones

El código y las rutas se pueden revisar sin ejecutar tráfico. La validación de
Compose no comprueba disponibilidad de los portales, selectores, rendimiento ni
compatibilidad efectiva del navegador. Este README no certifica pruebas de
carga ni ejecución en ARM64. Consultar también los README específicos de cada
paquete para sus tiempos, secciones reconstruidas y limitaciones.
