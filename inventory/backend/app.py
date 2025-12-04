from flask import Flask, jsonify
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow frontend to fetch data

# Load CSVs
train_df = pd.read_csv("train.csv")
test_df = pd.read_csv("test.csv")

# API to fetch train data
@app.route("/api/train")
def api_train():
    return jsonify(train_df.to_dict(orient="records"))

# API to fetch test data
@app.route("/api/test")
def api_test():
    return jsonify(test_df.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
