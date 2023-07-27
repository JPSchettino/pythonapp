from base import app, session, redirect, url_for, pd, render_template 
from rotas.filemanager import *
from rotas.estrutura import *

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
    summary.rename(index={'count': 'contagem', 'mean': 'média', 'std': 'desvio padrão', 'min': 'mínimo', '25%': '1º quartil', '50%': 'mediana', '75%': '3º quartil', 'max': 'máximo', 'unique': 'Níveis distintos'}, inplace=True)  # Traduz os nomes das métricas para o português
    summary_html = summary.to_html()

    return render_template('resumo.html', summary_html=summary_html, filters_string=filters_string)