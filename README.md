
## Installation

To set up this project on your local machine, follow these steps:

Clone the repository:
```bash
git clone https://github.com/lookitsme/smartChaulkidaar.git
```

Open Docker and in the cmd run 
```bash
docker compose up
```

If you dont have docker you can run it as follows:

Install virtualenv using:
```bash
pip install virtualenv
```

Create a virtual environment and activate it:
```bash
virtualenv env
env\Scripts\activate
```

Navigate to the project directory and setup environment:
```bash
cd smartchaukidaar
```
Create .env File: Create a file named .env in the project directory.
```bash
DATABASE_URL = "postgres://USER:PASSWORD@localhost:5432/DB_NAME"
SECRET_KEY = "your_secret_key"
```
NOTE: Make sure to replace YOUR_USER, YOUR_PASSWORD, YOUR_DB_NAME with your actual database credentials. Also, substitute YOUR_SECRET_KEY with your desired secret key.

Install dependencies:
```bash
pip install -r requirements.txt
```

Configure the database settings in settings.py and run migrations:
```bash
python manage.py makemigrations main_app
python manage.py migrate
```

Create a superuser account:
```bash
python manage.py createsuperuser
```
Start the development server:
```bash
python manage.py runserver
```

    
