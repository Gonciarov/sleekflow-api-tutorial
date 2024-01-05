from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="add any string...")
app.mount("/static", StaticFiles(directory="static"), name="static")

oauth = OAuth()
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id='923647480819-2mqr12c7ecrvhlsincgjmihb69mp4rfr.apps.googleusercontent.com',
    client_secret='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',
    client_kwargs={
        'scope': 'email openid profile',
        'redirect_url': 'http://localhost:8000/auth/callback'
    }
)


templates = Jinja2Templates(directory="templates")

openai_client = OpenAI(api_key="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")

@app.get("/")
def index(request: Request):
    user = request.session.get('user')
    if user:
        return RedirectResponse('welcome')

    return templates.TemplateResponse(
        name="home.html",
        context={"request": request}
    )


@app.get('/auth/welcome')
def welcome(request: Request):
    user = request.session.get('user')
    print(user['picture'])
    if not user:
        return RedirectResponse('/')
    return templates.TemplateResponse(
        name='welcome.html',
        context={'request': request, 'user': user}
    )


@app.get("/login")
async def login(request: Request):
    url = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, url)


@app.get('/auth/callback')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        return templates.TemplateResponse(
            name='error.html',
            context={'request': request, 'error': e.error}
        )
    user = token.get('userinfo')
    if user:
        request.session['user'] = dict(user)
    return RedirectResponse('welcome')


@app.get('/logout')
def logout(request: Request):
    request.session.pop('user')
    return RedirectResponse('/')

@app.get("/generate-image")
async def generate_image(request: Request, prompt: str):
    """
    Receives a prompt from the frontend, sends it to OpenAI's DALL-E,
    and returns the generated image.
    """
    try:
        # Generate an image from the prompt using DALL-E
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        # Extract the image URL from the response
        image_url = response.data[0].url

        if not image_url:
            raise HTTPException(status_code=500, detail="Failed to generate image")

        # Return the image URL
        return {"image_url": image_url}

    except Exception as e:
        print(e)  # Log the full exception
        raise HTTPException(status_code=500, detail=str(e))


