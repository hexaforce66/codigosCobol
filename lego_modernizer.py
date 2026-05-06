#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import json
import os
import re
import shutil
import subprocess
import time
import zlib

import boto3
import markdown
import requests
from botocore.config import Config


MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.meta.llama3-1-70b-instruct-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

REPO_NAME = os.getenv("REPO_NAME")
SOURCE_REPO_URL = os.getenv(
    "SOURCE_REPO_URL",
    "https://github.com/hexaforce66/codigosCobol/blob/main",
).rstrip("/")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_USER = os.getenv("CONFLUENCE_USER")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
SPACE_KEY = os.getenv("SPACE_KEY")
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")


bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=AWS_REGION,
    config=Config(read_timeout=300, connect_timeout=300, retries={"max_attempts": 2}),
)


def run(cmd, cwd=None, allow_fail=False):
    print(f"▶ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, text=True)
    if result.returncode != 0 and not allow_fail:
        raise RuntimeError(f"Command failed: {cmd}")
    return result.returncode


def call_agent(perfil, tarea, context):
    prompt = f"\n\nHuman: Eres {perfil}. {tarea}\nContexto:\n{context}\n\nAssistant:"
    body = json.dumps({"prompt": prompt, "max_gen_len": 4096, "temperature": 0.1})
    response = bedrock.invoke_model(modelId=MODEL_ID, body=body)
    return json.loads(response.get("body").read()).get("generation", "").strip()


def extraer_codigo_puro(texto):
    match = re.search(r"```java\s*([\s\S]*?)\s*```", texto)
    return match.group(1).strip() if match else texto.strip()


def normalizar_ruta_archivo(arch):
    ruta = arch.replace("\\", "/").lstrip("./")
    return "/" + ruta


def limpiar_mermaid_base(texto, node_spacing=80, rank_spacing=120, font_size="14px"):
    texto = texto.replace("```mermaid", "").replace("```", "").strip()
    texto = re.sub(
        r"^\s*(graph|flowchart)\s+(TD|TB|LR|RL)\s*",
        "",
        texto,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    texto = re.sub(r"-+>>+|-+>+|=+>+", "-->", texto)
    texto = re.sub(r"--\s*[^-\n]+?\s*-->", "-->", texto)
    texto = re.sub(r"\|.*?\|", "", texto)

    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N",
    }

    for k, v in reemplazos.items():
        texto = texto.replace(k, v)

    texto = texto.replace(chr(39), "").replace(chr(34), "")

    header = f"""%%{{init: {{
  "theme": "base",
  "flowchart": {{
    "defaultRenderer": "elk",
    "nodeSpacing": {node_spacing},
    "rankSpacing": {rank_spacing},
    "curve": "basis",
    "padding": 20
  }},
  "themeVariables": {{
    "primaryColor": "#004481",
    "primaryTextColor": "#ffffff",
    "lineColor": "#043263",
    "fontSize": "{font_size}"
  }}
}}}}%%
flowchart LR
"""
    return header + texto


def limpiar_mermaid_detallado(texto):
    return limpiar_mermaid_base(texto, node_spacing=120, rank_spacing=180, font_size="13px")


def procesar_texto_ia(texto_ia, lista_archivos):
    lineas = texto_ia.split("\n")

    while lineas and not (
        lineas[0].startswith("#")
        or lineas[0].startswith("**")
        or "|" in lineas[0]
        or lineas[0].startswith("1.")
    ):
        lineas.pop(0)

    t = "\n".join(lineas).strip()

    placeholder_md = (
        "[https://github.com/hexaforce66/codigosCobol/blob/main/NOMBRE_REAL]"
        "(https://github.com/hexaforce66/codigosCobol/blob/main/NOMBRE_REAL)"
    )
    placeholder_ver_codigo = (
        "[Ver Código](https://github.com/hexaforce66/codigosCobol/blob/main/NOMBRE_REAL)"
    )

    for arch in lista_archivos:
        ruta_limpia = normalizar_ruta_archivo(arch)
        nombre = os.path.basename(arch)
        link_real = f"[Ver Código]({SOURCE_REPO_URL}{ruta_limpia})"

        t = t.replace(placeholder_md, link_real)
        t = t.replace(placeholder_ver_codigo, link_real)
        t = t.replace(f"[Ver Código]({SOURCE_REPO_URL}/{nombre})", link_real)
        t = t.replace(f"({SOURCE_REPO_URL}/{nombre})", f"({SOURCE_REPO_URL}{ruta_limpia})")
        t = re.sub(
            rf"\[([^\]]*{re.escape(nombre)}[^\]]*)\]\({re.escape(SOURCE_REPO_URL)}/{re.escape(nombre)}\)",
            rf"[\1]({SOURCE_REPO_URL}{ruta_limpia})",
            t,
        )
        t = t.replace(arch.replace("\\", "/"), ruta_limpia)

    return t


def mermaid_img_url(code):
    data = {"code": code, "mermaid": {"theme": "default"}}
    compressed = zlib.compress(json.dumps(data).encode("utf-8"), level=9)
    b64 = base64.urlsafe_b64encode(compressed).decode("utf-8").rstrip("=")
    return f"https://mermaid.ink/img/pako:{b64}"


def scan_legacy_files():
    extensiones_legacy = (".CBL", ".CPY", ".COB", ".JCL")
    archivos_repo = []

    for root, _, files in os.walk("."):
        if ".git" in root or "modernized" in root or "repo_destino" in root:
            continue
        for file in files:
            if file.upper().endswith(extensiones_legacy):
                archivos_repo.append(os.path.join(root, file))

    return sorted(archivos_repo)


def publish_to_github():
    if not GITHUB_TOKEN or not REPO_NAME:
        print("⚠️ GITHUB_TOKEN o REPO_NAME no configurado. Se omite push a GitHub.")
        return

    if os.path.exists("repo_destino"):
        shutil.rmtree("repo_destino")

    run(f"git clone https://{GITHUB_TOKEN}@{REPO_NAME} repo_destino")
    run("cp -r modernized/* repo_destino/")
    run("git config user.email 'lego-bot@aws.com'", cwd="repo_destino")
    run("git config user.name 'Lego AI Modernizer'", cwd="repo_destino")
    run("git checkout -b modernization/$(date +%Y%m%d-%H%M%S)", cwd="repo_destino")
    run("git add .", cwd="repo_destino")
    run("git commit -m 'Modernización Pro'", cwd="repo_destino", allow_fail=True)
    run("git push origin HEAD", cwd="repo_destino", allow_fail=True)


def publish_to_confluence():
    if not all([CONFLUENCE_URL, CONFLUENCE_USER, CONFLUENCE_API_TOKEN, SPACE_KEY, PARENT_PAGE_ID]):
        print("⚠️ Variables de Confluence incompletas. Se omite publicación.")
        return

    readmes = []
    for root, _, files in os.walk("modernized"):
        for file in files:
            if file == "README.md":
                readmes.append(os.path.join(root, file))

    for md_path in readmes:
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()

        def replace_mermaid(match):
            mermaid_code = match.group(1).strip()
            url = mermaid_img_url(mermaid_code)
            return f'<br/><img src="{url}" alt="BPMN" style="max-width:100%; height:auto;"/><br/>'

        text = re.sub(r"```mermaid([\s\S]*?)```", replace_mermaid, text)
        html = markdown.markdown(text, extensions=["tables", "fenced_code"])

        titulo = f"Reporte AI - {os.path.basename(os.path.dirname(md_path))} - {time.strftime('%H:%M')}"

        payload = {
            "type": "page",
            "title": titulo,
            "space": {"key": SPACE_KEY},
            "ancestors": [{"id": PARENT_PAGE_ID}],
            "body": {"storage": {"value": html, "representation": "storage"}},
        }

        r = requests.post(
            CONFLUENCE_URL,
            auth=(CONFLUENCE_USER, CONFLUENCE_API_TOKEN),
            json=payload,
        )

        print(f"Status Confluence: {r.status_code} | Reporte: {titulo}")


def main():
    print("🚀 LEGO Modernizer v3.20 - Original Prompts + 2 BPMN")

    archivos_repo = scan_legacy_files()
    if not archivos_repo:
        raise RuntimeError("No se encontraron archivos .CBL, .COB, .CPY o .JCL")

    archivos_visibles = [normalizar_ruta_archivo(a) for a in archivos_repo]
    archivos_str = ", ".join(archivos_visibles)
    archivos_bpmn = [os.path.basename(a) for a in archivos_repo]
    archivos_bpmn_str = ", ".join(archivos_bpmn)

    codigo_completo = ""
    calls_detectados = set()
    copybooks_detectados = set()
    jcl_programas = set()
    datasets_jcl = set()
    dd_names = set()

    for archivo in archivos_repo:
        with open(archivo, "r", errors="ignore") as f:
            c = f.read()

        upper_c = c.upper()
        codigo_completo += f"\n--- ARCHIVO: {normalizar_ruta_archivo(archivo)} ---\n{c}\n"

        calls_detectados.update(re.findall(r"CALL\s+['\"]?([A-Z0-9_-]+)['\"]?", upper_c))
        copybooks_detectados.update(re.findall(r"\bCOPY\s+([A-Z0-9_-]+)", upper_c))
        jcl_programas.update(re.findall(r"EXEC\s+PGM=([A-Z0-9_-]+)", upper_c))
        datasets_jcl.update(re.findall(r"DSN=([A-Z0-9_.-]+)", upper_c))
        dd_names.update(re.findall(r"//([A-Z0-9_-]+)\s+DD\s+", upper_c))

    dependencias_detectadas = f"""
## Dependencias técnicas detectadas automáticamente

- Programas ejecutados por JCL: {", ".join(sorted(jcl_programas)) or "No detectados"}
- Subprogramas llamados por COBOL: {", ".join(sorted(calls_detectados)) or "No detectados"}
- Copybooks referenciados: {", ".join(sorted(copybooks_detectados)) or "No detectados"}
- DD names detectados en JCL: {", ".join(sorted(dd_names)) or "No detectados"}
- Datasets / archivos JCL: {", ".join(sorted(datasets_jcl)) or "No detectados"}
- Archivos incluidos en el análisis: {", ".join(archivos_visibles) or "No detectados"}
"""

    contexto_legacy = dependencias_detectadas + "\n\n" + codigo_completo
    dependencias_bpmn = f"""
## Dependencias técnicas detectadas automáticamente

- Programas ejecutados por JCL: {", ".join(sorted(jcl_programas)) or "No detectados"}
- Subprogramas llamados por COBOL: {", ".join(sorted(calls_detectados)) or "No detectados"}
- Copybooks referenciados: {", ".join(sorted(copybooks_detectados)) or "No detectados"}
- DD names detectados en JCL: {", ".join(sorted(dd_names)) or "No detectados"}
- Archivos incluidos en el análisis: {archivos_bpmn_str or "No detectados"}
"""

contexto_bpmn = dependencias_bpmn + "\n\n" + codigo_completo

    instruccion_directa = (
        "REGLA CRÍTICA: Responde DIRECTAMENTE con el contenido útil. "
        "NO saludes ni uses preámbulos tipo 'Claro'."
    )

    interpreter_prompt = (
        f"{instruccion_directa}\n"
        "Actúa como un Consultor Senior de Negocio Bancario. Tu tarea es explicar este sistema legacy.\n\n"
        "1. **OBJETIVO PRINCIPAL**: Función crítica en el banco.\n"
        "2. **FLUJO FUNCIONAL**: Proceso en 3 pasos clave.\n"
        "3. **VALOR DE NEGOCIO**: Riesgo operativo e impacto."
    )

    dependency_prompt = (
        "Actúa como un Analista Senior de Sistemas Mainframe. "
        "Analiza el sistema completo compuesto por JCL, COBOL y COPYBOOKS.\n\n"
        "Tu objetivo es reconstruir la arquitectura legacy del proceso.\n\n"
        "Genera estas secciones:\n"
        "1. **Programa principal**: identifica qué programa inicia el flujo y desde dónde se ejecuta.\n"
        "2. **Sistemas relacionados**: genera tabla Markdown "
        "| Archivo | Tipo | Detalle | Link | usando estos paths limpios: "
        f"{archivos_str}. "
        f"En Link usa [Ver Código]({SOURCE_REPO_URL}/PATH_REAL), reemplazando PATH_REAL por el path limpio real, por ejemplo /cobol/PROGRAMA.cbl o /jcl/JOB.jcl.\n"
        "3. **Mapa de dependencias**: tabla Markdown "
        "| Tipo | Nombre | Usado por | Propósito | Dependencias |.\n"
        "4. **Flujo batch JCL**: explica qué hace el JCL, qué programa ejecuta y qué archivos usa.\n"
        "5. **Flujo funcional consolidado**: explica el proceso end-to-end en lenguaje de negocio.\n"
        "6. **Riesgos técnicos**: dependencias críticas, copybooks compartidos, archivos sensibles o puntos de fallo.\n\n"
        "REGLA: No generes Java ni pruebas. Solo reconstruye el sistema legacy."
    )

    logic_prompt = (
        "Eres un experto en Ingeniería Inversa de Sistemas Bancarios. Tu misión es documentar la lógica de este sistema legacy.\n\n"
        "Genera un reporte con estas secciones:\n\n"
        "1. **REGLAS DE NEGOCIO**: Lista las políticas bancarias identificadas.\n"
        "2. **MATRIZ DE DECISIONES Y FÓRMULAS**:\n"
        "   - Si hay lógicas de 'Si ocurre A y B, entonces haz C', represéntalas en una tabla.\n"
        "   - Si hay cálculos (COMPUTE/MULTIPLY/ADD/SUBTRACT/DIVIDE), extrae la fórmula matemática clara.\n"
        "3. **MAPEO DE COMPONENTES**: Crea una tabla que relacione JCL, programas COBOL, copybooks y reglas de negocio.\n\n"
        "REGLA DE ORO: Usa términos de negocio. No menciones Java. No menciones SQL. Enfócate en la inteligencia del negocio."
    )

    glossary_prompt = (
        "Analiza la DATA DIVISION, WORKING-STORAGE SECTION, LINKAGE SECTION y COPYBOOKS del sistema.\n"
        "Genera un Diccionario de Datos Bancarios en una tabla Markdown con las siguientes columnas:\n"
        "- **Variable COBOL**: Nombre original del campo.\n"
        "- **Archivo origen**: Archivo donde aparece.\n"
        "- **Concepto de Negocio**: Nombre claro y amigable.\n"
        "- **Formato**: Longitud y tipo (Numérico, Alfanumérico, Decimal).\n"
        "- **Definición**: Explicación breve de su función en el negocio bancario.\n\n"
        "REGLA: Excluye variables técnicas de control (como contadores, índices de bucles o interruptores de fin de archivo) "
        "a menos que contengan lógica de negocio (como códigos de error)."
    )

    bpmn_ejecutivo_prompt = (
        "Actúa como un Arquitecto de Procesos BPMN. Representa el flujo lógico del sistema legacy en Mermaid.\n\n"
        "REGLAS CRÍTICAS:\n"
        "1. Usa 'flowchart LR'.\n"
        "2. Máximo 14 nodos principales. Agrupa pasos menores.\n"
        "3. Usa nombres cortos de negocio, máximo 4 palabras por nodo.\n"
        "4. Usa rectángulos A[Accion] y rombos B{Decision}.\n"
        "5. Usa solo flechas '-->'. No uses etiquetas en flechas.\n"
        "6. Si hay JCL, COBOL principal y subprogramas, usa subgraph para agruparlos.\n"
        "7. Dentro de cada subgraph usa 'direction TB'.\n"
        "8. No incluyas código técnico ni nombres de párrafos COBOL.\n"
        "9. El flujo debe mostrar el proceso end-to-end: entrada batch, validaciones, decisiones y salida.\n"
        "10. Evita nodos largos.\n\n"
        "REGLA DE ORO: Devuelve ÚNICAMENTE Mermaid válido, sin explicación."
    )

    bpmn_detallado_prompt = (
        "Actúa como un Arquitecto Mainframe y BPMN Senior. "
        "Representa el flujo DETALLADO del sistema legacy en Mermaid.\n\n"
        "OBJETIVO:\n"
        "Mapear cada proceso relevante del sistema: JCL, programa principal, subprogramas, copybooks, validaciones, decisiones, archivos de entrada y salida.\n\n"
        "REGLAS:\n"
        "1. Usa 'flowchart LR'.\n"
        "2. Usa subgraph para cada bloque: JCL, Programa Principal, Subprogramas, Copybooks, Archivos.\n"
        "3. Dentro de cada subgraph usa 'direction TB'.\n"
        "4. Incluye cada CALL detectado como nodo o subgraph.\n"
        "5. Incluye cada COPYBOOK relevante como nodo conectado al programa que lo usa.\n"
        "6. Incluye archivos de entrada/salida del JCL como nodos.\n"
        "7. Incluye decisiones de negocio como rombos B{Decision}.\n"
        "8. Incluye acciones como rectángulos A[Accion].\n"
        "9. No uses etiquetas en flechas. Solo '-->'.\n"
        "10. Usa nombres cortos pero específicos.\n"
        "11. No limites el diagrama a 12 nodos. Prioriza completitud.\n"
        "12. Evita texto largo en nodos. Máximo 5 palabras.\n\n"
        "ESTRUCTURA ESPERADA:\n"
        "subgraph JCL\n"
        "direction TB\n"
        "A[Leer parametros]\n"
        "B[Ejecutar programa]\n"
        "end\n\n"
        "subgraph Programa_Principal\n"
        "direction TB\n"
        "C[Leer registro]\n"
        "D{Registro valido?}\n"
        "end\n\n"
        "REGLA DE ORO: Devuelve ÚNICAMENTE Mermaid válido, sin explicación."
    )

    java_modular_prompt = (
        "Actúa como un Arquitecto Java Senior experto en migración COBOL a Java 17.\n\n"
        "OBJETIVO:\n"
        "Generar código Java funcionalmente equivalente al COBOL analizado.\n\n"
        "REGLAS CRÍTICAS:\n"
        "1. El código debe compilar en Java 17.\n"
        "2. Cada bloque ```java``` debe contener UNA SOLA clase, record, enum o interface pública.\n"
        "3. No pongas varias clases public en un mismo archivo.\n"
        "4. Incluye package com.bbva.modernizer; en cada clase.\n"
        "5. Incluye todos los imports necesarios.\n"
        "6. No uses Spring, @Service, @Autowired, repositories ni frameworks si no generas también sus clases.\n"
        "7. No uses métodos genéricos como isValid(), process() o validate() sin implementar lógica real.\n"
        "8. Cada IF, EVALUATE, PERFORM, COMPUTE, ADD, SUBTRACT, MULTIPLY o DIVIDE relevante del COBOL debe reflejarse en Java.\n"
        "9. Cada código de retorno, flag, estado o resultado COBOL debe modelarse como enum o constante.\n"
        "10. Usa exactamente los valores COBOL originales cuando existan, por ejemplo A/B/C, Y/N, L/M/H, no los traduzcas a ACTIVE/BLOCKED salvo que el COBOL lo use así.\n"
        "11. No inventes reglas que no estén en el COBOL o en las reglas detectadas.\n"
        "12. No omitas reglas por simplicidad.\n\n"
        "ARQUITECTURA:\n"
        "1. Genera un orquestador principal para el flujo principal.\n"
        "2. Genera una clase Java por cada subprograma COBOL detectado mediante CALL.\n"
        "3. Convierte COPYBOOKS, DATA DIVISION y LINKAGE SECTION en records o DTOs.\n"
        "4. Si hay JCL, genera un BatchOrchestrator simple que simule lectura, proceso y escritura.\n"
        "5. Separa validaciones, cálculos, reglas y logging en clases distintas.\n\n"
        "VALIDACIÓN FUNCIONAL:\n"
        "1. Implementa explícitamente validaciones de campos obligatorios.\n"
        "2. Implementa estados, flags, importes, límites, saldos, monedas y cálculos tal como aparezcan en COBOL.\n"
        "3. Implementa todos los caminos de aprobación, rechazo, error o revisión detectados.\n"
        "4. Si una regla no puede implementarse por falta de información, crea un método TODO con comentario claro, pero no inventes comportamiento.\n\n"
        "SALIDA:\n"
        "Devuelve únicamente bloques ```java ... ```.\n"
        "Cada bloque debe ser una clase/record/enum independiente y compilable."
    )

    test_modular_prompt = (
        "Actúa como un Ingeniero QA Senior experto en validación de migraciones COBOL a Java.\n\n"
        "OBJETIVO:\n"
        "Generar tests JUnit 5 que validen que el Java replica la lógica COBOL.\n\n"
        "REGLAS:\n"
        "1. Usa package com.bbva.modernizer; en cada test.\n"
        "2. Incluye imports de JUnit 5.\n"
        "3. No generes tests vacíos.\n"
        "4. No uses Mockito salvo que sea estrictamente necesario.\n"
        "5. No mockees reglas internas; prueba la lógica real.\n"
        "6. Cada regla de negocio detectada debe tener al menos un test.\n"
        "7. Cada código de retorno, flag o resultado debe tener al menos un test.\n"
        "8. Incluye flujo feliz, errores y casos borde.\n"
        "9. Los constructores usados en tests deben coincidir con las clases Java generadas.\n\n"
        "SALIDA:\n"
        "Devuelve únicamente bloques ```java ... ```."
    )

    gherkin_modular_prompt = (
        "Genera escenarios Gherkin EXHAUSTIVOS que cubran el flujo de negocio INTEGRADO.\n\n"
        "Considera la interacción entre JCL, programa principal, subprogramas COBOL, copybooks y archivos de entrada/salida.\n"
        "Incluye:\n"
        "1) Flujo feliz.\n"
        "2) Casos de borde.\n"
        "3) Casos de error.\n"
        "4) Escenarios donde una validación rechaza la operación.\n"
        "5) Escenarios batch de entrada y salida.\n\n"
        "Usa Background y Scenario Outline con Examples. Devuelve ÚNICAMENTE el bloque ```gherkin ... ```."
    )

    prompt_eval_modular = (
        "Genera EXCLUSIVAMENTE una tabla Markdown. NO añadas texto introductorio ni conclusiones.\n"
        "Formato: | Funcionalidad | Fiabilidad (%) | Cobertura (%) | Calidad (%) | Notas Justificativas |\n"
        "| --- | --- | --- | --- | --- |\n"
        "REGLA DE ORO PARA NOTAS: Redacta para perfiles de Negocio. "
        "En lugar de 'alta complejidad ciclomática', escribe 'código difícil de modificar'. "
        "En lugar de 'falta de inyección de dependencias', escribe 'arquitectura rígida que dificulta futuras actualizaciones'. "
        "Enfócate en riesgos, mantenibilidad y beneficios de negocio.\n"
        "ESPECÍFICO MODULAR: Evalúa si el Java generado replica la lógica COBOL. "
        "Penaliza si hay métodos genéricos sin implementación, clases que no compilan, reglas de negocio omitidas o códigos de retorno no implementados. "
        "Evalúa trazabilidad COBOL -> regla -> Java -> test."
    )

    print("🧠 Generando resumen...")
    interp = procesar_texto_ia(
        call_agent("Consultor Senior", interpreter_prompt, contexto_legacy),
        archivos_repo,
    )

    print("🧩 Reconstruyendo arquitectura legacy...")
    legacy_map = procesar_texto_ia(
        call_agent("Analista Mainframe", dependency_prompt, contexto_legacy),
        archivos_repo,
    )

    print("📋 Extrayendo reglas...")
    logic = call_agent("Arquitecto Legacy", logic_prompt, contexto_legacy)

    print("📖 Generando diccionario...")
    gloss = call_agent("Analista", glossary_prompt, contexto_legacy)

    print("🔄 Generando BPMN ejecutivo...")
    bpmn_ejecutivo = limpiar_mermaid_base(
        call_agent("BPMN Ejecutivo", bpmn_ejecutivo_prompt, contexto_bpmn),
        node_spacing=80,
        rank_spacing=120,
        font_size="14px",
    )

    print("🧬 Generando BPMN detallado...")
    bpmn_detallado = limpiar_mermaid_detallado(
        call_agent("BPMN Detallado", bpmn_detallado_prompt, contexto_bpmn)
    )

    contexto_java = f"""
REGLAS DE NEGOCIO DETECTADAS:
{logic}

DICCIONARIO DE DATOS:
{gloss}

DEPENDENCIAS:
{dependencias_detectadas}

CÓDIGO ORIGINAL:
{codigo_completo}
"""

    print("☕ Generando Java...")
    java_modular_raw = call_agent("Arquitecto Java", java_modular_prompt, contexto_java)
    clases_java = re.findall(r"```java\s*([\s\S]*?)\s*```", java_modular_raw)

    contexto_tests = f"""
REGLAS DE NEGOCIO DETECTADAS:
{logic}

JAVA GENERADO:
{java_modular_raw}

CÓDIGO ORIGINAL:
{codigo_completo}
"""

    print("🧪 Generando tests...")
    test_raw = call_agent("Ingeniero QA Senior", test_modular_prompt, contexto_tests)
    tests_java = re.findall(r"```java\s*([\s\S]*?)\s*```", test_raw)
    test = "\n\n".join(t.strip() for t in tests_java) if tests_java else test_raw.strip()

    print("🥒 Generando Gherkin...")
    gherkin = extraer_codigo_puro(
        call_agent("Especialista BDD Senior", gherkin_modular_prompt, contexto_legacy)
    )
    gherkin_clean = gherkin.replace("```gherkin", "").replace("```", "").strip()

    print("📊 Generando evaluación...")
    eval_tabla = call_agent(
        "Analista de Calidad Senior",
        prompt_eval_modular,
        java_modular_raw + "\n\n" + test + "\n\n" + gherkin_clean,
    )

    base = "modernized/sistema_consolidado"
    base_java = f"{base}/src/main/java/com/bbva/modernizer"

    os.makedirs(base_java, exist_ok=True)
    os.makedirs(f"{base}/src/test/java/com/bbva/modernizer", exist_ok=True)
    os.makedirs(f"{base}/src/test/resources/features", exist_ok=True)

    for idx, contenido_clase in enumerate(clases_java):
        nombre_match = re.search(r"(class|record|interface|enum)\s+(\w+)", contenido_clase)
        nombre_archivo = nombre_match.group(2) if nombre_match else f"ServicePart{idx}"
        with open(f"{base_java}/{nombre_archivo}.java", "w") as f:
            f.write(contenido_clase.strip())

    with open(f"{base}/src/test/java/com/bbva/modernizer/ModernizedSystemTest.java", "w") as f:
        f.write(test)

    with open(f"{base}/src/test/resources/features/sistema_consolidado.feature", "w") as f:
        f.write(gherkin_clean)

    with open(f"{base}/README.md", "w") as f:
        f.write(
            f"# 🚀 Reporte: SISTEMA CONSOLIDADO\n\n"
            f"## 🧠 Resumen del Programa\n{interp}\n\n"
            f"---\n\n"
            f"## 🧩 1. Arquitectura Legacy Detectada\n{legacy_map}\n\n"
            f"---\n\n"
            f"## 📖 2. Diccionario de Datos Bancarios\n{gloss}\n\n"
            f"---\n\n"
            f"## 📋 3. Especificación de Lógica y Reglas\n{logic}\n\n"
            f"---\n\n"
            f"## 🔄 4. Flujo Ejecutivo BPMN\n\n"
            f"Este diagrama muestra la visión resumida del proceso legacy.\n\n"
            f"```mermaid\n{bpmn_ejecutivo}\n```\n\n"
            f"---\n\n"
            f"## 🧬 4.1 Mapa Detallado de Procesos y Dependencias\n\n"
            f"Este diagrama muestra JCL, programas COBOL, CALLs, COPYBOOKS, validaciones y archivos.\n\n"
            f"```mermaid\n{bpmn_detallado}\n```\n\n"
            f"---\n\n"
            f"## 📊 5. Matriz de Calidad y Madurez\n{eval_tabla}\n\n"
            f"---\n\n"
            f"## 🧪 6. Escenarios Gherkin Generados\n\n"
            f"```gherkin\n{gherkin_clean}\n```\n"
        )

    print("📤 Publicando a GitHub...")
    publish_to_github()

    print("📝 Publicando a Confluence...")
    publish_to_confluence()

    print("✅ LEGO terminado correctamente")


if __name__ == "__main__":
    main()
