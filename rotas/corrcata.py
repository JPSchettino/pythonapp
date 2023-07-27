from base import app, session, redirect, url_for, pd, render_template, plt, sns, base64, os
from rotas.filemanager import *
from rotas.estrutura import *

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
    plt.rcParams['figure.figsize'] = [96, 96]

    # Generate the clustermap
    g = sns.clustermap(corr_matrix.fillna(0), annot=True, fmt='.1f', cmap="RdGy", linewidths=.01, annot_kws={"size":8})

    # Save figure
    g.fig.savefig('temp_plot.png', transparent=True)

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