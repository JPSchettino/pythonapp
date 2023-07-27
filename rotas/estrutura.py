from base import app, session, redirect, url_for, render_template, request


@app.route('/graficos', methods=['GET', 'POST'])
def graficos():
    return render_template('graficos.html')

@app.route('/central', methods=['POST'])
def central():
    if request.method == 'POST':
        
        # Salva cat_vars e num_vars na sessão
        session['cat_vars'] = [request.form.get(f'catVar{i}') for i in range(1, 5) if request.form.get(f'catVar{i}')]
        session['num_vars'] = request.form.getlist('numVar1[]')
        session['cata_vars'] = request.form.getlist('CATAVar1[]')
        session['jar_vars'] = request.form.getlist('JAR1[]')
        
    if 'dataframe' not in session:
        return redirect(url_for('index'))  # redireciona de volta para a página inicial se não há dados carregados
    return render_template('central.html')