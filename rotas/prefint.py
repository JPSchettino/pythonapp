from base import app, session, redirect, url_for, pd, render_template, jsonify, request, base64, plt,np, os,StandardScaler, FastICA ,KernelDensity,FuncFormatter, string, PCA, FactorAnalysis, LinearDiscriminantAnalysis, Line2D, cm, adjust_text,ConnectionPatch
from rotas.filemanager import *
from rotas.estrutura import *

@app.route('/prefint', methods=['POST','GET'])
def prefint():
    if 'dataframe' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        print("chegueiaqui")
        print(request.data)
        selected_variables = request.get_json(force=True)
        
        print(selected_variables)


        dataframe = pd.read_json(session['filtered_dataframe'])
        num_vars = session.get('num_vars', [])
        cat_1 = selected_variables['variable1']
        cat_2 = selected_variables['variable2']
        paleta = selected_variables['cor']
        
        showProducts = selected_variables.get('showProducts', False)
        showHedonic = selected_variables.get('showHedonic', False)
        red =  selected_variables['variable3']

        # Verifica se cat_1 ou cat_2 são variáveis numéricas
        if cat_1 in num_vars:
            cat_1_new_name = "_" + cat_1
            dataframe[cat_1_new_name] = dataframe[cat_1]
            cat_1 = cat_1_new_name

        if cat_2 in num_vars:
            cat_2_new_name = "_" + cat_2
            dataframe[cat_2_new_name] = dataframe[cat_2]
            cat_2 = cat_2_new_name

        # Filtra o dataframe para incluir apenas as colunas relevantes
        dataframe = dataframe[num_vars + [cat_1] + [cat_2]]


        # Filter the dataframe to include only the 'cata_vars' columns
        dataframe = dataframe[num_vars + [cat_1]+ [cat_2]]

        hedonic_scale_mapping = {
            'desgosteimuitíssimo': 1,
            'desgosteimuito': 2,
            'desgosteimoderadamente': 3,
            'desgosteiligeiramente': 4,
            'nãogosteinemdesgostei': 5,
            'gosteiligeiramente': 6,
            'gosteimoderadamente': 7,
            'gosteimuito': 8,
            'gosteimuitíssimo': 9
        }

        for col in num_vars:
            if dataframe[col].dtype == object:  # np.object significa que é uma string
                print(f"A coluna '{col}' contém strings. Convertendo para numéricos...")
                dataframe[col] = dataframe[col].apply(lambda x: ''.join(ch for ch in str(x) if ch not in string.punctuation))  # remove pontuação
                dataframe[col] = dataframe[col].str.lower().str.strip()  # transforma para minúsculas e remove espaços em branco
                dataframe[col] = dataframe[col].str.replace(' ', '')

                unique_values = dataframe[col].unique()
                print(f"Valores únicos na coluna '{col}' antes da conversão: {unique_values}")

                dataframe[col] = dataframe[col].map(hedonic_scale_mapping)
                
                null_values_after_conversion = dataframe[col].isnull().sum()
                if null_values_after_conversion > 0:
                    print(f"A coluna '{col}' contém {null_values_after_conversion} valores nulos após a conversão.")
            elif np.issubdtype(dataframe[col].dtype, np.number):
                print(f"A coluna '{col}' já contém numéricos.")
            else:
                print(f"Os valores da coluna '{col}' não são nem string nem numéricos.")

        print(dataframe[num_vars])

        def plot_map(plot_type, category=None, data=dataframe, show_products=showProducts, show_hedonic=showHedonic, produto = cat_1, use_ica = red == "ICA", use_fa=red == "FA", use_lda=red == "LDA",hedonic_features =num_vars, paleta = paleta):
            df = pd.DataFrame(data)

            scaler = StandardScaler()
            df_normalized = pd.DataFrame(scaler.fit_transform(df.select_dtypes(include=[np.number])), columns=df.select_dtypes(include=[np.number]).columns, index=df.index)
            print(df_normalized)
            if use_ica:
                ica = FastICA(n_components=2, random_state=42)  # set random_state to a fixed value
                result = ica.fit_transform(df_normalized)
                coordenadas = pd.DataFrame(result, columns=['IC1', 'IC2'], index=df_normalized.index)
                loadings = pd.DataFrame(ica.components_.T, columns=['IC1', 'IC2'], index=df_normalized.select_dtypes(include=[np.number]).columns)
            elif use_lda:
                lda = LinearDiscriminantAnalysis(n_components=2)
                result = lda.fit_transform(df_normalized, df[category])
                coordenadas = pd.DataFrame(result, columns=['LD1', 'LD2'], index=df_normalized.index)
                # Obter o número de classes
                num_classes = len(np.unique(df[category]))

                # Criar índices para cada classe
                indices = ['LD' + str(i+1) for i in range(num_classes)]

                # Criar DataFrame
                loadings = pd.DataFrame(lda.coef_, columns=df_normalized.columns, index=indices).T

            elif use_fa:
                fa = FactorAnalysis(n_components=2, random_state=42)
                result = fa.fit_transform(df_normalized)
                coordenadas = pd.DataFrame(result, columns=['FA1', 'FA2'], index=df_normalized.index)
                loadings = pd.DataFrame(fa.components_.T, columns=['FA1', 'FA2'], index=df_normalized.select_dtypes(include=[np.number]).columns)
 
            else:
                pca = PCA(n_components=2)
                result = pca.fit_transform(df_normalized)
                coordenadas = pd.DataFrame(result, columns=['PC1', 'PC2'], index=df_normalized.index)
                loadings = pd.DataFrame(pca.components_.T, columns=['PC1', 'PC2'], index=df_normalized.select_dtypes(include=[np.number]).columns)
            
            fig, ax = plt.subplots(figsize=(36,36))
            if plot_type == 'scatter' and category:
                unique_categories = df[category].unique()
                cmap = plt.get_cmap(paleta, len(unique_categories))
                color_dict = {cat: cmap(i) for i, cat in enumerate(unique_categories)}
                df['color'] = df[category].map(color_dict)
                for cat, color in color_dict.items():
                    ax.scatter([], [], color=color, label=cat)
            

            n = result.shape[0]
            h = n**(-1/6)
            kde = KernelDensity(bandwidth=h, kernel='gaussian')
            kde.fit(result)
            x_lim = max(-3, 3)
            y_lim = max(-3, 3)
            xy_max = max(x_lim,y_lim)
            x = np.linspace(-xy_max, xy_max, 100)
            y = np.linspace(-xy_max, xy_max, 100)
            X, Y = np.meshgrid(x, y)
            xy = np.vstack([X.ravel(), Y.ravel()]).T
            Z = np.exp(kde.score_samples(xy)).reshape(X.shape)
            Z_percentage = 100 * Z
            

            
            if plot_type == 'scatter':
                scatter = ax.scatter(
                    coordenadas['IC1'] if use_ica else coordenadas['FA1'] if use_fa else coordenadas['LD1'] if use_lda else coordenadas['PC1'],
                    coordenadas['IC2'] if use_ica else coordenadas['FA2'] if use_fa else coordenadas['LD2'] if use_lda else coordenadas['PC2'],
                    c=df['color'], s=500, alpha=0.7, edgecolors='w', linewidths=2
                )
                color_legend_handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=v, markersize=10) for v in color_dict.values()]
                legend1 = ax.legend(handles=color_legend_handles, labels=color_dict.keys(), loc='upper left', title=category, fontsize=20)
                legend1.get_title().set_fontsize(20)  
                ax.add_artist(legend1)
                circle = plt.Circle((0,0), 3, color='blue', fill=False)
                ax.set_aspect('equal')
                ax.add_artist(circle)
            elif plot_type == 'kde':
                n_levels = 15
                c = ax.contourf(X, Y, Z_percentage, levels=n_levels, cmap=paleta, alpha=0.5)
                cbar = fig.colorbar(c)
                
                def to_percent(y, position):
                    return str(y) + '%'
                
                formatter = FuncFormatter(to_percent)

                cbar.ax.yaxis.set_major_formatter(formatter)

                cbar.set_label('Densidade (%)', fontsize=30)
                
                cbar.ax.tick_params(labelsize=30)

            # Criar uma lista para conter os elementos da legenda
            legend_elements = []

            # Obtenha o número de produtos únicos
            unique_products = df[produto].unique()
            n_products = len(unique_products)

            # Crie uma paleta de cores usando "viridis"
            colors = cm.get_cmap(paleta, n_products)

            # Construa o color_dict associando cada produto a uma cor
            color_dict = {}
            for i, product in enumerate(unique_products):
                color_dict[product] = colors(i / (n_products - 1))

            # Restante do código, agora usando color_dict
            if show_products:
                product_symbols = [ 's', 'v', '^', '<', '>']

                # Crie a legenda usando color_dict
                product_legend_handles = []
                for i, product in enumerate(unique_products):
                    product_color = color_dict[product]
                    handle = Line2D([0], [0], marker=product_symbols[i % len(product_symbols)], color='w', markerfacecolor=product_color, markersize=10, label=product)
                    product_legend_handles.append(handle)

                legend_products = ax.legend(handles=product_legend_handles, loc='upper right', title=produto, fontsize=30)
                legend_products.get_title().set_fontsize(30)  
                ax.add_artist(legend_products)

                for i, product in enumerate(unique_products):
                    x_mean = coordenadas.loc[df[produto] == product, 'IC1' if use_ica else 'PC1' if not use_fa and not use_lda else 'FA1' if use_fa else 'LD1'].mean()
                    y_mean = coordenadas.loc[df[produto] == product, 'IC2' if use_ica else 'PC2' if not use_fa and not use_lda else 'FA2' if use_fa else 'LD2'].mean()
                    ax.scatter(x_mean, y_mean, marker=product_symbols[i % len(product_symbols)], label=product, s=1200, color=color_dict[product])

            positions = []  # Armazenar as posições das setas

            if show_hedonic:
                np.random.seed(42)
                texts = []  # Para armazenar os objetos de texto para ajuste

                for i, feature in enumerate(df.select_dtypes(include=[np.number]).columns):
                    modified_feature_name = feature.split('_')[-1]
                    modified_feature_name = modified_feature_name.capitalize()

                    x_value = loadings.loc[feature, 'IC1']*3 if use_ica else loadings.loc[feature, 'FA1']*3 if use_fa else loadings.loc[feature, 'LD1']*3 if use_lda else loadings.loc[feature, 'PC1']*3
                    y_value = loadings.loc[feature, 'IC2']*3 if use_ica else loadings.loc[feature, 'FA2']*3 if use_fa else loadings.loc[feature, 'LD2']*3 if use_lda else loadings.loc[feature, 'PC2']*3
                    random_factor = np.random.uniform(0.7, 0.9)
                    x_random = x_value * random_factor
                    y_random = y_value * random_factor
                    rand = np.random.uniform(-0.2, 0.2)

                    positions.append((x_random, y_random))
                    #positions.append((x_value/2, y_value/2))  # Adicionar posição da seta à lista

                    ax.arrow(0, 0, x_value, y_value, color='black', head_width=0.1, head_length=0.1)

                    text = ax.text(x_value + rand, y_value + rand, modified_feature_name, color='black', ha='center', va='center', fontsize=20, bbox=dict(boxstyle="round,pad=0.3", edgecolor='black', facecolor='aliceblue', alpha=0.9))
                    texts.append(text)

                # Ajustar a posição dos textos para evitar sobreposição
                adjust_text(texts)

                # Conectar os textos com suas respectivas setas
                for i, text in enumerate(texts):
                    x_text, y_text = text.get_position()
                    x_mid, y_mid = positions[i]
                    con = ConnectionPatch(xyA=(x_text, y_text), xyB=(x_mid, y_mid), coordsA="data", coordsB="data", axesA=ax, axesB=ax, color="grey", linewidth=1.2)
                    ax.add_artist(con)

                    
            ax.set_xlim(-x_lim, x_lim)
            ax.set_ylim(-y_lim, y_lim)

            ax.set_xlabel('FA1' if use_fa else 'IC1' if use_ica else 'LD1' if use_lda else 'PC1 - {0:.1f}%'.format(pca.explained_variance_ratio_[0]*100), fontsize=14)
            ax.set_ylabel('FA2' if use_fa else 'IC2' if use_ica else 'LD2' if use_lda else 'PC2 - {0:.1f}%'.format(pca.explained_variance_ratio_[1]*100), fontsize=14)
            ax.set_title('Análise de sentimentos', fontsize=40)

            ax.grid(True)
            plt.xticks([])
            plt.yticks([])

            # Save figure
            fig.savefig('temp_plot.png',transparent=True,bbox_inches='tight')

            # Open the image file in binary mode, convert it to base64 and decode it to unicode
            with open('temp_plot.png', 'rb') as f:
                image = base64.b64encode(f.read()).decode()

            # Remove the image file as it's no longer needed
            os.remove('temp_plot.png')

            # Reset the default figure size
            plt.rcParams['figure.figsize'] = [6.4, 4.8]
            return image

        # Render the images
        fig1 = plot_map('scatter', cat_2, dataframe, produto= cat_1)
        fig2 = plot_map('kde', cat_2, dataframe, produto = cat_1)

        # Save the images to BytesIO objects
      

        return jsonify({"graf1": fig1,"graf2": fig2,  "filters_string": "your_filters_string_here"})
    else:
        return render_template('prefint.html')