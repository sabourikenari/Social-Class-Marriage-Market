# %%
# import packages and change directory
import pandas as pd
import numpy as np

import os

path_code = "/home/workgroups/socialclass/Social-Class-Marriage-Market"

os.chdir(path_code)

os.getcwd()


# %%
# Use the exec() function to run another Python file
with open('./analysis/A1_2_create_negative_sample.py') as f:
    code = compile(f.read(), './analysis/A1_2_create_negative_sample.py', 'exec')
    exec(code)

# %run ./analysis/A1_2_create_negative_sample.py

for i in all_pairs.columns:
    print(i)

# %%
# all_pairs.to_stata('./data/A1_1_all_pairs.dta', write_index=False)

# %% [markdown]
# # Machine Learning Prediction Model: XGBoost

# %%
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

import xgboost as xgb

import matplotlib.pyplot as plt

# If you haven’t already:
# pip install xgboost scikit-learn


# %%
# === 1) Basic setup

df = all_pairs.copy()

# Label
y = df['match'].astype(int)

# Identify ID columns to avoid leakage (keep them only for grouping, drop from features)
id_cols = [c for c in df.columns if c.lower().startswith('id_spouse')]

# Build a group key so each person (either side) is not split across train/test
# Combine the two sides; fill NAs robustly.
man_id  = df[id_cols[0]] if 'id_spouse_m' in df else df.get('id_spouse', pd.Series(index=df.index, dtype='float'))
woman_id = df[id_cols[1]] if 'id_spouse_w' in df else df.get('id_spouse', pd.Series(index=df.index, dtype='float'))

# Best effort: if both 'id_spouse_m' and 'id_spouse_w' exist, use them; otherwise fall back to 'id_spouse'
man_id   = df.get('id_spouse_m', df.get('id_spouse'))
woman_id = df.get('id_spouse_w', df.get('id_spouse'))

groups = (man_id.astype('Int64').astype(str) + '-' + woman_id.astype('Int64').astype(str)).fillna('NA-NA')

# === 2) Choose feature columns
drop_cols = set(['match']) | set(id_cols)  # drop label and ID columns from features
X = df.drop(columns=list(drop_cols), errors='ignore')


# %%
# id_like = ['parent1','parent2_m','parent11','parent12','parent21_m','parent22_m','t_match_m','t_match_w']
id_like = ['t_match_m','t_match_w','spouse_province_m','spouse_province_w'
           ,'kommun1_m','kommun2_w','kommun12_m','kommun22_w','kommun21_w','kommun11_m'
           ,'parent2_w','parent21_w', 'parent22_w', 'parent1_m','parent11_m','parent12_m']
# id_like =['parent2_w','parent21_w', 'parent22_w','t_match', 'parent1_m','parent11_m','parent12_m']
X = X.drop(columns=id_like, errors='ignore')

for i in X.columns:
    print(i)

# %%
# === 3) Make categoricals work nicely

# XGBoost can handle pandas 'category' dtype directly (enable_categorical=True).
# We'll cast:
#   - object dtype columns
#   - code-like columns that are categorical despite numeric (e.g., lan*, kommun*, cob*)
cat_like_prefixes = ('lan1','lan2','cob1','cob2','educ1','educ2','kommun1','kommun2','lob1','lob2')  # adjust as needed for your schema

categorical_cols = (
    list(X.select_dtypes(include=['object']).columns) +
    [c for c in X.columns
     if c.startswith(cat_like_prefixes) and str(X[c].dtype) not in ('float64','float32','int64','int32')]
)

# Even if numerically typed, force to category for the prefixes (these are province/municipality/etc. codes)
for c in X.columns:
    if c.startswith(cat_like_prefixes):
        X[c] = X[c].astype('category')

for c in categorical_cols:
    X[c] = X[c].astype('category')

# Make sure numeric columns are numeric
# (XGBoost will accept category + numeric together)


# %%
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)



# sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
# train_idx, test_idx = next(sgkf.split(X, y, groups=groups))

# X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
# y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]


# %%
print("Train label counts:", np.bincount(y_train))
print("Test  label counts:", np.bincount(y_test))


# %%
# === 5) Handle class imbalance
neg = (y_train == 0).sum()
pos = (y_train == 1).sum()
scale_pos_weight = neg / max(pos, 1)

print(f"Train positives: {pos:,}, negatives: {neg:,}, scale_pos_weight={scale_pos_weight:.2f}")


# %%


# # Convert to DMatrix (XGBoost's internal format)
# dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=True)
# dvalid = xgb.DMatrix(X_test,  label=y_test,  enable_categorical=True)

# # Model parameters
# params = {
#     "objective": "binary:logistic",
#     "eval_metric": "auc",
#     "tree_method": "hist",
#     "learning_rate": 0.05,
#     "max_depth": 6,
#     "subsample": 0.8,
#     "colsample_bytree": 0.8,
#     "reg_lambda": 1.0,
#     "scale_pos_weight": scale_pos_weight,
#     "random_state": 42
# }

# # Watchlist for early stopping
# watchlist = [(dtrain, "train"), (dvalid, "eval")]

# # Train with early stopping
# booster = xgb.train(
#     params=params,
#     dtrain=dtrain,
#     num_boost_round=2000,
#     evals=watchlist,
#     early_stopping_rounds=100,
#     verbose_eval=50
# )

# # Predict on validation set
# y_pred_proba = booster.predict(dvalid)
# auc = roc_auc_score(y_test, y_pred_proba)
# print(f"Test ROC-AUC: {auc:.4f}")



# %%
exclude_keywords = ("lan", "cob", "lob", "swede")
cols_to_keep = [col for col in X_train.columns if not any(kw in col for kw in exclude_keywords)]
X_train_filtered = X_train[cols_to_keep]

for i in X_train_filtered.columns:
    print(i)


# %%

# -----------------------
# Define feature groups
# -----------------------
exclude_patterns = ("11", "12", "21", "22")
exclude_keywords = ("lan", "cob", "lob", "swede")

feature_groups = {
    "All Features": X_train.columns.tolist(),
    "Without Parental Background": [col for col in X_train.columns if not any(pat in col for pat in exclude_patterns)],
    "Only Parental Background" : [col for col in X_train.columns if any(pat in col for pat in exclude_patterns)],
    "Without Location Features": [col for col in X_train.columns if not any(kw in col for kw in exclude_keywords)],
    "Without Income" : [col for col in X_train.columns if "income" not in col],
    "Without Education" : [col for col in X_train.columns if "educ" not in col],
    "Without Age": [col for col in X_train.columns if "yob" not in col],
    "Only Men": [c for c in X_train.columns if c.endswith('_m')],
    "Only Women": [c for c in X_train.columns if c.endswith('_w')],
}

# -----------------------
# Model parameters
# -----------------------
params = {
    "objective": "binary:logistic",
    "eval_metric": "auc",
    "tree_method": "hist",
    "learning_rate": 0.05,
    "max_depth": 6,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 1.0,
    "scale_pos_weight": scale_pos_weight,
    "random_state": 42
}

# -----------------------
# Train & evaluate function
# -----------------------
def train_and_evaluate(X_train, y_train, X_test, y_test):
    dtrain = xgb.DMatrix(X_train, label=y_train, enable_categorical=True)
    dvalid = xgb.DMatrix(X_test,  label=y_test,  enable_categorical=True)

    booster = xgb.train(
        params=params,
        dtrain=dtrain,
        num_boost_round=4000,
        evals=[(dtrain, "train"), (dvalid, "eval")],
        early_stopping_rounds=100,
        verbose_eval=False
    )

    y_pred_proba = booster.predict(dvalid)
    auc = roc_auc_score(y_test, y_pred_proba)
    return auc

# -----------------------
# Run all models
# -----------------------
results = []

for name, cols in feature_groups.items():
    auc = train_and_evaluate(
        X_train[cols], y_train,
        X_test[cols], y_test
    )
    results.append({"Feature_Set": name, "AUC": auc})
    print(f"{name}: AUC = {auc:.4f}")

# -----------------------
# Results DataFrame
# -----------------------
results_df = pd.DataFrame(results).sort_values("AUC", ascending=False)
print("\nSummary of AUC results:")
print(results_df)




# %%
# -----------------------
# Bar plot with AUC labels
# -----------------------
plt.figure(figsize=(8,5))
bars = plt.barh(results_df["Feature_Set"], results_df["AUC"], color="skyblue")
plt.xlabel("Test Sample Area Under Curve (AUC)")
plt.ylabel("Feature Subset")
plt.title("Prediction Performance")
plt.gca().invert_yaxis()  # highest AUC on top
plt.grid(axis="x", linestyle="--", alpha=0.7)

# Add AUC value labels to each bar
for bar in bars:
    width = bar.get_width()
    plt.text(width + 0.01, bar.get_y() + bar.get_height()/2,
             f"{width:.3f}", va='center', fontsize=10)

# plt.show()

plt.savefig("./results/analysis/A1_1_auc_barplot.pdf", bbox_inches="tight")
plt.show()

# %%

# # --- Plot learning curves ---
# train_auc = evals_result['train']['auc']
# eval_auc  = evals_result['eval']['auc']

# plt.figure(figsize=(8,5))
# plt.plot(train_auc, label='Train AUC')
# plt.plot(eval_auc, label='Validation AUC')
# plt.xlabel('Boosting Round')
# plt.ylabel('AUC')
# plt.title('XGBoost AUC Over Time')
# plt.legend()
# plt.grid(True)
# plt.show()

# # --- Evaluate final test performance ---
# y_pred_proba = booster.predict(dvalid)
# auc = roc_auc_score(y_test, y_pred_proba)
# print(f"Test ROC-AUC: {auc:.4f}")


# %%
# # !pip install shap
# import shap

# # Create TreeExplainer
# explainer = shap.TreeExplainer(booster)

# # Compute SHAP values for validation data
# shap_values = explainer.shap_values(X_test)

# # --- Global summary plot ---
# shap.summary_plot(shap_values, X_test)

# # --- Example individual prediction explanation ---
# shap.force_plot(
#     explainer.expected_value, 
#     shap_values[0, :], 
#     X_test.iloc[0, :]
# )


# %%
# # Convert categorical columns to numeric codes
# X_test_encoded = X_test.copy()
# for col in X_test_encoded.select_dtypes(["category"]).columns:
#     X_test_encoded[col] = X_test_encoded[col].cat.codes

# # Compute SHAP values
# explainer = shap.TreeExplainer(booster)
# shap_values = explainer.shap_values(X_test_encoded)

# # Plot
# shap.summary_plot(shap_values, X_test_encoded)


# %%
# # Get feature importance as a dict
# score_dict = booster.get_score(importance_type="weight")

# # Build DataFrame with all features, filling missing with 0
# importance = pd.DataFrame({
#     "feature": X_train.columns,
#     "importance": [score_dict.get(f, 0) for f in X_train.columns]
# })

# importance = importance.sort_values("importance", ascending=False)
# print(importance.head(35))


# %%
# # Gain
# gain_dict = booster.get_score(importance_type="gain")
# # Cover
# cover_dict = booster.get_score(importance_type="cover")

# cover_dict


