from base import app, request, session, apply_filters, jsonify, json, pd, np, render_template,ALLOWED_EXTENSIONS, secure_filename, redirect, url_for, os

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

@app.route('/get_variables', methods=['GET'])
def get_variables():
    variable_names =  session.get('cat_vars', [])
    return jsonify(variable_names)

@app.route('/get_variables1', methods=['GET'])
def get_variables1():
    variable_names =  session.get('cat_vars', [])
    return jsonify(variable_names)
