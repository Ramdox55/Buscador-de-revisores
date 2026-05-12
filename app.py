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
        return 0

    # Separar keywords del autor
    author_keywords = [
        normalize_keyword(k)
        for k in str(author_keywords_string).split(";")
        if k.strip()
    ]

    total_matches = 0

    # Comparar TODAS las palabras
    for user_kw in user_keywords:

        for author_kw in author_keywords:

            # Coincidencia exacta
            if user_kw == author_kw:
                total_matches += 1

            # Coincidencia parcial
            elif user_kw in author_kw:
                total_matches += 1

            elif author_kw in user_kw:
                total_matches += 1

    return total_matches


# =========================
# HTML
# =========================

HTML = """

<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Buscador de Revisores</title>

    <style>

        body{
            font-family: Arial;
            margin:40px;
        }

        input{
            width:500px;
            padding:10px;
        }

        button{
            padding:10px;
        }

        .resultado{
            border:1px solid #ccc;
            padding:15px;
            margin-top:20px;
        }

    </style>

</head>

<body>

    <h1>Buscador de Revisores</h1>

    <form method="POST">

        <input
            type="text"
            name="keywords"
            placeholder="Coloca las palabras clave separadas por com. Ej: liderazgo, innovación, IA"
        >

        <button type="submit">
            Buscar
        </button>

    </form>

    {% if resultados %}

        <h2>Resultados</h2>

        {% for autor in resultados %}

            <div class="resultado">

                <h3>
                    {{ autor[COLUMNA_NOMBRE] }}
                </h3>

                <p>
                    <strong>Correo:</strong>
                    {{ autor[COLUMNA_CORREO] }}
                </p>

                <p>
                    <strong>Palabras clave:</strong>
                    {{ autor[COLUMNA_KEYWORDS] }}
                </p>

                <p>
                    <strong>Coincidencias:</strong>
                    {{ autor['match_score'] }}
                </p>

            </div>

        {% endfor %}

    {% endif %}

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
        indice["match_score"] = indice[COLUMNA_KEYWORDS].apply(
            lambda x: calculate_match_score(x, user_keywords)
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
