#!/usr/bin/env python3
"""
Compare LightRAG performance between Ollama and Azure OpenAI
"""
import asyncio
import time
import json
import aiohttp

class LightRAGComparison:
    def __init__(self):
        self.ollama_url = "http://localhost:9621"
        self.azure_url = "http://localhost:9622"
        self.test_queries = [
            "Who are the main characters in the story?",
            "What is the relationship between Scrooge and Bob Cratchit?",
            "What are the key themes in this story?",
            "How does Scrooge transform throughout the story?",
            "What role do the ghosts play in the narrative?"
        ]
        
    async def upload_document(self, base_url: str, file_path: str):
        """Upload document to LightRAG instance"""
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='book.txt')
                
                async with session.post(f"{base_url}/documents/upload", data=data) as resp:
                    return await resp.json()
    
    async def wait_for_processing(self, base_url: str, max_wait: int = 300):
        """Wait for document processing to complete"""
        print(f"⏳ Waiting for processing at {base_url}...")
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < max_wait:
                async with session.get(f"{base_url}/graphs?label=*&max_nodes=10") as resp:
                    data = await resp.json()
                    node_count = len(data.get('nodes', []))
                    if node_count > 0:
                        print(f"✅ Processing complete! Found {node_count} nodes")
                        return True
                await asyncio.sleep(5)
        
        print("⚠️  Processing timeout")
        return False
    
    async def query_rag(self, base_url: str, query: str, mode: str = "hybrid"):
        """Query LightRAG instance"""
        async with aiohttp.ClientSession() as session:
            payload = {"query": query, "mode": mode}
            start_time = time.time()
            
            async with session.post(f"{base_url}/query", json=payload) as resp:
                response_time = time.time() - start_time
                result = await resp.json()
                return {
                    "response": result.get("response", ""),
                    "response_time": response_time
                }
    
    async def compare_configs(self):
        """Run comparison between Ollama and Azure configurations"""
        print("🔬 LightRAG Model Comparison")
        print("=" * 50)
        
        # Test configurations
        configs = [
            {"name": "Ollama", "url": self.ollama_url},
            {"name": "Azure OpenAI", "url": self.azure_url}
        ]
        
        results = {}
        
        for config in configs:
            print(f"\n📊 Testing {config['name']} configuration...")
            config_results = {
                "queries": {},
                "avg_response_time": 0,
                "total_time": 0
            }
            
            # Check if service is running
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{config['url']}/health") as resp:
                        if resp.status != 200:
                            print(f"❌ {config['name']} service not available")
                            continue
            except:
                print(f"❌ Cannot connect to {config['name']} service")
                continue
            
            # Run queries
            total_time = 0
            for query in self.test_queries:
                print(f"\n🔍 Query: {query}")
                result = await self.query_rag(config['url'], query)
                
                print(f"⏱️  Response time: {result['response_time']:.2f}s")
                print(f"📝 Response preview: {result['response'][:150]}...")
                
                config_results["queries"][query] = result
                total_time += result['response_time']
            
            config_results["avg_response_time"] = total_time / len(self.test_queries)
            config_results["total_time"] = total_time
            results[config['name']] = config_results
        
        # Print comparison summary
        print("\n" + "=" * 50)
        print("📈 COMPARISON SUMMARY")
        print("=" * 50)
        
        for config_name, config_results in results.items():
            if config_results["queries"]:
                print(f"\n{config_name}:")
                print(f"  Average response time: {config_results['avg_response_time']:.2f}s")
                print(f"  Total time: {config_results['total_time']:.2f}s")
        
        # Save detailed results
        with open("comparison_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Detailed results saved to comparison_results.json")

async def main():
    comparator = LightRAGComparison()
    
    print("🚀 Starting LightRAG Model Comparison")
    print("Make sure both services are running:")
    print("  - Ollama: ./run_lightrag.sh ollama")
    print("  - Azure: ./run_lightrag.sh azure")
    print("")
    
    await comparator.compare_configs()

if __name__ == "__main__":
    asyncio.run(main())