"""Test script for the image analysis API."""

import requests
import base64
from PIL import Image
import io

# Create a simple test image
img = Image.new('RGB', (200, 200), color='blue')
buffer = io.BytesIO()
img.save(buffer, format='JPEG')
buffer.seek(0)

# Test 1: Upload endpoint
print("🧪 Testing /api/v1/analyze endpoint...")
files = {'file': ('test.jpg', buffer, 'image/jpeg')}
response = requests.post('http://localhost:8000/api/v1/analyze', files=files)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Upload test passed!")
    print(f"  Analysis ID: {result['analysis_id']}")
    print(f"  Status: {result['status']}")
    print(f"  Processing time: {result['processing_time']:.2f}s")
    if result.get('result'):
        print(f"  Description: {result['result']['description'][:100]}...")
        print(f"  Tags: {result['result']['tags']}")
else:
    print(f"❌ Upload test failed: {response.status_code}")
    print(f"  Error: {response.text}")

# Test 2: Base64 endpoint
print("\n🧪 Testing /api/v1/analyze/base64 endpoint...")
buffer.seek(0)
image_data = base64.b64encode(buffer.read()).decode()

data = {
    "image_data": image_data,
    "prompt": "Describe this image briefly"
}

response = requests.post('http://localhost:8000/api/v1/analyze/base64', json=data)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Base64 test passed!")
    print(f"  Analysis ID: {result['analysis_id']}")
    print(f"  Status: {result['status']}")
else:
    print(f"❌ Base64 test failed: {response.status_code}")
    print(f"  Error: {response.text}")

# Test 3: Process endpoint
print("\n🧪 Testing /api/v1/process endpoint...")
buffer.seek(0)
files = {'file': ('test.jpg', buffer, 'image/jpeg')}
response = requests.post('http://localhost:8000/api/v1/process', files=files)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Process test passed!")
    print(f"  Features: {result['features']}")
else:
    print(f"❌ Process test failed: {response.status_code}")
    print(f"  Error: {response.text}")

print("\n✅ All API tests completed!")
