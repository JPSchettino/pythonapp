from base import app, session, redirect, url_for, pd, render_template, jsonify, request, base64, plt,np, os
from rotas.filemanager import *
from rotas.estrutura import *


@app.route('/JAR', methods=['GET', 'POST'])
def jar():
    if 'dataframe' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':

        selected_variables = request.json
        cat_1 = selected_variables[0]
        cat_2 = selected_variables[1]
        df = pd.read_json(session['filtered_dataframe'])
        jar_columns = session.get('jar_vars', [])
        print(jar_columns)
        # Ordem das categorias e suas cores
        categories_order_colors = selected_variables[2]
        cortitulo = selected_variables[3]
        corsubtitulo = selected_variables[4]
        corrotulo = selected_variables[5]
        print(categories_order_colors)

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
        product_names = df[cat_1].unique()
        print(product_names)
        age_groups = df[cat_2].unique()
        print(age_groups)

        num_products = len(product_names)


        df = df[[cat_1, cat_2] + jar_columns]


        num_products = len(product_names)
        num_age_groups = len(age_groups)

        fig, axes = plt.subplots(num_products * (num_age_groups + 1), len(jar_columns), figsize=(38, 38 * num_products))
        #fig.annotate(product_name, (0, (p + 1) / num_products - 0.05), xycoords='figure fraction', ha='left', fontsize=15, fontweight='bold')
        
        # Criando os gráficos para cada coluna JAR e faixa etária
        # Para cada produto na lista, crie gráficos
        for p, product_name in enumerate(product_names):
            
            # Filtra os dados do dataframe
            filtered_df = df[df[cat_1] == product_name]
            
            #print(filtered_df)
            

            # Criando os gráficos para cada coluna JAR e faixa etária
            for i, age_group in enumerate(age_groups):
                age_df = filtered_df[filtered_df[cat_2] == age_group]
                

                for j, jar_column in enumerate(jar_columns):
                    # If the column is numeric, map the numbers to categories
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
                        label = legend_labels.get(category, category) if p == 0 and i == 0 and j == 0 and isinstance(category, str) else None
                        ax.barh(0, prop, height=0.4, left=left, color=color, label=label)
                        left += prop

                        # Adicionar a legenda apenas na primeira iteração
                        if p == 0 and i == 0 and j == 0:
                            #fig.legend(loc='upper center', bbox_to_anchor=(0.125, 0.74), fancybox=True, shadow=True)
                            legend = fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0.6), fancybox=True, shadow=True,ncol=5)
                            for text in legend.get_texts():
                                text.set_fontsize('xx-large')  # altera o tamanho da fonte
                                text.set_fontname('Sora')  # altera a fonte
                            
                        # Mostrar a porcentagem se for maior que 5%
                        if prop >= 0.05:
                            percentage = f"{prop * 100:.0f}%"
                            ax.text(left - prop / 2, 0, percentage, ha="center", va="center", fontsize=9.1+prop*10, fontweight='bold',color = corrotulo)

                        if i == 0 and j == len(jar_columns) // 2:
                            ax.annotate(product_name, xy=(0.5, 1.8), xycoords='axes fraction', ha='center', fontsize=17, fontweight='bold', color=cortitulo)

                    # Remover o que está antes do "_" e o próprio "_"
                    short_title = jar_column.split("_", 1)[-1]
                    #subtitle = ax.set_title(f"{short_title} - {age_group} - {product_name}", fontsize=10)
                    ax.annotate(f"{short_title} - {age_group}", xy=(0.5, 1.2), xycoords='axes fraction', ha='center', fontsize=15, va='center', fontweight='bold',color = corsubtitulo)
                    ax.set_xlim(0, 1)
                    ax.set_yticks([])
                    ax.set_xticks([])
                    
            for j in range(len(jar_columns)):
                ax = axes[(p + 1) * (len(age_groups) + 1) - 1, j]
                ax.axis('off')  # This makes the subplot blank

        #fig.tight_layout(pad=1.0)
        # set the spacing between subplots
        plt.subplots_adjust(left=0.1,
                            bottom=0.6,
                            right=0.9,
                            top=0.7,
                            wspace=0.4,
                            hspace=0.6)


        
            # Save figure
        fig.savefig('temp_plot.png',transparent=True,bbox_inches='tight')


        # Open the image file in binary mode, convert it to base64 and decode it to unicode
        with open('temp_plot.png', 'rb') as f:
            image = base64.b64encode(f.read()).decode()

        # Remove the image file as it's no longer needed
        os.remove('temp_plot.png')

        # Reset the default figure size
        plt.rcParams['figure.figsize'] = [6.4, 4.8]
        
        filters = session.get('filters', {}) # Obtenha os filtros da sessão
        filter_strings = []
        for key, value in filters.items():
            filter_value = ', '.join(value['values'])
            filter_strings.append(f'{key}: {filter_value}')
        filters_string = ', '.join(filter_strings)

        return jsonify({'corrgraf': image, 'filters_string': filters_string})
        
    else:
        return render_template('JAR.html')