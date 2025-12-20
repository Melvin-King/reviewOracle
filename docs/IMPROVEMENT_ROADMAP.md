# E-V-W 评估栈改进路线图

## 当前系统分析

### 已完成的功能
- ✅ Step 1: 结构化提取（Extraction Agent）
- ✅ Step 2: 事实验证（Verification Agent）
- ✅ Step 3: 偏差计算（Weighting Agent）
- ✅ Step 4: 合成决策（Synthesis Agent）
- ✅ 三种 RAG 实现（Simple, Embedding, Hybrid）

### 当前限制
1. RAG 检索精度仍有提升空间
2. 观点提取可能遗漏或错误分类
3. 验证结果依赖 LLM，可能存在偏差
4. 权重计算相对简单
5. 报告生成较为基础

---

## 改进方向

### 一、RAG 系统优化

#### 1.1 重排序（Reranking）⭐ 高优先级

**问题**：初步检索的结果可能不够精确

**方案**：使用 Cross-Encoder 对检索结果进行重排序

```python
from sentence_transformers import CrossEncoder

class RerankingRAG:
    def __init__(self):
        self.retriever = HybridRAG()  # 初步检索
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    
    def retrieve(self, query, top_k=5):
        # 1. 初步检索（返回更多候选）
        candidates = self.retriever.retrieve_relevant_chunks(query, top_k=20)
        
        # 2. 重排序
        pairs = [[query, chunk] for chunk, _ in candidates]
        scores = self.reranker.predict(pairs)
        
        # 3. 按新分数排序
        reranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return reranked[:top_k]
```

**预期效果**：
- 检索精度提升 10-20%
- 更准确的上下文选择

**实施难度**：中等

---

#### 1.2 查询扩展（Query Expansion）

**问题**：查询可能不够完整，遗漏相关概念

**方案**：使用 LLM 或同义词库扩展查询

```python
def expand_query(self, query: str) -> str:
    """扩展查询，添加同义词和相关概念"""
    # 方法1: 使用 LLM 生成同义词
    prompt = f"Generate synonyms and related terms for: {query}"
    synonyms = self.llm.call(prompt)
    
    # 方法2: 使用 WordNet 等工具
    # synonyms = get_synonyms_from_wordnet(query)
    
    expanded = f"{query} {' '.join(synonyms)}"
    return expanded
```

**预期效果**：
- 召回率提升 15-25%
- 能找到更多相关文本

**实施难度**：低

---

#### 1.3 智能分块策略

**问题**：当前分块可能切断完整句子或概念

**方案**：按论文结构（章节、段落）智能分块

```python
def smart_chunk_text(self, paper_text: str) -> List[Dict]:
    """按论文结构分块，保留元数据"""
    chunks = []
    
    # 识别章节
    sections = self.extract_sections(paper_text)
    
    for section_name, content in sections.items():
        # 按段落分割
        paragraphs = content.split('\n\n')
        
        # 合并小段落，保持语义完整性
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < 500:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'section': section_name,
                        'type': 'paragraph'
                    })
                current_chunk = para + "\n\n"
    
    return chunks
```

**预期效果**：
- 保持语义完整性
- 可以按章节过滤（如只搜索实验部分）

**实施难度**：中等

---

#### 1.4 多轮检索（Multi-turn Retrieval）

**问题**：单次检索可能不够，需要迭代优化

**方案**：基于初步结果进行二次检索

```python
def multi_turn_retrieve(self, query: str, top_k: int = 5):
    """多轮检索"""
    # 第一轮：原始查询
    results1 = self.retrieve(query, top_k=10)
    
    # 从结果中提取关键信息
    key_phrases = self.extract_key_phrases(results1)
    
    # 第二轮：扩展查询
    expanded_query = f"{query} {' '.join(key_phrases)}"
    results2 = self.retrieve(expanded_query, top_k=10)
    
    # 合并和去重
    return self.merge_results(results1, results2, top_k)
```

**预期效果**：
- 更全面的检索覆盖
- 能找到间接相关的文本

**实施难度**：中等

---

### 二、Extraction Agent 优化

#### 2.1 改进观点提取准确性

**问题**：可能遗漏观点或错误分类

**方案**：
1. **多轮提取**：先粗提取，再细化
2. **验证机制**：检查提取的完整性
3. **主题分类优化**：使用更细粒度的主题

```python
def extract_claims_improved(self, review_text: str):
    """改进的提取方法"""
    # 第一轮：粗提取
    rough_claims = self.llm.extract_rough_claims(review_text)
    
    # 第二轮：细化和验证
    refined_claims = []
    for claim in rough_claims:
        # 验证是否完整
        if self.is_complete_claim(claim):
            # 细化分类
            claim['topic'] = self.refine_topic(claim)
            claim['substantiation_type'] = self.refine_substantiation(claim)
            refined_claims.append(claim)
    
    return refined_claims
```

**预期效果**：
- 提取准确率提升 15-20%
- 减少遗漏和错误分类

**实施难度**：中等

---

#### 2.2 细粒度主题分类

**问题**：当前主题分类较粗（5个主题）

**方案**：扩展主题体系

```python
TOPICS = {
    "Novelty": ["novelty", "innovation", "originality"],
    "Experiments": ["experiments", "evaluation", "results", "benchmarks"],
    "Writing": ["writing", "clarity", "presentation", "organization"],
    "Significance": ["significance", "impact", "importance", "contribution"],
    "Reproducibility": ["reproducibility", "code", "implementation", "details"],
    # 新增主题
    "Methodology": ["method", "approach", "algorithm", "technique"],
    "Theoretical": ["theory", "analysis", "proof", "theoretical"],
    "Related Work": ["related work", "literature", "comparison"],
    "Limitations": ["limitations", "weaknesses", "issues"]
}
```

**预期效果**：
- 更精确的主题分类
- 更细粒度的评估

**实施难度**：低

---

#### 2.3 证据类型细化

**问题**：当前只有 3 种证据类型，可能不够精细

**方案**：扩展证据类型分类

```python
SUBSTANTIATION_TYPES = {
    "Specific_Citation": "有具体引用（如论文名、作者、年份）",
    "Specific_Claim": "有具体声明（如方法、数据、结果）",
    "Vague_Reference": "模糊引用（如'某些研究'、'相关工作'）",
    "Vague_Claim": "模糊声明（如'性能好'、'效果不错'）",
    "Personal_Opinion": "个人观点（如'我认为'、'在我看来'）",
    "None": "无证据"
}
```

**预期效果**：
- 更精确的偏差计算
- 更好的权重分配

**实施难度**：低

---

### 三、Verification Agent 优化

#### 3.1 多证据验证

**问题**：当前只使用 top-k 个文本块，可能遗漏关键证据

**方案**：使用多个证据源进行交叉验证

```python
def verify_claim_improved(self, claim: Dict, paper_text: str) -> Dict:
    """改进的验证方法"""
    # 1. 检索多个相关段落（top-10）
    contexts = self.rag.retrieve_relevant_chunks(query, top_k=10)
    
    # 2. 分组验证
    supporting_evidence = []
    contradicting_evidence = []
    
    for context, score in contexts:
        # 对每个段落单独验证
        result = self.verify_against_context(claim, context)
        if result['supports']:
            supporting_evidence.append((context, result['confidence']))
        elif result['contradicts']:
            contradicting_evidence.append((context, result['confidence']))
    
    # 3. 综合判断
    final_result = self.synthesize_evidence(
        supporting_evidence, 
        contradicting_evidence
    )
    
    return final_result
```

**预期效果**：
- 验证准确率提升 10-15%
- 更可靠的验证结果

**实施难度**：高

---

#### 3.2 置信度校准

**问题**：LLM 给出的置信度可能不够准确

**方案**：基于证据数量和质量校准置信度

```python
def calibrate_confidence(self, verification_result: Dict) -> float:
    """校准置信度"""
    base_confidence = verification_result['confidence']
    
    # 因素1: 证据数量
    num_evidence = len(verification_result['supporting_evidence'])
    evidence_bonus = min(0.1, num_evidence * 0.02)
    
    # 因素2: 证据质量（相关性分数）
    avg_evidence_score = np.mean([e[1] for e in verification_result['supporting_evidence']])
    quality_bonus = avg_evidence_score * 0.1
    
    # 因素3: 是否有矛盾证据
    if verification_result['contradicting_evidence']:
        contradiction_penalty = -0.15
    else:
        contradiction_penalty = 0
    
    calibrated = base_confidence + evidence_bonus + quality_bonus + contradiction_penalty
    return max(0.0, min(1.0, calibrated))
```

**预期效果**：
- 置信度更准确
- 更好的决策依据

**实施难度**：中等

---

#### 3.3 处理图表和公式

**问题**：当前只处理文本，无法验证图表、公式相关的观点

**方案**：
1. 提取图表标题和说明
2. 提取公式及其上下文
3. 在验证时考虑这些信息

```python
def extract_non_text_elements(self, paper_text: str) -> Dict:
    """提取非文本元素"""
    elements = {
        'figures': self.extract_figures(paper_text),
        'tables': self.extract_tables(paper_text),
        'equations': self.extract_equations(paper_text)
    }
    return elements

def verify_with_elements(self, claim: Dict, paper_text: str, elements: Dict):
    """考虑非文本元素的验证"""
    # 检查观点是否涉及图表
    if self.mentions_figures(claim):
        # 检索相关图表
        relevant_figures = self.find_relevant_figures(claim, elements['figures'])
        # 验证观点与图表是否一致
        ...
```

**预期效果**：
- 能验证更多类型的观点
- 提高验证覆盖率

**实施难度**：高

---

### 四、Weighting Agent 优化

#### 4.1 多因素权重计算

**问题**：当前只考虑空洞和幻觉，可能不够全面

**方案**：引入更多因素

```python
def calculate_weight_improved(self, reviewer_id: str, claims: List[Dict], 
                             verifications: Dict[str, Dict]) -> float:
    """改进的权重计算"""
    # 因素1: 空洞指数
    hollowness = self.calculate_hollowness(claims)
    
    # 因素2: 幻觉指数
    hallucination = self.calculate_hallucination(claims, verifications)
    
    # 因素3: 观点数量（太少可能不够全面）
    num_claims = len(claims)
    completeness_penalty = 0.1 if num_claims < 5 else 0
    
    # 因素4: 观点多样性（主题分布）
    topics = [c.get('topic') for c in claims]
    topic_diversity = len(set(topics)) / len(topics) if topics else 0
    diversity_bonus = topic_diversity * 0.1
    
    # 因素5: 平均置信度
    avg_confidence = np.mean([
        v.get('confidence', 0.5) 
        for v in verifications.values()
    ])
    confidence_bonus = (avg_confidence - 0.5) * 0.2
    
    # 综合计算
    bias_index = (
        self.alpha * hollowness + 
        self.beta * hallucination +
        completeness_penalty
    )
    
    weight = 1.0 - bias_index + diversity_bonus + confidence_bonus
    return max(0.0, min(1.0, weight))
```

**预期效果**：
- 更全面的权重评估
- 更公平的评审者评价

**实施难度**：中等

---

#### 4.2 动态权重调整

**问题**：不同主题可能需要不同的权重策略

**方案**：根据主题调整权重计算

```python
def calculate_topic_specific_weight(self, reviewer_id: str, topic: str, 
                                   claims: List[Dict], verifications: Dict):
    """主题特定的权重计算"""
    topic_claims = [c for c in claims if c.get('topic') == topic]
    
    # 不同主题的权重策略不同
    if topic == "Novelty":
        # 新颖性更看重证据质量
        weight = self.calculate_weight_with_emphasis(
            topic_claims, verifications, 
            emphasis='evidence_quality'
        )
    elif topic == "Experiments":
        # 实验更看重验证准确性
        weight = self.calculate_weight_with_emphasis(
            topic_claims, verifications,
            emphasis='verification_accuracy'
        )
    else:
        weight = self.calculate_weight(topic_claims, verifications)
    
    return weight
```

**预期效果**：
- 更精细的权重分配
- 考虑不同主题的特点

**实施难度**：中等

---

### 五、Synthesis Agent 优化

#### 5.1 更详细的报告生成

**问题**：当前报告较为基础

**方案**：生成更详细、结构化的报告

```python
def generate_detailed_report(self, paper_id: str, ...) -> str:
    """生成详细报告"""
    report = {
        'executive_summary': self.generate_summary(...),
        'reviewer_analysis': self.analyze_reviewers(...),
        'topic_evaluation': self.evaluate_topics(...),
        'key_claims': self.extract_key_claims(...),
        'contradictions': self.find_contradictions(...),
        'recommendations': self.generate_recommendations(...),
        'appendix': self.generate_appendix(...)
    }
    return self.format_report(report)
```

**预期效果**：
- 更全面的报告
- 更好的决策支持

**实施难度**：中等

---

#### 5.2 可视化支持

**问题**：纯文本报告不够直观

**方案**：添加图表和可视化

```python
def generate_visualizations(self, data: Dict):
    """生成可视化图表"""
    # 1. 评审者权重分布图
    self.plot_reviewer_weights(data['weights'])
    
    # 2. 主题分数雷达图
    self.plot_topic_scores(data['topic_scores'])
    
    # 3. 验证结果分布图
    self.plot_verification_distribution(data['verifications'])
    
    # 4. 时间线（如果有多个版本的评审）
    self.plot_review_timeline(data['reviews'])
```

**预期效果**：
- 更直观的结果展示
- 更好的理解

**实施难度**：低（使用 matplotlib/seaborn）

---

#### 5.3 对比分析

**问题**：无法对比不同论文或不同评审轮次

**方案**：支持对比分析

```python
def compare_papers(self, paper_ids: List[str]) -> str:
    """对比多篇论文"""
    results = {}
    for paper_id in paper_ids:
        results[paper_id] = self.load_all_results(paper_id)
    
    # 生成对比报告
    comparison = {
        'weights_comparison': self.compare_weights(results),
        'topics_comparison': self.compare_topics(results),
        'overall_trends': self.analyze_trends(results)
    }
    
    return self.format_comparison(comparison)
```

**预期效果**：
- 支持批量分析
- 发现模式和趋势

**实施难度**：中等

---

### 六、系统级优化

#### 6.1 错误处理和容错

**问题**：当前错误处理不够完善

**方案**：
1. 添加重试机制
2. 优雅降级
3. 详细的错误日志

```python
@retry(max_attempts=3, backoff=2)
def verify_claim_with_retry(self, claim: Dict, paper_text: str):
    """带重试的验证"""
    try:
        return self.verify_claim(claim, paper_text)
    except LLMError as e:
        # 降级到简单验证
        return self.simple_verify(claim, paper_text)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return self.get_default_result(claim)
```

**实施难度**：低

---

#### 6.2 性能优化

**问题**：处理大量观点时可能较慢

**方案**：
1. **批量处理**：批量调用 LLM
2. **并行处理**：多线程/多进程
3. **缓存机制**：缓存相似查询的结果

```python
def process_claims_parallel(self, claims: List[Dict], paper_text: str):
    """并行处理观点"""
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(self.verify_claim, claim, paper_text)
            for claim in claims
        ]
        verifications = [f.result() for f in futures]
    
    return verifications
```

**预期效果**：
- 处理速度提升 3-4 倍
- 更好的用户体验

**实施难度**：中等

---

#### 6.3 评估指标

**问题**：缺乏系统性能评估指标

**方案**：添加评估指标

```python
class EvaluationMetrics:
    def calculate_metrics(self, results: Dict) -> Dict:
        """计算评估指标"""
        return {
            'extraction_coverage': self.calc_coverage(results),
            'verification_accuracy': self.calc_accuracy(results),
            'weight_correlation': self.calc_correlation(results),
            'report_quality': self.calc_report_quality(results)
        }
```

**实施难度**：中等

---

#### 6.4 可扩展性

**问题**：当前设计可能不够灵活

**方案**：
1. **插件系统**：支持自定义 Agent
2. **配置模板**：不同场景的配置模板
3. **API 接口**：提供 REST API

```python
class PluginSystem:
    def register_agent(self, name: str, agent_class):
        """注册自定义 Agent"""
        self.agents[name] = agent_class
    
    def use_agent(self, name: str, *args, **kwargs):
        """使用注册的 Agent"""
        return self.agents[name](*args, **kwargs)
```

**实施难度**：高

---

## 优先级排序

### 高优先级（立即实施）
1. ⭐ **RAG 重排序**：显著提升检索精度
2. ⭐ **查询扩展**：提高召回率
3. ⭐ **多证据验证**：提高验证准确性
4. ⭐ **错误处理**：提高系统稳定性

### 中优先级（近期实施）
1. 智能分块策略
2. 多因素权重计算
3. 置信度校准
4. 详细报告生成
5. 性能优化（并行处理）

### 低优先级（长期规划）
1. 处理图表和公式
2. 可视化支持
3. 对比分析
4. 插件系统
5. API 接口

---

## 实施建议

### 阶段一：核心优化（1-2周）
- RAG 重排序
- 查询扩展
- 错误处理改进

### 阶段二：功能增强（2-3周）
- 多证据验证
- 多因素权重计算
- 智能分块

### 阶段三：用户体验（1-2周）
- 详细报告生成
- 可视化支持
- 性能优化

### 阶段四：高级功能（长期）
- 图表处理
- 对比分析
- 插件系统

---

## 预期效果

实施这些改进后，预期：
- **检索精度**：提升 20-30%
- **验证准确率**：提升 15-20%
- **权重公平性**：提升 10-15%
- **报告质量**：显著提升
- **系统稳定性**：大幅提升

---

## 总结

改进方向涵盖：
1. **RAG 系统**：重排序、查询扩展、智能分块
2. **Agent 优化**：提取准确性、验证可靠性、权重公平性
3. **报告生成**：更详细、可视化、对比分析
4. **系统级**：错误处理、性能优化、可扩展性

建议优先实施高优先级项目，这些能带来最大的性能提升。

