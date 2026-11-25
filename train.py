"""
train.py — Huấn luyện & đánh giá mô hình phân loại Intent (DUT AI Student Assistant Final).
"""
import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from nlp_utils import norm, preprocess_for_ml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "intent_dataset_final.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "intent_model.joblib")
EVAL_PATH = os.path.join(MODEL_DIR, "evaluation.json")


def build_pipeline() -> Pipeline:
    features = FeatureUnion([
        ("word", TfidfVectorizer(
            ngram_range=(1, 2),
            analyzer="word",
            min_df=1,
            sublinear_tf=True,
        )),
        ("char_wb", TfidfVectorizer(
            ngram_range=(3, 5),
            analyzer="char_wb",
            min_df=1,
            sublinear_tf=True,
        )),
    ])
    return Pipeline([
        ("features", features),
        ("clf", LinearSVC(C=1.0, class_weight="balanced", random_state=42)),
    ])


def main():
    df = pd.read_csv(DATA_PATH).dropna(subset=["Câu hỏi", "Nhãn"])
    X_raw = df["Câu hỏi"].astype(str).tolist()
    y = df["Nhãn"].astype(str).tolist()
    labels = sorted(set(y))

    X_proc = [preprocess_for_ml(q) for q in X_raw]
    X_no_accent = [preprocess_for_ml(norm(q)) for q in X_raw]

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_preds = cross_val_predict(build_pipeline(), X_proc, y, cv=skf)

    cv_preds_no_accent = np.empty(len(y), dtype=object)
    for train_idx, test_idx in skf.split(X_proc, y):
        fold_pipe = build_pipeline()
        fold_pipe.fit([X_proc[i] for i in train_idx], [y[i] for i in train_idx])
        fold_pred = fold_pipe.predict([X_no_accent[i] for i in test_idx])
        for idx, p in zip(test_idx, fold_pred):
            cv_preds_no_accent[idx] = p

    final_pipe = build_pipeline()
    final_pipe.fit(X_proc, y)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(final_pipe, MODEL_PATH)

    cm = confusion_matrix(y, cv_preds, labels=labels)
    report = {
        "version": "Final",
        "evaluation_method": "5-Fold Stratified Cross-Validation",
        "samples": len(df),
        "class_distribution": df["Nhãn"].value_counts().to_dict(),
        "cv_accuracy_accented": round(float(accuracy_score(y, cv_preds)), 4),
        "cv_macro_f1_accented": round(float(f1_score(y, cv_preds, average="macro")), 4),
        "cv_accuracy_no_accent": round(float(accuracy_score(y, cv_preds_no_accent)), 4),
        "cv_macro_f1_no_accent": round(float(f1_score(y, cv_preds_no_accent, average="macro")), 4),
        "labels": labels,
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(
            y, cv_preds, output_dict=True, zero_division=0
        ),
    }

    with open(EVAL_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    summary = {k: v for k, v in report.items() if k not in ("classification_report", "confusion_matrix")}
    print("=== DUT AI FINAL — TRAINING & 5-FOLD CV SUMMARY ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
