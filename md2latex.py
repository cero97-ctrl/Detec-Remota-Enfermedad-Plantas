#!/usr/bin/env python3
import sys
import re
import os

def convert_md_to_tex(md_file):
    if not os.path.exists(md_file):
        print(f"Error: El archivo '{md_file}' no existe.")
        sys.exit(1)

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- 1. Estructura básica del documento ---
    header = r"""\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage[spanish]{babel}
\usepackage{hyperref}
\usepackage{graphicx}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{amsmath}
\usepackage{textcomp}
\usepackage{longtable}
\usepackage{xltabular}
\usepackage{booktabs}
\usepackage{geometry}
\geometry{a4paper, margin=1in}

\lstset{
    basicstyle=\ttfamily\small,
    extendedchars=true,
    columns=fullflexible,
    keepspaces=true,
    literate={á}{{\'a}}1 {é}{{\'e}}1 {í}{{\'i}}1 {ó}{{\'o}}1 {ú}{{\'u}}1 {ñ}{{\~n}}1 {Á}{{\'A}}1 {É}{{\'E}}1 {Í}{{\'I}}1 {Ó}{{\'O}}1 {Ú}{{\'U}}1 {Ñ}{{\~N}}1 {¡}{{!`}}1 {¿}{{?`}}1 {°}{{$^\circ$}}1
}

\title{Documento convertido}
\author{}
\date{}

\begin{document}

\maketitle
"""
    footer = r"""
\end{document}
"""

    # --- 2. Pre-procesamiento: Proteger bloques ---
    protected_blocks = {}
    
    def save_block(text):
        key = f"@@PROTECTEDBLOCK{len(protected_blocks)}@@"
        protected_blocks[key] = text
        return key

    # 2.1 Bloques de código ```lang ... ```
    def callback_code_block(match):
        lang = match.group(1).strip() if match.group(1) else ""
        if lang.lower() == 'g-code':
            lang = 'gcode'
        elif lang.lower() in ['cpp', 'c++']:
            lang = 'C++'
        code = match.group(2)
        latex_code = f"\\begin{{lstlisting}}\n{code}\n\\end{{lstlisting}}"
        return save_block(latex_code)

    content = re.sub(r'```([^\n]*)\n(.*?)```', callback_code_block, content, flags=re.DOTALL)

    # 2.2 Fórmulas matemáticas bloque $$ ... $$
    def callback_math_block(match):
        latex_code = f"\\[\n{match.group(1)}\n\\]"
        return save_block(latex_code)
    
    content = re.sub(r'\$\$(.*?)\$\$', callback_math_block, content, flags=re.DOTALL)

    # 2.3 Fórmulas en línea $ ... $
    def callback_inline_math(match):
        math_content = match.group(1)
        math_content = math_content.replace('\\\\', '\\')
        latex_code = f"${math_content}$"
        return save_block(latex_code)

    content = re.sub(r'(?<![\$\\])\$(?!\$)(.*?)(?<![\$\\])\$(?!\$)', callback_inline_math, content)

    # --- 3. Procesamiento de Markdown ---

    # Pre-procesar listas para evitar conflictos con cursiva
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Listas desordenadas
        if re.match(r'^\s*([-*])\s', line):
            lines[i] = re.sub(r'^\s*([-*])\s', '@@ULITEM@@ ', line, 1)
        # Listas ordenadas
        elif re.match(r'^\s*\d+\.\s', line):
            lines[i] = re.sub(r'^\s*(\d+\.)\s', r'@@OLITEM@@ ', line, 1)
    content = '\n'.join(lines)

    # Eliminar escapes de punto en Markdown (ej. 1\. -> 1.) antes de escapar backslashes
    content = content.replace(r'\.', '.')

    # Escapar caracteres especiales de LaTeX (excepto en bloques protegidos)
    # Orden importante: primero backslash, luego otros
    content = content.replace('\\', '\\textbackslash{}')
    content = content.replace('{', '\\{')
    content = content.replace('}', '\\}')
    content = content.replace('%', '\\%')
    content = content.replace('$', '\\$')
    content = content.replace('_', '\\_')
    content = content.replace('&', '\\&')
    content = content.replace('#', '\\#')

    # Reemplazos de caracteres Unicode problemáticos
    content = content.replace('🚀', '')
    content = content.replace('🛠', '')
    content = content.replace('⚠️', '\\textbf{Warning:}')
    content = content.replace('️', '') # Carácter invisible Variation Selector-16
    content = content.replace('μ', '$\\mu$')
    content = content.replace('∘', '$^\\circ$')

    # Comillas dobles a comillas de LaTeX
    content = re.sub(r'"([^"]*)"', r"``\1''", content)

    # Negrita y Cursiva
    # Usamos DOTALL para permitir que la negrita abarque varias líneas si es necesario
    content = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', content, flags=re.DOTALL)
    content = re.sub(r'\*(.*?)\*', r'\\textit{\1}', content)
    
    # Código en línea `...`
    content = re.sub(r'`(.*?)`', r'\\texttt{\1}', content)

    # Imágenes !alt
    content = re.sub(r'!\[(.*?)\]\((.*?)\)', 
                     r'\\begin{figure}[h]\n\\centering\n\\includegraphics[width=0.8\\textwidth]{\2}\n\\caption{\1}\n\\end{figure}', 
                     content)
    
    # Enlaces text
    content = re.sub(r'\[(.*?)\]\((.*?)\)', r'\\href{\2}{\1}', content)

    # Encabezados
    # Nota: Como ya escapamos # a \#, buscamos \#
    content = re.sub(r'^\\# (.*?)$', r'\\section*{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^\\#\\# (.*?)$', r'\\subsection*{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^\\#\\#\\# (.*?)$', r'\\subsubsection*{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^\\#\\#\\#\\# (.*?)$', r'\\paragraph*{\1}', content, flags=re.MULTILINE)

    # --- 4. Procesamiento línea por línea (Listas y Tablas) ---
    lines = content.split('\n')
    new_lines = []
    in_itemize = False
    in_enumerate = False
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Listas desordenadas
        if stripped.startswith('@@ULITEM@@'):
            if not in_itemize:
                if in_enumerate: 
                    new_lines.append(r'\end{enumerate}')
                    in_enumerate = False
                new_lines.append(r'\begin{itemize}')
                in_itemize = True
            item_content = re.sub(r'^@@ULITEM@@\s*', '', stripped)
            new_lines.append(f'    \\item {item_content.strip()}')
            continue
        
        # Listas ordenadas
        elif stripped.startswith('@@OLITEM@@'):
            if not in_enumerate:
                if in_itemize:
                    new_lines.append(r'\end{itemize}')
                    in_itemize = False
                new_lines.append(r'\begin{enumerate}')
                in_enumerate = True
            item_content = re.sub(r'^@@OLITEM@@\s*', '', stripped)
            new_lines.append(f'    \\item {item_content.strip()}')
            continue
            
        # Cierre de listas
        elif stripped == "" or (not stripped.startswith('@@ULITEM@@') and not stripped.startswith('@@OLITEM@@')):
             if in_itemize:
                 new_lines.append(r'\end{itemize}')
                 in_itemize = False
             if in_enumerate:
                 new_lines.append(r'\end{enumerate}')
                 in_enumerate = False

        # Tablas
        # Detectar fila de tabla: empieza y termina con | (escapado como \| o no, pero aquí ya escapamos &)
        # Nota: Como escapamos | -> \| no, | no es especial en LaTeX texto normal, pero sí en Markdown.
        # Pero espera, escapamos caracteres especiales antes. | no se escapó.
        if re.match(r'^\s*\|.*\|\s*$', line):
            if not in_table:
                in_table = True
                # Contar columnas basado en separadores |
                cols = line.count('|') - 1
                if cols > 1:
                    align_str = 'l ' + 'X ' * (cols - 1)
                else:
                    align_str = 'X'
                new_lines.append(r'\begin{xltabular}{\textwidth}{@{}' + align_str.strip() + r'@{}}')
                new_lines.append(r'\toprule')
                
                # Procesar header
                # Quitamos el primer y último | y dividimos
                cells = [c.strip() for c in line.strip().split('|')[1:-1]]
                new_lines.append(' & '.join(cells) + r' \\ \midrule')
                new_lines.append(r'\endhead')
            elif re.match(r'^\s*\|[\s\-:|]+\|\s*$', line):
                # Es la línea separadora |---|---|
                continue 
            else:
                # Fila de datos
                cells = [c.strip() for c in line.strip().split('|')[1:-1]]
                new_lines.append(' & '.join(cells) + r' \\')
            continue
        else:
            if in_table:
                new_lines.append(r'\bottomrule')
                new_lines.append(r'\end{xltabular}')
                in_table = False

        new_lines.append(line)

    # Cierres finales
    if in_itemize: new_lines.append(r'\end{itemize}')
    if in_enumerate: new_lines.append(r'\end{enumerate}')
    if in_table: new_lines.append(r'\bottomrule' + '\n' + r'\end{xltabular}')

    content = '\n'.join(new_lines)

    # --- 5. Restaurar bloques protegidos ---
    # Restauramos en orden inverso o simplemente iteramos.
    # Como las claves son únicas, el orden no debería importar mucho si no hay anidamiento (que no hay aquí).
    for key, val in protected_blocks.items():
        content = content.replace(key, val)

    # Guardar resultado
    base_name = os.path.splitext(md_file)[0]
    tex_file = f"{base_name}.tex"
    
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(header + content + footer)
    print(f"¡Éxito! Archivo convertido: {tex_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 md2latex.py <archivo.md>")
        sys.exit(1)
    
    convert_md_to_tex(sys.argv[1])