# Association-Rule-Mining-with-SMC

## Data

- Source: [Diabetes Health Indicators Dataset](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset?resource=download)

## Environment Setup

```ps
python -m venv smc

\smc\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Running Example

```
python .\secure-multipaty-computation\apriori.py -M3 -I0
python .\secure-multipaty-computation\apriori.py -M3 -I1
python .\secure-multipaty-computation\apriori.py -M3 -I2
```