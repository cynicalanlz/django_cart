<h1>Installation</h1>
<h2>Step 1</h2>

```
virtualenv -p python3.7 venv
source venv/bin/activate
pip install -r reqs.txt
./manage.py makemigrations
./manage.py migrate
./manage.py createsuperuser
```

<h2>Step 2</h2>
- Login to website, 
- add product quantitites in admin panel 
- navigate to front page.