
from base import app, session, redirect, url_for, pd, render_template, jsonify, request, px 
from rotas.filemanager import *
from rotas.estrutura import *

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

@app.route('/visualizacao', methods=['GET', 'POST'])
def visualizacao():
    if 'dataframe' not in session:
        return redirect(url_for('central'))
    
    dataframe = pd.read_json(session['filtered_dataframe'])
    cat_vars = session.get('cat_vars', [])
    num_vars = session.get('num_vars', [])
    cat_levels = {}
    
    for num_var in num_vars:
        for cat_var in cat_vars:
            cat_levels[cat_var] = dataframe[cat_var].unique().tolist()

    graphs = {}

    for num_var in num_vars:
        graphs[num_var] = {}
        for cat_var in cat_vars:
            graph_data = dataframe.groupby(cat_var)[num_var].describe()
            graphs[num_var][f"barplot_{cat_var}"] = graph_data.to_dict()
            graphs[num_var][f"boxplot_{cat_var}"] = graph_data.to_dict()

        graph_data = dataframe[num_var].value_counts(normalize=True)
        graphs[num_var][f"histogram"] = graph_data.to_dict()

    filters = session.get('filters', {})
    filter_strings = []
    for key, value in filters.items():
        filter_value = ', '.join(value['values'])
        filter_strings.append(f'{key}: {filter_value}')
    filters_string = ', '.join(filter_strings)

    session['graphs'] = graphs
    print(graphs)
    data = jsonify(graphs)
    return data

@app.route('/boxplot', methods=['GET', 'POST'])
def boxplot():
    if 'dataframe' not in session:
        return redirect(url_for('central'))
    
    dataframe = pd.read_json(session['filtered_dataframe'])
    cat_vars = session.get('cat_vars', [])
    num_vars = session.get('num_vars', [])
    cat_levels = {}
    
    for num_var in num_vars:
        for cat_var in cat_vars:
            cat_levels[cat_var] = dataframe[cat_var].unique().tolist()

    graphs = {}

    for num_var in num_vars:
        graphs[num_var] = {}
        for cat_var in cat_vars:
            # Cálculo de estatísticas descritivas
            graph_data = dataframe.groupby(cat_var)[num_var].describe()
            
            # Adicionando média, mediana e quartis
            boxplot_stats = {
                'mean': dataframe.groupby(cat_var)[num_var].mean().to_dict(),
                'median': dataframe.groupby(cat_var)[num_var].median().to_dict(),
                'q1': graph_data['25%'].to_dict(),
                'q3': graph_data['75%'].to_dict(),
                'min': graph_data['min'].to_dict(),
                'max': graph_data['max'].to_dict()
            }
            
            # Incluindo rótulos para média e mediana
            label_stats = {
                'mean_label': {key: f'Média: {value:.2f}' for key, value in boxplot_stats['mean'].items()},
                'median_label': {key: f'Mediana: {value:.2f}' for key, value in boxplot_stats['median'].items()}
            }
            
            graphs[num_var][f"boxplot_{cat_var}"] = {
                'boxplot_stats': boxplot_stats,
                'labels': label_stats
            }

        graph_data = dataframe[num_var].value_counts(normalize=True)
        graphs[num_var][f"histogram"] = graph_data.to_dict()

    filters = session.get('filters', {})
    filter_strings = []
    for key, value in filters.items():
        filter_value = ', '.join(value['values'])
        filter_strings.append(f'{key}: {filter_value}')
    filters_string = ', '.join(filter_strings)

    session['graphs'] = graphs
    print(graphs)
    return render_template('boxplot.html', num_vars=num_vars, filters_string=filters_string, cat_vars=cat_vars, cat_levels=cat_levels, graphs=graphs)

@app.route('/barplot', methods=['GET', 'POST'])
def barplot():
    if 'dataframe' not in session:
        return redirect(url_for('central'))
    
    dataframe = pd.read_json(session['filtered_dataframe'])
    cat_vars = session.get('cat_vars', [])
    num_vars = session.get('num_vars', [])
    cat_levels = {}
    
    for num_var in num_vars:
        for cat_var in cat_vars:
            cat_levels[cat_var] = dataframe[cat_var].unique().tolist()

    graphs = {}

    for num_var in num_vars:
        graphs[num_var] = {}
        for cat_var in cat_vars:
            graph_data = dataframe.groupby(cat_var)[num_var].describe()
            graphs[num_var][f"barplot_{cat_var}"] = graph_data.to_dict()
            graphs[num_var][f"boxplot_{cat_var}"] = graph_data.to_dict()

        graph_data = dataframe[num_var].value_counts(normalize=True)
        graphs[num_var][f"histogram"] = graph_data.to_dict()

    filters = session.get('filters', {})
    filter_strings = []
    for key, value in filters.items():
        filter_value = ', '.join(value['values'])
        filter_strings.append(f'{key}: {filter_value}')
    filters_string = ', '.join(filter_strings)

    session['graphs'] = graphs
    print(graphs)
    return render_template('barplot.html', num_vars=num_vars, filters_string=filters_string, cat_vars=cat_vars, cat_levels=cat_levels,graphs=graphs)  # Substitua 'seu_arquivo.html' pelo nome do seu arquivo HTML




@app.route('/TabelaHedonica', methods=['GET', 'POST'])
def TabelaHedonica():
    if 'dataframe' not in session:
        return redirect(url_for('central'))
    
    dataframe = pd.read_json(session['filtered_dataframe'])
    cat_vars = session.get('cat_vars', [])
    num_vars = session.get('num_vars', [])
    cat_levels = {}
    
    for num_var in num_vars:
        for cat_var in cat_vars:
            cat_levels[cat_var] = dataframe[cat_var].unique().tolist()

    graphs = {}

    for num_var in num_vars:
        graphs[num_var] = {}
        for cat_var in cat_vars:
            graph_data = dataframe.groupby(cat_var)[num_var].describe()
            graphs[num_var][f"barplot_{cat_var}"] = graph_data.to_dict()
            graphs[num_var][f"boxplot_{cat_var}"] = graph_data.to_dict()

        graph_data = dataframe[num_var].value_counts(normalize=True)
        graphs[num_var][f"histogram"] = graph_data.to_dict()

    filters = session.get('filters', {})
    filter_strings = []
    for key, value in filters.items():
        filter_value = ', '.join(value['values'])
        filter_strings.append(f'{key}: {filter_value}')
    filters_string = ', '.join(filter_strings)

    session['graphs'] = graphs
    print(graphs)
    return render_template('TabelaHedonica.html', num_vars=num_vars, filters_string=filters_string, cat_vars=cat_vars, cat_levels=cat_levels,graphs=graphs)  # Substitua 'seu_arquivo.html' pelo nome do seu arquivo HTML




@app.route('/histogram', methods=['GET', 'POST'])
def histogram():
    if 'dataframe' not in session:
        return redirect(url_for('central'))
    
    dataframe = pd.read_json(session['filtered_dataframe'])
    cat_vars = session.get('cat_vars', [])
    num_vars = session.get('num_vars', [])
    cat_levels = {}
    
    for num_var in num_vars:
        for cat_var in cat_vars:
            cat_levels[cat_var] = dataframe[cat_var].unique().tolist()

    graphs = {}

    for num_var in num_vars:
        graphs[num_var] = {}
        for cat_var in cat_vars:
            graph_data = dataframe.groupby(cat_var)[num_var].describe()
            graphs[num_var][f"barplot_{cat_var}"] = graph_data.to_dict()
            graphs[num_var][f"boxplot_{cat_var}"] = graph_data.to_dict()

        graph_data = dataframe[num_var].value_counts(normalize=True)
        graphs[num_var][f"histogram"] = graph_data.to_dict()

    filters = session.get('filters', {})
    filter_strings = []
    for key, value in filters.items():
        filter_value = ', '.join(value['values'])
        filter_strings.append(f'{key}: {filter_value}')
    filters_string = ', '.join(filter_strings)

    session['graphs'] = graphs
    print(graphs)
    return render_template('histogram.html', num_vars=num_vars, filters_string=filters_string, cat_vars=cat_vars, cat_levels=cat_levels,graphs=graphs)  # Substitua 'seu_arquivo.html' pelo nome do seu arquivo HTML

