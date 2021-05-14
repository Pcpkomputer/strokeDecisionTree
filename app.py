from flask import Flask, render_template,request, url_for, redirect, session
import pandas as pd 
import json
import mysql.connector
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.impute import KNNImputer
from sklearn.tree import *
from sklearn.metrics import f1_score

app = Flask(__name__)

app.secret_key="strokedecisiontreee"

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="strokedecisiontree"
)


@app.route("/login", methods=["POST","GET"])
def login():
    if 'login' in session:
        return redirect(url_for("index"))
    
    if request.method=="POST":
        email = request.form["email"]
        password = request.form["password"]

        mydb.connect()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM user WHERE user.email=%s",(email,))
        result = cursor.fetchone()
        cursor.close()
        mydb.close()

        if result==None:
            return render_template("login.html",error="Akun tidak ditemukan...")
        
        u = result[1]
        p = result[2]

        if u==email and p==password:
            session["login"]=True
            return redirect(url_for("index"))
        else:
            return render_template("login.html",error="Login gagal...")

    return render_template("login.html")

@app.route("/", methods=["POST","GET"])
def index():
    if 'login' not in session:
        return redirect(url_for("login"))
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
    if 'login' not in session:
        return redirect(url_for("login"))
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

@app.route("/evaluasi", methods=["GET","POST"])
def evaluasi():
    if 'login' not in session:
        return redirect(url_for("login"))
    if request.method=="POST":
        mydb.connect()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM dataset")
        dataset = cursor.fetchall()
        cursor.close()
        mydb.close()

        dataframe = pd.DataFrame(dataset, columns=["gender","age","hypertension","heart_disease","ever_married","work_type","Residence_type","avg_glucose_level","bmi","smoking_status","stroke"])
        
        dataframe["bmi"] = dataframe["bmi"].replace([-1],np.nan)

        cat = ['gender','ever_married','Residence_type','smoking_status','work_type']
        for i in cat:
            dummy = pd.get_dummies(dataframe[i],drop_first=True,prefix=f"{i}_")
            dataframe = pd.concat([dataframe,dummy],axis=1)

        dataframe = dataframe.drop([*cat],axis=1)

        X = dataframe.drop('stroke',axis=1).values
        y = dataframe['stroke'].values

        skf = StratifiedKFold(n_splits=5)
        skf.get_n_splits(X, y)

        kfold = []
        fscore = []

        for train_index, test_index in skf.split(X, y):
            X_train, X_test = X[train_index], X[test_index]
            y_train, y_test = y[train_index], y[test_index]
            
            imputer = KNNImputer(n_neighbors=2)
            X_train = imputer.fit_transform(X_train)
            X_test = imputer.fit_transform(X_test)
            
            clf = DecisionTreeClassifier()
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            f = f1_score(y_true = y_test , y_pred = y_pred,average = 'weighted')

            payload = []
            
            for index, fold in enumerate(X_test):
                payload.append([*fold,y_test[index],y_pred[index]])

            kfold.append(payload);
            fscore.append(f)

        
        json_ = []

        for item in kfold:
            p = []
            for x in item:
                p.append(
                    {
                        "age":int(x[0]),
                        "hypertension":float(x[1]),
                        "heart_disease":int(x[2]),
                        "avg_glucose_level":float(x[3]),
                        "bmi":float(x[4]),
                        "gender__Male":int(x[5]),
                        "gender__Other":int(x[6]),
                        "ever_married__Yes":int(x[7]),
                        "Residence_type__Urban":int(x[8]),
                        "smoking_status__formerly smoked":int(x[9]),
                        "smoking_status__never smoked":int(x[10]),
                        "smoking_status__smokes":int(x[11]),
                        "work_type__Never_worked":int(x[12]),
                        "work_type__Private":int(x[13]),
                        "work_type__Self-employed":int(x[14]),
                        "work_type__children":int(x[15]),
                        "actual":int(x[16]),
                        "predicted":int(x[17])
                    }
                )
            json_.append(p)


        return render_template("evaluasi.html",payload=enumerate(json_),testing=json_,fscore=fscore)
    return render_template("evaluasi.html")

@app.route("/klasifikasi", methods=["POST","GET"])
def klasifikasi():
    if 'login' not in session:
        return redirect(url_for("login"))
    if request.method=="POST":
        gender = request.form["gender"]
        age = request.form["age"]
        hypertension = request.form["hypertension"]
        heartdisease = request.form["heartdisease"]
        evermarried = request.form["evermarried"]
        worktype = request.form["worktype"]
        residencetype = request.form["residencetype"]
        averageglucoselevel = request.form["averageglucoselevel"]
        bmi = request.form["bmi"]
        smokingstatus = request.form["smokingstatus"]


        mydb.connect()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM dataset")
        dataset = cursor.fetchall()
        cursor.close()
        mydb.close()

        dataframe = pd.DataFrame([*dataset,(gender,int(age),int(hypertension),int(heartdisease),evermarried,worktype,residencetype,float(averageglucoselevel),float(bmi),smokingstatus,"undefined")], columns=["gender","age","hypertension","heart_disease","ever_married","work_type","Residence_type","avg_glucose_level","bmi","smoking_status","stroke"])
        
        dataframe["bmi"] = dataframe["bmi"].replace([-1],np.nan)

        cat = ['gender','ever_married','Residence_type','smoking_status','work_type']
        for i in cat:
            dummy = pd.get_dummies(dataframe[i],drop_first=True,prefix=f"{i}_")
            dataframe = pd.concat([dataframe,dummy],axis=1)

        dataframe = dataframe.drop([*cat],axis=1)

        X = dataframe.drop('stroke',axis=1)
        y = dataframe['stroke']

        predictedsoon = X.iloc[len(X)-1]


        #########################################################################################

        dataframe = pd.DataFrame(dataset, columns=["gender","age","hypertension","heart_disease","ever_married","work_type","Residence_type","avg_glucose_level","bmi","smoking_status","stroke"])
        
        dataframe["bmi"] = dataframe["bmi"].replace([-1],np.nan)

        cat = ['gender','ever_married','Residence_type','smoking_status','work_type']
        for i in cat:
            dummy = pd.get_dummies(dataframe[i],drop_first=True,prefix=f"{i}_")
            dataframe = pd.concat([dataframe,dummy],axis=1)

        dataframe = dataframe.drop([*cat],axis=1)

        X = dataframe.drop('stroke',axis=1).values
        y = dataframe['stroke'].values


        imputer = KNNImputer(n_neighbors=2)
        X_train = imputer.fit_transform(X)

        clf = DecisionTreeClassifier()
        clf.fit(X_train, y)


        prediksi = clf.predict([predictedsoon])
   
        return render_template("klasifikasi.html",hasil=prediksi[0])
    return render_template("klasifikasi.html")

if __name__=='__main__':
    app.run(debug=True)