#!/bin/bash

# Nombre del archivo: clonar_repo.sh

# Función para mostrar el uso correcto
usage() {
    echo "Uso: $0 <URL_DEL_REPOSITORIO> [DIRECTORIO_DESTINO]"
    echo "Ejemplo: $0 https://github.com/usuario/repo.git mi-proyecto"
    exit 1
}

# Verificar si git está instalado
if ! command -v git &> /dev/null; then
    echo "Error: git no está instalado. Por favor instálalo primero."
    exit 1
fi

# Verificar argumentos
REPO_URL=$1
TARGET_DIR=$2

if [ -z "$REPO_URL" ]; then
    usage
fi

echo "Iniciando clonación desde: $REPO_URL"

# Ejecutar el comando de clonación
if [ -z "$TARGET_DIR" ]; then
    # Si no se especifica directorio, git usará el nombre del repo
    git clone "$REPO_URL"
else
    git clone "$REPO_URL" "$TARGET_DIR"
fi

# Verificar si el comando fue exitoso
if [ $? -eq 0 ]; then
    echo "✅ Repositorio clonado exitosamente."
else
    echo "❌ Hubo un error al clonar el repositorio."
fi
