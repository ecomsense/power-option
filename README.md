# Developer Manual

A real-time, high-performance option trading terminal built with FastAPI and WebSockets. This application allows for monitoring NIFTY/BANKNIFTY/FINNIFTY option chains, visualizing premium data via TradingView Lightweight Charts, and executing multi-leg strategies with automated order slicing.

## setup the application (creating a virtualenv) 
```text
python -m venv virtualenv_name


```
## get the latest code from github
after activating the virtualenv, run the following command to clone the repository. this will create the power-option inside the virtualenv_name folder.

```text
git clone https://github.com/ecomsense/power-option
```

## 📁 power-option/
```text
.
├── factory/            # Configuration templates
├── data/               # the changing state of the application are stored here
├── requirements.txt    # Python dependencies
└── src/                # Application source code
    ├── static/         # Frontend assets (dashboard.js, style.css)
    └── templates/      # HTML UI (index.html)
    ├── api.py          # Broker API & Order slicing logic
    ├── constants.py    # The singletons needed for the application
    ├── main.py         # FastAPI entry point
    ├── symbols.py      # The trading symbols obtained from broker
    ├── wsocket.py      # WebSocket management

```
## install the project requirements
```text
pip install -r requirements.txt
```


## run the application
change to directory src\ and run it 

```text
python main.py

```
this will create power-option.yml in your virtualenv_name\ directory

fill up the necessary credentials based on the example given inside factory/power-option.yml



