// Simple test script to check backend connectivity
async function testBackendConnectivity() {
  console.log("Testing backend connectivity...");
  
  try {
    console.log("Testing ping endpoint...");
    const pingResponse = await fetch("http://localhost:8000/api/ping");
    
    if (pingResponse.ok) {
      const pingText = await pingResponse.text();
      console.log(`✅ Ping successful! Response: ${pingText}`);
    } else {
      console.error(`❌ Ping failed with status: ${pingResponse.status}`);
    }
  } catch (error) {
    console.error(`❌ Connection error: ${error.message}`);
  }
}

// Run the test
testBackendConnectivity();
