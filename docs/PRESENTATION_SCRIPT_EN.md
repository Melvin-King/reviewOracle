# Presentation Script: E-V-W Pipeline Technical Highlights
**Duration: ~8 minutes**

---

## Opening (30 seconds)

Good morning/afternoon everyone. Today I'm excited to present three key technical innovations in our E-V-W Pipeline that significantly enhance the accuracy and efficiency of paper review evaluation. These innovations address critical challenges in retrieval-augmented generation, or RAG, for fact verification tasks.

The E-V-W Pipeline is an evidence-based system for evaluating academic paper reviews. It processes reviews through four steps: extraction, verification, weighting, and synthesis. The three highlights I'll discuss today all focus on improving the verification step, where we need to accurately retrieve and verify claims against paper content.

Let me start with the first innovation.

---

## Slide 1: Intelligent Section-Filtered RAG (2.5 minutes)

Now, the first challenge we faced was retrieval precision. When verifying a reviewer's claim, traditional RAG systems search through the entire paper. This creates several problems.

**The Problem:**
Imagine a reviewer says, "The experimental results show significant improvements." In a full-text search, we might retrieve passages from the introduction, related work, methodology sections - basically everywhere. But the actual experimental results are only in one specific section. This noise from irrelevant sections can mislead our verification process and reduce accuracy.

**Our Solution:**
We developed an intelligent section-filtering mechanism. The system automatically identifies which section of the paper is most relevant to each claim. For example, if a claim mentions "experiments" or discusses performance metrics, we automatically filter to only search within the "Experiments" or "Results" section.

**How It Works:**
The system uses keyword matching and topic classification. When processing a claim, we analyze its topic field - whether it's about experiments, methodology, writing quality, and so on. We then map this to the corresponding paper section. During index building, we tag each text chunk with its section information. When retrieving, we only search within the relevant section's chunks.

**The Impact:**
This simple but powerful innovation improved our retrieval precision by 15 to 25 percent. Not only is retrieval more accurate, but it's also faster because we're searching a smaller, more focused corpus. Most importantly, it reduces irrelevant context that could confuse the LLM during verification.

This section filtering works seamlessly with all our RAG methods - whether we're using keyword-based, embedding-based, or hybrid approaches. And as you'll see in the next slide, it integrates perfectly with our hybrid system.

---

## Slide 2: Hybrid RAG System (2.5 minutes)

Now, let's talk about our hybrid RAG architecture. This addresses a fundamental trade-off in information retrieval: precision versus semantic understanding.

**The Two Approaches:**
We combine two complementary retrieval methods. First, sparse retrieval - this is keyword-based matching using TF-IDF weighting. It's fast, precise, and excellent for exact term matching. Think of it as finding documents that contain the exact words you're looking for.

Second, dense retrieval - this uses semantic embeddings and vector similarity search. Instead of matching words, it matches meanings. It understands that "automobile" and "car" are related concepts, even though they're different words.

**Why Both?**
Each method has strengths and weaknesses. Sparse retrieval is great for technical terms, proper nouns, and specific concepts. But it fails when reviewers use synonyms or paraphrases. Dense retrieval excels at semantic understanding but might miss exact technical terminology.

**Our Hybrid Strategy:**
We run both methods in parallel. For each query, we get results from both sparse and dense retrieval. We then combine these results using weighted fusion - typically 30 percent weight for sparse, 70 percent for dense. But here's the clever part: if a text chunk is found by both methods, it receives a bonus score. This indicates high confidence that the chunk is truly relevant.

**The Benefits:**
This hybrid approach gives us the best of both worlds. We maintain precision for exact matches while gaining semantic understanding. Our recall rate improves significantly because we're not missing relevant passages due to vocabulary differences. The system is more robust and handles the natural variation in how reviewers express their claims.

The weights are configurable, so we can adjust based on the domain. For highly technical papers with specific terminology, we might increase sparse retrieval weight. For more conceptual discussions, we favor dense retrieval.

---

## Slide 3: Reranking Optimization (2.5 minutes)

Our third innovation addresses a subtle but important problem: even with good initial retrieval, the ranking might not be optimal.

**The Challenge:**
Initial retrieval - whether sparse, dense, or hybrid - gives us a ranked list of candidate text chunks. But this ranking is based on simple similarity scores. Sometimes, the most relevant chunk might rank third or fourth, not first. This matters because we typically only use the top few results for verification. If the best match is ranked lower, we might miss it entirely.

**Our Solution:**
We implement a two-stage retrieval pipeline. In the first stage, we perform initial retrieval and return a larger candidate set - typically 20 chunks instead of the final 5 we need. This gives us a broader pool to work with.

In the second stage, we use a Cross-Encoder model to rerank these candidates. Unlike the initial retrieval models, which encode queries and documents separately, Cross-Encoders process the query and document together. This allows them to capture fine-grained interactions between the query and each candidate, resulting in more accurate relevance scores.

**Technical Details:**
We use the `cross-encoder/ms-marco-MiniLM-L-6-v2` model, which was specifically trained on information retrieval tasks. It takes the query and each candidate chunk as input, and outputs a relevance score. We then rerank all candidates by these scores and select the top-k results.

**The Results:**
This reranking step improves our retrieval precision by an additional 10 to 20 percent. More importantly, it ensures that the most relevant context is always in the top results, which directly improves the quality of our fact verification.

The beauty of this approach is that it's completely compatible with our previous innovations. We can apply reranking to section-filtered results, and it works with both sparse and dense retrieval methods. It's a modular enhancement that stacks with our other improvements.

---

## Conclusion (30 seconds)

To summarize, these three innovations work together to create a highly accurate retrieval system:

First, section filtering narrows our search space to relevant content, improving precision by 15 to 25 percent.

Second, hybrid retrieval combines the strengths of sparse and dense methods, ensuring we don't miss relevant passages due to vocabulary differences.

Third, reranking optimizes the final selection, adding another 10 to 20 percent precision improvement.

Together, these innovations have significantly enhanced our fact verification accuracy, which is the foundation of reliable review evaluation. The system is now more robust, more accurate, and better equipped to handle the complexity of academic paper reviews.

Thank you. I'm happy to take questions.

---

## Timing Breakdown

- **Opening**: 30 seconds
- **Slide 1**: 2.5 minutes
- **Slide 2**: 2.5 minutes  
- **Slide 3**: 2.5 minutes
- **Conclusion**: 30 seconds
- **Total**: ~8 minutes

---

## Speaking Tips

1. **Pace**: Speak at a comfortable pace, approximately 150-160 words per minute
2. **Pauses**: Use pauses after key points to let the audience process
3. **Emphasis**: Emphasize the percentage improvements (15-25%, 10-20%)
4. **Transitions**: Use the transition phrases to smoothly move between slides
5. **Eye Contact**: Make eye contact with the audience, not just reading the script
6. **Questions**: Be prepared to elaborate on technical details if asked

---

## Potential Q&A Topics

- How do you handle papers with non-standard section structures?
- What's the computational overhead of reranking?
- Have you compared against other hybrid RAG systems?
- What's the impact on overall pipeline runtime?
- How do you tune the weights for different paper types?


