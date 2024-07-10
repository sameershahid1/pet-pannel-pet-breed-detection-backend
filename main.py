from fastapi import FastAPI, UploadFile,HTTPException, status, Depends
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from datetime import datetime, timedelta, timezone
from fastapi.middleware.cors import CORSMiddleware
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
import utils.data_type as data_type
import config.database as database
import utils.helping as helping
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Union
import numpy as np
import shutil

origins = ["http://localhost:3000"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIRECTORY = "check"
Path(UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)

@app.post("/login")
async def login(user:data_type.LoginRequest):
    try:
        userCollection=database.db.get_collection("users")
        data = userCollection.find_one({"email":user.email})
        if data:
            isPassMatch=helping.verify_password(user.password,data['password'])
            if isPassMatch:
                access_token_expires = timedelta(minutes=helping.ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = helping.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
                return data_type.Token(access_token=access_token, token_type="bearer",message="Successfully Loge in")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="incorrect password",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="incorrect email or password",
        )
    except Exception as e:
        return {"message":e,"status":False}


@app.post("/sign-up")
async def registration(user: data_type.RegistrationRequest):
    try:
        userCollection=database.db.get_collection("users")
        data = userCollection.find_one({"email":user.email})
        if data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email is already registered",
        )
        else:
            passwordHash=helping.get_password_hash(user.password)
            data={"firstName": user.firstName,"lastName": user.lastName, "email":user.email,"password":passwordHash}
            userCollection.insert_one(data)
            return {"message":"Successfully Registered"}
    except Exception as e:
        return e



@app.post("/breed/dog")
async def AutismCheck(image: Union[UploadFile, None] = None,user: data_type.User = Depends(helping.get_current_user)):
    try:
       if image is None:
            return {"message": "No image provided"}
       img_path = Path(UPLOAD_DIRECTORY) / image.filename
       with img_path.open("wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
       predicted_breed = helping.predict_breed(img_path)
       return {"message":"Successfully predicted breed", "breed": predicted_breed}
    except Exception as e:
        return {"message":"Error with your code"}


@app.post("/breed/list")
async def AutismCheck(image: Union[UploadFile, None] = None,user: data_type.User = Depends(helping.get_current_user)):
    try:
        petCollection=database.db.get_collection("pets")
        dogs = petCollection.find({})
        breed_counts = {}
        for dog in dogs:
            breed = dog["breed"]
            breed_counts[breed] = breed_counts.get(breed, 0) + 1
        return {"message":"Successfully predicted breed", "records": breed_counts}
    except Exception as e:
        return {"message":"Error with your code"}



