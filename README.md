# ms-covid-19-ildc-research
ILDC Research for facing covid-19 disease

To run service and animation:

1. Setup:
```
    git clone https://github.com/ms-covid-19/ms-covid-19-ildc-research.git
    cd ms-covid-19-ildc-research
    pip install -U flask
    pip install -U numpy
    pip install -U pandas
    pip install -U requests
```
2. Run:
```
    cd ms-covid-19-ildc-research\geo-visualizer-service
    python geo-visualizer-service.py
```
And then open https://ms-covid-19.github.io/geo-visualizer/?servicebase=http://localhost:8090
