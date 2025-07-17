#!/usr/bin/env python3
"""Test script for history API endpoints."""
import asyncio
import httpx
import json

async def test_history_endpoints():
    """Test history API endpoints including chat deletion."""
    base_url = "http://localhost:8000/api/history"
    
    print("=== Testing History API Endpoints ===\n")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test GET /api/history/ - List conversations
            print("1. Testing GET /api/history/ (list conversations)...")
            response = await client.get(f"{base_url}/")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get('conversations', [])
                print(f"   Found {len(conversations)} conversations")
                
                if conversations:
                    # Show first few conversations
                    for i, conv in enumerate(conversations[:3]):
                        print(f"   - {conv.get('thread_id', 'Unknown')} - {conv.get('preview', 'No preview')[:50]}...")
                    
                    # Test deletion with the first conversation
                    test_thread_id = conversations[0].get('thread_id')
                    if test_thread_id:
                        print(f"\n2. Testing DELETE /api/history/{test_thread_id} (delete conversation)...")
                        delete_response = await client.delete(f"{base_url}/{test_thread_id}")
                        print(f"   Status: {delete_response.status_code}")
                        
                        if delete_response.status_code == 204:
                            print("   ✅ Chat deletion successful (204 No Content)")
                            
                            # Verify deletion by listing conversations again
                            print("\n3. Verifying deletion by listing conversations again...")
                            verify_response = await client.get(f"{base_url}/")
                            if verify_response.status_code == 200:
                                verify_data = verify_response.json()
                                new_conversations = verify_data.get('conversations', [])
                                print(f"   Conversations after deletion: {len(new_conversations)}")
                                
                                # Check if the deleted conversation is gone
                                deleted_found = any(conv.get('thread_id') == test_thread_id for conv in new_conversations)
                                if not deleted_found:
                                    print("   ✅ Conversation successfully removed from list")
                                else:
                                    print("   ❌ Conversation still appears in list")
                            else:
                                print(f"   Error verifying deletion: {verify_response.status_code}")
                                
                        elif delete_response.status_code == 404:
                            print("   ⚠️  Conversation not found (404)")
                        else:
                            print(f"   ❌ Deletion failed with status: {delete_response.status_code}")
                            print(f"   Error: {delete_response.text}")
                    else:
                        print("   ⚠️  No thread_id found in conversation data")
                else:
                    print("   No conversations found to test deletion")
            else:
                print(f"   Error: {response.status_code} - {response.text}")
            
            # Test deletion of non-existent conversation
            print(f"\n4. Testing deletion of non-existent conversation...")
            fake_thread_id = "non-existent-thread-id"
            fake_delete_response = await client.delete(f"{base_url}/{fake_thread_id}")
            print(f"   Status: {fake_delete_response.status_code}")
            if fake_delete_response.status_code == 404:
                print("   ✅ Correctly returned 404 for non-existent conversation")
            else:
                print(f"   ⚠️  Unexpected response: {fake_delete_response.text}")
            
            print("\n=== History API Test Complete ===")
            
        except httpx.ConnectError:
            print("❌ Error: Could not connect to the server.")
            print("   Make sure the backend is running on http://localhost:8000")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_history_endpoints())