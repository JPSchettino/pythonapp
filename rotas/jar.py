from base import app, session, redirect, url_for, pd, render_template, jsonify, request, base64, plt, np, os
from rotas.filemanager import *
from rotas.estrutura import *

@app.route('/JAR', methods=['GET', 'POST'])
def jar():
    if 'dataframe' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        data = request.json
        cat_1 = data['selectedVariable1']
        cat_2 = data['selectedVariable2']
        selected_categories = data['selectedCategories']
        df = pd.read_json(session['filtered_dataframe'])
        jar_columns = session.get('jar_vars', [])
        categories_order_colors = data['colors']
        cortitulo = data['colorTitulo']
        corsubtitulo = data['colorSubtitulo']
        corrotulo = data['colorRotulo']

        numeric_to_category = {
            1: "muito abaixo do ideal",
            2: "abaixo do ideal",
            3: "ideal",
            4: "acima do ideal",
            5: "muito acima do ideal",
        }
        legend_labels = {
            "muito abaixo do ideal": "Muito abaixo do ideal",
            "abaixo do ideal": "Abaixo do ideal",
            "ideal": "Ideal",
            "acima do ideal": "Acima do ideal",
            "muito acima do ideal": "Muito acima do ideal"
        }

        if cat_1 == "Nenhum" or not cat_1:
            product_names = [""]
        else:
            product_names = df[cat_1].unique() if cat_1 in df.columns else [""]
            if selected_categories:
                df = df[df[cat_1].isin(selected_categories)]
                product_names = [name for name in product_names if name in selected_categories]

        if cat_2 == "Nenhum" or not cat_2:
            age_groups = [""]
        else:
            age_groups = df[cat_2].unique() if cat_2 in df.columns else [""]

        columns_to_consider = [c for c in [cat_1, cat_2] if c != "Nenhum" and c in df.columns]
        df = df[columns_to_consider + jar_columns]

        num_products = len(product_names)
        num_age_groups = len(age_groups)

        fig, axes = plt.subplots(num_products * (num_age_groups + 1), len(jar_columns), figsize=(38, 38 * num_products))

        for p, product_name in enumerate(product_names):
            filtered_df = df if product_name == "" else df[df[cat_1] == product_name]

            for i, age_group in enumerate(age_groups):
                age_df = filtered_df if age_group == "" else filtered_df[filtered_df[cat_2] == age_group]

                for j, jar_column in enumerate(jar_columns):
                    if pd.api.types.is_numeric_dtype(age_df[jar_column]):
                        age_df[jar_column] = age_df[jar_column].map(numeric_to_category)

                    proportions = (
                        age_df[jar_column]
                        .str.lower()
                        .str.strip()
                        .value_counts(normalize=True)
                        .reindex(categories_order_colors.keys())
                        .fillna(0)
                    )

                    ax = axes[p * (len(age_groups) + 1) + i, j]
                    left = np.zeros(1)
                    for idx, (category, prop) in enumerate(proportions.items()):
                        color = categories_order_colors[category]
                        label = legend_labels.get(category, category) if p == 0 and i == 0 and j == 0 else None
                        ax.barh(0, prop, height=0.4, left=left, color=color, label=label)
                        left += prop

                        if p == 0 and i == 0 and j == 0:
                            legend = fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0.6), fancybox=True, shadow=True, ncol=5)
                            for text in legend.get_texts():
                                text.set_fontsize('xx-large')
                                text.set_fontname('Sora')
                            
                        if prop >= 0.05:
                            percentage = f"{prop * 100:.0f}%"
                            ax.text(left - prop / 2, 0, percentage, ha="center", va="center", fontsize=9.1 + prop * 10, fontweight='bold', color=corrotulo)

                        if i == 0 and j == len(jar_columns) // 2:
                            ax.annotate(product_name, xy=(0.5, 1.8), xycoords='axes fraction', ha='center', fontsize=17, fontweight='bold', color=cortitulo)

                    short_title = jar_column.split("_", 1)[-1]
                    ax.annotate(f"{short_title} - {age_group}", xy=(0.5, 1.2), xycoords='axes fraction', ha='center', fontsize=15, va='center', fontweight='bold', color=corsubtitulo)
                    ax.set_xlim(0, 1)
                    ax.set_yticks([])
                    ax.set_xticks([])

            for j in range(len(jar_columns)):
                ax = axes[(p + 1) * (len(age_groups) + 1) - 1, j]
                ax.axis('off')

        plt.subplots_adjust(left=0.1, bottom=0.6, right=0.9, top=0.7, wspace=0.4, hspace=0.6)

        fig.savefig('temp_plot.png', transparent=True, bbox_inches='tight')

        with open('temp_plot.png', 'rb') as f:
            image = base64.b64encode(f.read()).decode()
        os.remove('temp_plot.png')

        plt.rcParams['figure.figsize'] = [6.4, 4.8]

        filters = session.get('filters', {})
        filter_strings = []
        for key, value in filters.items():
            filter_value = ', '.join(value['values'])
            filter_strings.append(f'{key}: {filter_value}')
        filters_string = ', '.join(filter_strings)

        return jsonify({'corrgraf': image, 'filters_string': filters_string})

    else:
        return render_template('JAR.html')

@app.route('/get_categories', methods=['GET'])
def get_categories():
    variable = request.args.get('variable')
    df = pd.read_json(session['filtered_dataframe'])
    if variable and variable in df.columns:
        categories = df[variable].dropna().unique().tolist()
        return jsonify(categories)
    return jsonify([])

