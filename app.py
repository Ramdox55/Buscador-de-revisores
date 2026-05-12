from flask import Flask, render_template_string, request
import pandas as pd
import unicodedata

app = Flask(__name__)

# =====================================
# CARGAR EXCEL
# =====================================

indice = pd.read_excel("Autores Completo.xlsx")

# CAMBIA ESTOS NOMBRES
# POR LOS DE TU EXCEL

COLUMNA_NOMBRE = "author_name"
COLUMNA_KEYWORDS = "Columna2"
COLUMNA_CORREO = "Columna3"

# =====================================
# FUNCIONES
# =====================================

def remove_accents(input_str):

    if not isinstance(input_str, str):
        return ""

    processed = input_str.lower()

    processed = processed.replace("ñ", "__NY__")

    normalized = unicodedata.normalize("NFD", processed)

    without_accents = ''.join(
        c for c in normalized
        if unicodedata.category(c) != 'Mn'
    )

    final = without_accents.replace("__NY__", "ñ")

    return final


# SINÓNIMOS

synonym_map = {
    "marketing": ["mercadotecnia"],
    "educacion": ["enseñanza", "formacion"],
    "ia": ["inteligencia artificial"],
    "machine learning": ["aprendizaje automatico"]
}


def normalize_keyword(keyword):

    keyword = remove_accents(str(keyword).strip())

    for preferred, synonyms in synonym_map.items():

        if keyword == preferred:
            return preferred

        if keyword in synonyms:
            return preferred

    return keyword


# =====================================
# CALCULAR COINCIDENCIAS
# =====================================

def calculate_match_score(author_keywords_string, user_keywords):

    if pd.isna(author_keywords_string):
        return 0, [], []

    # Keywords originales
    original_keywords = [
        k.strip()
        for k in str(author_keywords_string).split(";")
        if k.strip()
    ]

    # Keywords normalizadas
    normalized_author_keywords = [
        normalize_keyword(k)
        for k in original_keywords
    ]

    matched_keywords_count = {}

    total_matches = 0

    # Comparar keywords
    for user_kw in user_keywords:

        for i, author_kw in enumerate(normalized_author_keywords):

            matched = False

            # Coincidencia exacta únicamente
            if user_kw.strip() == author_kw.strip():
                matched = True

            if matched:

                total_matches += 1

                original_word = original_keywords[i]

                # Contar coincidencias
                if original_word not in matched_keywords_count:
                    matched_keywords_count[original_word] = 1
                else:
                    matched_keywords_count[original_word] += 1

    # Lista bonita
    matched_keywords = [
        f"{kw} ({count})"
        for kw, count in matched_keywords_count.items()
    ]

    # Resto de keywords
    remaining_keywords = sorted([
        kw for kw in original_keywords
        if kw not in matched_keywords_count
    ])

    return total_matches, matched_keywords, remaining_keywords


# =====================================
# HTML
# =====================================

HTML = """

<!DOCTYPE html>
<html lang="es">

<head>

    <meta charset="UTF-8">

    <title>
        Buscador de Revisores
    </title>

    <style>

        body{
            font-family:'Segoe UI',sans-serif;
            background:linear-gradient(135deg,#0f172a,#1e293b);
            margin:0;
            padding:40px;
            color:#e2e8f0;
        }

        .container{
            max-width:1000px;
            margin:auto;
        }

        h1{
            text-align:center;
            margin-bottom:40px;
            color:white;
            font-size:42px;
        }

        .search-box{
            background:#111827;
            padding:25px;
            border-radius:18px;
            box-shadow:0 8px 24px rgba(0,0,0,0.35);
            margin-bottom:35px;
            border:1px solid #334155;
        }

        form{
            display:flex;
            gap:12px;
        }

        input{
            flex:1;
            padding:16px;
            border:none;
            border-radius:12px;
            background:#1e293b;
            color:white;
            font-size:16px;
            outline:none;
        }

        input::placeholder{
            color:#94a3b8;
        }

        button{
            padding:16px 26px;
            background:linear-gradient(135deg,#06b6d4,#3b82f6);
            color:white;
            border:none;
            border-radius:12px;
            cursor:pointer;
            font-size:16px;
            font-weight:bold;
            transition:0.2s;
        }

        button:hover{
            transform:translateY(-2px);
            opacity:0.95;
        }

        .resultado{
            background:#111827;
            border-radius:18px;
            padding:28px;
            margin-bottom:22px;
            box-shadow:0 8px 24px rgba(0,0,0,0.25);
            border:1px solid #334155;
        }

        .autor{
            font-size:28px;
            font-weight:700;
            margin-bottom:12px;
            color:white;
        }

        .ranking{
            display:flex;
            align-items:center;
            gap:10px;
            margin-bottom:18px;
        }

        .ranking-number{
            background:linear-gradient(135deg,#f59e0b,#f97316);
            color:white;
            width:42px;
            height:42px;
            border-radius:50%;
            display:flex;
            align-items:center;
            justify-content:center;
            font-weight:bold;
            font-size:18px;
            box-shadow:0 4px 12px rgba(249,115,22,0.4);
        }

        .ranking-text{
            color:#cbd5e1;
            font-size:15px;
            font-weight:600;
            letter-spacing:0.5px;
        }

        .badge{
            display:inline-block;
            background:linear-gradient(135deg,#22c55e,#16a34a);
            color:white;
            padding:8px 14px;
            border-radius:999px;
            font-size:14px;
            margin-bottom:20px;
            font-weight:bold;
        }

        .section-title{
            font-weight:bold;
            margin-top:18px;
            margin-bottom:10px;
            color:#cbd5e1;
            font-size:15px;
            text-transform:uppercase;
            letter-spacing:1px;
        }

        .keywords{
            line-height:2;
        }

        .matched{
            background:linear-gradient(135deg,#06b6d4,#3b82f6);
            color:white;
            padding:8px 12px;
            border-radius:999px;
            display:inline-block;
            margin:5px;
            font-size:14px;
            font-weight:500;
            box-shadow:0 4px 10px rgba(59,130,246,0.3);
        }

        details{
            margin-top:18px;
            background:#1e293b;
            border-radius:12px;
            padding:14px;
        }

        summary{
            cursor:pointer;
            color:#38bdf8;
            font-weight:bold;
            outline:none;
        }

        .other-keywords{
            margin-top:14px;
            color:#cbd5e1;
            line-height:1.8;
        }

        .empty{
            text-align:center;
            margin-top:50px;
            color:#94a3b8;
            font-size:18px;
        }

        #loading{
            display:none;
            margin-top:18px;
        }
        
        .loading-box{
            background:#1e293b;
            color:white;
            padding:14px;
            border-radius:12px;
            font-size:16px;
            text-align:center;
            border:1px solid #334155;
            animation:pulse 1s infinite;
        }

        @keyframes pulse{

            0%{
                opacity:0.5;
            }

            50%{
                opacity:1;
            }

            100%{
                opacity:0.5;
            }

        }

    </style>

</head>

<body>

    <div class="container">

        <h1>
            Buscador de Revisores
        </h1>

        <div class="search-box">

            <form method="POST" onsubmit="mostrarCarga()">

                <input
                    type="text"
                    name="keywords"
                    placeholder="Coloca las palabras clave separadas por coma. Ej: liderazgo, innovación, IA"
                >

                <button type="submit">
                    Buscar
                </button>

            </form>

        </div>

        <div id="loading">

            <div class="loading-box">
                Buscando coincidencias...
            </div>

        </div>

        {% if resultados is not none and resultados|length > 0 %}

            {% for autor in resultados %}

                {% set rank = loop.index %}

                <div class="resultado">

                    <div class="ranking">

                        <span class="ranking-number">
                            #{{ rank }}
                        </span>

                        <span class="ranking-text">
                            Coincidencia destacada
                        </span>

                    </div>

                    <div class="autor">
                        {{ autor[COLUMNA_NOMBRE] }}
                    </div>

                    <div class="badge">
                        {{ autor['match_score'] }} coincidencias
                    </div>

                    <div class="section-title">
                        Correo
                    </div>

                    <div>
                        {{ autor[COLUMNA_CORREO] }}
                    </div>

                    <div class="section-title">
                        Palabras coincidentes
                    </div>

                    <div class="keywords">

                        {% for kw in autor['matched_keywords'] %}

                            <span class="matched">
                                {{ kw }}
                            </span>

                        {% endfor %}

                    </div>

                    <details>

                        <summary>
                            Ver resto de palabras clave
                        </summary>

                        <div class="other-keywords">

                            {{ autor['remaining_keywords'] | join(', ') }}

                        </div>

                    </details>

                </div>

            {% endfor %}

        {% elif resultados is not none %}

            <div class="empty">

                No se encontraron coincidencias para esa búsqueda.

            </div>

        {% endif %}

    </div>

    <script>

        function mostrarCarga(){

            document.getElementById("loading").style.display = "block";

        }

    </script>

</body>

</html>

"""

# =====================================
# RUTA PRINCIPAL
# =====================================

@app.route("/", methods=["GET", "POST"])
def home():

    resultados = None

    if request.method == "POST":

        texto_busqueda = request.form["keywords"]

        # Procesar keywords del usuario
        user_keywords = [
            normalize_keyword(k)
            for k in texto_busqueda.split(",")
            if k.strip()
        ]

        # Calcular resultados
        indice[[
            "match_score",
            "matched_keywords",
            "remaining_keywords"
        ]] = indice[COLUMNA_KEYWORDS].apply(
            lambda x: pd.Series(
                calculate_match_score(x, user_keywords)
            )
        )

        # Filtrar
        resultados_df = indice[
            indice["match_score"] > 0
        ]

        # Ordenar
        resultados_df = resultados_df.sort_values(
            by="match_score",
            ascending=False
        )

        resultados = resultados_df.to_dict(
            orient="records"
        )

    return render_template_string(
        HTML,
        resultados=resultados,
        COLUMNA_NOMBRE=COLUMNA_NOMBRE,
        COLUMNA_KEYWORDS=COLUMNA_KEYWORDS,
        COLUMNA_CORREO=COLUMNA_CORREO
    )

# =====================================
# EJECUTAR
# =====================================

if __name__ == "__main__":
    app.run(debug=True)
