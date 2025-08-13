from __future__ import annotations

import socket
import subprocess
import threading
import time
from ipaddress import IPv4Network, IPv4Address
from typing import Dict, List, Optional, Callable, Set, Tuple
from queue import Queue
import concurrent.futures

try:
    from scapy.all import ARP, Ether, srp, IP, ICMP, sr1  # type: ignore
    SCAPY_AVAILABLE = True
except Exception:
    SCAPY_AVAILABLE = False

try:
    import psutil  # type: ignore
    PSUTIL_AVAILABLE = True
except Exception:
    PSUTIL_AVAILABLE = False


class ScanResult:
    """Results of network scanning."""
    
    def __init__(self, ip: str, is_up: bool, hostname: Optional[str] = None, 
                 open_ports: Optional[List[int]] = None, response_time: Optional[float] = None):
        self.ip = ip
        self.is_up = is_up
        self.hostname = hostname
        self.open_ports = open_ports if open_ports is not None else []
        self.response_time = response_time


class NetworkScanner:
    """Network scanner with light and heavy scanning modes."""
    
    def __init__(self):
        self._running = False
        self._scan_thread: Optional[threading.Thread] = None
        self._result_callback: Optional[Callable[[ScanResult], None]] = None
        self._progress_callback: Optional[Callable[[int, int], None]] = None
        self._completion_callback: Optional[Callable[[], None]] = None
        
        # Scan configuration
        self.ip_range: str = ""
        self.port_range: str = "22,80,443,8080"
        self.scan_mode: str = "light"  # "light" or "heavy"
        self.max_threads: int = 50
        self.timeout: float = 1.0
        
    def set_result_callback(self, callback: Callable[[ScanResult], None]) -> None:
        """Set callback for receiving scan results."""
        self._result_callback = callback
        
    def set_progress_callback(self, callback: Callable[[int, int], None]) -> None:
        """Set callback for progress updates (current, total)."""
        self._progress_callback = callback
        
    def set_completion_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for scan completion."""
        self._completion_callback = callback
    
    def auto_detect_network_range(self, interface: Optional[str] = None) -> str:
        """Automatically detect network range based on interface."""
        if not PSUTIL_AVAILABLE:
            return "192.168.1.0/24"  # Default fallback
            
        try:
            if interface:
                # Use specific interface
                addrs = psutil.net_if_addrs().get(interface, [])
            else:
                # Use first active interface with IPv4
                stats = psutil.net_if_stats()
                addrs = []
                for if_name, st in stats.items():
                    if st.isup and not if_name.startswith(('lo', 'loopback')):
                        if_addrs = psutil.net_if_addrs().get(if_name, [])
                        for addr in if_addrs:
                            if getattr(addr, 'family', None) == socket.AF_INET:
                                addrs = if_addrs
                                break
                        if addrs:
                            break
            
            # Find IPv4 address and netmask
            for addr in addrs:
                if getattr(addr, 'family', None) == socket.AF_INET:
                    ip = addr.address
                    netmask = addr.netmask
                    if ip and netmask and not ip.startswith('127.'):
                        # Calculate network range
                        network = IPv4Network(f"{ip}/{netmask}", strict=False)
                        return str(network)
                        
        except Exception:
            pass
            
        return "192.168.1.0/24"  # Default fallback
    
    def _parse_port_range(self, port_string: str) -> List[int]:
        """Parse port range string like '22,80,443,8080-8090'."""
        ports = []
        if not port_string.strip():
            return [22, 80, 443, 8080]  # Default ports
            
        for part in port_string.split(','):
            part = part.strip()
            if '-' in part:
                try:
                    start, end = map(int, part.split('-', 1))
                    ports.extend(range(start, end + 1))
                except ValueError:
                    pass
            else:
                try:
                    ports.append(int(part))
                except ValueError:
                    pass
        
        return sorted(set(ports))  # Remove duplicates and sort
    
    def _resolve_hostname(self, ip: str) -> Optional[str]:
        """Resolve hostname for IP address."""
        try:
            return socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror):
            return None
    
    def _ping_host(self, ip: str) -> Tuple[bool, Optional[float]]:
        """Ping host to check if it's up."""
        try:
            if SCAPY_AVAILABLE:
                # Use scapy for ICMP ping
                start_time = time.time()
                response = sr1(IP(dst=ip)/ICMP(), timeout=self.timeout, verbose=0)
                if response:
                    response_time = time.time() - start_time
                    return True, response_time
                return False, None
            else:
                # Use system ping as fallback
                import platform
                param = '-n' if platform.system().lower() == 'windows' else '-c'
                command = ['ping', param, '1', '-W', str(int(self.timeout * 1000)), ip]
                result = subprocess.run(command, capture_output=True, timeout=self.timeout + 1)
                return result.returncode == 0, None
        except Exception:
            return False, None
    
    def _arp_scan(self, ip: str) -> Tuple[bool, Optional[float]]:
        """Perform ARP scan to check if host is up."""
        if not SCAPY_AVAILABLE:
            return self._ping_host(ip)
            
        try:
            start_time = time.time()
            arp_request = ARP(pdst=ip)
            broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast / arp_request
            answered_list = srp(arp_request_broadcast, timeout=self.timeout, verbose=0)[0]
            
            if answered_list:
                response_time = time.time() - start_time
                return True, response_time
            return False, None
        except Exception:
            return self._ping_host(ip)  # Fallback to ping
    
    def _scan_port(self, ip: str, port: int) -> bool:
        """Scan single port on host."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def _scan_host_light(self, ip: str) -> ScanResult:
        """Light scan: check if host is up using ARP/ICMP."""
        is_up, response_time = self._arp_scan(ip)
        hostname = None
        
        if is_up:
            hostname = self._resolve_hostname(ip)
            
        return ScanResult(
            ip=ip,
            is_up=is_up,
            hostname=hostname,
            response_time=response_time
        )
    
    def _scan_host_heavy(self, ip: str) -> ScanResult:
        """Heavy scan: check host and scan ports."""
        # First check if host is up
        is_up, response_time = self._arp_scan(ip)
        hostname = None
        open_ports = []
        
        if is_up:
            hostname = self._resolve_hostname(ip)
            
            # Scan ports
            ports_to_scan = self._parse_port_range(self.port_range)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                port_futures = {
                    executor.submit(self._scan_port, ip, port): port 
                    for port in ports_to_scan
                }
                
                for future in concurrent.futures.as_completed(port_futures):
                    if not self._running:  # Check if scan was stopped
                        break
                    port = port_futures[future]
                    try:
                        if future.result():
                            open_ports.append(port)
                    except Exception:
                        pass
            
            open_ports.sort()
            
        return ScanResult(
            ip=ip,
            is_up=is_up,
            hostname=hostname,
            open_ports=open_ports,
            response_time=response_time
        )
    
    def _scan_worker(self, ip_queue: Queue, results_queue: Queue) -> None:
        """Worker thread for scanning hosts."""
        while self._running:
            try:
                ip = ip_queue.get_nowait()
            except:
                break
                
            if self.scan_mode == "light":
                result = self._scan_host_light(ip)
            else:
                result = self._scan_host_heavy(ip)
                
            results_queue.put(result)
            ip_queue.task_done()
    
    def _scan_thread_func(self) -> None:
        """Main scanning thread function."""
        try:
            # Parse IP range
            network = IPv4Network(self.ip_range, strict=False)
            hosts = list(network.hosts())
            
            # Add network and broadcast addresses for small networks
            if network.num_addresses <= 256:
                hosts.insert(0, network.network_address)
                hosts.append(network.broadcast_address)
            
            total_hosts = len(hosts)
            completed = 0
            
            # Create queues
            ip_queue = Queue()
            results_queue = Queue()
            
            # Fill IP queue
            for host in hosts:
                ip_queue.put(str(host))
            
            # Start worker threads
            workers = []
            num_workers = min(self.max_threads, total_hosts)
            
            for _ in range(num_workers):
                worker = threading.Thread(target=self._scan_worker, args=(ip_queue, results_queue))
                worker.daemon = True
                worker.start()
                workers.append(worker)
            
            # Process results
            while completed < total_hosts and self._running:
                try:
                    result = results_queue.get(timeout=0.1)
                    completed += 1
                    
                    if self._result_callback:
                        self._result_callback(result)
                        
                    if self._progress_callback:
                        self._progress_callback(completed, total_hosts)
                        
                except:
                    continue
            
            # Wait for all workers to finish
            for worker in workers:
                worker.join(timeout=1.0)
                
        except Exception as e:
            # Handle errors gracefully
            pass
        finally:
            self._running = False
            if self._completion_callback:
                self._completion_callback()
    
    def start_scan(self) -> bool:
        """Start network scan."""
        if self._running:
            return False
            
        if not self.ip_range:
            return False
            
        self._running = True
        self._scan_thread = threading.Thread(target=self._scan_thread_func)
        self._scan_thread.daemon = True
        self._scan_thread.start()
        return True
    
    def stop_scan(self) -> None:
        """Stop network scan."""
        self._running = False
        if self._scan_thread:
            self._scan_thread.join(timeout=2.0)
            self._scan_thread = None
    
    def is_running(self) -> bool:
        """Check if scan is currently running."""
        return self._running