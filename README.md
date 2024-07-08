# pythonapp

Bem-vindo ao repositório do **pythonapp**, um aplicativo avançado para análise de dados sensoriais. Este documento fornece uma visão geral das pastas e arquivos principais do projeto, explicando suas respectivas funções.

## Estrutura do Projeto

### rotas
Esta pasta contém as páginas principais do aplicativo, focadas em várias análises de dados sensoriais.

- **corrcata.py**: Página de correlação CATA.
- **estrutura.py**: Estrutura das páginas de gráficos.
- **filemanager.py**: Gerenciador de arquivos de diferentes extensões.
- **graficos.py**: Gráficos simples para análise de dados.
- **jar.py**: Gráfico das variáveis JAR segmentadas por atributos.
- **prefint.py**: Mapa de preferências internas.
- **resumo.py**: Resumo da base de dados.
- **teste.py**: Testes estatísticos de significância.

### static
Esta pasta contém os arquivos CSS estáticos utilizados no aplicativo.

### templates
Esta pasta contém os templates HTML usados para renderizar as páginas web.

### app.py
Arquivo principal do aplicativo, responsável pelo núcleo do funcionamento.

### base.py
Chamadas de funções base utilizadas em várias partes do aplicativo.

### filters.py
Contém a lógica dos filtros principais utilizados nas análises.

## Passo a Passo para Clonar e Rodar o Repositório

Siga as instruções abaixo para clonar e executar o projeto em sua máquina local:

1. **Crie e ative um ambiente virtual (opcional, mas recomendado)**
   ```sh
   git clone https://github.com/JPSchettino/pythonapp.git
   cd pythonapp


2. **Clone o repositório**
   ```sh
   python -m venv venv
    source venv/bin/activate  # No Windows, use `venv\Scripts\activate`




3. **Instale as dependências**
   ```sh
   pip install -r requirements.txt


4. **Rode o app**
   ```sh
   python app.py


