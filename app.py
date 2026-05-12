from flask import Flask, render_template_string, request
import pandas as pd
import unicodedata

app = Flask(__name__)

# =========================
# CARGAR EXCEL
# =========================

indice = pd.read_excel("Autores Completo.xlsx")

# IMPORTANTE:
# Ajusta estos nombres EXACTAMENTE
# como aparecen en tu Excel.

COLUMNA_NOMBRE = "author_name"
COLUMNA_KEYWORDS = "Columna2"
COLUMNA_CORREO = "Columna3"


# =========================
# FUNCIONES
# =========================

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


# Diccionario de sinónimos
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

            # Coincidencia exacta
            if user_kw == author_kw:
                matched = True

            # Coincidencia parcial
            elif user_kw in author_kw:
                matched = True

            elif author_kw in user_kw:
                matched = True

            if matched:

                total_matches += 1

                original_word = original_keywords[i]

                # Contar coincidencias
                if original_word not in matched_keywords_count:
                    matched_keywords_count[original_word] = 1
                else:
                    matched_keywords_count[original_word] += 1

    # Convertir a lista bonita
    matched_keywords = [
        f"{kw} ({count})"
        for kw, count in matched_keywords_count.items()
    ]

    # Resto de palabras
    remaining_keywords = sorted([
        kw for kw in original_keywords
        if kw not in matched_keywords_count
    ])

    return total_matches, matched_keywords, remaining_keywords

# =========================
# HTML
# =========================

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
            font-family: Arial, sans-serif;
            background-color:#f4f6f9;
            margin:0;
            padding:40px;
            color:#333;
        }

        .container{
            max-width:1000px;
            margin:auto;
        }

        h1{
            text-align:center;
            margin-bottom:40px;
            color:#1f2937;
        }

        .search-box{
            background:white;
            padding:25px;
            border-radius:12px;
            box-shadow:0px 4px 12px rgba(0,0,0,0.08);
            margin-bottom:30px;
        }

        form{
            display:flex;
            gap:10px;
        }

        input{
            flex:1;
            padding:14px;
            border:1px solid #ccc;
            border-radius:8px;
            font-size:16px;
        }

        button{
            padding:14px 24px;
            background:#2563eb;
            color:white;
            border:none;
            border-radius:8px;
            cursor:pointer;
            font-size:16px;
            font-weight:bold;
        }

        button:hover{
            background:#1d4ed8;
        }

        .resultado{
            background:white;
            border-radius:12px;
            padding:24px;
            margin-bottom:20px;
            box-shadow:0px 4px 10px rgba(0,0,0,0.06);
        }

        .autor{
            font-size:24px;
            font-weight:bold;
            margin-bottom:10px;
            color:#111827;
        }

        .badge{
            display:inline-block;
            background:#dbeafe;
            color:#1d4ed8;
            padding:6px 12px;
            border-radius:20px;
            font-size:14px;
            margin-bottom:15px;
            font-weight:bold;
        }

        .section-title{
            font-weight:bold;
            margin-top:15px;
            margin-bottom:8px;
            color:#374151;
        }

        .keywords{
            line-height:1.8;
        }

        .matched{
            background:#dcfce7;
            color:#166534;
            padding:6px 10px;
            border-radius:16px;
            display:inline-block;
            margin:4px;
            font-size:14px;
        }

        .other-keywords{
            color:#555;
            margin-top:10px;
        }

        details{
            margin-top:15px;
        }

        summary{
            cursor:pointer;
            color:#2563eb;
            font-weight:bold;
        }

        .empty{
            text-align:center;
            margin-top:40px;
            color:#666;
        }

    </style>

</head>

<body>

    <div class="container">

        <h1>
            Buscador de Revisores
        </h1>

        <div class="search-box">

            <form method="POST">

                <input
                    type="text"
                    name="keywords"
                    placeholder="Ej: liderazgo, innovación, IA"
                >

                <button type="submit">
                    Buscar
                </button>

            </form>

        </div>

        {% if resultados %}

            {% for autor in resultados %}

                <div class="resultado">

                    <div class="autor">
                        {{ autor[COLUMNA_NOMBRE] }}
                    </div>

                    <div class="badge">
                        {{ autor['match_score'] }} coincidencias
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

        {% else %}

            <div class="empty">

                Realiza una búsqueda para ver resultados.

            </div>

        {% endif %}

    </div>

</body>

</html>

"""


# =========================
# RUTA PRINCIPAL
# =========================

@app.route("/", methods=["GET", "POST"])
def home():

    resultados = []

    if request.method == "POST":

        texto_busqueda = request.form["keywords"]

        # Separar keywords del usuario
        user_keywords = [
            normalize_keyword(k)
            for k in texto_busqueda.split(",")
            if k.strip()
        ]

        # Calcular puntuación
        indice[[
            "match_score",
            "matched_keywords",
            "remaining_keywords"
        ]] = indice[COLUMNA_KEYWORDS].apply(
            lambda x: pd.Series(
                calculate_match_score(x, user_keywords)
            )
        )

        # Filtrar resultados útiles
        resultados_df = indice[
            indice["match_score"] > 0
        ]

        # Ordenar
        resultados_df = resultados_df.sort_values(
            by="match_score",
            ascending=False
        )

        # Convertir a lista
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


# =========================
# EJECUTAR
# =========================

if __name__ == "__main__":
    app.run(debug=True)
