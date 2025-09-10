import pandas as pd
import xgboost as xgb
from flask import Flask, request, jsonify
import sqlite3

# Initialize Flask app
app = Flask(__name__)

# Load the trained model
model = xgb.Booster()
model.load_model("xgboost_model.pkl")  # Update path to your model

# SQLite database setup
DATABASE_PATH = 'model.sql'  # Path to SQLite database

def init_db():
    # Initialize SQLite database from the SQL dump
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Read model.sql file and execute the SQL statements to create the schema and insert data
    with open('/mnt/data/model.sql', 'r') as sql_file:
        sql_script = sql_file.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()

# Load data from SQLite database
def load_data_from_sqlite():
    conn = sqlite3.connect(DATABASE_PATH)
    query = 'SELECT * FROM model'  # SQL query to select all data from the 'model' table
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Endpoint to perform inference based on user input
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get input data from request
        data = request.get_json()  # Example: {"Pregnancies": 5, "Glucose": 110, "BloodPressure": 70, ...}
        
        # Create a DataFrame for the input
        input_df = pd.DataFrame([data])

        # Prepare data for prediction (you can modify this to match your model's expected format)
        dmatrix = xgb.DMatrix(input_df)

        # Predict using the model
        prediction = model.predict(dmatrix)

        # Return the prediction result
        return jsonify({"prediction": prediction.tolist()})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Endpoint to run inference on data from the SQLite database
@app.route('/predict_from_db/<int:id>', methods=['GET'])
def predict_from_db(id):
    try:
        # Load the data from the SQLite database
        df = load_data_from_sqlite()

        # Find the row based on the provided id
        row = df[df['id'] == id]

        if row.empty:
            return jsonify({"error": "No data found for the provided ID"}), 404
        
        # Prepare data for prediction (dropping 'id' and 'Outcome' columns)
        input_df = row.drop(columns=['id', 'Outcome'])

        # Prepare data for prediction
        dmatrix = xgb.DMatrix(input_df)

        # Predict using the model
        prediction = model.predict(dmatrix)

        # Return the prediction result
        return jsonify({"id": id, "prediction": prediction.tolist()})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    init_db()  # Initialize the SQLite database with the SQL dump
    app.run(debug=True, host='0.0.0.0', port=6968)

