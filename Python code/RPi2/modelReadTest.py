from joblib import load
import pandas as pd

modelo = load('modelo_alterno.joblib')


data = {
    'max_x': 0,
    'std_x': 0,
    'rms_x': 0,
    'max_y': 0,
    'std_y': 0,
    'rms_y': 0,
    #'max_z': 0,
    #'std_z': 0,
    #'rms_z': 0,
}

observables = pd.DataFrame(data, index=[0])

#print(modelo.n_iter_)

#print(observables)

pred_ = modelo.predict(observables)
print(f'Prediction: {pred_}')
print((pred_[0]) == 0)
