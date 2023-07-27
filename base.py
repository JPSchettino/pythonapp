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
ALLOWED_EXTENSIONS = {'xls', 'xlsx'}
# Configurar Flask-Session
from io import BytesIO
import base64
from scipy import stats
from scipy.stats import shapiro, f_oneway, kruskal, ttest_ind, mannwhitneyu
from statsmodels.graphics.gofplots import qqplot
logging.getLogger('matplotlib').setLevel(logging.WARNING)
import matplotlib.pyplot as plt
import os
import plotly.graph_objs as go
from scipy.stats import probplot
import seaborn as sns
from bs4 import BeautifulSoup
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import KernelDensity
from PIL import Image
import string
from matplotlib.ticker import FuncFormatter
from sklearn.decomposition import FastICA
from sklearn.decomposition import FactorAnalysis
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

def plot_to_base64(fig):
    img = BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', transparent=True)
    img.seek(0)
    return base64.b64encode(img.read()).decode()


app = Flask(__name__)
app.secret_key = '3232'
app.config['UPLOAD_FOLDER'] = ''
app.config['SESSION_TYPE'] = 'filesystem'
app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False

Session(app)