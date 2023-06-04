from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
from scipy.stats import kruskal, chi2_contingency
from werkzeug.utils import secure_filename
from filters import apply_filters
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns
import base64
import io
import os
import logging
from itertools import combinations
import plotly.graph_objects as go
import plotly.express as px
# Configurar o logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Usar o logger
logger.debug('Mensagem de depuração')
logger.info('Mensagem informativa')
logger.warning('Mensagem de aviso')
logger.error('Mensagem de erro')
logger.critical('Mensagem crítica')
app = Flask(__name__)
app.secret_key = '3232'
app.config['UPLOAD_FOLDER'] = ''
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
# Configurar Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
from io import BytesIO
import base64
from scipy import stats
from scipy.stats import shapiro, f_oneway, kruskal, ttest_ind, mannwhitneyu
from statsmodels.graphics.gofplots import qqplot
import matplotlib.pyplot as plt
import os
import plotly.graph_objs as go
from scipy.stats import probplot
import seaborn as sns
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False
from bs4 import BeautifulSoup

Session(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/apply_filter', methods=['POST'])
def apply_filter():
    filters = json.loads(request.form['filters'])
    session['filters'] = filters  
    dataframe = pd.read_json(session['dataframe'])
    filtered_dataframe = apply_filters(dataframe, filters)
    session['filtered_dataframe'] = filtered_dataframe.to_json()
    print(filtered_dataframe)
    return "Filtros aplicados", 200

@app.route('/get_unique_values', methods=['POST'])
def get_unique_values():
    column = request.form.get('column')

    if 'dataframe' not in session:
        return jsonify(unique_values=[])

    uploaded_dataframe = pd.read_json(session['dataframe'])

    is_numeric = np.issubdtype(uploaded_dataframe[column].dtype, np.number)

    unique_values = sorted(uploaded_dataframe[column].unique().tolist())

    return jsonify(is_numeric=is_numeric, unique_values=unique_values)

@app.route('/get_columns', methods=['POST'])
def get_columns():
    file = request.files['inputFile']
    df = pd.read_excel(file)
    session['dataframe'] = df.to_json()

    columns = df.columns.tolist()
    return jsonify(columns=columns)

@app.route('/get_filter_options', methods=['POST'])
def get_filter_options():
    if 'dataframe' not in session:
        return jsonify({"is_categorical": False, "levels": []})

    column = request.form.get('column')

    uploaded_dataframe = pd.read_json(session['dataframe'])

    is_categorical = uploaded_dataframe[column].dtype == 'object'
    levels = []

    if is_categorical:
        levels = uploaded_dataframe[column].unique().tolist()

    return jsonify({"is_categorical": is_categorical, "levels": levels})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'inputFile' not in request.files:
        return "No file part", 400

    file = request.files['inputFile']
    if file.filename == '':
        return "No selected file", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        uploaded_dataframe = pd.read_excel(filepath)
        session['dataframe'] = uploaded_dataframe.to_json()
        return redirect(url_for('central'))  # redireciona para a página central após o upload

    return "Invalid file", 400


@app.route('/central', methods=['POST'])
def central():
    if request.method == 'POST':
        
        # Salva cat_vars e num_vars na sessão
        session['cat_vars'] = [request.form.get(f'catVar{i}') for i in range(1, 4) if request.form.get(f'catVar{i}')]
        session['num_vars'] = request.form.getlist('numVar1[]')
        session['cata_vars'] = request.form.getlist('CATAVar1[]')
        
    if 'dataframe' not in session:
        return redirect(url_for('index'))  # redireciona de volta para a página inicial se não há dados carregados
    return render_template('central.html')

@app.route('/resumo', methods=['GET', 'POST'])
def resumo():
    if 'dataframe' not in session:
        return redirect(url_for('index'))

    dataframe = pd.read_json(session['filtered_dataframe'])
      # Substitui NaN por '-'

    filters = session.get('filters', {})  # Obtenha os filtros da sessão
    filter_strings = []
    for key, value in filters.items():
        filter_value = ', '.join(value['values'])
        filter_strings.append(f'{key}: {filter_value}')
    filters_string = ', '.join(filter_strings)

    summary = dataframe.describe(include='all')
    summary.fillna('-', inplace=True)
    summary.rename(index={'count': 'contagem', 'mean': 'média', 'std': 'desvio padrão', 'min': 'mínimo', '25%': '1º quartil', '50%': 'mediana', '75%': '3º quartil', 'max': 'máximo'}, inplace=True)  # Traduz os nomes das métricas para o português
    summary_html = summary.to_html()

    return render_template('resumo.html', summary_html=summary_html, filters_string=filters_string)

@app.route('/update_color', methods=['POST'])
def update_color():
    if 'dataframe' not in session:
        return redirect(url_for('central'))

    # Receber o JSON com as cores atualizadas
    updated_colors = request.json

    dataframe = pd.read_json(session['filtered_dataframe'])
    cat_vars = session.get('cat_vars', [])
    num_vars = session.get('num_vars', [])
    cat_levels = {}

    graphs = {}

    for num_var in num_vars:
        graphs[num_var] = {}
        for cat_var in cat_vars:
            # Barplot
            current_colors = updated_colors.get(num_var, {}).get("barplot_" + cat_var, {})
            bar_fig = px.bar(dataframe, x=cat_var, y=num_var)
            for trace in bar_fig.data:
                if trace.name in current_colors and current_colors[trace.name] != "#000000":
                    trace.marker.color = current_colors[trace.name]
            graphs[num_var][f"barplot_{cat_var}"] = {
                            'html': bar_fig.to_html(full_html=False),
                            'categories': dataframe[cat_var].unique().tolist(),
                        }

            # Boxplot
            current_colors = updated_colors.get(num_var, {}).get("boxplot_" + cat_var, {})
            box_fig = px.box(dataframe, x=cat_var, y=num_var)
            for trace in box_fig.data:
                if trace.name in current_colors and current_colors[trace.name] != "#000000":
                    trace.marker.color = current_colors[trace.name]
            graphs[num_var][f"boxplot_{cat_var}"] = {
                                        'html': box_fig.to_html(full_html=False),
                                        'categories': dataframe[cat_var].unique().tolist(),
                                    }

            # Histogram
            current_colors = updated_colors.get(num_var, {}).get("histogram", {})
            hist_fig = px.histogram(dataframe, x=cat_var, y=num_var, nbins=20, histnorm='probability density')
            for trace in hist_fig.data:
                if trace.name in current_colors and current_colors[trace.name] != "#000000":
                    trace.marker.color = current_colors[trace.name]
            graphs[num_var][f"histogram"] =  {
                            'html': hist_fig.to_html(full_html=False),
                            'categories': dataframe[cat_var].unique().tolist(),
                        }

    session['graphs'] = graphs
    session['color_updated'] = True

    return jsonify(success=True)

@app.route('/grafico', methods=['GET', 'POST'])
def grafico():
    if 'dataframe' not in session:
        return redirect(url_for('central'))
    
    dataframe = pd.read_json(session['filtered_dataframe'])
    cat_vars = session.get('cat_vars', [])
    num_vars = session.get('num_vars', [])
    cat_levels={}
        # Verifica se os gráficos já foram criados
    if 'graphs' in session and len(session['graphs']) != 0 and session.get('color_updated', False):


        for num_var in num_vars:
            for cat_var in cat_vars:
                cat_levels[cat_var] = dataframe[cat_var].unique().tolist()
                

        graphs = session['graphs']
        print("ooooooooooooooooOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO")
        #print(graphs)
        filters = session.get('filters', {}) # Obtenha os filtros da sessão
        filter_strings = []
        for key, value in filters.items():
            filter_value = ', '.join(value['values'])
            filter_strings.append(f'{key}: {filter_value}')
        filters_string = ', '.join(filter_strings)
        session['color_updated'] = False

    else:
        graphs = {}

        for num_var in num_vars:
            graphs[num_var] = {}
            # Create a barplot for each numerical variable
            for cat_var in cat_vars:
                bar_fig = px.bar(dataframe, x=cat_var, y=num_var)
                bar_fig.update_layout(
                    title=f"Gráfico de barras para {cat_var} e {num_var}",
                    xaxis_title=cat_var,
                    yaxis_title=num_var,
                    height=600,  # Adjust the size of the graph
                    width=900
                )
                graphs[f"barplot_{num_var}_{cat_var}"] = bar_fig.to_html(full_html=False)
                graphs[num_var][f"barplot_{cat_var}"] = {
                            'html': bar_fig.to_html(full_html=False),
                            'categories': dataframe[cat_var].unique().tolist(),
                        }

            # Create a boxplot for each numerical variable
            for cat_var in cat_vars:
                cat_levels[cat_var] = dataframe[cat_var].unique().tolist()
                box_fig = px.box(dataframe, x=cat_var, y=num_var)
                box_fig.update_layout(
                    title=f"Boxplots para a variável numérica {num_var}",
                    xaxis_title=cat_var,
                    yaxis_title=num_var,
                    height=600,  # Adjust the size of the graph
                    width=900
                )
                graphs[f"boxplot_{num_var}_{cat_var}"] = box_fig.to_html(full_html=False)
                graphs[num_var][f"boxplot_{cat_var}"] = {
                                        'html': box_fig.to_html(full_html=False),
                                        'categories': dataframe[cat_var].unique().tolist(),
                                    }
                                        
            # Create a frequency histogram for each numerical variable
            hist_fig = px.histogram(dataframe, x=cat_vars, nbins=20, histnorm='probability density')
            hist_fig.update_traces(hovertemplate='Frequência: %{y:.2%}')  # Show percentages on hover
            hist_fig.update_layout(
                title=f"Histogramas de frequência para a variável numérica {num_var}",
                xaxis_title='Categorias',
                yaxis_title='Frequência',
                height=600,  # Adjust the size of the graph
                width=900
            )
            graphs[f"histogram_{num_var}"] = hist_fig.to_html(full_html=False)
            graphs[num_var][f"histogram"] =  {
                            'html': hist_fig.to_html(full_html=False),
                            'categories': dataframe[cat_var].unique().tolist(),
                        }




        filters = session.get('filters', {}) # Obtenha os filtros da sessão
        filter_strings = []
        for key, value in filters.items():
            filter_value = ', '.join(value['values'])
            filter_strings.append(f'{key}: {filter_value}')
        filters_string = ', '.join(filter_strings)
        session['graphs'] = graphs

        

    return render_template('grafico.html', graphs=graphs, num_vars=num_vars, filters_string=filters_string,cat_vars=cat_vars, cat_levels=cat_levels)




@app.route('/teste', methods=['GET', 'POST'])
def teste():
    if 'filtered_dataframe' not in session:
        return redirect(url_for('index'))

    df = pd.read_json(session['filtered_dataframe'])
    cat_vars = session.get('cat_vars', [])
    num_vars = session.get('num_vars', [])

    
    qqplots_encoded = []
    residualplots_encoded = []
    results_normality = []
    results_tests = []
    results_descriptive = []

    for cat_var in cat_vars:
        for num_var in num_vars:
            groups = df.groupby(cat_var)[num_var].apply(list)

            for i, group in enumerate(groups):
                # Testes de normalidade
                k2, p = stats.normaltest(group)
                results_normality.append({'Variable': f'{cat_var} = {groups.keys()[i]}', 'Test': 'Normality', 'Statistic': k2, 'p-value': p})
                
                # Descriptive statistics
                mean = np.mean(group)
                std = np.std(group)
                results_descriptive.append({'Variable': f'{cat_var} = {groups.keys()[i]}', 'Mean': mean, 'Std Dev': std})

                # Se a distribuição for normal, aplicar um teste paramétrico (ex: T-test)
                if p > 0.05:
                    # Como é um teste paramétrico, precisamos de pelo menos duas amostras.
                    if i < len(groups) - 1:
                        t_stat, t_p = stats.ttest_ind(group, groups[i+1])
                        mean_diff = np.mean(group) - np.mean(groups[i+1])
                        results_tests.append({'Variable': f'{cat_var} = {groups.keys()[i]} vs {groups.keys()[i+1]} + {num_var}', 'Test': 'T-test', 'Statistic': t_stat, 'p-value': t_p, 'Mean Difference': mean_diff})

                # Se a distribuição não for normal, aplicar um teste não paramétrico (ex: Mann-Whitney U-test)
                else:
                    # Como é um teste não paramétrico, precisamos de pelo menos duas amostras.
                    if i < len(groups) - 1:
                        u_stat, u_p = stats.mannwhitneyu(group, groups[i+1])
                        mean_diff = np.mean(group) - np.mean(groups[i+1])
                        results_tests.append({'Variable': f'{cat_var} = {groups.keys()[i]} vs {groups.keys()[i+1]}+ {num_var}', 'Test': 'Mann-Whitney U-test', 'Statistic': u_stat, 'p-value': u_p, 'Mean Difference': mean_diff})


                # Testes qui-quadrado
                contingency_table = pd.crosstab(df[cat_var], df[num_var])
                chi2, p, dof, expected = stats.chi2_contingency(contingency_table)
                

            # Gere o gráfico Q-Q
            fig, ax = plt.subplots()
            stats.probplot(group, dist="norm", plot=ax)
            ax.set_title(f'Q-Q plot: {cat_var} = {groups.keys()[i]}')
            plt.close(fig)
            qqplots_encoded.append(plot_to_base64(fig))

            # Gere o gráfico de resíduos qui-quadrados padronizados
            expected_df = pd.DataFrame(expected, index=contingency_table.index, columns=contingency_table.columns)
            standardized_residuals = (contingency_table - expected_df) / np.sqrt(expected_df)
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(standardized_residuals, annot=True, cmap="coolwarm", center=0, vmin=-2, vmax=2)
            ax.set_title(f'Standardized Residuals: {cat_var} x {num_var}')
            plt.close(fig)
            residualplots_encoded.append(plot_to_base64(fig))

    results_normality_df = pd.DataFrame(results_normality)
    results_tests_df = pd.DataFrame(results_tests)
    results_descriptive_df = pd.DataFrame(results_descriptive)

    results_normality_df.rename(columns={'Variable': 'Variável', 'Test': 'Teste', 'Statistic': 'Estatística do teste', 'p-value': 'p-valor'}, inplace=True)  # Traduz os nomes das métricas para o português
    results_tests_df.rename(columns={'Variable': 'Variável', 'Test': 'Teste', 'Statistic': 'Estatística do teste', 'p-value': 'p-valor','Mean Difference':'Diferença entre as médias'}, inplace=True)  # Traduz os nomes das métricas para o português
    results_descriptive_df.rename(columns={'Variable': 'Variável', 'Mean': 'Média', 'Std Dev': 'Desvio padrão'}, inplace=True)  # Traduz os nomes das métricas para o português
    
    
    results_normality_html = results_normality_df.to_html(index=False).replace("<table", "<table class='results'").replace("<thead>", "<thead class='thead-dark'>")
    results_tests_html = results_tests_df.to_html(index=False).replace("<table", "<table class='results'").replace("<thead>", "<thead class='thead-dark'>")
    results_descriptive_html = results_descriptive_df.to_html(index=False).replace("<table", "<table class='results'").replace("<thead>", "<thead class='thead-dark'>")

    # Adiciona destaque vermelho para os p-valores significativos
    def highlight_p_values(html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('table')
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if cells:
                p_value = float(cells[-1].text)
                if p_value < 0.05:
                    span = soup.new_tag('span', style="color: red")
                    span.string = cells[-1].text
                    cells[-1].string.replace_with(span)
        return str(soup)
    
    def highlight_p_values2(html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('table')
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if cells:
                p_value = float(cells[-2].text)
                if p_value < 0.05:
                    span = soup.new_tag('span', style="color: red")
                    span.string = cells[-2].text
                    cells[-2].string.replace_with(span)
        return str(soup)


    

    results_normality_html = highlight_p_values(results_normality_html)
    results_tests_html = highlight_p_values2(results_tests_html)



    filters = session.get('filters', {}) # Obtenha os filtros da sessão
    filter_strings = []
    for key, value in filters.items():
        filter_value = ', '.join(value['values'])
        filter_strings.append(f'{key}: {filter_value}')
    filters_string = ', '.join(filter_strings)



    return render_template('teste.html', results_normality_html=results_normality_html, 
                           results_tests_html=results_tests_html, 
                           results_descriptive_html=results_descriptive_html,  qqplots_encoded=qqplots_encoded,
                            residualplots_encoded=residualplots_encoded,filters_string=filters_string)

def plot_to_base64(fig):
    img = BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    return base64.b64encode(img.read()).decode()


@app.route('/CORRCATA', methods=['GET', 'POST'])
def CORRCATA():
    if 'dataframe' not in session:
        return redirect(url_for('index'))

    dataframe = pd.read_json(session['filtered_dataframe'])
    cata_vars = session.get('cata_vars', [])

    # Filter the dataframe to include only the 'cata_vars' columns
    dataframe = dataframe[cata_vars]

    # Calculate the correlation matrix
    corr_matrix = dataframe.corr()

    # Set the default figure size
    plt.rcParams['figure.figsize'] = [48, 48]

    # Generate the clustermap
    g = sns.clustermap(corr_matrix.fillna(0), annot=True, fmt='.1f', cmap="RdGy", linewidths=.01, annot_kws={"size":8})

    # Save figure
    g.fig.savefig('temp_plot.png')

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

    return render_template('CORRCATA.html', corrgraf=image, filters_string= filters_string)

if __name__ == '__main__':
    app.run(debug=True)