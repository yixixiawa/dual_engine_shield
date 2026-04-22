#!/usr/bin/env python3
# Test script to verify model unloading

import torch
from api.coding_detect import VulnScanner

print("Starting test...")

# Create scanner
scanner = VulnScanner()

# Check initial memory
if torch.cuda.is_available():
    print(f"Initial GPU memory: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
    print(f"Initial GPU cached: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")
else:
    print("No GPU available")

# Scan a file
print("Scanning file...")
result = scanner.scan_file('D:/anyworkspace/quanzhan/django-backend/testing_data/test.c')
print(f"Scan completed, found {len(result)} vulnerabilities")

# Check memory after scan
if torch.cuda.is_available():
    print(f"GPU memory after scan: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
    print(f"GPU cached after scan: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")

# Cleanup
print("Cleaning up...")
scanner.cleanup()

# Check memory after cleanup
if torch.cuda.is_available():
    print(f"GPU memory after cleanup: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
    print(f"GPU cached after cleanup: {torch.cuda.memory_reserved() / 1024**3:.2f} GB")

print("Test completed!")