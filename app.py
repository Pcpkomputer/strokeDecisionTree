from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("importdataset.html")

@app.route("/preprocessing")
def preprocessing():
    return render_template("preprocessing.html")

@app.route("/evaluasi")
def evaluasi():
    return render_template("evaluasi.html")

@app.route("/klasifikasi")
def klasifikasi():
    return render_template("klasifikasi.html")

if __name__=='__main__':
    app.run(debug=True)