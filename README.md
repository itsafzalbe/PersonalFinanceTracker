# FE_Django

A Django-based frontend project.

## Getting Started

### Prerequisites
- Python 3.8+
- Django 3.2+
- pip

### Installation

1. Clone the repository
```bash
git clone <repository-url>
cd FE_Django
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

### Running the Project

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000/`

## Project Structure

```
FE_Django/
├── manage.py
├── requirements.txt
├── app/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── templates/
└── config/
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```

## Contributing

Submit pull requests or issues as needed.

## License

[Add your license here]