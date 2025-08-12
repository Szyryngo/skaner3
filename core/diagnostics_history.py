"""
Moduł zarządzania historią diagnostyki systemu i decyzji AI.
Zapewnia funkcjonalność zapisu, odczytu i zarządzania historią:
- Decyzji AI dotyczących optymalizacji
- Uruchomień aplikacji
- Danych systemowych w czasie

Funkcje:
    DiagnosticsHistory: Klasa zarządzająca historią diagnostyki
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import threading


@dataclass
class AIDecision:
    """Struktura przechowująca pojedynczą decyzję AI."""
    timestamp: float
    decision_type: str
    score: float
    is_anomaly: bool
    reasons: List[str]
    packet_info: Dict[str, Any]
    ml_decision: Optional[float] = None
    stream_score: Optional[float] = None
    stream_z: Optional[float] = None


@dataclass
class SystemSnapshot:
    """Struktura przechowująca snapshot systemu."""
    timestamp: float
    cpu_percent: float
    ram_percent: float
    disk_usage_percent: float
    network_packets_total: int
    ai_anomalies_count: int
    active_connections: int


@dataclass
class SessionInfo:
    """Struktura przechowująca informacje o sesji."""
    session_id: str
    start_time: float
    end_time: Optional[float]
    packets_processed: int
    anomalies_detected: int
    configuration: Dict[str, Any]


class DiagnosticsHistory:
    """Zarządza historią diagnostyki systemu i decyzji AI."""
    
    def __init__(self, history_dir: str = "diagnostics_history", max_history_days: int = 30):
        """
        Inicjalizuje zarządcę historii.
        
        Args:
            history_dir: Katalog do przechowywania plików historii
            max_history_days: Maksymalna liczba dni przechowywania historii
        """
        self.history_dir = history_dir
        self.max_history_days = max_history_days
        self._lock = threading.Lock()
        
        # Utwórz katalog jeśli nie istnieje
        os.makedirs(self.history_dir, exist_ok=True)
        
        # Pliki historii
        self.ai_decisions_file = os.path.join(self.history_dir, "ai_decisions.json")
        self.system_snapshots_file = os.path.join(self.history_dir, "system_snapshots.json")
        self.sessions_file = os.path.join(self.history_dir, "sessions.json")
        
        # Cache w pamięci dla lepszej wydajności
        self._ai_decisions: List[AIDecision] = []
        self._system_snapshots: List[SystemSnapshot] = []
        self._sessions: List[SessionInfo] = []
        
        # Wczytaj istniejącą historię
        self._load_history()
        
        # Wyczyść starą historię
        self._cleanup_old_entries()
    
    def add_ai_decision(self, decision: AIDecision) -> None:
        """Dodaje nową decyzję AI do historii."""
        with self._lock:
            self._ai_decisions.append(decision)
            # Ogranicz rozmiar cache
            if len(self._ai_decisions) > 10000:
                self._ai_decisions = self._ai_decisions[-5000:]
            self._save_ai_decisions()
    
    def add_system_snapshot(self, snapshot: SystemSnapshot) -> None:
        """Dodaje nowy snapshot systemu do historii."""
        with self._lock:
            self._system_snapshots.append(snapshot)
            # Ogranicz rozmiar cache
            if len(self._system_snapshots) > 1000:
                self._system_snapshots = self._system_snapshots[-500:]
            self._save_system_snapshots()
    
    def start_session(self, session_id: str, configuration: Dict[str, Any]) -> None:
        """Rozpoczyna nową sesję diagnostyczną."""
        session = SessionInfo(
            session_id=session_id,
            start_time=time.time(),
            end_time=None,
            packets_processed=0,
            anomalies_detected=0,
            configuration=configuration
        )
        with self._lock:
            self._sessions.append(session)
            self._save_sessions()
    
    def end_session(self, session_id: str, packets_processed: int, anomalies_detected: int) -> None:
        """Kończy sesję diagnostyczną."""
        with self._lock:
            for session in self._sessions:
                if session.session_id == session_id and session.end_time is None:
                    session.end_time = time.time()
                    session.packets_processed = packets_processed
                    session.anomalies_detected = anomalies_detected
                    break
            self._save_sessions()
    
    def get_ai_decisions(self, hours: Optional[int] = None, limit: Optional[int] = None) -> List[AIDecision]:
        """
        Pobiera decyzje AI z określonego okresu.
        
        Args:
            hours: Liczba godzin wstecz (None = wszystkie)
            limit: Maksymalna liczba wyników (None = bez limitu)
        """
        with self._lock:
            decisions = self._ai_decisions.copy()
        
        if hours is not None:
            cutoff_time = time.time() - (hours * 3600)
            decisions = [d for d in decisions if d.timestamp >= cutoff_time]
        
        # Sortuj od najnowszych
        decisions.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit is not None:
            decisions = decisions[:limit]
        
        return decisions
    
    def get_system_snapshots(self, hours: Optional[int] = None) -> List[SystemSnapshot]:
        """Pobiera snapshoty systemu z określonego okresu."""
        with self._lock:
            snapshots = self._system_snapshots.copy()
        
        if hours is not None:
            cutoff_time = time.time() - (hours * 3600)
            snapshots = [s for s in snapshots if s.timestamp >= cutoff_time]
        
        # Sortuj od najnowszych
        snapshots.sort(key=lambda x: x.timestamp, reverse=True)
        
        return snapshots
    
    def get_sessions(self, days: Optional[int] = None) -> List[SessionInfo]:
        """Pobiera informacje o sesjach z określonego okresu."""
        with self._lock:
            sessions = self._sessions.copy()
        
        if days is not None:
            cutoff_time = time.time() - (days * 86400)
            sessions = [s for s in sessions if s.start_time >= cutoff_time]
        
        # Sortuj od najnowszych
        sessions.sort(key=lambda x: x.start_time, reverse=True)
        
        return sessions
    
    def get_summary_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Pobiera statystyki podsumowujące z ostatnich N godzin."""
        cutoff_time = time.time() - (hours * 3600)
        
        # Decyzje AI
        recent_decisions = [d for d in self._ai_decisions if d.timestamp >= cutoff_time]
        anomalies_count = sum(1 for d in recent_decisions if d.is_anomaly)
        
        # Snapshoty systemu
        recent_snapshots = [s for s in self._system_snapshots if s.timestamp >= cutoff_time]
        
        # Oblicz średnie zasoby systemowe
        avg_cpu = 0.0
        avg_ram = 0.0
        avg_disk = 0.0
        if recent_snapshots:
            avg_cpu = sum(s.cpu_percent for s in recent_snapshots) / len(recent_snapshots)
            avg_ram = sum(s.ram_percent for s in recent_snapshots) / len(recent_snapshots)
            avg_disk = sum(s.disk_usage_percent for s in recent_snapshots) / len(recent_snapshots)
        
        # Sesje
        recent_sessions = [s for s in self._sessions if s.start_time >= cutoff_time]
        active_sessions = [s for s in recent_sessions if s.end_time is None]
        
        return {
            "period_hours": hours,
            "ai_decisions_total": len(recent_decisions),
            "anomalies_detected": anomalies_count,
            "anomaly_rate": (anomalies_count / len(recent_decisions)) if recent_decisions else 0.0,
            "avg_cpu_percent": round(avg_cpu, 1),
            "avg_ram_percent": round(avg_ram, 1),
            "avg_disk_percent": round(avg_disk, 1),
            "system_snapshots_count": len(recent_snapshots),
            "sessions_total": len(recent_sessions),
            "active_sessions": len(active_sessions),
            "timestamp": time.time()
        }
    
    def _load_history(self) -> None:
        """Wczytuje historię z plików."""
        # AI decisions
        try:
            if os.path.exists(self.ai_decisions_file):
                with open(self.ai_decisions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._ai_decisions = [AIDecision(**item) for item in data]
        except Exception:
            self._ai_decisions = []
        
        # System snapshots
        try:
            if os.path.exists(self.system_snapshots_file):
                with open(self.system_snapshots_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._system_snapshots = [SystemSnapshot(**item) for item in data]
        except Exception:
            self._system_snapshots = []
        
        # Sessions
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._sessions = [SessionInfo(**item) for item in data]
        except Exception:
            self._sessions = []
    
    def _save_ai_decisions(self) -> None:
        """Zapisuje decyzje AI do pliku."""
        try:
            with open(self.ai_decisions_file, 'w', encoding='utf-8') as f:
                data = [asdict(decision) for decision in self._ai_decisions]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _save_system_snapshots(self) -> None:
        """Zapisuje snapshoty systemu do pliku."""
        try:
            with open(self.system_snapshots_file, 'w', encoding='utf-8') as f:
                data = [asdict(snapshot) for snapshot in self._system_snapshots]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _save_sessions(self) -> None:
        """Zapisuje informacje o sesjach do pliku."""
        try:
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                data = [asdict(session) for session in self._sessions]
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _cleanup_old_entries(self) -> None:
        """Usuwa stare wpisy z historii."""
        cutoff_time = time.time() - (self.max_history_days * 86400)
        
        with self._lock:
            # Wyczyść stare decyzje AI
            self._ai_decisions = [d for d in self._ai_decisions if d.timestamp >= cutoff_time]
            
            # Wyczyść stare snapshoty systemu
            self._system_snapshots = [s for s in self._system_snapshots if s.timestamp >= cutoff_time]
            
            # Wyczyść stare sesje
            self._sessions = [s for s in self._sessions if s.start_time >= cutoff_time]
            
            # Zapisz po wyczyszczeniu
            self._save_ai_decisions()
            self._save_system_snapshots()
            self._save_sessions()