from base import app, session, redirect, url_for, pd, render_template, jsonify, request, base64, plt,np, os,StandardScaler, FastICA ,KernelDensity,FuncFormatter, string, PCA, FactorAnalysis, LinearDiscriminantAnalysis
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
        showProducts = selected_variables.get('showProducts', False)
        showHedonic = selected_variables.get('showHedonic', False)
        red =  selected_variables['variable3']

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

        def plot_map(plot_type, category=None, data=dataframe, show_products=showProducts, show_hedonic=showHedonic, produto = cat_1, use_ica = red == "ICA", use_fa=red == "FA", use_lda=red == "LDA",hedonic_features =num_vars):
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
                loadings = pd.DataFrame(lda.coef_, columns=df_normalized.columns, index=['LD1', 'LD2']).T
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

            if plot_type == 'scatter' and category:
                unique_categories = df[category].unique()
                cmap = plt.get_cmap('viridis', len(unique_categories))
                color_dict = {cat: cmap(i) for i, cat in enumerate(unique_categories)}
                df['color'] = df[category].map(color_dict)

            n = result.shape[0]
            h = n**(-1/6)
            kde = KernelDensity(bandwidth=h, kernel='gaussian')
            kde.fit(result)
            x_lim = max(abs(result[:, 0].min()), result[:, 0].max())
            y_lim = max(abs(result[:, 1].min()), result[:, 1].max())

            x = np.linspace(-x_lim, x_lim, 100)
            y = np.linspace(-y_lim, y_lim, 100)
            X, Y = np.meshgrid(x, y)
            xy = np.vstack([X.ravel(), Y.ravel()]).T
            Z = np.exp(kde.score_samples(xy)).reshape(X.shape)
            Z_percentage = 100 * Z
            

            fig, ax = plt.subplots(figsize=(18,18))
            if plot_type == 'scatter':
                scatter = ax.scatter(
                    coordenadas['IC1'] if use_ica else coordenadas['FA1'] if use_fa else coordenadas['LD1'] if use_lda else coordenadas['PC1'],
                    coordenadas['IC2'] if use_ica else coordenadas['FA2'] if use_fa else coordenadas['LD2'] if use_lda else coordenadas['PC2'],
                    c=df['color'], s=500, alpha=0.7, edgecolors='w', linewidths=2
                )
                handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=v, markersize=10) for v in color_dict.values()]
                ax.legend(handles, color_dict.keys(), title=category)
                circle = plt.Circle((0,0), 3, color='blue', fill=False)
                ax.set_aspect('equal')
                ax.add_artist(circle)
            elif plot_type == 'kde':
                n_levels = 25
                c = ax.contourf(X, Y, Z_percentage, levels=n_levels, cmap='viridis', alpha=0.5)
                cbar = fig.colorbar(c)
                
                def to_percent(y, position):
                    return str(y) + '%'
                
                formatter = FuncFormatter(to_percent)

                cbar.ax.yaxis.set_major_formatter(formatter)

                cbar.set_label('Densidade (%)', fontsize=14)

            if show_products:
                for i, product in enumerate(df[produto].unique()):
                    ax.text(coordenadas.loc[df[produto] == product, 'IC1' if use_ica else 'PC1' if not use_fa and not use_lda else 'FA1' if use_fa else 'LD1'].mean(), 
                    coordenadas.loc[df[produto] == product, 'IC2' if use_ica else 'PC2' if not use_fa and not use_lda else 'FA2' if use_fa else 'LD2'].mean(), 
                    product, fontsize=12, ha='center')

            if show_hedonic:
                for i, feature in enumerate(df.select_dtypes(include=[np.number]).columns):
                    ax.arrow(0, 0, loadings.loc[feature, 'IC1']*3 if use_ica else loadings.loc[feature, 'FA1']*3 if use_fa else loadings.loc[feature, 'LD1']*3 if use_lda else loadings.loc[feature, 'PC1']*3, 
                    loadings.loc[feature, 'IC2']*3 if use_ica else loadings.loc[feature, 'FA2']*3 if use_fa else loadings.loc[feature, 'LD2']*3 if use_lda else loadings.loc[feature, 'PC2']*3, color='r', head_width=0.1, head_length=0.1)
                    ax.text(loadings.loc[feature, 'IC1']*3 + 0.2 if use_ica else loadings.loc[feature, 'FA1']*3 + 0.2 if use_fa else loadings.loc[feature, 'LD1']*3 + 0.2 if use_lda else loadings.loc[feature, 'PC1']*3 + 0.2, 
                    loadings.loc[feature, 'IC2']*3 + 0.2 if use_ica else loadings.loc[feature, 'FA2']*3 + 0.2 if use_fa else loadings.loc[feature, 'LD2']*3 + 0.2 if use_lda else loadings.loc[feature, 'PC2']*3 + 0.2, feature, color='r', ha='center', va='center')

            ax.set_xlim(-x_lim, x_lim)
            ax.set_ylim(-y_lim, y_lim)

            ax.set_xlabel('FA1' if use_fa else 'IC1' if use_ica else 'LD1' if use_lda else 'PC1 - {0:.1f}%'.format(pca.explained_variance_ratio_[0]*100), fontsize=14)
            ax.set_ylabel('FA2' if use_fa else 'IC2' if use_ica else 'LD2' if use_lda else 'PC2 - {0:.1f}%'.format(pca.explained_variance_ratio_[1]*100), fontsize=14)
            ax.set_title('Mapa de Preferência Interna', fontsize=20)

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
        fig1 = plot_map('scatter', cat_2, dataframe, produto=cat_1)
        fig2 = plot_map('kde', None, dataframe, produto = cat_1)

        # Save the images to BytesIO objects
      

        return jsonify({"graf1": fig1,"graf2": fig2,  "filters_string": "your_filters_string_here"})
    else:
        return render_template('prefint.html')