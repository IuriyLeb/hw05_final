## YaTube 
YaTube is a service for creating posts. Users can leave comments, as well as subscribe to the authors they like.

# Installation

Сlone repository in your local mashine

```bash
git clone https://github.com/IuriyLeb/yatube_final.git
```

Create and activate virualenv

```bash
python -m venv venv
```

```bash
source venv/Scripts/activate
```

Then you need to install requirements

```bash
pip install -r requirements.txt
```

Create and make migrations

```bash
python manage.py makemigrations
```

```bash
python manage.py migrate
```

Run project on your local machine

```bash
python manage.py runserver
```

### About us
Author: [Lebeda Iuriy](https://github.com/IuriyLeb)

This project was done as a part of learning in [Yandex.Practicum](https://practicum.yandex.ru/) courses.

If you have any suggestions/comments, open pull requests or contact me by email.

### Contributing


Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

### License
[MIT](https://choosealicense.com/licenses/mit/)
