#!/usr/bin/env python3
"""
Comprehensive crawler with proper category-specific image sources
"""

import os
import sys
import json
import time
import argparse
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveCrawler:
    """Comprehensive crawler with category-specific high-quality images"""
    
    def __init__(self, output_dir: str = "crawl_cache"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Category-specific image sources (high-quality curated)
        self.category_sources = {
            'nature': [
                'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1504700610630-ac6aba3536d3?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1472214103451-9374bd1d04bc?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=1080&h=1920&fit=crop'
            ],
            'space': [
                'https://images.unsplash.com/photo-1446776877081-d282a0f896e2?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1464207687429-7505649dae38?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1444927714506-8492d94b5ba0?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1500472675609-0c4f22a1c7f5?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1464207687429-7505649dae38?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop'
            ],
            'abstract': [
                'https://images.unsplash.com/photo-1542281286-9e0a16bb7366?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1579952363873-27d3bfad9c0d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557672172-298e090bd0f1?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1526374965029-3d4ee85d6a95?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1530543322-592d72ae42d9?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1558618047-3dde7d52540d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1080&h=1920&fit=crop'
            ],
            'minimal': [
                'https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1516110833967-0b5640006de4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1516110833967-0b5640006de4?w=1080&h=1920&fit=crop'
            ],
            'technology': [
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop'
            ],
            'cyberpunk': [
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop'
            ],
            'gaming': [
                'https://images.unsplash.com/photo-1511512578047-dfb367046420?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1542751371-adc38448a05e?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1593305841991-05c297ba4575?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop'
            ],
            'anime': [
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1542281286-9e0a16bb7366?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1579952363873-27d3bfad9c0d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557672172-298e090bd0f1?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1526374965029-3d4ee85d6a95?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1530543322-592d72ae42d9?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1558618047-3dde7d52540d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?w=1080&h=1920&fit=crop'
            ],
            'cars': [
                'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1449426468159-d96dbf08f19f?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1486496572940-2bb2341fdbdf?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1502877338535-766e1452684a?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1547036967-23d11aacaee0?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=1080&h=1920&fit=crop'
            ],
            'sports': [
                'https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1554068865-24cecd4e34b8?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1546519638-68e109498ffc?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1554068865-24cecd4e34b8?w=1080&h=1920&fit=crop'
            ],
            'architecture': [
                'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1486718448742-163732cd1544?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1582407947304-fd86f028f716?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1511818966892-d5d671d18392?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1592069700471-c1b8b63e3c8c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1527359443443-84a48aec73d2?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1496564203457-11bb12075d90?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1513694203232-719a280e022f?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=1080&h=1920&fit=crop'
            ],
            'art': [
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=1080&h=1920&fit=crop'
            ],
            'dark': [
                'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1504700610630-ac6aba3536d3?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1472214103451-9374bd1d04bc?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1504700610630-ac6aba3536d3?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1472214103451-9374bd1d04bc?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=1080&h=1920&fit=crop'
            ],
            'neon': [
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1535378620166-273708d44e4c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=1080&h=1920&fit=crop'
            ],
            'pastel': [
                'https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1516110833967-0b5640006de4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1524484485831-a92ffc0de03f?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1531297484001-80022131f5a1?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1516110833967-0b5640006de4?w=1080&h=1920&fit=crop'
            ],
            'vintage': [
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1504700610630-ac6aba3536d3?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1472214103451-9374bd1d04bc?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1080&h=1920&fit=crop'
            ],
            'gradient': [
                'https://images.unsplash.com/photo-1542281286-9e0a16bb7366?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1579952363873-27d3bfad9c0d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557672172-298e090bd0f1?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1550684848-fac1c5b4e853?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1526374965029-3d4ee85d6a95?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1530543322-592d72ae42d9?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1558618047-3dde7d52540d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1549692520-acc6669e2f0c?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1080&h=1920&fit=crop'
            ],
            'seasonal': [
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1504700610630-ac6aba3536d3?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1472214103451-9374bd1d04bc?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1080&h=1920&fit=crop',
                'https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=1080&h=1920&fit=crop'
            ]
        }
        
        # Image variations for diversity
        self.variations = [
            {}, # base
            {'auto': 'enhance'},
            {'auto': 'compress'},
            {'auto': 'faces'},
            {'fm': 'jpg', 'q': '90'},
            {'fm': 'jpg', 'q': '85'},
            {'fm': 'jpg', 'q': '80'},
            {'fm': 'jpg', 'q': '95'},
            {'crop': 'entropy'},
            {'crop': 'attention'},
            {'crop': 'faces'},
            {'crop': 'entropy', 'auto': 'enhance'},
            {'crop': 'attention', 'auto': 'enhance'},
            {'crop': 'faces', 'auto': 'enhance'},
            {'crop': 'entropy', 'fm': 'jpg', 'q': '90'},
            {'crop': 'attention', 'fm': 'jpg', 'q': '85'},
            {'crop': 'faces', 'fm': 'jpg', 'q': '80'},
            {'crop': 'entropy', 'auto': 'compress'},
            {'crop': 'attention', 'auto': 'compress'},
            {'crop': 'faces', 'auto': 'compress'}
        ]
        
        # Downloaded images tracking
        self.downloaded_hashes: Set[str] = set()
        self.load_existing_hashes()
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WallpaperCollection/1.0 (Comprehensive)'
        })
    
    def load_existing_hashes(self):
        """Load hashes of already downloaded images"""
        hash_file = self.output_dir / 'downloaded_hashes.json'
        if hash_file.exists():
            try:
                with open(hash_file, 'r') as f:
                    self.downloaded_hashes = set(json.load(f))
            except Exception as e:
                logger.warning(f"Could not load existing hashes: {e}")
    
    def save_downloaded_hashes(self):
        """Save downloaded hashes to file"""
        hash_file = self.output_dir / 'downloaded_hashes.json'
        with open(hash_file, 'w') as f:
            json.dump(list(self.downloaded_hashes), f)
    
    def get_image_hash(self, image_data: bytes) -> str:
        """Generate hash for image data"""
        return hashlib.md5(image_data).hexdigest()
    
    def is_duplicate(self, image_data: bytes) -> bool:
        """Check if image is already downloaded"""
        image_hash = self.get_image_hash(image_data)
        return image_hash in self.downloaded_hashes
    
    def generate_image_url(self, base_url: str, variation: Dict) -> str:
        """Generate image URL with variations"""
        if not variation:
            return base_url
        
        # Add variation parameters
        params = []
        for key, value in variation.items():
            params.append(f"{key}={value}")
        
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}{'&'.join(params)}"
    
    def download_image(self, url: str, filename: str, metadata: Dict) -> bool:
        """Download image with duplicate detection"""
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get image data
            image_data = response.content
            
            # Check for duplicates
            if self.is_duplicate(image_data):
                logger.info(f"Duplicate image skipped: {filename}")
                return False
            
            # Save image
            filepath = self.output_dir / filename
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            # Save metadata
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Track hash
            image_hash = self.get_image_hash(image_data)
            self.downloaded_hashes.add(image_hash)
            
            logger.info(f"Downloaded: {filename}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {filename}: {e}")
            return False
    
    def crawl_category(self, category: str, limit: int = 50) -> Dict:
        """Crawl high-quality images for a specific category"""
        logger.info(f"Crawling category: {category}")
        
        if category not in self.category_sources:
            logger.error(f"Category '{category}' not supported")
            return {'success': False, 'error': f"Category '{category}' not supported"}
        
        downloaded = 0
        skipped = 0
        errors = 0
        
        # Get base URLs for this category
        base_urls = self.category_sources[category]
        
        # Generate combinations with variations
        combinations = []
        for base_url in base_urls:
            for variation in self.variations:
                combinations.append((base_url, variation))
        
        # Shuffle for randomness
        random.shuffle(combinations)
        
        # Download images
        for i, (base_url, variation) in enumerate(combinations):
            if downloaded >= limit:
                break
                
            # Generate URL with variation
            url = self.generate_image_url(base_url, variation)
            
            # Create filename
            filename = f"{category}_{downloaded + 1:03d}.jpg"
            
            # Create metadata
            metadata = {
                'id': f"{category}_{downloaded + 1:03d}",
                'source': 'comprehensive_crawler',
                'category': category,
                'title': f'{category.title()} Wallpaper {downloaded + 1}',
                'description': f'High-quality {category} wallpaper from curated sources',
                'width': 1080,
                'height': 1920,
                'tags': self.generate_category_tags(category),
                'download_url': url,
                'source_url': url,
                'variation': variation,
                'crawled_at': datetime.now().isoformat() + 'Z'
            }
            
            # Download image
            if self.download_image(url, filename, metadata):
                downloaded += 1
            else:
                skipped += 1
            
            # Small delay to be respectful
            time.sleep(0.1)
        
        # Save hash tracking
        self.save_downloaded_hashes()
        
        # Generate summary
        summary = {
            'category': category,
            'downloaded': downloaded,
            'skipped': skipped,
            'errors': errors,
            'total_attempted': downloaded + skipped + errors,
            'crawl_time': datetime.now().isoformat() + 'Z'
        }
        
        logger.info(f"Crawl completed for {category}: {downloaded} images")
        return summary
    
    def generate_category_tags(self, category: str) -> List[str]:
        """Generate appropriate tags for category"""
        base_tags = [category, 'wallpaper', 'hd', 'high resolution', 'mobile']
        
        # Category-specific tags
        category_tags = {
            'nature': ['landscape', 'natural', 'outdoor', 'scenic', 'wildlife'],
            'space': ['cosmic', 'universe', 'astronomy', 'galaxy', 'stellar'],
            'abstract': ['geometric', 'modern', 'artistic', 'pattern', 'creative'],
            'minimal': ['clean', 'simple', 'zen', 'monochrome', 'elegant'],
            'technology': ['tech', 'digital', 'futuristic', 'electronic', 'innovation'],
            'cyberpunk': ['neon', 'futuristic', 'digital', 'dystopian', 'sci-fi'],
            'gaming': ['game', 'gamer', 'esports', 'console', 'entertainment'],
            'anime': ['manga', 'japanese', 'animation', 'kawaii', 'otaku'],
            'cars': ['automotive', 'racing', 'speed', 'vehicle', 'transportation'],
            'sports': ['athletic', 'fitness', 'competition', 'action', 'energy']
        }
        
        specific_tags = category_tags.get(category, [])
        return base_tags + specific_tags
    
    def crawl_all_categories_parallel(self, categories: List[str], limit_per_category: int = 50, max_workers: int = 3) -> Dict:
        """Crawl all categories in parallel"""
        logger.info(f"Starting parallel crawl for {len(categories)} categories...")
        
        results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Submit jobs
            future_to_category = {
                executor.submit(self.crawl_category, category, limit_per_category): category
                for category in categories
            }
            
            # Collect results
            for future in as_completed(future_to_category):
                category = future_to_category[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"✅ {category}: {result['downloaded']} downloaded")
                except Exception as e:
                    logger.error(f"❌ {category} failed: {e}")
                    results.append({'category': category, 'downloaded': 0, 'skipped': 0, 'errors': 1, 'total_attempted': 0})
        
        return {
            'total_categories': len(results),
            'total_downloaded': sum(r['downloaded'] for r in results),
            'total_skipped': sum(r['skipped'] for r in results),
            'total_errors': sum(r['errors'] for r in results),
            'category_results': results
        }

def main():
    parser = argparse.ArgumentParser(description='Comprehensive category crawler')
    parser.add_argument('--categories', default='nature,space,abstract,minimal,technology', 
                       help='Comma-separated list of categories')
    parser.add_argument('--limit', type=int, default=50, help='Max images per category')
    parser.add_argument('--workers', type=int, default=3, help='Max parallel workers')
    parser.add_argument('--output', default='crawl_cache', help='Output directory')
    
    args = parser.parse_args()
    
    # Parse categories
    categories = [cat.strip() for cat in args.categories.split(',')]
    
    # Create crawler
    crawler = ComprehensiveCrawler(args.output)
    
    # Crawl all categories
    start_time = time.time()
    results = crawler.crawl_all_categories_parallel(categories, args.limit, args.workers)
    processing_time = time.time() - start_time
    
    # Print results
    print(f"\n🎉 Comprehensive crawl complete!")
    print(f"📊 Total Categories: {results['total_categories']}")
    print(f"✅ Total Downloaded: {results['total_downloaded']}")
    print(f"⏭️  Total Skipped: {results['total_skipped']}")
    print(f"❌ Total Errors: {results['total_errors']}")
    print(f"⏱️  Processing Time: {processing_time:.1f} seconds")
    
    print(f"\n📁 Category Breakdown:")
    for result in results['category_results']:
        print(f"   {result['category']:12} : {result['downloaded']:3d} downloaded")
    
    print(f"\n🔄 Next steps:")
    print(f"1. Review images: python scripts/review_images.py --input {args.output}")
    print(f"2. Process approved: python scripts/process_approved.py")
    print(f"3. Generate indexes: python scripts/generate_index_simple.py --update-all")

if __name__ == "__main__":
    main()