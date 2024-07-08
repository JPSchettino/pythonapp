from base import app, session, request, redirect, url_for, render_template, Session
from rotas.corrcata import *
from rotas.graficos import *
from rotas.jar import *
from rotas.prefint import *
from rotas.resumo import *
from rotas.teste import *
from rotas.estrutura import *




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
