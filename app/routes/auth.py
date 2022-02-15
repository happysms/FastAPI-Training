from datetime import timedelta, datetime
import jwt
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
import bcrypt
from app.database.conn import db
from app.database.schema import Users
from app.models import SnsType, Token, UserToken, UserRegister
from fastapi import APIRouter, Depends
from app.common.consts import JWT_SECRET, JWT_ALGORITHM

router = APIRouter(prefix="/auth")


@router.post("/register/{sns_type}", status_code=201, response_model=Token)
async def register(sns_type: SnsType, reg_info: UserRegister, session: Session = Depends(db.session)):
    """
        회원가입 API
        :param sns_type:
        :param reg_info:
        :param session:
        :return:
    """
    print(sns_type, SnsType.email)
    if sns_type == SnsType.email:
        print("마")
        is_exist = await is_email_exist(reg_info.email)
        if not reg_info.email or not reg_info.pw:
            return JSONResponse(status_code=400, content=dict(msg="Email and PW must be provided"))
        if is_exist:
            return JSONResponse(status_code=400, content=dict(msg="EMAIL_EXISTS"))

        hash_pw = bcrypt.hashpw(reg_info.pw.encode("utf-8"), bcrypt.gensalt())
        new_user = Users.create(session, auto_commit=True, pw=hash_pw, email=reg_info.email)

        token = dict(
            Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(new_user).dict(exclude={'pw', 'marketing_agree'}), )}")

        return token

    return JSONResponse(status_code=400, content=dict(msg="NOT_SUPPORTED"))


@router.post("/login/{sns_type}", status_code=200)
async def login(sns_type: SnsType, user_info: UserRegister):
    if sns_type == SnsType.email:
        is_exist = await is_email_exist(user_info.email)
        if not user_info.email or not user_info.pw:
            return JSONResponse(status_code=400, content=dict(msg="Email and PW must be provided"))

        if not is_exist:
            return JSONResponse(status_code=400, content=dict(msg="No_match_user"))

        user = Users.get(email=user_info.email)
        is_verified = bcrypt.checkpw(user_info.pw.encode("utf-8"), user.pw.encode("utf-8"))
        if not is_verified:
            return JSONResponse(status_code=400, content=dict(msg="No_match_user"))

        token = dict(
            Authorization=f"Bearer {create_access_token(data=UserToken.from_orm(user).dict(exclude={'pw', 'marketing_agree'}), )}")

        return token

    return JSONResponse(status_code=400, content=dict(msg="NOT_SUPPORTED"))


async def is_email_exist(email: str):
    get_email = Users.get(email=email)
    if get_email:
        return True
    return False


def create_access_token(*, data: dict = None, expires_delta: int = None):
    to_encode = data.copy()
    if expires_delta:
        to_encode.update({"exp": datetime.utcnow() + timedelta(hours=expires_delta)})

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MywibmFtZSI6bnVsbCwicGhvbmVfbnVtYmVyIjpudWxsLCJwcm9maWxlX2ltZyI6bnVsbCwic25zX3R5cGUiOm51bGx9.O0y-NVKB6eq_8pH38LBXIn1WhAt0MNS1XS9D7-5n5ew
