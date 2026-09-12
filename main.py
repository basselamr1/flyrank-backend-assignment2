from ast import Dict
from typing import Any
from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import sqlite3 

DB_NAME = "tasks.db"

db = []

app = FastAPI(
    title = "Task Management API", 
    description = "A complete CRUD API for managing your daily tasks."
)

class Task(BaseModel):
    title:str | None = Field(default = None, min_length=1, description="Title of the task.")
    done: bool | None = Field(default = False, description= "Status of the task if done or not.")

class TaskUpdate(BaseModel):
    title: str | None = Field( default=None,min_length=1)
    done: bool | None = None
    
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Invalid input data format or missing required fields."}
    )

def get_db():
    return sqlite3.connect(DB_NAME)

def initialize_database():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        done BOOLEAN NOT NULL DEFAULT 0
        )
        """
    )
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title,done) VALUES(? ,?)", 
            [
                ("Learn FastAPI", 1),
                ("Build a REST API", 1),
                ("Learn SQLite", 0)
            ]
            
        )
    conn.commit()
    conn.close()

initialize_database()

@app.get("/")
async def get_api_description():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"] }

@app.get("/health")
async def get_server_status():
    return {"status": "ok"}

@app.get('/tasks', status_code= status.HTTP_200_OK)
async def get_tasks():
    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * from tasks")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

@app.get('/tasks/{id}', status_code= status.HTTP_200_OK)
async def get_task(id:int):
    task = next((item for item in db if item['id'] == id), None)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id: {id} was not found."
        ) 
    return task

@app.post('/tasks', status_code=status.HTTP_201_CREATED)
async def add_task(task: Task):
    new_id = max((item['id'] for item in db), default = 0) + 1

    if(not task.title or task.title==""):
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task title can't be empty."
        )

    new_task = {
        "id": new_id,
        "title": task.title, 
        "done": task.done
    }

    db.append(new_task)
    return new_task, db

@app.put('/tasks/{id}', status_code= status.HTTP_200_OK)
async def update_task(task:TaskUpdate, id:int):
    existing_task = next((item for item in db if item['id'] == id), None)
    if existing_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Task with id: {id} not found."
        )
    if task.title is None and task.done is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Empty body: You must provide a title or done status."
        )

    if task.title is not None and task.done is not None:
        existing_task['title'] = task.title
        existing_task['done'] = task.done
    
    if task.title is not None and task.done is None:
        existing_task['title'] = task.title

    if task.title is None and task.done is not None:
        existing_task['done'] = task.done
    
    return existing_task, db

@app.delete('/tasks/{id}',status_code= status.HTTP_204_NO_CONTENT)
async def delete_task(id: int):
    task_index = next(
        (index for index, item in enumerate(db) if item["id"] == id), None)

    if task_index is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Unknown task id."
        )
    del db[task_index]
    
