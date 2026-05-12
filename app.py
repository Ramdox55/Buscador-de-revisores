from flask import Flask, render_template, request

    for preferred_term, synonyms in synonym_dict.items():
        if normalized_kw == preferred_term or normalized_kw in synonyms:
            return preferred_term

    return normalized_kw


# Función para calcular la puntuación de coincidencia
def calculate_match_score(author_keywords_string, user_keywords_list):

    if pd.isna(author_keywords_string):
        return 0

    # Procesar palabras clave del autor
    author_keywords = [
        normalize_keyword_with_synonyms(kw, synonym_map)
        for kw in str(author_keywords_string).split(';')
        if kw.strip()
    ]

    total_match_count = 0

    for user_kw in user_keywords_list:
        # Buscar coincidencias parciales
        total_match_count += sum(
            1 for ak in author_keywords
            if user_kw in ak
        )

    return total_match_count


@app.route('/', methods=['GET', 'POST'])
def home():

    resultados = []

    if request.method == 'POST':

        # Obtener palabras clave del formulario
        user_paper_keywords_str = request.form['keywords']

        # Procesar palabras clave del usuario
        user_paper_keywords = [
            normalize_keyword_with_synonyms(kw, synonym_map)
            for kw in user_paper_keywords_str.split(',')
            if kw.strip()
        ]

        # Calcular puntuación
        indice['match_score'] = indice['Columna2'].apply(
            lambda x: calculate_match_score(x, user_paper_keywords)
        )

        # Filtrar resultados útiles
        resultados_df = indice[indice['match_score'] > 0]

        # Ordenar de mayor a menor coincidencia
        resultados_df = resultados_df.sort_values(
            by='match_score',
            ascending=False
        )

        # Convertir a diccionario para HTML
        resultados = resultados_df.to_dict(orient='records')

    return render_template(
        'index.html',
        resultados=resultados
    )


if __name__ == '__main__':
    app.run(debug=True)
