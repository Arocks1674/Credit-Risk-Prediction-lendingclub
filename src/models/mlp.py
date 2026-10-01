"""A small feed-forward neural network (the "ANN") for default probability, in PyTorch.

Two hidden layers with dropout, binary cross-entropy, AdamW, and early stopping on a
time-based validation set, so the number of epochs is chosen on data the model never trains on.
"""
import copy

import numpy as np
import torch
from sklearn.metrics import roc_auc_score
from torch import nn


class MLPClassifier:
    def __init__(self, hidden=(128, 64), dropout=0.2, lr=1e-3, weight_decay=1e-4, batch_size=2048,
                 max_epochs=40, patience=4, seed=42, verbose=True):
        self.hidden, self.dropout, self.lr, self.weight_decay = hidden, dropout, lr, weight_decay
        self.batch_size, self.max_epochs, self.patience = batch_size, max_epochs, patience
        self.seed, self.verbose = seed, verbose
        self.history_ = []

    def _net(self, n_in: int) -> nn.Module:
        layers, d = [], n_in
        for h in self.hidden:
            layers += [nn.Linear(d, h), nn.ReLU(), nn.Dropout(self.dropout)]
            d = h
        layers.append(nn.Linear(d, 1))
        return nn.Sequential(*layers)

    def fit(self, X, y, X_val, y_val):
        torch.manual_seed(self.seed)
        rng = np.random.default_rng(self.seed)
        X = torch.as_tensor(np.asarray(X, dtype=np.float32))
        y = torch.as_tensor(np.asarray(y, dtype=np.float32))
        self.net_ = self._net(X.shape[1])
        opt = torch.optim.AdamW(self.net_.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        loss_fn = nn.BCEWithLogitsLoss()
        best, best_state, bad = -np.inf, None, 0
        for epoch in range(1, self.max_epochs + 1):
            self.net_.train()
            order = rng.permutation(len(X))
            for i in range(0, len(X), self.batch_size):
                idx = order[i:i + self.batch_size]
                opt.zero_grad()
                loss = loss_fn(self.net_(X[idx]).squeeze(1), y[idx])
                loss.backward()
                opt.step()
            auc = roc_auc_score(y_val, self.predict_proba(X_val)[:, 1])
            self.history_.append({"epoch": epoch, "val_auc": auc})
            if self.verbose:
                print(f"  MLP epoch {epoch:2d}  validation AUC {auc:.4f}")
            if auc > best + 1e-4:
                best, best_state, bad = auc, copy.deepcopy(self.net_.state_dict()), 0
            else:
                bad += 1
                if bad >= self.patience:
                    break
        self.net_.load_state_dict(best_state)
        self.best_epoch_ = max(self.history_, key=lambda h: h["val_auc"])["epoch"]
        return self

    @torch.no_grad()
    def predict_proba(self, X) -> np.ndarray:
        self.net_.eval()
        X = torch.as_tensor(np.asarray(X, dtype=np.float32))
        p = torch.cat([torch.sigmoid(self.net_(X[i:i + 65536])).squeeze(1)
                       for i in range(0, len(X), 65536)]).numpy()
        return np.column_stack([1 - p, p])
