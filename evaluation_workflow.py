from statistics import mean

import pandas as pd


def precision_at_k(y_true, y_pred, k):
    """
    Relevancy of items in top-k predicted recommendations.
    For cases with no predicted recommendations, precision is automatically 1.
    ! Order un-aware metric.
    """
    if len(y_pred) == 0:
        return 1
    else:
        y_pred_at_k = y_pred[:k]
        tp = 0
        fp = 0
        for pred in y_pred_at_k:
            if pred in y_true:
                tp += 1
            else:
                fp += 1
        precision_at_k = tp / (tp + fp)
        return precision_at_k


def recall_at_k(y_true, y_pred, k):
    """
    Coverage of relevant items in top-k predicted recommendations.
    For cases with no predicted recommendations, recall is automatically 0.
    ! Order un-aware metric.
    """
    if len(y_pred) == 0:
        return 0
    else:
        y_pred_at_k = y_pred[:k]
        tp = 0
        fn = 0
        for true in y_true:
            if true in y_pred_at_k:
                tp += 1
            else:
                fn += 1
        recall_at_k = tp / (tp + fn)
        return recall_at_k


def f1_score_at_k(precision_at_k, recall_at_k):
    """
    F1 score for k predictions.
    ! Order un-aware metric.
    """
    if precision_at_k == 0 and recall_at_k == 0:
        return 0
    else:
        return (2 * precision_at_k * recall_at_k) / (precision_at_k + recall_at_k)


def avg_precision(y_true, y_preds):
    """
    How do ranked predictions compare to ground truth?
    ! Order-aware metric.
    """
    correct_preds = 0
    running_sum = 0
    for k in range(len(y_preds)):
        if y_preds[k] in y_true:
            correct_preds += 1
            running_sum += correct_preds / (k + 1)
    avg_precision = running_sum / len(y_true)
    return avg_precision


class ValidationBook:
    def __init__(self, b_id, recs):
        self.b_id = b_id
        self.recs = recs


def parse_eval_set(filename):
    df_val = pd.read_csv(filename)
    val_books = []
    for index, row in df_val.iterrows():
        b_id = row[0]
        recs = []
        for rec in row[1:]:
            if isinstance(rec, str):
                rec_splitted = rec.split()
                if len(rec_splitted) > 1:
                    recs.extend([int(r) for r in rec_splitted])
                else:
                    recs.append(int(rec))
        if len(recs) > 0:
            val_books.append(ValidationBook(b_id, recs))

    print(
        f"Number of books with recommendations in validation set: {len(val_books)} of {len(df_val)}"
    )
    print(
        f"Average number of recommendations per book in validation set: {round(mean([len(v.recs) for v in val_books]),1)}"
    )

    return val_books


def compute_metrics(val_books, predictions_dict):
    for k in [1, 2, 3, 5, 6, 7]:
        precision_at_k_values = []
        recall_at_k_values = []
        f1_at_k_values = []

        if k == 1:
            avg_precision_values = []

        for vb in val_books:
            p = precision_at_k(vb.recs, predictions_dict[vb.b_id], k)
            r = recall_at_k(vb.recs, predictions_dict[vb.b_id], k)
            f1 = f1_score_at_k(p, r)
            precision_at_k_values.append(p)
            recall_at_k_values.append(r)
            f1_at_k_values.append(f1)

            if k == 1:
                ap = avg_precision(vb.recs, predictions_dict[vb.b_id])
                avg_precision_values.append(ap)

        # compute average across validation set
        p_at_k = round(mean(precision_at_k_values) * 100, 2)
        r_at_k = round(mean(recall_at_k_values) * 100, 2)
        f1_at_k = round(mean(f1_at_k_values) * 100, 2)
        mean_avg_precision = round(mean(avg_precision_values) * 100, 2)

        print(f"Precision@{k}: {p_at_k}%")
        print(f"Recall@{k}: {r_at_k}%")
        print(f"F1-Measure@{k}: {f1_at_k}%")
        print("-------")

    print(f"Mean Average Precision: {mean_avg_precision}%")


def evaluate_recommender(preds_dict, val_set="dmc21_amazon_validation.csv"):
    """Function to call from outside, performs whole evaluation workflow."""
    val_books = parse_eval_set(val_set)
    compute_metrics(val_books, preds_dict)
