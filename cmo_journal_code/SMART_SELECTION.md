# Smart Component Selection & Search Strategy

## Date: November 19, 2025

This document describes the smart component selection and search strategy features in CMOv4.

---

## Features

### 1. **Architecture Pattern Recommendations**

Each architecture pattern comes with recommended component sets:

#### **Monolith Architecture**
- **Recommended Components** (5):
  - ✅ Web Frontend
  - ✅ Application Server
  - ✅ Database
  - ✅ Cache
  - ✅ Monitoring

**Use Case**: Simple applications, rapid prototyping, small teams
**Benefits**: Easier deployment, simpler management, lower operational overhead

---

#### **Microservices Architecture**
- **Recommended Components** (8):
  - ✅ Web Frontend
  - ✅ Application Server
  - ✅ Database
  - ✅ Cache
  - ✅ Monitoring
  - ✅ Message Queue
  - ✅ Load Balancer
  - ✅ Object Storage

**Use Case**: Scalable applications, distributed teams, independent deployments
**Benefits**: Better scalability, fault isolation, technology diversity

---

#### **Event-Driven Architecture**
- **Recommended Components** (9):
  - ✅ Web Frontend
  - ✅ Application Server
  - ✅ Database
  - ✅ Cache
  - ✅ Monitoring
  - ✅ Message Queue
  - ✅ Serverless / Lambda
  - ✅ Object Storage
  - ✅ Analytics

**Use Case**: Real-time processing, asynchronous workflows, event streaming
**Benefits**: Loose coupling, high scalability, reactive systems

---

## 2. **Component Selection Intelligence**

### **Required Components** (Marked with *)
These are recommended for most architectures:
- Web Frontend*
- Application Server*
- Database*

### **Optional Components**
User can choose based on specific needs:
- Cache
- Monitoring
- Message Queue
- Object Storage
- Load Balancer
- Backup
- Security / Secrets
- CDN
- Analytics
- Encryption / KMS
- Container Runtime
- Serverless / Lambda

### **Smart Selection Button**
Clicking "✨ Apply recommended components for this pattern" automatically selects the optimal component set for the chosen architecture pattern.

---

## 3. **CSP Search Strategy Configuration**

### **Search Strategies**

#### **Random Sampling**
- **Speed**: ⚡ Fast
- **Coverage**: Medium
- **Best For**: Quick exploration, large solution spaces
- **Description**: Randomly samples the solution space to quickly find diverse solutions
- **Trade-offs**: May miss optimal solutions, but runs quickly

#### **Sequential Search**
- **Speed**: 🐢 Slower
- **Coverage**: High
- **Best For**: Small solution spaces, deterministic results
- **Description**: Systematically explores solutions in a deterministic order
- **Trade-offs**: Thorough but can be slow for large spaces

#### **Adaptive Search** (Default)
- **Speed**: ⚡⚡ Balanced
- **Coverage**: High
- **Best For**: Most use cases, intelligent optimization
- **Description**: Learns from results and adapts search strategy dynamically
- **Trade-offs**: Best balance of speed and quality

---

### **Sample Size Configuration**

Controls how many solutions the CSP explores:

- **100-500**: Very fast, fewer solutions, good for prototyping
- **500-1000**: Balanced, recommended for most cases
- **1000-5000**: Thorough, slower, better quality solutions
- **5000-10000**: Exhaustive, slowest, maximum quality

**Default**: 1000 samples

**Impact on Results**:
- Higher sample size = More solutions explored = Better optimization = Longer runtime
- Lower sample size = Fewer solutions = Faster results = May miss optimal solutions

---

## 4. **Frontend-Backend Integration**

### **Frontend Sends:**
```javascript
{
  "scenario": {
    "architecture": {
      "architecture_pattern": "microservices",
      "components": [...],
      "relationships": [],
      "multi_tenancy": false
    },
    "constraints": {
      "maxBudget": 10000,
      "maxLatency": 150,
      "requiredProviders": ["AWS", "Azure", "GCP"],
      "securityLevel": "medium"
    },
    "config": {
      "search_strategy": "adaptive",    // ← New!
      "sample_size": 1000               // ← New!
    },
    "usage_profile": {...}
  }
}
```

### **Backend Processes:**
1. Extracts `config` from scenario
2. Updates `CSP_CONFIG` with custom search strategy and sample size
3. Runs CSP with configured strategy
4. Returns optimized solutions

---

## 5. **UI/UX Improvements**

### **Visual Indicators**
- 🔵 Blue highlight for required components
- ⭐ Star icon for recommended components
- ✨ Sparkle icon for smart selection button
- 🔍 Search icon for CSP strategy section

### **Contextual Help**
- Each search strategy shows description on selection
- Sample size input shows impact hint
- Component count displays in real-time

### **Smart Defaults**
- Architecture pattern: Microservices
- Search strategy: Adaptive
- Sample size: 1000
- Providers: All three (AWS, Azure, GCP). In the CMOv4 UI these are fixed for the main experiments; custom scripts or API clients may still override `requiredProviders` for alternative studies.

---

## 6. **Usage Flow**

### **Quick Start (Recommended)**
1. Select architecture pattern (e.g., "Microservices")
2. Click "✨ Apply recommended components"
3. Adjust workload profile if needed
4. Keep default search strategy (Adaptive)
5. Click "Run Custom Benchmark"

### **Advanced Configuration**
1. Select architecture pattern
2. Manually select components based on specific needs
3. Choose CSP search strategy:
   - Random for quick exploration
   - Sequential for deterministic results
   - Adaptive for best quality
4. Adjust sample size based on time/quality trade-off
5. Configure workload profile
6. Click "Run Custom Benchmark"

---

## 7. **Best Practices**

### **For Development/Testing**
- Use Random sampling with 500 samples
- Select minimal components
- Run multiple quick benchmarks

### **For Production Planning**
- Use Adaptive search with 2000-5000 samples
- Apply recommended components
- Fine-tune based on specific requirements
- Run with realistic workload profiles

### **For Research/Analysis**
- Use Sequential search with 5000+ samples
- Select all relevant components
- Compare multiple architecture patterns
- Document and analyze trade-offs

---

## 8. **Technical Implementation**

### **Backend CSP Configuration**
The `config` object updates the CSP engine:

```python
# In optimizer.py
if config:
    original_config = CSP_CONFIG.copy()
    CSP_CONFIG.update(config)
    # CSP now uses custom search_strategy and sample_size
```

### **Search Strategy Mapping**
- `random` → Random sampling of solution space
- `sequential` → Ordered enumeration of solutions
- `adaptive` → Heuristic-guided intelligent search

### **Sample Size Impact**
Controls the number of candidate solutions generated before filtering and ranking.

---

## 9. **Performance Considerations**

| Configuration | Solutions Explored | Avg. Runtime | Quality | Use Case |
|--------------|-------------------|--------------|---------|----------|
| Random, 500 | 500 | ~2-5s | Good | Quick tests |
| Adaptive, 1000 | 1000 | ~5-10s | Great | Default |
| Adaptive, 3000 | 3000 | ~15-30s | Excellent | Production |
| Sequential, 5000 | 5000 | ~30-60s | Best | Research |

---

## 10. **Future Enhancements**

- [ ] Auto-detect optimal sample size based on component count
- [ ] Show component dependency graph
- [ ] Validate component compatibility
- [ ] Suggest components based on workload profile
- [ ] Historical optimization patterns
- [ ] Cost prediction before running benchmark
- [ ] Multi-pattern comparison mode

---

## Summary

The smart component selection and search strategy features provide:

✅ **Intelligent Defaults**: Pattern-based component recommendations  
✅ **Flexible Control**: Manual override for specific needs  
✅ **Performance Tuning**: Configurable search strategy and sample size  
✅ **Better UX**: Visual indicators and contextual help  
✅ **Production Ready**: Proper backend integration and validation  

These features make CMOv4 more accessible for beginners while providing advanced control for experts.
