"""
Unit tests for CIDR allocation and validation in Prisma SASE 5G.
"""
import unittest
from src.cidr import (
    DEFAULT_UE_CIDR_BLOCKS,
    parse_cidr_blocks,
    is_ip_in_cidr,
    get_allocatable_ips,
    get_next_available_ip
)

class TestCIDRModule(unittest.TestCase):
    def test_default_cidr_blocks(self):
        self.assertIn("10.56.0.192/27", DEFAULT_UE_CIDR_BLOCKS)
        self.assertIn("10.56.0.224/27", DEFAULT_UE_CIDR_BLOCKS)

    def test_parse_cidr_blocks(self):
        cidrs = parse_cidr_blocks("10.56.0.192/27, 10.56.0.224/27")
        self.assertEqual(len(cidrs), 2)
        self.assertEqual(str(cidrs[0]), "10.56.0.192/27")
        self.assertEqual(str(cidrs[1]), "10.56.0.224/27")

    def test_is_ip_in_cidr(self):
        cidr_str = "10.56.0.192/27, 10.56.0.224/27"
        # Valid host IPs in 10.56.0.192/27 (193 - 222)
        self.assertTrue(is_ip_in_cidr("10.56.0.193", cidr_str))
        self.assertTrue(is_ip_in_cidr("10.56.0.195", cidr_str))
        self.assertTrue(is_ip_in_cidr("10.56.0.222", cidr_str))
        
        # Valid host IPs in 10.56.0.224/27 (225 - 254)
        self.assertTrue(is_ip_in_cidr("10.56.0.225", cidr_str))
        self.assertTrue(is_ip_in_cidr("10.56.0.250", cidr_str))
        self.assertTrue(is_ip_in_cidr("10.56.0.254", cidr_str))

        # Invalid: network / broadcast addresses
        self.assertFalse(is_ip_in_cidr("10.56.0.192", cidr_str)) # Network address
        self.assertFalse(is_ip_in_cidr("10.56.0.223", cidr_str)) # Broadcast address

        # Invalid: out of range (user tested 10.58.0.195)
        self.assertFalse(is_ip_in_cidr("10.58.0.195", cidr_str))
        self.assertFalse(is_ip_in_cidr("192.168.1.1", cidr_str))
        self.assertFalse(is_ip_in_cidr("invalid-ip", cidr_str))

    def test_get_allocatable_ips(self):
        ips = get_allocatable_ips("10.56.0.192/27", limit=10)
        self.assertEqual(len(ips), 10)
        self.assertEqual(ips[0], "10.56.0.193")
        self.assertEqual(ips[1], "10.56.0.194")
        self.assertEqual(ips[2], "10.56.0.195")

    def test_get_next_available_ip(self):
        cidr_str = "10.56.0.192/27"
        used_ips = {"10.56.0.193", "10.56.0.194"}
        next_ip = get_next_available_ip(cidr_str, used_ips)
        self.assertEqual(next_ip, "10.56.0.195")

if __name__ == "__main__":
    unittest.main()
