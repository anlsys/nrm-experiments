#!/usr/bin/env python
# coding: utf-8

import pickle

exec(open("./dev/hnrm-experiments/bandits/experiment.py").read(), globals())


with open("./dict.pkl","rb") as f:
    results = pickle.load(f)

result_df = pd.concat(
    [history_to_dataframe(key, history) for key, history in results.items()]
)

result_df.to_csv("./dev/hnrm-experiments/bandits/internal-control-experiments.csv")


