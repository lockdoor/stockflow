conda

```
conda env list
```

check env stockflow is existed

if not create env stockflow
```
conda create --name stockflow
```

activate
```
conda activate stockflow
```

install package requirement
```
pip install -r requirements.txt
```

run server
```
python3 manage.py runserver 0.0.0.0:8000
```