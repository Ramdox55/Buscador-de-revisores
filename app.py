from flask import Flask, render_template, request
    # Comparar cada palabra del usuario
    for user_kw in user_keywords_list:

        for author_kw in author_keywords:

            # Coincidencia exacta
            if user_kw == author_kw:
                total_match_count += 1

            # Coincidencia parcial
            elif user_kw in author_kw or author_kw in user_kw:
                total_match_count += 1

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
