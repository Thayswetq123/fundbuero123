import streamlit as st
from PIL import Image
import numpy as np
from keras.models import load_model
import sqlite3
import io
import datetime
import bcrypt

st.set_page_config(page_title="Fundbüro KI")

st.title("Fundbüro KI System")

# Datenbank
conn = sqlite3.connect("fund.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT UNIQUE,
password BLOB
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS items(
username TEXT,
image BLOB,
label TEXT,
date TEXT
)
""")

conn.commit()

# KI Modell laden
model = load_model("keras_model.h5", compile=False)
labels = open("labels.txt").readlines()

def predict(image):

    image=image.resize((224,224))

    arr=np.asarray(image)

    arr=(arr.astype(np.float32)/127.5)-1

    data=np.expand_dims(arr,0)

    prediction=model.predict(data)

    index=np.argmax(prediction)

    label=labels[index].strip()

    return label


def register(username,password):

    hashed=bcrypt.hashpw(password.encode(),bcrypt.gensalt())

    try:
        c.execute(
        "INSERT INTO users VALUES (?,?)",
        (username,hashed)
        )
        conn.commit()
        return True
    except:
        return False


def login(username,password):

    c.execute(
    "SELECT password FROM users WHERE username=?",
    (username,)
    )

    result=c.fetchone()

    if result:
        if bcrypt.checkpw(password.encode(),result[0]):
            return True

    return False


if "user" not in st.session_state:
    st.session_state.user=None


if st.session_state.user is None:

    tab1,tab2=st.tabs(["Login","Register"])

    with tab1:

        user=st.text_input("Username")
        pw=st.text_input("Password",type="password")

        if st.button("Login"):

            if login(user,pw):
                st.session_state.user=user
                st.rerun()
            else:
                st.error("Login falsch")

    with tab2:

        new_user=st.text_input("Neuer Username")
        new_pw=st.text_input("Neues Passwort",type="password")

        if st.button("Registrieren"):

            if register(new_user,new_pw):
                st.success("Account erstellt")
            else:
                st.error("Username existiert")

    st.stop()


tab1,tab2,tab3=st.tabs(["Upload","Kamera","Fundbüro"])


with tab1:

    file=st.file_uploader(
    "Bild hochladen",
    type=["jpg","jpeg","png","bmp","webp"]
    )

    if file:

        image=Image.open(file).convert("RGB")

        label=predict(image)

        st.image(image)

        st.success(label)

        buffer=io.BytesIO()

        image.save(buffer,format="PNG")

        c.execute(
        "INSERT INTO items VALUES (?,?,?,?)",
        (
        st.session_state.user,
        buffer.getvalue(),
        label,
        datetime.date.today()
        )
        )

        conn.commit()


with tab2:

    cam=st.camera_input("Foto aufnehmen")

    if cam:

        image=Image.open(cam).convert("RGB")

        label=predict(image)

        st.image(image)

        st.success(label)


with tab3:

    search=st.text_input("Suche Gegenstand")

    date=st.text_input("Datum YYYY-MM-DD")

    rows=c.execute("SELECT * FROM items").fetchall()

    for r in rows:

        user,img,label,d=r

        if search and search.lower() not in label.lower():
            continue

        if date and date!=d:
            continue

        st.image(img,width=200)

        st.write(label)

        st.write(d)
