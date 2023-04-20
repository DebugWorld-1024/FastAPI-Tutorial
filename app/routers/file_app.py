import os
import pandas as pd
from io import BytesIO
from typing import List
from urllib import parse
from fastapi import APIRouter, HTTPException, UploadFile, Query, Security, responses

from app.data_model import response_data
from app.routers.login_app import verify_token
from app.response_status_code import ResponseStatusCode


file_app = APIRouter()

current_path = os.path.split(os.path.realpath(__file__))[0]
root_path = os.path.join(current_path, '../../', 'workspace')


@file_app.post('/db/file',
               dependencies=[Security(verify_token, scopes=["Write"])],
               description='上传/更新文件')
async def post_file(file: UploadFile):
    file_type = file.filename.split(".")[-1]
    if file_type not in ["csv", "json", "xls", "xlsx"]:
        raise HTTPException(status_code=ResponseStatusCode.FILE_TYPE_ERR.code,
                            detail=ResponseStatusCode.FILE_TYPE_ERR.message)

    file_content = await file.read()
    if len(file_content) >= 20 * 1024 * 1024:       # 20M
        raise HTTPException(status_code=ResponseStatusCode.FILE_SIZE_ERR.code,
                            detail=ResponseStatusCode.FILE_SIZE_ERR.message)

    if not os.path.exists(root_path):
        os.makedirs(root_path)

    with open(os.path.join(root_path, file.filename), 'wb') as f:
        f.write(file_content)

    return response_data(data=True)


@file_app.delete('/db/file',
                 dependencies=[Security(verify_token, scopes=["Write"])],
                 description="批量删除文件")
async def delete_file(files_name: List[str] = Query(description="文件名字", example=["test.xlsx", "test.csv"])):

    for file_name in files_name:
        for item in ['..', '/', '\\']:
            if item in file_name:
                raise HTTPException(status_code=ResponseStatusCode.FILE_PATH_ERR.code,
                                    detail=ResponseStatusCode.FILE_PATH_ERR.message)

        path = os.path.join(root_path, file_name)
        if os.path.exists(path):
            os.remove(path)
    return response_data(data=True)


@file_app.get('/db/file',
              dependencies=[Security(verify_token, scopes=["Read"])],
              description="获取文件名")
async def get_file():
    files = []
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    for file in os.listdir(root_path):
        path = os.path.join(root_path, file)
        if not file.startswith('.') and not os.path.isdir(path):        # 过滤文件夹和隐藏文件
            files.append({
                'file_name': file,
                'file_size': os.path.getsize(path)
            })

    return response_data(data=files)


@file_app.get('/db/download_file',
              dependencies=[Security(verify_token, scopes=["Read"])],
              description="下载文件")
async def download_file(file_name: str = Query(description="文件名字", example="test.csv")):
    return responses.FileResponse(path=os.path.join(root_path, file_name), filename=file_name)


@file_app.get('/db/file_data',
              dependencies=[Security(verify_token, scopes=["Read"])],
              description="查看指定数量的文件数据，只支持查看csv、xlsx、xls、json文件")
async def file_data(file_name: str = Query(description="文件名字", example="test.csv"),
                    limit: int = Query(description="行数")):
    file_type = file_name.split('.')[-1]
    path = os.path.join(root_path, file_name)

    if file_type in ['xls', 'xlsx']:
        buffer = BytesIO()
        df = pd.read_excel(path, nrows=limit)
        df.to_excel(buffer, index=False)
        return responses.Response(
            buffer.getvalue(),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={parse.quote(file_name)}"}
        )
    elif file_type == 'csv':
        df = pd.read_csv(path, nrows=limit)
        return responses.Response(
            df.to_csv(index=False),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={parse.quote(file_name)}"}
        )
    elif file_type == 'json':
        df = pd.read_json(path, orient='records')
        return responses.Response(
            df.head(limit).to_json(orient='records'),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={parse.quote(file_name)}"}
        )
    else:
        raise HTTPException(status_code=ResponseStatusCode.FILE_TYPE_ERR.code,
                            detail=ResponseStatusCode.FILE_TYPE_ERR.message)
