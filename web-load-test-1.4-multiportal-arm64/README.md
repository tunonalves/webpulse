# web-load-test 1.4 multiportal - ARM64

Paquete reconstruido a partir del estado documentado del proyecto el 2026-08-18. No es una copia byte-a-byte del directorio original.

## Estado representado
- Objetivo: Orange Pi Zero 3 / Zero 2W, ARM64/aarch64.
- 5 contenedores, 6 usuarios totales.
- La Tecla: 2 usuarios; resto: 1.
- `headless: true` y bloqueo de imágenes/media/fuentes; JavaScript habilitado.
- `reading: 3-6 s`, `session restart: 60-120 s`.
- Imagen objetivo: `web-load-test-playwright:1.4-arm64`.
- Cadena Rio conserva `/Noticias` y `section_content_wait_seconds: 2.5`.
- Incluye `ajustar_carga.sh`.

## Uso
```bash
cp .env.example .env
./manage.sh up
./manage.sh stats
./manage.sh inspect
```

Los YAML de los cuatro portales no-Cadena usan `/` como sección de descubrimiento porque el material fuente no incluía sus rutas originales exactas.
