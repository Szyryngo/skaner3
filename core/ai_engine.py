from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

try:
    from sklearn.ensemble import IsolationForest  # type: ignore
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

from .utils import PacketInfo


class AIEngine:
    """Silnik wykrywania anomalii: heurystyka + IsolationForest (opcjonalnie).

    Jeśli ML jest włączony i dostępny sklearn, model jest trenowany okresowo
    na ostatnich N próbkach i wykrywa odchylenia w n-owym wymiarze cech.
    """

    def __init__(
        self,
        *,
        large_packet_threshold: int = 1400,
        ml_enabled: bool = True,
        ml_contamination: float = 0.02,
        ml_refit_interval: int = 500,
        ml_buffer_size: int = 4000,
    ) -> None:
        self.large_packet_threshold = large_packet_threshold
        self.ml_enabled = ml_enabled and SKLEARN_AVAILABLE
        self.ml_contamination = ml_contamination
        self.ml_refit_interval = max(100, ml_refit_interval)
        self.ml_buffer_size = max(500, ml_buffer_size)

        self._buffer: List[np.ndarray] = []
        self._model: Optional[IsolationForest] = None
        self._seen: int = 0
        self._last_reasons: List[str] = []
        self._last_combined_score: Optional[float] = None
        self._last_ml_decision: Optional[float] = None

    # --- Feature engineering ---
    @staticmethod
    def _protocol_to_int(protocol: str) -> int:
        mapping = {"TCP": 1, "UDP": 2, "IP": 3}
        return mapping.get(protocol.upper(), 0)

    def _packet_to_features(self, p: PacketInfo) -> np.ndarray:
        proto = float(self._protocol_to_int(p.protocol))
        dst_port = float(p.dst_port or 0)
        src_port = float(p.src_port or 0)
        length = float(p.length)
        return np.array([length, proto, src_port, dst_port], dtype=np.float64)

    # --- ML lifecycle ---
    def _maybe_refit(self) -> None:
        if not self.ml_enabled:
            return
        if len(self._buffer) < self.ml_refit_interval:
            return
        X = np.vstack(self._buffer[-self.ml_buffer_size :])
        self._model = IsolationForest(
            n_estimators=100,
            contamination=self.ml_contamination,
            random_state=42,
            n_jobs=1,
        )
        self._model.fit(X)

    # --- Public API ---
    def analyze_packet(self, packet: PacketInfo) -> Dict[str, object]:
        reasons: List[str] = []

        # Heurystyka bazowa
        heuristic_score = 0.0
        if packet.length >= self.large_packet_threshold:
            heuristic_score += 0.4
            reasons.append(f"large_length>={self.large_packet_threshold}")
        if packet.dst_port is not None and packet.dst_port in {23, 3389, 1900}:
            heuristic_score += 0.2
            reasons.append("suspicious_dst_port")

        # ML
        ml_score = None
        is_ml_anomaly = False
        if self.ml_enabled:
            feat = self._packet_to_features(packet)
            self._buffer.append(feat)
            if len(self._buffer) > self.ml_buffer_size:
                self._buffer.pop(0)
            self._seen += 1

            if self._model is None or (self._seen % self.ml_refit_interval == 0):
                try:
                    self._maybe_refit()
                except Exception:
                    self._model = None

            if self._model is not None:
                try:
                    # decision_function: dodatnie = normalne, ujemne = anomalie
                    decision = float(self._model.decision_function(feat.reshape(1, -1))[0])
                    ml_score = max(0.0, -decision)  # większy = bardziej anomalny
                    is_ml_anomaly = decision < 0.0
                    if is_ml_anomaly:
                        reasons.append("iforest_decision<0")
                except Exception:
                    self._model = None

        # Fuzja wyników
        combined_score = heuristic_score
        if ml_score is not None:
            combined_score += min(1.0, ml_score)
        is_anomaly = (combined_score >= 0.7) or is_ml_anomaly

        self._last_reasons = reasons
        self._last_combined_score = float(combined_score if combined_score is not None else heuristic_score)
        try:
            self._last_ml_decision = float(decision)  # type: ignore[name-defined]
        except Exception:
            self._last_ml_decision = None

        return {
            "is_anomaly": bool(is_anomaly),
            "score": round(float(combined_score if combined_score is not None else heuristic_score), 3),
            "reasons": reasons,
        }

    def get_status(self) -> Dict[str, object]:
        return {
            "sklearn_available": SKLEARN_AVAILABLE,
            "ml_enabled": self.ml_enabled,
            "contamination": self.ml_contamination,
            "refit_interval": self.ml_refit_interval,
            "buffer_size": self.ml_buffer_size,
            "samples_seen": self._seen,
            "model_ready": self._model is not None,
            "last_score": self._last_combined_score,
            "last_reasons": self._last_reasons,
            "last_ml_decision": self._last_ml_decision,
        }
