from fastapi import Depends,HTTPException, status
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import utils.data_type as data_type
import config.database as database
from jose import JWTError,jwt
from tensorflow.keras.preprocessing import image as tkimg
from tensorflow.keras.models import load_model
import tensorflow as tf
import numpy as np



SECRET_KEY="d742e68876723b8ba6fae9c1c33c12e5a0023fb6c7a07158daac74fe08c2deeb30060af11979caafdc4afca172184b0138bf6029180e23da80d21e00ed4f7d4d"
ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*7
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class_names = ['husky', 'beagle', 'rottweiler', 'german-shepherd', 'dalmatian', 'poodle', 'bulldog', 'labrador-retriever']

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


def preprocess_image(image_path, target_size=(224, 224)):
    img = tkimg.load_img(image_path, target_size=target_size)
    img_array = tkimg.img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0
    return img_array


def predict_breed(img_path):
    model = tf.keras.models.load_model('./model.h5', compile=False)
    img_array = preprocess_image(img_path)
    predictions = model.predict(img_array)
    predicted_class = np.argmax(predictions, axis=1)
    print(predicted_class)
    return class_names[predicted_class[0]]


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = data_type.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    userCollection=database.db.get_collection("users")
    user = userCollection.find_one({"email":token_data.email})
    if user is None:
        raise credentials_exception
    return user