import pandas as pd

data = {
    "calories": [420, 380, 390],
    "duration": [50, 40, 45]}

DATA_SET_A = pd.DataFrame(data)
    

DATA_SET_B = DATA_SET_A

DATA_SET_C = pd.concat([DATA_SET_A, DATA_SET_B], axis=0)