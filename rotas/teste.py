
from base import app, session, redirect, url_for, pd, render_template, stats, plt,np, sns, plot_to_base64, BeautifulSoup 
from rotas.filemanager import *
from rotas.estrutura import *

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
                results_descriptive.append({'Variable': f'{cat_var} = {groups.keys()[i]} - {num_var}', 'Mean': mean, 'Std Dev': std})

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
    
    significant_vars = set(results_tests_df[results_tests_df['p-valor'] < 0.05]['Variável'].str.split(' vs ').str[0].str.split(' - ').str[0])
    
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
    
    def highlight_p_values1(html, significant_vars):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find('table')
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if cells:
                variable = cells[0].text.split(' - ')[0]  # Extrai o nome da variável
                if variable in significant_vars:
                    span = soup.new_tag('span', style="color: blue")  # Aqui escolhi a cor azul, mas você pode alterar conforme preferir
                    span.string = cells[0].text
                    cells[0].string.replace_with(span)
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
    results_descriptive_html = highlight_p_values1(results_descriptive_html, significant_vars)



    filters = session.get('filters', {}) # Obtenha os filtros da sessão
    filter_strings = []
    for key, value in filters.items():
        filter_value = ', '.join(value['values'])
        filter_strings.append(f'{key}: {filter_value}')
    filters_string = ', '.join(filter_strings)

    print(results_normality_html)

    return render_template('teste.html', results_normality_html=results_normality_html, 
                           results_tests_html=results_tests_html, 
                           results_descriptive_html=results_descriptive_html,  qqplots_encoded=qqplots_encoded,
                            residualplots_encoded=residualplots_encoded,filters_string=filters_string)