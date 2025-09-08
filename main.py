from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import shutil
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional
import jwt

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

# Mount static directory for CSS and assets
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")

def get_user_id(request: Request):
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user_response = supabase.auth.get_user(access_token)
        if user_response.user:
            return str(user_response.user.id)
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.get("/", response_class=HTMLResponse)
async def auth(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})

@app.post("/signup")
async def signup(email: str = Form(...), password: str = Form(...)):
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if response.user:
            return RedirectResponse(url="/dashboard", status_code=303)
        else:
            return RedirectResponse(url="/?error=signup_failed", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/?error={str(e)}", status_code=303)

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user and response.session:
            # For simplicity, we'll use a cookie to store the access token
            # In production, you might want to use proper JWT handling
            response_obj = RedirectResponse(url="/dashboard", status_code=303)
            response_obj.set_cookie(
                key="access_token",
                value=response.session.access_token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax"
            )
            return response_obj
        else:
            return RedirectResponse(url="/?error=invalid_credentials", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/?error={str(e)}", status_code=303)

@app.post("/logout")
async def logout():
    try:
        supabase.auth.sign_out()
        response = RedirectResponse(url="/", status_code=303)
        response.delete_cookie("access_token")
        return response
    except Exception as e:
        return RedirectResponse(url=f"/?error={str(e)}", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # Check if user is authenticated
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/", status_code=303)

    try:
        # Verify the token with Supabase
        user_response = supabase.auth.get_user(access_token)
        if user_response.user:
            # For now, static data placeholders can be passed if needed
            # TODO: Add database connection and fetch data for dashboard here
            return templates.TemplateResponse("dashboard.html", {"request": request, "user": user_response.user})
        else:
            return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return RedirectResponse(url="/", status_code=303)

@app.get("/manage", response_class=HTMLResponse)
async def manage(request: Request):
    # Check authentication
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/", status_code=303)

    try:
        user_response = supabase.auth.get_user(access_token)
        if not user_response.user:
            return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return RedirectResponse(url="/", status_code=303)

    # Placeholder for Manage page, can be implemented later
    # TODO: Add database connection and fetch/manipulate data for manage page here
    return templates.TemplateResponse("manage.html", {"request": request})

@app.post("/upload-photo")
async def upload_photo(file: UploadFile = File(...)):
    # Read file content
    file_content = await file.read()

    # Save the uploaded file to the uploads directory
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    # Upload to Supabase storage
    try:
        supabase.storage.from_('files').upload(file.filename, file_content)
        supabase_url = supabase.storage.from_('files').get_public_url(file.filename)
    except Exception as e:
        supabase_url = None  # Or handle error

    # Return the URLs
    return {"local_url": f"/uploads/{file.filename}", "supabase_url": supabase_url}

@app.get("/edit/{type}/{item_id}", response_class=HTMLResponse)
async def edit(request: Request, type: str, item_id: str):
    item = None
    if type == "menu-photo":
        response = supabase.table('menu_photo').select('*').eq('id', item_id).execute()
        if response.data:
            item = response.data[0]
    elif type == "menu-list":
        response = supabase.table('menu_list').select('*').eq('id', item_id).execute()
        if response.data:
            item = response.data[0]
    elif type == "event":
        response = supabase.table('events').select('*').eq('id', item_id).execute()
        if response.data:
            item = response.data[0]
    elif type == "room":
        response = supabase.table('rooms').select('*').eq('id', item_id).execute()
        if response.data:
            item = response.data[0]
    
    if not item:
        return templates.TemplateResponse("edit.html", {"request": request, "type": type, "item_id": item_id, "error": "Item not found", "item": None})
    
    return templates.TemplateResponse("edit.html", {"request": request, "type": type, "item_id": item_id, "item": item})

# API Endpoints for Rooms
from pydantic import BaseModel

class Room(BaseModel):
    number: str
    type: str
    status: str = "available"

@app.get("/api/rooms")
async def get_rooms(request: Request):
    user_id = get_user_id(request)
    response = supabase.table('rooms').select('*').eq('user_id', user_id).execute()
    return response.data

@app.post("/api/rooms")
async def add_room(room: Room, request: Request):
    user_id = get_user_id(request)
    data = room.dict()
    data['user_id'] = user_id
    response = supabase.table('rooms').insert(data).execute()
    return response.data

@app.put("/api/rooms/{room_id}")
async def update_room(room_id: str, room: Room, request: Request):
    user_id = get_user_id(request)
    response = supabase.table('rooms').update(room.dict()).eq('id', room_id).eq('user_id', user_id).execute()
    return response.data

@app.put("/api/rooms/{room_id}/toggle")
async def toggle_room_status(room_id: str, request: Request):
    user_id = get_user_id(request)
    # First, get current status
    response = supabase.table('rooms').select('status').eq('id', room_id).eq('user_id', user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Room not found")
    current_status = response.data[0]['status']
    new_status = 'occupied' if current_status == 'available' else 'available'
    update_response = supabase.table('rooms').update({'status': new_status}).eq('id', room_id).eq('user_id', user_id).execute()
    return update_response.data

@app.delete("/api/rooms/{room_id}")
async def delete_room(room_id: str, request: Request):
    user_id = get_user_id(request)
    response = supabase.table('rooms').delete().eq('id', room_id).eq('user_id', user_id).execute()
    return response.data

# API Endpoints for Menu Photo
class MenuPhoto(BaseModel):
    name: str
    description: str = ""
    photo_url: str

@app.get("/api/menu_photo")
async def get_menu_photo(request: Request):
    user_id = get_user_id(request)
    response = supabase.table('menu_photo').select('*').eq('user_id', user_id).execute()
    return response.data

@app.post("/api/menu_photo")
async def add_menu_photo(item: MenuPhoto, request: Request):
    user_id = get_user_id(request)
    data = item.dict()
    data['user_id'] = user_id
    response = supabase.table('menu_photo').insert(data).execute()
    return response.data

@app.put("/api/menu_photo/{item_id}")
async def update_menu_photo(item_id: str, item: MenuPhoto, request: Request):
    user_id = get_user_id(request)
    response = supabase.table('menu_photo').update(item.dict()).eq('id', item_id).eq('user_id', user_id).execute()
    return response.data

@app.delete("/api/menu_photo/{item_id}")
async def delete_menu_photo(item_id: str, request: Request):
    user_id = get_user_id(request)
    response = supabase.table('menu_photo').delete().eq('id', item_id).eq('user_id', user_id).execute()
    return response.data

# API Endpoints for Menu List
class MenuList(BaseModel):
    title: str
    description: str = ""
    price: float

@app.get("/api/menu_list")
async def get_menu_list(request: Request):
    user_id = get_user_id(request)
    response = supabase.table('menu_list').select('*').eq('user_id', user_id).execute()
    return response.data

@app.post("/api/menu_list")
async def add_menu_list(item: MenuList, request: Request):
    user_id = get_user_id(request)
    data = item.dict()
    data['user_id'] = user_id
    response = supabase.table('menu_list').insert(data).execute()
    return response.data

@app.put("/api/menu_list/{item_id}")
async def update_menu_list(item_id: str, item: MenuList, request: Request):
    user_id = get_user_id(request)
    response = supabase.table('menu_list').update(item.dict()).eq('id', item_id).eq('user_id', user_id).execute()
    return response.data

@app.delete("/api/menu_list/{item_id}")
async def delete_menu_list(item_id: str, request: Request):
    user_id = get_user_id(request)
    response = supabase.table('menu_list').delete().eq('id', item_id).eq('user_id', user_id).execute()
    return response.data

# API Endpoints for Events
class Event(BaseModel):
    name: str
    venue: str
    date: str
    time: str

@app.get("/api/events")
async def get_events(request: Request):
    user_id = get_user_id(request)
    response = supabase.table('events').select('*').eq('user_id', user_id).execute()
    return response.data

@app.post("/api/events")
async def add_event(event: Event, request: Request):
    user_id = get_user_id(request)
    data = event.dict()
    data['user_id'] = user_id
    response = supabase.table('events').insert(data).execute()
    return response.data

@app.put("/api/events/{event_id}")
async def update_event(event_id: str, event: Event, request: Request):
    user_id = get_user_id(request)
    response = supabase.table('events').update(event.dict()).eq('id', event_id).eq('user_id', user_id).execute()
    return response.data

@app.delete("/api/events/{event_id}")
async def delete_event(event_id: str, request: Request):
    user_id = get_user_id(request)
    response = supabase.table('events').delete().eq('id', event_id).eq('user_id', user_id).execute()
    return response.data
