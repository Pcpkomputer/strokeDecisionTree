from flask import Flask, render_template,request, url_for, redirect
import pandas as pd 
import json
import mysql.connector
import numpy as np

app = Flask(__name__)

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="strokedecisiontree"
)


@app.route("/", methods=["POST","GET"])
def index():
    if request.method=="POST" and request.files:
        try:
            dataset = pd.read_csv(request.files["dataset"])
            arr = []
            for x in dataset.iterrows():
                # gender                     Female
                # age                            46
                # hypertension                    0
                # heart_disease                   0
                # ever_married                  Yes
                # work_type                Govt_job
                # Residence_type              Urban
                # avg_glucose_level           55.84
                # bmi                          27.8
                # smoking_status       never smoked
                # stroke                          0

                gender = x[1]["gender"]
                age = x[1]["age"]
                hypertension = x[1]["hypertension"]
                heart_disease = x[1]["heart_disease"]
                ever_married = x[1]["ever_married"]
                work_type = x[1]["work_type"]
                residence_type = x[1]["Residence_type"]
                avg_glucose_level = x[1]["avg_glucose_level"]
                bmi = x[1]["bmi"]
                smoking_status = x[1]["smoking_status"]
                stroke = x[1]["stroke"]

                if str(bmi)=="nan":
                    bmi=-1
                

                arr.append((gender,age,hypertension,heart_disease,ever_married,work_type,residence_type,avg_glucose_level,bmi,smoking_status,stroke))


            mydb.connect()
            cursor = mydb.cursor()
            cursor.execute("DELETE FROM dataset")
            mydb.commit()
            mydb.close()
            cursor.close()


            mydb.connect()
            cursor = mydb.cursor()
            cursor.executemany("INSERT INTO dataset VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",arr)
            mydb.commit()
            mydb.close()
            cursor.close()

            return redirect(url_for("index"))
        except Exception as e:
            return str(e)

    mydb.connect()
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM dataset")
    result = cursor.fetchall()
    mydb.commit()
    mydb.close()
    cursor.close()

    payload = []

    count = 0;
    for x in result:
        count = count+1
        payload.append({
            "id":count,
            "gender":x[0],
            "age":x[1],
            "hypertension":x[2],
            "heart disease":x[3],
            "ever married":x[4],
            "work type":x[5],
            "residence type":x[6],
            "average glucose level":x[7],
            "bmi":x[8],
            "smoking":x[9],
            "stroke":x[10]
        })

    return render_template("importdataset.html", data=json.dumps(payload))

@app.route("/preprocessing", methods=["POST","GET"])
def preprocessing():
    if request.method=="POST":

        mydb.connect()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM dataset")
        dataset = cursor.fetchall()
        cursor.close()
        mydb.close()

        dataframe = pd.DataFrame(dataset, columns=["gender","age","hypertension","heart_disease","ever_married","work_type","Residence_type","avg_glucose_level","bmi","smoking_status","stroke"])
        
        #dataframe["bmi"] = dataframe["bmi"].replace([-1],np.nan)

        cat = ['gender','ever_married','Residence_type','smoking_status','work_type']
        for i in cat:
            dummy = pd.get_dummies(dataframe[i],drop_first=True,prefix=f"{i}_")
            dataframe = pd.concat([dataframe,dummy],axis=1)

        dataframe = dataframe.drop([*cat],axis=1)

        payload = []
        for item in dataframe.itertuples():
            payload.append(tuple(item)[1:])

        mydb.connect()
        cursor = mydb.cursor()
        cursor.execute("DELETE FROM preprocessing")
        cursor.executemany("INSERT INTO preprocessing VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",payload)
        mydb.commit()
        cursor.close()
        mydb.close()

        return redirect(url_for("preprocessing"))

    mydb.connect()
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM preprocessing")
    rows = cursor.fetchall()
    cursor.close()
    mydb.close()

    data = []
    for x in rows:
        data.append({
            "age":x[0],
            "hypertension":x[1],
            "heart_disease":x[2],
            "avg_glucose_level":x[3],
            "bmi":x[4],
            "stroke":x[5],
            "gender__Male":x[6],
            "gender__Other":x[7],
            "ever_married__Yes":x[8],
            "Residence_type__Urban":x[9],
            "smoking_status__formerly smoked":x[10],
            "smoking_status__never smoked":x[11],
            "smoking_status__smokes":x[12],
            "work_type__Never_worked":x[13],
            "work_type__Private":x[14],
            "work_type__Self-employed":x[15],
            "work_type__children":x[16],
        })

    return render_template("preprocessing.html", data=json.dumps(data))

@app.route("/evaluasi")
def evaluasi():
    return render_template("evaluasi.html")

@app.route("/klasifikasi")
def klasifikasi():
    return render_template("klasifikasi.html")

if __name__=='__main__':
    app.run(debug=True)