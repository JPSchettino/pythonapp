window.addEventListener('load', function() {

    console.log("boxplot.js carregado")

    // Função para criar o boxplot
    function createBoxplot(boxplotData) {
        // Limpando qualquer gráfico existente
        d3.select('#boxplot').html("");

        // Configurando o SVG para o boxplot
        var margin = {top: 10, right: 50, bottom: 20, left: 50},
            width = 800 - margin.left - margin.right,
            height = 500 - margin.top - margin.bottom;

        var svg = d3.select('#boxplot').append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        // Criando o boxplot
        var boxWidth = 50;

        var boxplot = svg.selectAll('.box')
            .data(boxplotData)
            .enter().append('g')
            .attr('transform', function(d, i) {
                return 'translate(' + i * boxWidth + ',0)';
            });

        // Adicionando linhas (whiskers) ao boxplot
        boxplot.append('line')
            .attr('x1', boxWidth / 2)
            .attr('y1', function(d) { return height - d.min; })
            .attr('x2', boxWidth / 2)
            .attr('y2', function(d) { return height - d.max; });

        // Adicionando retângulo central (box) ao boxplot
        boxplot.append('rect')
            .attr('width', boxWidth)
            .attr('x', 0)
            .attr('y', function(d) { return height - d['75%']; })
            .attr('height', function(d) { return d['75%'] - d['25%']; });

        // Adicionando linha mediana ao boxplot
        boxplot.append('line')
            .attr('x1', 0)
            .attr('y1', function(d) { return height - d['50%']; })
            .attr('x2', boxWidth)
            .attr('y2', function(d) { return height - d['50%']; });
    }

    // Função para gerar dados do boxplot
    function generateBoxplotData(numericData) {
        // Encontrando as categorias dinamicamente
        const categories = Object.keys(numericData).filter(key => key.startsWith('boxplot_'));

        // Inicializando o array de dados do boxplot
        const boxplotData = categories.map(category => {
            // Removendo o prefixo 'boxplot_' para obter o nome original da categoria
            const categoryName = category.replace('boxplot_', '');

            // Convertendo os dados em um formato utilizável para o boxplot
            const boxData = Object.keys(numericData[category]).map(key => {
                return {
                    key: key,
                    min: numericData[category][key]['min'],
                    max: numericData[category][key]['max'],
                    '25%': numericData[category][key]['25%'],
                    '50%': numericData[category][key]['50%'],
                    '75%': numericData[category][key]['75%']
                };
            });

            return {
                category: categoryName,
                data: boxData
            };
        });

        return boxplotData;
    }

    // Fazendo a requisição do JSON
    document.addEventListener('DOMContentLoaded', function(){
    d3.json('/visualizacao', function(error, data) {
        console.log("oi")
        if (error) throw error;
        console.log(data);
        console.log(Object.keys(data))
        console.log("oi")
        // Preenchendo a seleção dropdown com as variáveis numéricas
        var dropdown = d3.select('#numVarSelect');
        dropdown.selectAll('option')
            .data(Object.keys(data))
            .enter()
            .append('option')
            .attr('value', function(d) { return d; })
            .text(function(d) { return d; });

        // Criando o boxplot para a chave selecionada
        dropdown.on('change', function() {
            var key = dropdown.property('value');

            // Gerando os dados do boxplot
            var boxplotData = generateBoxplotData(data[key]);

            // Criando o boxplot para cada categoria
            boxplotData.forEach(item => {
                createBoxplot(item.data);
            });
        });

        // Gerando o boxplot inicial
        dropdown.dispatch('change');
    });
});

});

