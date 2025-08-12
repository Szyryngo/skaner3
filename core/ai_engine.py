from __future__ import annotations

from typing import Dict, List, Optional
from collections import deque

import numpy as np

try:
    from sklearn.ensemble import IsolationForest  # type: ignore
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

try:
    from river.anomaly import HalfSpaceTrees  # type: ignore
    RIVER_AVAILABLE = True
except Exception:
    RIVER_AVAILABLE = False

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
        ml_stream_enabled: bool = True,
        stream_z_threshold: float = 2.5,
        combined_threshold: float = 0.7,
    ) -> None:
        self.large_packet_threshold = large_packet_threshold
        self.ml_enabled = ml_enabled and SKLEARN_AVAILABLE
        self.ml_contamination = ml_contamination
        self.ml_refit_interval = max(100, ml_refit_interval)
        self.ml_buffer_size = max(500, ml_buffer_size)
        self.ml_stream_enabled = ml_stream_enabled and RIVER_AVAILABLE
        self.stream_z_threshold = stream_z_threshold
        self.combined_threshold = combined_threshold

        self._buffer: List[np.ndarray] = []
        self._model: Optional[IsolationForest] = None
        self._seen: int = 0
        self._last_reasons: List[str] = []
        self._last_combined_score: Optional[float] = None
        self._last_ml_decision: Optional[float] = None
        # Streaming model state
        self._stream_model: Optional[HalfSpaceTrees] = HalfSpaceTrees() if self.ml_stream_enabled else None
        self._stream_count: int = 0
        self._stream_mean: float = 0.0
        self._stream_m2: float = 0.0
        self._last_stream_score: Optional[float] = None
        self._last_stream_z: Optional[float] = None

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

    def _packet_to_stream_features(self, p: PacketInfo) -> Dict[str, float]:
        return {
            "length": float(p.length),
            "proto": float(self._protocol_to_int(p.protocol)),
            "src_port": float(p.src_port or 0),
            "dst_port": float(p.dst_port or 0),
        }

    def _stream_update_stats(self, value: float) -> None:
        # Welford's online algorithm
        self._stream_count += 1
        delta = value - self._stream_mean
        self._stream_mean += delta / self._stream_count
        delta2 = value - self._stream_mean
        self._stream_m2 += delta * delta2

    def _stream_std(self) -> float:
        if self._stream_count < 2:
            return 0.0
        return float(np.sqrt(self._stream_m2 / (self._stream_count - 1)))

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

        # ML batch (IsolationForest)
        ml_score = None
        is_ml_anomaly = False
        decision = None  # Inicjalizacja zmiennej
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

        # ML streaming (Half-Space Trees)
        stream_score = None
        stream_z = None
        is_stream_anomaly = False
        if self.ml_stream_enabled and self._stream_model is not None:
            try:
                fdict = self._packet_to_stream_features(packet)
                stream_score = float(self._stream_model.score_one(fdict))
                # Z-score na podstawie statystyk z poprzednich próbek
                if self._stream_count >= 30:
                    std = self._stream_std()
                    if std > 1e-9:
                        stream_z = (stream_score - self._stream_mean) / std
                        if stream_z >= self.stream_z_threshold:
                            is_stream_anomaly = True
                            reasons.append("hst_z>=threshold")
                # Ucz się po wygenerowaniu oceny
                self._stream_model = self._stream_model.learn_one(fdict)
                self._stream_update_stats(stream_score)
            except Exception:
                self._stream_model = None

        # Fuzja wyników
        combined_score = heuristic_score
        if ml_score is not None:
            combined_score += min(1.0, ml_score)
        if stream_z is not None and self.stream_z_threshold > 0:
            combined_score += float(max(0.0, min(1.0, stream_z / self.stream_z_threshold)))
        is_anomaly = (combined_score >= self.combined_threshold) or is_ml_anomaly or is_stream_anomaly

        self._last_reasons = reasons
        self._last_combined_score = float(combined_score if combined_score is not None else heuristic_score)
        try:
            self._last_ml_decision = float(decision) if decision is not None else None
        except Exception:
            self._last_ml_decision = None
        self._last_stream_score = stream_score
        self._last_stream_z = stream_z

        return {
            "is_anomaly": bool(is_anomaly),
            "score": round(float(combined_score if combined_score is not None else heuristic_score), 3),
            "reasons": reasons,
            "combined_score": round(float(combined_score if combined_score is not None else heuristic_score), 3),
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
            "river_available": RIVER_AVAILABLE,
            "stream_enabled": self.ml_stream_enabled,
            "stream_threshold_z": self.stream_z_threshold,
            "stream_count": self._stream_count,
            "last_stream_score": self._last_stream_score,
            "last_stream_z": self._last_stream_z,
        }


def get_ai_status():
    """
    Zwraca status AI oraz kluczowe parametry.
    Przykład zwracanych danych można dostosować do realnej implementacji.
    """
    # Przykładowe dane – zamień na realne źródło statusu w swoim projekcie
    status = "Działa"
    aktualny_model = "Model_v1"
    ilosc_watkow = 4
    return {
        "Status AI": status,
        "Model": aktualny_model,
        "Wątki AI": ilosc_watkow
    }
