# 📚 LightRAG Usage Guide - Dual Configuration

## 🚀 Quick Start

### Option 1: Using Ollama (Local Models)
```bash
./run_lightrag.sh ollama
```
- **URL**: http://localhost:9621
- **LLM**: qwen2:latest
- **Embedding**: nomic-embed-text (768 dimensions)
- **Storage**: ./rag_storage_ollama

### Option 2: Using Azure OpenAI
```bash
./run_lightrag.sh azure
```
- **URL**: http://localhost:9622
- **LLM**: gpt-4o
- **Embedding**: text-embedding-3-large (3072 dimensions)
- **Storage**: ./rag_storage_azure

## 📋 Step-by-Step Usage

### 1. Start Your Preferred Configuration
```bash
# For local Ollama models
./run_lightrag.sh ollama

# For Azure OpenAI
./run_lightrag.sh azure
```

### 2. Access the Web UI
- **Ollama**: http://localhost:9621
- **Azure**: http://localhost:9622

### 3. Upload Documents

#### Via Web UI:
1. Click **"Documents"** tab
2. Click **"Upload Document"**
3. Select your file and upload
4. Monitor processing progress

#### Via API:
```bash
# For Ollama (port 9621)
curl -X POST "http://localhost:9621/documents/upload" \
  -F "file=@book.txt"

# For Azure (port 9622)
curl -X POST "http://localhost:9622/documents/upload" \
  -F "file=@book.txt"
```

### 4. Explore the Knowledge Graph
1. Navigate to **"Graph"** tab
2. Interact with the visualization:
   - **Drag** nodes to rearrange
   - **Click** nodes to see connections
   - **Zoom** with mouse wheel
   - **Search** for specific entities

### 5. Query Your Knowledge

#### Query Modes:
- **naive**: Simple keyword search
- **local**: Entity-focused search
- **global**: Concept-based search
- **hybrid**: Combined approach
- **mix**: Best overall (recommended)

#### Example Queries:
```bash
# Ollama API query
curl -X POST "http://localhost:9621/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main themes?",
    "mode": "hybrid"
  }'

# Azure API query
curl -X POST "http://localhost:9622/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main themes?",
    "mode": "hybrid"
  }'
```

## 🔄 Switching Between Configurations

```bash
# Stop current instance
docker compose down

# Start different configuration
./run_lightrag.sh [ollama|azure]
```

## 📊 Comparing Performance

Run the comparison script:
```bash
python3 compare_models.py
```

This will:
- Test both configurations
- Measure response times
- Compare answer quality
- Save results to `comparison_results.json`

## 🛠️ Monitoring and Debugging

### View Logs:
```bash
# Follow logs in real-time
docker logs -f lightrag

# View last 100 lines
docker logs lightrag --tail 100
```

### Check Status:
```bash
# Ollama instance
curl http://localhost:9621/health | jq

# Azure instance
curl http://localhost:9622/health | jq
```

### Monitor Processing:
```bash
./monitor_progress.sh
```

## 💡 Tips and Best Practices

### For Ollama:
- ✅ **Pros**: Free, private, runs locally
- ❌ **Cons**: Slower, requires good hardware
- 💡 **Tip**: Use for development and testing

### For Azure OpenAI:
- ✅ **Pros**: Faster, better quality, GPT-4
- ❌ **Cons**: Costs money, requires internet
- 💡 **Tip**: Use for production and better results

### General Tips:
1. **Document Size**: Start with smaller documents for testing
2. **Query Modes**: Use "mix" mode for best results
3. **Storage**: Each configuration has separate storage
4. **Processing Time**: 
   - Ollama: 5-15 minutes per document
   - Azure: 2-5 minutes per document

## 🔧 Troubleshooting

### Ollama Issues:
```bash
# Check if Ollama is running
ollama list

# Pull required models
ollama pull qwen2:latest
ollama pull nomic-embed-text
```

### Azure Issues:
- Verify API keys in `.env.azure`
- Check endpoint URLs
- Ensure internet connectivity

### Docker Issues:
```bash
# Reset everything
docker compose down -v
docker system prune -a

# Rebuild
docker compose build --no-cache
```

## 📁 File Structure
```
LightRAG/
├── .env.ollama          # Ollama configuration
├── .env.azure           # Azure configuration
├── run_lightrag.sh      # Launcher script
├── compare_models.py    # Performance comparison
├── monitor_progress.sh  # Progress monitor
├── rag_storage_ollama/  # Ollama data
└── rag_storage_azure/   # Azure data
```

## 🎯 Next Steps
1. Upload your documents
2. Explore the knowledge graph
3. Try different query modes
4. Compare both configurations
5. Choose the best one for your needs

Happy exploring! 🚀