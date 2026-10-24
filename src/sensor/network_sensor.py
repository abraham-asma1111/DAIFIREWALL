"""
Network Sensor Agent
Captures live network traffic and extracts features for AI detection
Deployed on customer servers (banks, government, fintech)

"""

import numpy as np
from scapy.all import sniff, IP, TCP, UDP
from collections import defaultdict
import time
import threading
from datetime import datetime


class NetworkSensor:
    """
    Lightweight sensor agent that:
    1. Captures network packets
    2. Extracts 20 flow features
    3. Sends to AI backend for decision
    4. Does NOT capture raw packets (privacy/security)
    """
    
    def __init__(self, interface="eth0", flow_timeout=60):
        """
        Initialize network sensor
        
        Args:
            interface: Network interface to monitor (eth0, wlan0, etc.)
            flow_timeout: Seconds before flow expires
        """
        self.interface = interface
        self.flow_timeout = flow_timeout
        
        # Flow tracking: {(src_ip, dst_ip, src_port, dst_port, protocol): FlowData}
        self.flows = defaultdict(lambda: {
            'start_time': None,
            'packets': [],
            'fwd_packets': 0,
            'bwd_packets': 0,
            'fwd_bytes': 0,
            'bwd_bytes': 0,
            'flags': defaultdict(int),
            'iat': [],
            'last_packet_time': None
        })
        
        self.is_running = False
        self.callback = None
        
    def set_callback(self, callback):
        """
        Set callback function to receive extracted features
        callback(features: np.array, flow_key: tuple)
        """
        self.callback = callback
    
    def extract_flow_key(self, packet):
        """Extract flow identifier from packet"""
        if IP not in packet:
            return None
        
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        
        if TCP in packet:
            src_port = packet[TCP].sport
            dst_port = packet[TCP].dport
            protocol = 6  # TCP
        elif UDP in packet:
            src_port = packet[UDP].sport
            dst_port = packet[UDP].dport
            protocol = 17  # UDP
        else:
            return None
        
        # Canonical flow key (bidirectional)
        if (src_ip, src_port) < (dst_ip, dst_port):
            return (src_ip, dst_ip, src_port, dst_port, protocol)
        else:
            return (dst_ip, src_ip, dst_port, src_port, protocol)
    
    def packet_handler(self, packet):
        """Process each captured packet"""
        flow_key = self.extract_flow_key(packet)
        if not flow_key:
            return
        
        flow = self.flows[flow_key]
        current_time = time.time()
        
        # Initialize flow
        if flow['start_time'] is None:
            flow['start_time'] = current_time
        
        # Determine direction (forward or backward)
        is_forward = (packet[IP].src == flow_key[0])
        
        # Update counters
        packet_len = len(packet)
        if is_forward:
            flow['fwd_packets'] += 1
            flow['fwd_bytes'] += packet_len
        else:
            flow['bwd_packets'] += 1
            flow['bwd_bytes'] += packet_len
        
        # Inter-arrival time
        if flow['last_packet_time'] is not None:
            iat = current_time - flow['last_packet_time']
            flow['iat'].append(iat)
        flow['last_packet_time'] = current_time
        
        # TCP flags
        if TCP in packet:
            tcp_flags = packet[TCP].flags
            if tcp_flags.S:
                flow['flags']['SYN'] += 1
            if tcp_flags.R:
                flow['flags']['RST'] += 1
            if tcp_flags.P:
                flow['flags']['PSH'] += 1
            if tcp_flags.A:
                flow['flags']['ACK'] += 1
            if tcp_flags.F:
                flow['flags']['FIN'] += 1
            if tcp_flags.U:
                flow['flags']['URG'] += 1
        
        # Store packet info
        flow['packets'].append({
            'time': current_time,
            'len': packet_len,
            'direction': 'fwd' if is_forward else 'bwd'
        })
        
        # Check if flow should be processed
        flow_duration = current_time - flow['start_time']
        if flow_duration > self.flow_timeout or flow['fwd_packets'] + flow['bwd_packets'] > 100:
            self.process_flow(flow_key, flow)
            del self.flows[flow_key]
    
    def process_flow(self, flow_key, flow):
        """Extract 20 features from completed flow"""
        if flow['fwd_packets'] == 0 and flow['bwd_packets'] == 0:
            return
        
        # Calculate features
        duration = flow['last_packet_time'] - flow['start_time'] if flow['last_packet_time'] else 0
        
        # Feature extraction (20 features matching CICIDS 2017)
        features = np.zeros(20, dtype=np.float32)
        
        # 1. Flow Duration (milliseconds)
        features[0] = duration * 1000
        
        # 2-3. Total Fwd/Bwd Packets
        features[1] = flow['fwd_packets']
        features[2] = flow['bwd_packets']
        
        # 4-5. Total Length Fwd/Bwd Packets
        features[3] = flow['fwd_bytes']
        features[4] = flow['bwd_bytes']
        
        # 6-7. Flow Bytes/s, Flow Packets/s
        total_packets = flow['fwd_packets'] + flow['bwd_packets']
        total_bytes = flow['fwd_bytes'] + flow['bwd_bytes']
        if duration > 0:
            features[5] = total_bytes / duration
            features[6] = total_packets / duration
        
        # 8-10. Flow IAT (Mean, Std, Max)
        if flow['iat']:
            features[7] = np.mean(flow['iat'])
            features[8] = np.std(flow['iat']) if len(flow['iat']) > 1 else 0
            features[9] = np.max(flow['iat'])
        
        # 11-12. Fwd/Bwd IAT Mean (simplified - using flow IAT)
        features[10] = features[7]  # Approximation
        features[11] = features[7]  # Approximation
        
        # 13-16. Flag Counts
        features[12] = flow['flags']['SYN']
        features[13] = flow['flags']['RST']
        features[14] = flow['flags']['PSH']
        features[15] = flow['flags']['ACK']
        
        # 17. Destination Port
        features[16] = flow_key[3]  # dst_port
        
        # 18-19. Packet Length Mean, Variance
        packet_lens = [p['len'] for p in flow['packets']]
        if packet_lens:
            features[17] = np.mean(packet_lens)
            features[18] = np.var(packet_lens)
        
        # 20. Average Packet Size
        features[19] = total_bytes / total_packets if total_packets > 0 else 0
        
        # Normalize features (0-1 range for model input)
        # NOTE: In production, use pre-fitted scaler from training
        features = self.normalize_features(features)
        
        # Send to callback (AI detection)
        if self.callback:
            self.callback(features, flow_key)
    
    def normalize_features(self, features):
        """
        Normalize features to [0, 1] range
        TODO: Use pre-fitted MinMaxScaler from training
        """
        # Simple normalization for now (replace with proper scaler in production)
        # This is placeholder - actual scaler should be loaded from training
        features_normalized = np.clip(features / np.array([
            1e6,  # Duration
            100, 100,  # Packets
            1e5, 1e5,  # Bytes
            1e6, 1e3,  # Flow rates
            1, 1, 1,  # IAT
            1, 1,  # IAT mean
            10, 10, 10, 100,  # Flags
            65535,  # Port
            1500, 1e6,  # Packet len
            1500  # Avg size
        ]), 0, 1)
        
        return features_normalized.astype(np.float32)
    
    def start(self):
        """Start packet capture"""
        self.is_running = True
        print(f"✓ Network sensor started on interface: {self.interface}")
        print("  Capturing traffic and extracting features...")
        print("  Press Ctrl+C to stop")
        
        try:
            sniff(
                iface=self.interface,
                prn=self.packet_handler,
                store=False,  # Don't store packets (memory efficient)
                stop_filter=lambda x: not self.is_running
            )
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop packet capture"""
        self.is_running = False
        print("\n✓ Network sensor stopped")
        
        # Process remaining flows
        for flow_key, flow in list(self.flows.items()):
            self.process_flow(flow_key, flow)
        
        self.flows.clear()


# Example callback for testing
def example_callback(features, flow_key):
    """Example callback that receives extracted features"""
    src_ip, dst_ip, src_port, dst_port, protocol = flow_key
    protocol_name = "TCP" if protocol == 6 else "UDP"
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Flow detected:")
    print(f"  {src_ip}:{src_port} → {dst_ip}:{dst_port} ({protocol_name})")
    print(f"  Features: {features[:5]}... (showing first 5 of 20)")
    print(f"  Ready for AI detection!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("NETWORK SENSOR TEST")
    print("="*70)
    print("\nNOTE: Requires root/sudo privileges to capture packets")
    print("Usage: sudo python src/sensor/network_sensor.py")
    print()
    
    # Create sensor
    sensor = NetworkSensor(interface="eth0")  # Change to your interface
    sensor.set_callback(example_callback)
    
    # Start capturing
    try:
        sensor.start()
    except PermissionError:
        print("\n❌ ERROR: Packet capture requires root privileges")
        print("Run with: sudo python src/sensor/network_sensor.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Make sure:")
        print("  1. You have root/sudo privileges")
        print("  2. The interface name is correct (eth0, wlan0, etc.)")
        print("  3. Scapy is installed: pip install scapy")
