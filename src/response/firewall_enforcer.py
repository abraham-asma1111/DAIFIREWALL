"""
Firewall Enforcer
Enforces AI decisions using iptables
Blocks, rate-limits, or redirects traffic based on AI predictions

"""

import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import json
import os


class FirewallEnforcer:
    """
    Enforces firewall decisions using iptables
    Requires root/sudo privileges
    """
    
    def __init__(self, log_file="logs/enforcement.log"):
        """Initialize enforcer"""
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Track blocked IPs and their expiry
        self.blocked_ips: Dict[str, datetime] = {}
        self.rate_limited_ips: Dict[str, datetime] = {}
        
        # Initialize iptables chain
        self.init_iptables_chain()
    
    def init_iptables_chain(self):
        """
        Initialize custom iptables chain for AI firewall
        Creates: AIFW_INPUT chain
        """
        try:
            # Create custom chain
            subprocess.run([
                "iptables", "-N", "AIFW_INPUT"
            ], stderr=subprocess.DEVNULL)  # Ignore if exists
            
            # Insert at top of INPUT chain
            subprocess.run([
                "iptables", "-I", "INPUT", "-j", "AIFW_INPUT"
            ], check=False)
            
            self.logger.info("Initialized AIFW_INPUT iptables chain")
            print("✓ iptables chain initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize iptables: {e}")
            print(f"⚠️  Warning: iptables initialization failed")
            print(f"   Run with sudo or check iptables availability")
    
    def enforce(self, decision: str, src_ip: str, dst_ip: str = None, 
                dst_port: int = None, duration_minutes: int = 60):
        """
        Enforce firewall decision
        
        Args:
            decision: ALLOW, BLOCK, RATE_LIMIT, FLAG_MONITOR, HONEYPOT
            src_ip: Source IP address
            dst_ip: Destination IP (optional)
            dst_port: Destination port (optional)
            duration_minutes: How long to enforce (for BLOCK/RATE_LIMIT)
        """
        try:
            if decision == "BLOCK":
                return self.block_ip(src_ip, duration_minutes)
            
            elif decision == "RATE_LIMIT":
                return self.rate_limit_ip(src_ip, duration_minutes)
            
            elif decision == "HONEYPOT":
                return self.redirect_to_honeypot(src_ip, dst_port)
            
            elif decision == "FLAG_MONITOR":
                return self.flag_for_monitoring(src_ip, dst_ip, dst_port)
            
            elif decision == "ALLOW":
                # No action needed - traffic allowed by default
                self.logger.info(f"ALLOW: {src_ip}")
                return {"status": "allowed", "action": "none"}
            
            else:
                self.logger.warning(f"Unknown decision: {decision}")
                return {"status": "error", "message": f"Unknown decision: {decision}"}
        
        except Exception as e:
            self.logger.error(f"Enforcement error: {e}")
            return {"status": "error", "message": str(e)}
    
    def block_ip(self, ip: str, duration_minutes: int = 60):
        """
        Block IP address using iptables
        
        Args:
            ip: IP address to block
            duration_minutes: How long to block
        """
        try:
            # Add block rule
            subprocess.run([
                "iptables", "-I", "AIFW_INPUT",
                "-s", ip,
                "-j", "DROP"
            ], check=True)
            
            # Track expiry
            expiry = datetime.now() + timedelta(minutes=duration_minutes)
            self.blocked_ips[ip] = expiry
            
            self.logger.info(f"BLOCKED: {ip} until {expiry}")
            
            return {
                "status": "blocked",
                "ip": ip,
                "expires_at": expiry.isoformat(),
                "duration_minutes": duration_minutes
            }
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to block {ip}: {e}")
            return {"status": "error", "message": "iptables command failed"}
    
    def unblock_ip(self, ip: str):
        """Remove block rule for IP"""
        try:
            subprocess.run([
                "iptables", "-D", "AIFW_INPUT",
                "-s", ip,
                "-j", "DROP"
            ], check=True)
            
            if ip in self.blocked_ips:
                del self.blocked_ips[ip]
            
            self.logger.info(f"UNBLOCKED: {ip}")
            return {"status": "unblocked", "ip": ip}
        
        except subprocess.CalledProcessError:
            return {"status": "error", "message": "Rule not found"}
    
    def rate_limit_ip(self, ip: str, duration_minutes: int = 60):
        """
        Rate limit IP (max 10 connections per second)
        
        Args:
            ip: IP address
            duration_minutes: How long to rate limit
        """
        try:
            # Create rate limit rule (10/sec with burst of 20)
            subprocess.run([
                "iptables", "-I", "AIFW_INPUT",
                "-s", ip,
                "-m", "limit",
                "--limit", "10/sec",
                "--limit-burst", "20",
                "-j", "ACCEPT"
            ], check=True)
            
            # Drop excess packets
            subprocess.run([
                "iptables", "-A", "AIFW_INPUT",
                "-s", ip,
                "-j", "DROP"
            ], check=True)
            
            expiry = datetime.now() + timedelta(minutes=duration_minutes)
            self.rate_limited_ips[ip] = expiry
            
            self.logger.info(f"RATE_LIMITED: {ip} until {expiry}")
            
            return {
                "status": "rate_limited",
                "ip": ip,
                "rate": "10/sec",
                "expires_at": expiry.isoformat()
            }
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to rate limit {ip}: {e}")
            return {"status": "error", "message": str(e)}
    
    def redirect_to_honeypot(self, ip: str, dst_port: int = None):
        """
        Redirect traffic to honeypot for analysis
        
        Args:
            ip: Source IP
            dst_port: Destination port (optional)
        """
        honeypot_ip = "192.168.100.100"  # Configure your honeypot IP
        honeypot_port = 8080
        
        try:
            # Redirect to honeypot using NAT
            if dst_port:
                subprocess.run([
                    "iptables", "-t", "nat", "-I", "PREROUTING",
                    "-s", ip,
                    "-p", "tcp", "--dport", str(dst_port),
                    "-j", "DNAT",
                    "--to-destination", f"{honeypot_ip}:{honeypot_port}"
                ], check=True)
            else:
                subprocess.run([
                    "iptables", "-t", "nat", "-I", "PREROUTING",
                    "-s", ip,
                    "-j", "DNAT",
                    "--to-destination", honeypot_ip
                ], check=True)
            
            self.logger.warning(f"HONEYPOT: {ip} → {honeypot_ip} (ZERO-DAY SUSPECTED!)")
            
            return {
                "status": "redirected_to_honeypot",
                "ip": ip,
                "honeypot": honeypot_ip,
                "reason": "Zero-day attack suspected"
            }
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to redirect {ip} to honeypot: {e}")
            return {"status": "error", "message": str(e)}
    
    def flag_for_monitoring(self, src_ip: str, dst_ip: str = None, dst_port: int = None):
        """
        Flag traffic for monitoring (log but don't block)
        
        Args:
            src_ip: Source IP
            dst_ip: Destination IP
            dst_port: Destination port
        """
        try:
            # Add logging rule (doesn't block traffic)
            log_prefix = f"AIFW_MONITOR: {src_ip} "
            
            subprocess.run([
                "iptables", "-I", "AIFW_INPUT",
                "-s", src_ip,
                "-j", "LOG",
                "--log-prefix", log_prefix,
                "--log-level", "4"
            ], check=True)
            
            self.logger.info(f"FLAGGED: {src_ip} for monitoring")
            
            return {
                "status": "flagged",
                "ip": src_ip,
                "action": "monitoring_enabled"
            }
        
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to flag {src_ip}: {e}")
            return {"status": "error", "message": str(e)}
    
    def cleanup_expired(self):
        """Remove expired blocks and rate limits"""
        now = datetime.now()
        
        # Unblock expired IPs
        for ip, expiry in list(self.blocked_ips.items()):
            if now >= expiry:
                self.unblock_ip(ip)
        
        # TODO: Remove expired rate limit rules
        # More complex - need to identify specific rules
    
    def get_status(self):
        """Get current enforcement status"""
        return {
            "blocked_ips": len(self.blocked_ips),
            "rate_limited_ips": len(self.rate_limited_ips),
            "blocked_list": list(self.blocked_ips.keys()),
            "rate_limited_list": list(self.rate_limited_ips.keys())
        }
    
    def clear_all_rules(self):
        """Clear all AIFW rules (use with caution!)"""
        try:
            # Flush custom chain
            subprocess.run(["iptables", "-F", "AIFW_INPUT"], check=True)
            
            self.blocked_ips.clear()
            self.rate_limited_ips.clear()
            
            self.logger.info("Cleared all AIFW rules")
            return {"status": "cleared"}
        
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    print("\n" + "="*70)
    print("FIREWALL ENFORCER TEST")
    print("="*70)
    print("\n⚠️  NOTE: Requires root/sudo privileges")
    print("Usage: sudo python src/response/firewall_enforcer.py\n")
    
    # Test enforcement
    enforcer = FirewallEnforcer()
    
    print("\nCurrent status:")
    print(enforcer.get_status())
    
    print("\n" + "="*70)
    print("Test enforcement (change IP to test):")
    print("="*70)
    
    test_ip = "192.168.1.100"  # Change to a test IP
    
    print(f"\n1. Blocking {test_ip}...")
    result = enforcer.block_ip(test_ip, duration_minutes=1)
    print(f"   Result: {result}")
    
    print(f"\n2. Status after block:")
    print(f"   {enforcer.get_status()}")
    
    print(f"\n3. Unblocking {test_ip}...")
    result = enforcer.unblock_ip(test_ip)
    print(f"   Result: {result}")
    
    print("\n✓ Test complete")
    print("Check logs: logs/enforcement.log")
